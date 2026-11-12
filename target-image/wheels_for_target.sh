#!/bin/sh
# Which wheels exist for a board that is not this machine?
# Run on x86-64 Linux with pip 26 and uv 0.13. The target is Python 3.12 on aarch64.
out=$(mktemp -d)
uv venv -q "$out/venv" 2>/dev/null     # uv needs an environment, even for a dry run
export VIRTUAL_ENV=$out/venv
pipdl="python3 -m pip download --quiet --only-binary=:all: --no-deps \
  --implementation cp --python-version 3.12 --abi cp312 -d $out"

echo "== pip, glibc 2.17 (manylinux2014)"
$pipdl --platform manylinux2014_aarch64 numpy pyserial
ls -1 $out | grep -v venv

echo "== pip, glibc 2.28"
rm -f $out/*.whl
$pipdl --platform manylinux_2_28_aarch64 numpy
ls -1 $out | grep -v venv

echo "== pip, musl (Alpine)"
rm -f $out/*.whl
$pipdl --platform musllinux_1_2_aarch64 numpy
ls -1 $out | grep -v venv

echo "== pip, 32-bit Arm, numpy"
rm -f $out/*.whl
$pipdl --platform manylinux2014_armv7l numpy 2>&1 | tail -2
echo "== pip, 32-bit Arm, pyserial (pure Python)"
$pipdl --platform manylinux2014_armv7l pyserial
ls -1 $out | grep -v venv

echo "== uv, glibc 2.17, source builds allowed"
uv pip install --dry-run --python-platform aarch64-manylinux2014 \
  --python-version 3.12 numpy 2>&1 | grep '^ +'
echo "== uv, glibc 2.17, wheels only"
uv pip install --dry-run --no-build --python-platform aarch64-manylinux2014 \
  --python-version 3.12 numpy 2>&1 | grep '^ +'
rm -rf $out
