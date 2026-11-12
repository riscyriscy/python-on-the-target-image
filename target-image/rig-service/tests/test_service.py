import contextlib
import os
import socket
import threading
import time
from pathlib import Path

import pytest

from rig_service import service as rig_service


def listen(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> socket.socket:
    path = str(tmp_path / "notify.sock")
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(path)
    server.settimeout(0.05)
    monkeypatch.setenv("NOTIFY_SOCKET", path)
    monkeypatch.setenv("WATCHDOG_USEC", "400000")  # WatchdogSec=0.4: pings every 0.2 s
    return server


def collect(server: socket.socket, seconds: float) -> list[str]:
    messages, end = [], time.monotonic() + seconds
    while time.monotonic() < end:
        with contextlib.suppress(TimeoutError):
            messages.append(server.recv(64).decode())
    return messages


def test_ready_then_pings_while_work_returns(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = listen(tmp_path, monkeypatch)
    stop = threading.Event()
    thread = threading.Thread(target=rig_service.run, args=(lambda: time.sleep(0.01), stop))
    thread.start()
    messages = collect(server, 1.1)
    stop.set()
    thread.join()
    assert messages[0] == "READY=1"
    assert messages.count("WATCHDOG=1") >= 4  # about five pings in 1.1 s


def test_no_pings_once_work_hangs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    server = listen(tmp_path, monkeypatch)
    stop, hang = threading.Event(), threading.Event()
    calls = []

    def work() -> None:
        calls.append(1)
        if len(calls) > 20:
            hang.wait(5)  # the stuck call: a read that never returns
        time.sleep(0.01)

    thread = threading.Thread(target=rig_service.run, args=(work, stop, 0.3))
    thread.start()
    first = collect(server, 0.6).count("WATCHDOG=1")  # work() is returning
    late = collect(server, 1.0).count("WATCHDOG=1")  # work() has been stuck for more than 0.3 s
    stop.set()
    hang.set()
    thread.join()
    assert first >= 2
    assert late <= 1  # at most the ping that was already due when the stall started


def test_silent_outside_systemd(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    rig_service.notify("READY=1")  # no socket named: nothing is sent and nothing is raised
    assert os.environ.get("NOTIFY_SOCKET") is None
