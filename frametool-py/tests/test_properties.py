"""Property-based tests: Hypothesis generates the inputs, the tests state what must always hold."""

import contextlib

from hypothesis import example, given, settings
from hypothesis import strategies as st

from frametool import cobs
from frametool.link import FrameSplitter
from frametool.protocol import Frame, FrameError, Telemetry

# derandomize=True makes every run use the same examples, so CI results do not flicker
settings.register_profile("ci", max_examples=300, derandomize=True, deadline=None)
settings.load_profile("ci")

payloads = st.binary(max_size=200)
frames = st.builds(Frame, type=st.integers(0, 255), seq=st.integers(0, 255), payload=payloads)


# Hypothesis generates short inputs, so the block limit of 254 is named here as examples
@given(st.binary(max_size=1000))
@example(b"\x01" * 253)
@example(b"\x01" * 254)
@example(b"\x01" * 255)
def test_cobs_round_trip(data: bytes) -> None:
    assert cobs.decode(cobs.encode(data)) == data


@given(st.binary(max_size=1000))
@example(b"\x01" * 254)
def test_cobs_no_zero_bounded(data: bytes) -> None:
    encoded = cobs.encode(data)
    assert 0 not in encoded
    assert len(encoded) <= len(data) + len(data) // 254 + 1  # the COBS worst case


@given(st.binary(max_size=300))
def test_cobs_decode_never_crashes(data: bytes) -> None:
    with contextlib.suppress(cobs.CobsError):  # the only exception a caller has to handle
        cobs.decode(data)


@given(frames)
def test_frame_round_trip(frame: Frame) -> None:
    assert Frame.from_bytes(frame.to_bytes()) == frame


@given(frames, st.data())
def test_bit_flip_rejected(frame: Frame, data: st.DataObject) -> None:
    raw = bytearray(frame.to_bytes())
    bit = data.draw(st.integers(0, len(raw) * 8 - 1))
    raw[bit // 8] ^= 1 << (bit % 8)
    try:
        Frame.from_bytes(bytes(raw))
    except FrameError:
        return
    raise AssertionError(f"flip of bit {bit} was accepted")


@given(st.binary(min_size=9, max_size=9))
def test_telemetry_round_trip(payload: bytes) -> None:
    assert Telemetry.from_bytes(payload).to_bytes() == payload


@given(st.lists(frames, max_size=8), st.lists(st.integers(1, 40), min_size=1, max_size=30))
def test_splitter_ignores_chunking(sent: list[Frame], chunk_sizes: list[int]) -> None:
    stream = b"".join(cobs.encode(f.to_bytes()) + b"\x00" for f in sent)
    splitter, pos = FrameSplitter(), 0
    received: list[Frame] = []
    for size in chunk_sizes * (len(stream) // len(chunk_sizes) + 2):
        received += splitter.feed(stream[pos : pos + size])
        pos += size
    assert received == sent
    assert splitter.stats.good == len(sent)


# Noise: arbitrary bytes, and runs of non-zero bytes longer than MAX_ENCODED, which reach the
# resynchronisation branch that random bytes almost never reach
long_run = st.binary(min_size=301, max_size=600).map(lambda b: b.replace(b"\x00", b"\x01"))
noise = st.one_of(st.binary(max_size=2000), long_run)


@given(noise, frames)
def test_splitter_resyncs_after_noise(noise: bytes, frame: Frame) -> None:
    good = cobs.encode(frame.to_bytes()) + b"\x00"
    flipped = bytearray(frame.to_bytes())
    flipped[-1] ^= 1  # one bit of the CRC: the length is right and the CRC is wrong
    bad = cobs.encode(bytes(flipped)) + b"\x00"
    splitter = FrameSplitter()
    received = list(splitter.feed(noise + b"\x00" + bad + good))  # must not raise
    assert received[-1] == frame  # the good frame that follows the damage is found
    assert splitter.stats.good == len(received)
    assert splitter.stats.bad_crc >= 1
