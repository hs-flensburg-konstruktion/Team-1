"""Nonblocking Qt process supervisor for the offline firmware installer."""

import json
from pathlib import Path
import sys
import tempfile

from PySide6.QtCore import QObject, QProcess, QTimer, Signal


class FlashProcess(QObject):
    event = Signal(dict)
    succeeded = Signal(dict)
    failed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.finished.connect(self._finished)
        self.process.errorOccurred.connect(self._process_error)
        self.poll = QTimer(self)
        self.poll.setInterval(80)
        self.poll.timeout.connect(self._read_events)
        self.deadline = QTimer(self)
        self.deadline.setSingleShot(True)
        self.deadline.setInterval(240000)
        self.deadline.timeout.connect(self._timeout)
        self.busy = False
        self.job_dir = None
        self.terminal = False
        self.offset = 0
        self.pending = b""

    def start(self, selected, action="install"):
        if self.busy:
            return
        self.job_dir = tempfile.TemporaryDirectory(prefix="otoskop-flash-")
        job = Path(self.job_dir.name) / "job.json"
        job.write_text(json.dumps(dict(action=action, selected=selected)))
        self.offset, self.pending, self.terminal = 0, b"", False
        self.busy = True
        args = ["--device-worker", str(job)]
        if not getattr(sys, "frozen", False):
            args.insert(0, str(Path(__file__).resolve().parent.parent / "main.py"))
        self.process.start(sys.executable, args)
        self.poll.start()
        self.deadline.start()

    def _read_events(self):
        if self.job_dir is None:
            return
        path = Path(self.job_dir.name) / "events.jsonl"
        try:
            with path.open("rb") as file:
                file.seek(self.offset)
                data = file.read(65536)
                self.offset += len(data)
        except OSError:
            return
        self.pending += data
        while b"\n" in self.pending:
            line, self.pending = self.pending.split(b"\n", 1)
            try:
                event = json.loads(line)
            except (ValueError, UnicodeError):
                continue
            if not isinstance(event, dict):
                continue
            self.event.emit(event)
            if event.get("event") == "done":
                self.terminal = True
                self.result = event["result"]
            elif event.get("event") == "error":
                self.terminal = True
                self.error = (event.get("code", "internal"), event.get("detail", ""))
        if len(self.pending) > 65536:
            self.pending = b""

    def _finished(self, exit_code, _status):
        if not self.busy:
            return
        while True:
            before = self.offset
            self._read_events()
            if self.offset == before:
                break
        self.poll.stop()
        self.deadline.stop()
        self.busy = False
        if self.terminal and hasattr(self, "result") and exit_code == 0:
            self.succeeded.emit(self.result)
        else:
            code, detail = getattr(self, "error", ("internal", f"Worker exit {exit_code}"))
            self.failed.emit(code, detail)
        for attr in ("result", "error"):
            if hasattr(self, attr):
                delattr(self, attr)
        self.job_dir.cleanup()
        self.job_dir = None

    def _process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart and self.busy:
            self.error = ("internal", self.process.errorString())
            self._finished(-1, QProcess.ExitStatus.CrashExit)

    def _timeout(self):
        self.error = ("timeout", "USB installer exceeded its time limit")
        self.process.kill()
