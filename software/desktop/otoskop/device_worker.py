"""USB operations run in an isolated process, independent of the GUI console."""

import io
import json
from pathlib import Path
import re
import sys

from .firmware_bundle import InstallError, confirm_port, install_firmware, load_bundle


class EventStream(io.TextIOBase):
    def __init__(self, emit):
        self.emit = emit
        self.buffer = ""
        self.base, self.span, self.progress = 0, 0, -1

    def write(self, value):
        self.buffer += str(value)
        while "\n" in self.buffer or "\r" in self.buffer:
            match = re.search(r"[\r\n]", self.buffer)
            line, self.buffer = self.buffer[:match.start()], self.buffer[match.end():]
            line = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", line).strip()
            if line:
                self.emit(dict(event="log", text=line[:2000]))
            percent = re.search(r"([0-9]+(?:\.[0-9]+)?)%", line)
            if percent and self.span:
                progress = min(80, int(self.base + self.span * float(percent[1]) / 100))
                if progress > self.progress:
                    self.progress = progress
                    self.emit(dict(event="progress", progress=progress))
        if len(self.buffer) > 4096:
            self.buffer = self.buffer[-4096:]
        return len(value)

    def flush(self):
        pass


def run_job(job_path):
    path = Path(job_path).resolve()
    # This file is in the GUI's private temporary job directory. No reliance on
    # stdout: a windowed Windows/PyInstaller app can have sys.stdout == None.
    with (path.parent / "events.jsonl").open("w", encoding="utf-8", buffering=1) as events:
        def raw(event):
            events.write(json.dumps(event, ensure_ascii=True) + "\n")

        sink = EventStream(raw)

        def emit(event):
            if event.get("stage") == "write":
                sink.base, sink.span = event.get("base", 15), event.get("span", 0)
            elif event.get("event") == "stage":
                sink.span = 0
            raw(event)

        sys.stdout, sys.stderr = sink, sink
        try:
            job = json.loads(path.read_text())
            bundle = load_bundle()
            import esptool
            from esptool.logger import log
            log.set_verbosity("verbose")
            if esptool.__version__ != "5.1.0":
                raise InstallError("bundle", "Unexpected esptool version")
            if job.get("action") == "self-test":
                from esptool.loader import StubFlasher
                from esptool.targets.esp32s3 import ESP32S3ROM
                stub = StubFlasher(ESP32S3ROM)
                raw(dict(event="done", result=dict(firmware_version=bundle.manifest["version"],
                                                     esptool_version=esptool.__version__, stub_bytes=len(stub.text))))
            elif job.get("action") == "install":
                selected = confirm_port(job["selected"])
                install_firmware(bundle, selected, emit)
            else:
                raise InstallError("bundle", "Invalid worker operation")
            return 0
        except InstallError as exc:
            raw(dict(event="error", code=exc.code, detail=exc.detail))
        except Exception as exc:
            raw(dict(event="error", code="internal", detail=str(exc)))
        return 1
