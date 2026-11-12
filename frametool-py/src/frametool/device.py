"""Stands in for the firmware: streams COBS-framed telemetry, corrupting every 7th frame."""

from __future__ import annotations

import asyncio
import math

from frametool import cobs
from frametool.protocol import Frame, MessageType, Telemetry, TelemetryStatus


def make_frame(seq: int, uptime_ms: int, corrupt: bool = False) -> bytes:
    temp = 25.0 + 10.0 * math.sin(uptime_ms / 1000)
    status = TelemetryStatus.OVER_TEMP if temp > 34.0 else TelemetryStatus.NONE
    payload = Telemetry(uptime_ms, temp, 3.3, status).to_bytes()
    raw = bytearray(Frame(MessageType.TELEMETRY, seq & 0xFF, payload).to_bytes())
    if corrupt:
        raw[5] ^= 0x40  # flip a payload bit after the CRC was computed
    return cobs.encode(raw) + b"\x00"


async def run(writer: asyncio.StreamWriter, period_s: float = 0.1) -> None:
    loop = asyncio.get_running_loop()
    start = loop.time()
    seq = 0
    while True:
        seq += 1
        # Absolute deadlines, like vTaskDelayUntil: processing time does not accumulate as drift
        await asyncio.sleep(max(0.0, start + seq * period_s - loop.time()))
        writer.write(make_frame(seq - 1, round(seq * period_s * 1000), corrupt=(seq - 1) % 7 == 6))
        await writer.drain()  # back-pressure if the reader falls behind
