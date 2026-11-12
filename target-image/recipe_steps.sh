#!/bin/sh
# Run the two commands that python_pep517.bbclass runs for python3-rig-service, on this machine.
# do_compile builds a wheel without build isolation, do_install unpacks it into the staging folder D.
# --prefix=/usr stands in for the patched sysconfig of the image python, which reports /usr.
# POKY is a Poky checkout. Its python3-installer recipe patches installer 0.7.0 to add --interpreter.
set -eu
POKY=${POKY:-$HOME/poky}
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d)
uv venv -q "$work/venv" --python 3.12
uv pip install -q --python "$work/venv/bin/python" build installer==0.7.0 setuptools wheel
patch -s -p2 -d "$work/venv/lib/python3.12/site-packages" \
    < "$POKY/meta/recipes-devtools/python/python3-installer/interpreter.patch"
nativepython3=$work/venv/bin/python
cp -r "$here/rig-service" "$work/S"
D=$work/D

echo "== do_compile"
$nativepython3 -m build --no-isolation --wheel --outdir "$work/dist" "$work/S" 2>&1 | tail -1
echo "== do_install"
$nativepython3 -m installer --compile-bytecode=0 --interpreter "/usr/bin/env python3" --prefix=/usr --destdir="$D" "$work/dist"/*.whl
cd "$D" && find . -type f | sort | sed 's#^\./##'
echo "== the installed command"
head -1 usr/bin/rig-service

echo "== the unit that do_install:append adds"
install -D -m 0644 "$work/S/systemd/rig-service.service" "$D/usr/lib/systemd/system/rig-service.service"
systemd-analyze verify "$D/usr/lib/systemd/system/rig-service.service" && echo "systemd-analyze verify: no messages, exit status $?"
rm -rf "$work"
