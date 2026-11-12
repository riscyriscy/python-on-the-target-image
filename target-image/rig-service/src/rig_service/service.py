"""A service for systemd (Type=notify): READY=1 at start, WATCHDOG=1 while work() progresses."""

from __future__ import annotations

import os
import socket
import threading
import time
from collections.abc import Callable


def notify(message: str) -> None:
    """sd_notify without libsystemd: one datagram to the socket named in NOTIFY_SOCKET."""
    path = os.environ.get("NOTIFY_SOCKET")
    if not path:
        return  # not started by systemd: do nothing
    if path.startswith("@"):
        path = "\0" + path[1:]  # an abstract socket
    with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as sock:
        sock.sendto(message.encode(), path)


def watchdog_interval() -> float | None:
    usec = os.environ.get("WATCHDOG_USEC")
    # systemd advises pinging at half the timeout
    return int(usec) / 1_000_000 / 2 if usec else None


def run(work: Callable[[], None], stop: threading.Event, max_stall_s: float = 1.0) -> None:
    """Call work() in a loop. A second thread pings the watchdog while work() keeps returning."""
    progress = time.monotonic()
    lock = threading.Lock()

    def pinger() -> None:
        interval = watchdog_interval()
        while interval is not None and not stop.wait(interval):
            with lock:
                stalled = time.monotonic() - progress > max_stall_s
            if not stalled:
                notify("WATCHDOG=1")

    notify("READY=1")
    threading.Thread(target=pinger, daemon=True).start()
    while not stop.is_set():
        work()  # a read, a query or a write: whatever shows that the service is alive
        with lock:
            progress = time.monotonic()
    notify("STOPPING=1")
