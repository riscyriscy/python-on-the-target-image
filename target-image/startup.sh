#!/bin/sh
# What does an interpreter start cost, and what does each import add?
# Usage: sh startup.sh PYTHON   (for example the bin/python3.14 of a CPython tree)
py=${1:-python3.14}
runs=40
# mean wall time of $runs runs of one command line, in milliseconds with one decimal
ms() {
    start=$(date +%s%N)
    i=0; while [ $i -lt $runs ]; do "$@" >/dev/null 2>&1; i=$((i + 1)); done
    end=$(date +%s%N)
    echo $(( (end - start) / (runs * 100000) )) | awk '{printf "%5.1f ms", $1 / 10}'
}
echo "interpreter alone:          $(ms $py -c pass)"
echo "without site (-S):          $(ms $py -S -c pass)"
echo "isolated, no site (-I -S):  $(ms $py -I -S -c pass)"
for m in json struct socket threading ctypes sqlite3 ssl asyncio; do
    printf "import %-18s %s\n" "$m:" "$(ms $py -c "import $m")"
done
echo "modules loaded at start:    $($py -c 'import sys; print(len(sys.modules))') with site, $($py -S -c 'import sys; print(len(sys.modules))') without"
