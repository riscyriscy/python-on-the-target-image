"""Byte stream in, validated frames out: the 'driver task' of the host tool."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterable, Iterator
from dataclasses import dataclass

from frametool import cobs
from frametool.protocol import BadCrcError, Frame, FrameError

MAX_ENCODED = 300  # longest legal COBS-encoded frame plus margin


@dataclass(slots=True)
class LinkStats:
    good: int = 0
    bad_crc: int = 0
    malformed: int = 0


class FrameSplitter:
    """Accumulates bytes and yields decoded frames at each 0x00 delimiter.

    Pure logic with no I/O, so the same class serves asyncio, threads, pyserial and tests.
    """

    def __init__(self, stats: LinkStats | None = None) -> None:
        self.stats = stats or LinkStats()
        self._pending = bytearray()

    def feed(self, data: Iterable[int]) -> Iterator[Frame]:
        for b in data:
            if b != 0:
                self._pending.append(b)
                if len(self._pending) > MAX_ENCODED:  # lost a delimiter: resync
                    self._pending.clear()
                    self.stats.malformed += 1
                continue
            if self._pending:
                try:
                    frame = Frame.from_bytes(cobs.decode(self._pending))
                except BadCrcError:
                    self.stats.bad_crc += 1
                except (FrameError, cobs.CobsError):
                    self.stats.malformed += 1
                else:
                    self.stats.good += 1
                    yield frame
                self._pending.clear()


async def read_frames(
    reader: asyncio.StreamReader, splitter: FrameSplitter
) -> AsyncIterator[Frame]:
    while chunk := await reader.read(4096):
        for frame in splitter.feed(chunk):
            yield frame
