"""python -m frametool: live demo (simulated device -> TCP -> frame reader), or --selftest."""

from __future__ import annotations

import argparse
import asyncio
import contextlib

from frametool import device
from frametool.crc16 import CHECK_VALUE, crc16, crc16_native
from frametool.link import FrameSplitter, read_frames
from frametool.protocol import MessageType, Telemetry


async def demo(seconds: float) -> None:
    async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        with contextlib.suppress(ConnectionError):
            await device.run(writer)

    server = await asyncio.start_server(serve, "127.0.0.1", 0)  # port 0: any free port
    port = server.sockets[0].getsockname()[1]
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    splitter = FrameSplitter()

    async def consume() -> None:
        async for frame in read_frames(reader, splitter):
            if frame.type == MessageType.TELEMETRY:
                t = Telemetry.from_bytes(frame.payload)
                flags = f"  [{t.status.name}]" if t.status else ""
                print(
                    f"#{frame.seq:3}  {t.uptime_ms / 1000:5.1f}s  {t.temperature_c:6.2f} C  "
                    f"{t.supply_v:.3f} V{flags}"
                )

    async with server:
        with contextlib.suppress(TimeoutError):
            async with asyncio.timeout(seconds):  # cancels everything inside when it expires
                await consume()
        writer.close()
    s = splitter.stats
    print(f"good={s.good} bad_crc={s.bad_crc} malformed={s.malformed}")


def main() -> int:
    parser = argparse.ArgumentParser(prog="frametool")
    parser.add_argument("--seconds", type=float, default=3.0)
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        ok = crc16(b"123456789") == CHECK_VALUE
        impl = "native C extension" if crc16_native else "pure Python"
        print(f"crc16 implementation: {impl}, check value {'ok' if ok else 'WRONG'}")
        return 0 if ok else 1
    asyncio.run(demo(args.seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
