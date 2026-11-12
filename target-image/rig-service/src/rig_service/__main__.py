"""rig-service: count frames, report to systemd, stop on SIGTERM."""

import argparse
import signal
import threading
from collections.abc import Sequence
from types import FrameType

from frametool.crc16 import crc16

from rig_service.service import run


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rig-service")
    parser.add_argument("--interval", type=float, default=0.5, help="seconds between frames")
    parser.add_argument("--report", type=int, default=20, help="print one line per this many frames")
    args = parser.parse_args(argv)

    stop = threading.Event()

    def on_signal(_signum: int, _frame: FrameType | None) -> None:
        stop.set()

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)

    count = 0

    def work() -> None:
        nonlocal count
        count += 1
        if count % args.report == 0:
            print(f"frames {count} crc16 {crc16(count.to_bytes(4, 'big')):#06x}", flush=True)
        stop.wait(args.interval)

    run(work, stop)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
