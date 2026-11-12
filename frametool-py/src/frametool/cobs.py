"""Consistent Overhead Byte Stuffing: removes 0x00 so it can delimit frames on the wire."""


class CobsError(ValueError):
    pass


def encode(src: bytes | bytearray | memoryview) -> bytes:
    out = bytearray(b"\x00")  # placeholder for the first code byte
    code_index, code = 0, 1
    for b in src:
        if b == 0:
            out[code_index] = code
            code_index, code = len(out), 1
            out.append(0)
            continue
        out.append(b)
        code += 1
        if code == 0xFF:
            out[code_index] = code
            code_index, code = len(out), 1
            out.append(0)
    out[code_index] = code
    return bytes(out)


def decode(src: bytes | bytearray | memoryview) -> bytes:
    out = bytearray()
    i, n = 0, len(src)
    while i < n:
        code = src[i]
        i += 1
        if code == 0 or i + code - 1 > n:
            raise CobsError(f"bad code byte {code:#04x} at offset {i - 1}")
        out += src[i : i + code - 1]
        i += code - 1
        if code < 0xFF and i < n:
            out.append(0)
    return bytes(out)
