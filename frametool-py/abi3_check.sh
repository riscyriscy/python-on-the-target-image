#!/bin/sh
# Builds one stable-ABI wheel with Python 3.14, then installs it into Python 3.12, 3.14 and 3.15
# environments and runs the tests there. The free-threaded 3.15t build refuses the wheel.
set -eu
cd "$(dirname "$0")"
rm -rf dist
uv build --wheel --python 3.14 -C wheel.py-api=cp312 -o dist . > /dev/null 2>&1
wheel=$(ls dist/*.whl)
echo "wheel: $(basename "$wheel"), $(wc -c < "$wheel") bytes"
for v in 3.12 3.14 3.15; do
    env=$(mktemp -d)/venv
    py="$env/bin/python"
    uv venv --python "$v" -q "$env"
    uv pip install -q --python "$py" pytest hypothesis pyserial "$wheel"
    "$py" -c "import sys, frametool._crc16 as m; print(sys.version.split()[0], m.__file__.split('/')[-1])"
    "$py" -m pytest -q tests | tail -1
done
env=$(mktemp -d)/venv
uv venv --python 3.15t -q "$env"
echo "3.15t:"
uv pip install --python "$env/bin/python" "$wheel" 2>&1 | grep -o "built for the stable ABI.*" || true
