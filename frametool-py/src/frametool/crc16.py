"""CRC-16/CCITT-FALSE, pure Python. Must match native/crc16.c bit for bit."""

from collections.abc import Buffer, Callable

CHECK_VALUE = 0x29B1  # CRC of b"123456789"


def _build_table() -> tuple[int, ...]:
    table = []
    for i in range(256):
        crc = i << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF  # Python ints never overflow: mask explicitly, as uint16_t would
        table.append(crc)
    return tuple(table)


_TABLE = _build_table()


def crc16_py(data: Buffer) -> int:
    crc = 0xFFFF
    # The raw bytes of any contiguous buffer, as the C code reads them: a memoryview of an
    # array('h') would otherwise iterate over 16-bit items
    octets = data if isinstance(data, (bytes, bytearray)) else memoryview(data).cast("B")
    for b in octets:  # iterating bytes yields ints 0..255
        crc = ((crc << 8) & 0xFFFF) ^ _TABLE[(crc >> 8) ^ b]
    return crc


crc16_native: Callable[[Buffer], int] | None
try:
    # C extension built by CMake via scikit-build-core (same crc16.c as the firmware)
    from frametool._crc16 import crc16 as crc16_native
except ImportError:  # pure-Python install or source checkout without a build
    crc16_native = None

crc16: Callable[[Buffer], int] = crc16_native or crc16_py
