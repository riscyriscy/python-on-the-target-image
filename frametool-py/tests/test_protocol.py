import pytest

from frametool.protocol import BadCrcError, Frame, MessageType, Telemetry, TelemetryStatus


def test_telemetry_wire_format_matches_c_struct() -> None:
    t = Telemetry(123456, -12.34, 3.301, TelemetryStatus.UNDER_VOLTAGE)
    # 123456 ms, -1234 (0xFB2E), 3301 mV (0x0CE5), flags 0x02, all little-endian, 9 bytes
    assert t.to_bytes().hex() == "40e201002efbe50c02"
    assert Telemetry.from_bytes(t.to_bytes()) == t


def test_frame_round_trip() -> None:
    f = Frame(MessageType.TELEMETRY, 9, b"\x01\x02\x03")
    assert Frame.from_bytes(f.to_bytes()) == f


def test_corrupted_frame_is_rejected() -> None:
    raw = bytearray(Frame(MessageType.PING, 1, b"abc").to_bytes())
    raw[4] ^= 0x01
    with pytest.raises(BadCrcError):
        Frame.from_bytes(bytes(raw))
