#!/bin/sh
# What does BitBake make of the two recipes of meta-rig?
# Run inside an initialised build directory of a Poky checkout (source oe-init-build-env), after
# bitbake-layers add-layer .../meta-rig. Written for Poky 5.0.15 (Scarthgap), machine qemux86-64.
names() { tr ' ' '\n' | grep -E '^(python3|cmake|ninja)' | sort -u | paste -sd' ' | fold -s -w 90; }
get() { bitbake-getvar -r "$1" --value "$2" 2>/dev/null | tr -s ' ' | sed 's#^/.*recipe-sysroot#<recipe-sysroot>#; s#=/[^ ]*recipe-sysroot#=<recipe-sysroot>#'; }

echo "== parse every recipe of every layer"
bitbake -p >/dev/null 2>&1; echo "bitbake -p exit status $?"
echo "== the recipes of meta-rig"
bitbake-layers show-recipes 'python3-rig-service' 'python3-frametool' 2>/dev/null | grep -v '^WARNING: You\|^NOTE\|^=\|^Loading\|^Loaded\|^Parsing\|^Summary'
echo "== resolve the dependencies of python3-rig-service"
bitbake -g python3-rig-service >/dev/null 2>&1; echo "bitbake -g exit status $?, $(wc -l < pn-buildlist) recipes in the build list"
grep -E '^(python3-build-native|python3-installer-native|python3-setuptools-native|python3-frametool)$' pn-buildlist
echo "== python3-rig-service, DEPENDS (build tools and Python only)"
get python3-rig-service DEPENDS | names
echo "== python3-rig-service, RDEPENDS"
get python3-rig-service RDEPENDS:python3-rig-service | names
echo "== python3-frametool, DEPENDS (build tools and Python only)"
get python3-frametool DEPENDS | names
echo "== python3-frametool, EXTRA_OECMAKE"
get python3-frametool EXTRA_OECMAKE
echo "== do_unpack"
bitbake -f -c unpack python3-rig-service python3-frametool 2>&1 | grep -E 'do_unpack: Succeeded' | sed 's/^NOTE: recipe //'
