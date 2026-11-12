import os
from array import array

import pytest

from frametool.crc16 import CHECK_VALUE, crc16_native, crc16_py


def test_pure_python_check_value() -> None:
    assert crc16_py(b"123456789") == CHECK_VALUE


@pytest.mark.skipif(crc16_native is None, reason="C extension not built")
def test_native_matches_pure_python() -> None:
    assert crc16_native is not None
    assert crc16_native(b"123456789") == CHECK_VALUE
    for size in (0, 1, 255, 4096):
        data = os.urandom(size)
        assert crc16_native(data) == crc16_py(data)


@pytest.mark.skipif(crc16_native is None, reason="C extension not built")
def test_native_accepts_any_bytes_like_but_not_str() -> None:
    assert crc16_native is not None
    assert crc16_native(bytearray(b"123456789")) == CHECK_VALUE
    assert crc16_native(memoryview(b"xx123456789")[2:]) == CHECK_VALUE
    with pytest.raises(TypeError):
        crc16_native("123456789")  # type: ignore[arg-type]


@pytest.mark.skipif(crc16_native is None, reason="C extension not built")
def test_both_paths_read_the_raw_bytes_of_any_buffer() -> None:
    assert crc16_native is not None
    items = array("h", [1, 2, 3])  # 6 bytes, and iterating gives 3 ints
    assert crc16_py(items) == crc16_native(items) == crc16_py(items.tobytes())
    strided = memoryview(b"123456789")[::2]  # not contiguous: neither path can read it
    with pytest.raises(TypeError):
        crc16_py(strided)
    with pytest.raises(BufferError):
        crc16_native(strided)
