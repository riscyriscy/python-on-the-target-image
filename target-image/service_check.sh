#!/bin/sh
# Check rig-service on this machine: its tests, a run that stops on SIGTERM, and its unit file.
# Run: sh target-image/service_check.sh   (PY must have pytest; the default is the python3 on PATH)
PY=${PY:-python3}
here=$(cd "$(dirname "$0")" && pwd)
export PYTHONPATH=$here/rig-service/src:$here/../frametool-py/src

echo "== tests"
$PY -m pytest -q -p no:cacheprovider "$here/rig-service/tests" 2>&1 | tail -1
echo "== run, then SIGTERM after 1.5 s"
$PY -m rig_service --interval 0.05 --report 10 &
pid=$!
sleep 1.5
kill -TERM $pid
wait $pid
echo "exit status $?"
echo "== the unit"
systemd-analyze verify "$here/rig-service/systemd/rig-service.service" && echo "no messages, exit status $?"
