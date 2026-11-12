# Python on the Target Image: companion code

Source code for "Python on the Target Image" (C. Paul Gordon, November 2026), a supplement to the
second book of the From Embedded C to Python series, "Python Beside C". Every listing in the document
comes from this repository, and every script was run as written. The `.out.txt` files hold the output
that the document shows.

`frametool-py/` is the `frametool` package of "Python Beside C", Phase 2, with its C extension. The
scripts of `target-image/` build it for another processor and package it, so a copy is included here.

## Layout

| Path | What it is |
|---|---|
| `target-image/wheels_for_target.sh` | Which wheels exist for aarch64, musl and 32-bit Arm |
| `target-image/cross_wheel.sh` | A wheel of frametool cross-built for aarch64 with scikit-build-core, installed into a folder and tested under qemu |
| `target-image/footprint_tree.sh`, `startup.sh` | Size of a CPython tree before and after trimming, and start-up times |
| `target-image/yocto_packages.py` | The `python3-*` packages of a Yocto release that a program needs |
| `target-image/rig-service/` | A systemd service package with its tests and unit file |
| `target-image/meta-rig/` | A Yocto layer with a recipe for `rig-service` and one for `frametool`; `make_sources.sh` packs their tarballs |
| `target-image/recipe_steps.sh` | The build and install commands of the Yocto Python class, run on this machine |
| `target-image/yocto_check.sh` | BitBake parse, dependency and unpack check; needs a Poky checkout |
| `target-image/service_check.sh`, `ro_trial.sh` | The service, its unit and a read-only root file system trial |
| `frametool-py/` | The `frametool` package with the C extension, from "Python Beside C" |

## Requirements

- [uv](https://docs.astral.sh/uv/)
- CMake 3.21+ and a C compiler
- A Poky checkout, `qemu-user` and `gcc-aarch64-linux-gnu` (for the cross build, the recipes and the BitBake check)
- systemd (`systemd-analyze verify`) for the unit check

## Licence

MIT. See `LICENSE`.
