#!/bin/sh
# How much of a CPython tree does an image need?  Usage: sh footprint_tree.sh PYTHON_TREE
# PYTHON_TREE is a self-contained CPython 3.14 tree, such as the ones that uv installs.
src=$1
work=$(mktemp -d)
cp -a "$src" "$work/py" && cd "$work/py" || exit 1
mib() { du -sk "$1" | awk '{printf "%.1f MiB", $1 / 1024}'; }

echo "as installed:        $(mib .) (stdlib $(mib lib/python3.14), executable $(mib bin/python3.14))"
find . -name __pycache__ -prune -exec rm -rf {} +
echo "without bytecode:    $(mib .)"

# Remove what a headless tool never imports or runs.
rm -rf share include lib/tcl* lib/itcl* lib/libtcl* lib/libpython* lib/pkgconfig \
  lib/python3.14/test lib/python3.14/idlelib lib/python3.14/tkinter \
  lib/python3.14/turtledemo lib/python3.14/turtle.py lib/python3.14/ensurepip \
  lib/python3.14/pydoc_data lib/python3.14/config-3.14* \
  lib/python3.14/lib-dynload/_tkinter* lib/python3.14/lib-dynload/_test* \
  lib/python3.14/lib-dynload/_ctypes_test* bin/idle* bin/pydoc* bin/*-config bin/pip*
echo "after removing them: $(mib .) (stdlib $(mib lib/python3.14), lib-dynload $(mib lib/python3.14/lib-dynload))"
rm -rf "$work"
