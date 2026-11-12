import asyncio

import pytest

from frametool import device
from frametool.link import FrameSplitter, read_frames


def stream(n: int) -> bytes:
    return b"".join(device.make_frame(i, i * 100, corrupt=(i % 7 == 6)) for i in range(n))


def test_splitter_counts_good_and_corrupt_frames() -> None:
    splitter = FrameSplitter()
    frames = list(splitter.feed(stream(14)))
    assert [f.seq for f in frames] == [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]
    assert (splitter.stats.good, splitter.stats.bad_crc) == (12, 2)


def test_splitter_handles_arbitrary_chunking() -> None:
    data, splitter = stream(14), FrameSplitter()
    frames = [f for i in range(0, len(data), 3) for f in splitter.feed(data[i : i + 3])]
    assert len(frames) == 12


def test_resyncs_after_garbage() -> None:
    splitter = FrameSplitter()
    frames = list(splitter.feed(b"\x7f" * 1000 + b"\x00" + stream(3)))
    assert len(frames) == 3 and splitter.stats.malformed >= 1


def test_over_pyserial_loopback() -> None:
    serial = pytest.importorskip("serial")
    port = serial.serial_for_url("loop://", timeout=0.2)  # a real pyserial port object, no hardware
    port.write(stream(7))
    frames = list(FrameSplitter().feed(port.read(4096)))
    port.close()
    assert len(frames) == 6


def test_asyncio_stream_reader() -> None:
    async def run() -> int:
        reader = asyncio.StreamReader()
        reader.feed_data(stream(7))
        reader.feed_eof()
        return len([f async for f in read_frames(reader, FrameSplitter())])

    assert asyncio.run(run()) == 6
