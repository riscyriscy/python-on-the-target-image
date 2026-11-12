#!/bin/sh
# Python on a read-only root file system: where bytecode goes, and what pre-compiling saves at start-up.
# Run: sh target-image/ro_trial.sh   (Linux, needs unshare and mount rights; it uses a private mount namespace)
set -eu
PY=${PY:-python3.14}
SRC=$(cd "$(dirname "$0")/../frametool-py/src" && pwd)
work=$(mktemp -d)
mkdir "$work/app" "$work/ro"
cp -r "$SRC/frametool" "$work/app/" && find "$work/app" -name __pycache__ -prune -exec rm -rf {} +

t() {  # average wall time in ms of 20 imports of frametool.link, with the given PYTHONPATH
    start=$(date +%s%N)
    for i in $(seq 20); do PYTHONPATH=$1 $PY -c 'import frametool.link'; done
    end=$(date +%s%N)
    echo $(( (end - start) / 20000000 ))
}
count() { find "$1" -name '*.pyc' | wc -l; }

echo "1. writable tree, first import writes the cache:   pyc files before $(count "$work/app"), after $(PYTHONPATH=$work/app $PY -c 'import frametool.link'; count "$work/app")"
find "$work/app" -name __pycache__ -prune -exec rm -rf {} +
echo "2. writable tree, PYTHONDONTWRITEBYTECODE=1:        pyc files after import: $(PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=$work/app $PY -c 'import frametool.link'; count "$work/app")"

unshare -m sh -c "
  mount --bind $work/app $work/ro && mount -o remount,bind,ro $work/ro
  echo '3. read-only mount, no cache:                        import works, status' \$(PYTHONPATH=$work/ro $PY -c 'import frametool.link; print(\"ok\")')
  echo \"   ... average start-up: \$(PYTHONPATH=$work/ro; export PYTHONPATH; start=\$(date +%s%N); for i in \$(seq 20); do $PY -c 'import frametool.link'; done; end=\$(date +%s%N); echo \$(( (end - start) / 20000000 )))\" ms
"
$PY -m compileall -q "$work/app"
echo "4. compiled at build time: pyc files $(count "$work/app")"
unshare -m sh -c "
  mount --bind $work/app $work/ro && mount -o remount,bind,ro $work/ro
  echo \"   ... read-only mount, cache present: average start-up: \$(PYTHONPATH=$work/ro; export PYTHONPATH; start=\$(date +%s%N); for i in \$(seq 20); do $PY -c 'import frametool.link'; done; end=\$(date +%s%N); echo \$(( (end - start) / 20000000 )))\" ms
"
echo "5. PYTHONPYCACHEPREFIX=/tmp/pyc: $(rm -rf /tmp/pyc; find "$work/app" -name __pycache__ -prune -exec rm -rf {} +; PYTHONPYCACHEPREFIX=/tmp/pyc PYTHONPATH=$work/app $PY -c 'import frametool.link'; echo "$(count "$work/app") pyc files under the tree, $(find /tmp/pyc -path '*frametool*' -name '*.pyc' | wc -l) for frametool under /tmp/pyc")"
rm -rf "$work" /tmp/pyc
