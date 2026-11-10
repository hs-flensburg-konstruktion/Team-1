"""Dispatch a bundled USB worker before importing or creating any GUI."""
import sys


def run():
    if len(sys.argv) == 3 and sys.argv[1] == "--device-worker":
        from .device_worker import run_job
        return run_job(sys.argv[2])
    from .app import main
    return main()
