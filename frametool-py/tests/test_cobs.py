import pytest

from frametool import cobs


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"\x00",
        b"\x11\x00\x00\x22\x00",
        bytes(range(1, 255)),
        bytes(range(256)) * 3,
        b"\x01" * 600,
    ],
    ids=["empty", "zero", "zeros", "254-run", "all-values", "long-run"],
)
def test_round_trip_and_no_zeros(data: bytes) -> None:
    encoded = cobs.encode(data)
    assert 0 not in encoded
    assert cobs.decode(encoded) == data


def test_rejects_truncated_input() -> None:
    with pytest.raises(cobs.CobsError):
        cobs.decode(b"\x05\x11\x22")
