"""Time three CRC-16 routines on a 15-byte frame and a 1 MiB image: the pure-Python one in
frametool, the standard library's binascii.crc_hqx, and the C extension.

The frametool functions come from the package, so the script runs from an environment where
frametool is installed with its extension. It checks that all three agree before it times them.
Run: python bench/crc_bench.py
"""

import binascii
import sys
import timeit
from collections.abc import Callable

from frametool.crc16 import crc16_native, crc16_py

REPEAT = 5  # the best of 5 runs is reported, because noise only ever adds time


def best_seconds(fn: Callable[[bytes], int], data: bytes, number: int) -> float:
    return min(timeit.repeat(lambda: fn(data), number=number, repeat=REPEAT)) / number


def main() -> None:
    if crc16_native is None:
        sys.exit("the C extension is not installed in this environment")
    frame = bytes(range(15))
    image = bytes(i * 31 & 0xFF for i in range(1 << 20))
    # binascii.crc_hqx is CRC-16/CCITT-FALSE when it starts from 0xFFFF, the same CRC as frametool
    candidates: list[tuple[str, Callable[[bytes], int]]] = [
        ("pure Python (table driven)", crc16_py),
        ("binascii.crc_hqx (standard library)", lambda d: binascii.crc_hqx(d, 0xFFFF)),
        ("C extension (bitwise C loop)", crc16_native),
    ]
    for data in (frame, image):
        assert len({fn(data) for _, fn in candidates}) == 1
    print(f"python {sys.version.split()[0]}, best of {REPEAT} runs")
    for label, data, number in (("15-byte frame", frame, 100_000), ("1 MiB image", image, 20)):
        unit, scale = ("us", 1e6) if len(data) < 100 else ("ms", 1e3)
        print(f"  {label}")
        base = 0.0
        for name, fn in candidates:
            seconds = best_seconds(fn, data, number)
            base = base or seconds
            print(f"    {name:37s} {seconds * scale:8.2f} {unit}   {base / seconds:5.1f} times")


if __name__ == "__main__":
    main()
