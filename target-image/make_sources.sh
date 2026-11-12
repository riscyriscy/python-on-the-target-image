#!/bin/sh
# Pack the two projects as the tarballs that the recipes of meta-rig name in SRC_URI.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
cd "$here"
tar -czf meta-rig/recipes-rig/python3-rig-service/files/rig-service-1.0.tar.gz \
    --transform 's#^rig-service#rig-service-1.0#' --exclude=__pycache__ --exclude='*.egg-info' \
    rig-service
tar -czf meta-rig/recipes-rig/python3-frametool/files/frametool-1.2.0.tar.gz \
    --transform 's#^frametool-py#frametool-1.2.0#' --exclude=__pycache__ --exclude='build*' \
    --exclude='*.so' --exclude=uv.lock --exclude=.vscode --exclude=bench --exclude=abi3_check.sh \
    --exclude=cross --exclude='.venv' -C .. frametool-py
ls -l meta-rig/recipes-rig/*/files/*.tar.gz
