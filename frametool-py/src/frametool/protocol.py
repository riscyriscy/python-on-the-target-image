"""Frame and message definitions shared with the firmware (see native/telemetry.h)."""

from __future__ import annotations

import enum
import struct
from dataclasses import dataclass
from typing import ClassVar

from frametool.crc16 import crc16

HEADER = struct.Struct("<BBH")  # type u8, seq u8, payload length u16, little-endian
CRC = struct.Struct("<H")


class MessageType(enum.IntEnum):
    PING = 0x01
    PONG = 0x02
    TELEMETRY = 0x10
    SET_RATE = 0x20


class FrameError(Exception):
    pass


class BadCrcError(FrameError):
    pass


@dataclass(frozen=True, slots=True)
class Frame:
    type: int  # int, not MessageType: an unknown type from the wire must not raise here
    seq: int
    payload: bytes

    def to_bytes(self) -> bytes:
        body = HEADER.pack(self.type, self.seq, len(self.payload)) + self.payload
        return body + CRC.pack(crc16(body))

    @classmethod
    def from_bytes(cls, raw: bytes) -> Frame:
        if len(raw) < HEADER.size + CRC.size:
            raise FrameError("too short")
        ftype, seq, length = HEADER.unpack_from(raw)
        if len(raw) != HEADER.size + length + CRC.size:
            raise FrameError("length mismatch")
        (crc,) = CRC.unpack_from(raw, len(raw) - CRC.size)
        if crc != crc16(raw[: -CRC.size]):
            raise BadCrcError("bad CRC")
        return cls(ftype, seq, bytes(raw[HEADER.size : HEADER.size + length]))


class TelemetryStatus(enum.IntFlag):
    NONE = 0
    OVER_TEMP = 1 << 0
    UNDER_VOLTAGE = 1 << 1
    SENSOR_FAULT = 1 << 2


@dataclass(frozen=True, slots=True)
class Telemetry:
    """Engineering-units view of telemetry_t (packed, 9 bytes, little-endian)."""

    WIRE: ClassVar[struct.Struct] = struct.Struct("<IhHB")  # u32 ms, i16 c-degC, u16 mV, u8 flags

    uptime_ms: int
    temperature_c: float
    supply_v: float
    status: TelemetryStatus

    def to_bytes(self) -> bytes:
        return self.WIRE.pack(
            self.uptime_ms,
            round(self.temperature_c * 100),
            round(self.supply_v * 1000),
            self.status,
        )

    @classmethod
    def from_bytes(cls, payload: bytes) -> Telemetry:
        ms, cdeg, mv, status = cls.WIRE.unpack(payload)  # struct.error if not exactly 9 bytes
        return cls(ms, cdeg / 100, mv / 1000, TelemetryStatus(status))
