"""Which python3-* packages of a Yocto release does a program need?

Usage: python yocto_packages.py python3-manifest.json MODULE [MODULE ...]

Run it with the same minor version as the image (Scarthgap ships 3.12), with the program on
PYTHONPATH. It imports the modules, takes the standard library files that were loaded, finds the
package of the manifest that holds each file, adds the packages they depend on, and prints the
size of every package as the files stand in this interpreter's standard library.
"""

import fnmatch
import json
import subprocess
import sys
import sysconfig
from pathlib import Path

stdlib = Path(sysconfig.get_paths()["stdlib"])
text = "".join(line for line in Path(sys.argv[1]).read_text().splitlines(True) if not line.startswith("#"))
manifest = json.loads(text)


def patterns(package: str) -> list[str]:
    prefix = "${libdir}/python${PYTHON_MAJMIN}/"
    return [f[len(prefix):] for f in manifest[package]["files"] if f.startswith(prefix)]


def holder(rel: str) -> str:
    """The package whose file list names this file, or a directory above it."""
    for package in manifest:
        for pattern in patterns(package):
            if fnmatch.fnmatch(rel, pattern) or rel.startswith(pattern.rstrip("/") + "/"):
                return package
    return "core"


def size(package: str) -> int:
    total = 0
    for pattern in patterns(package):
        for path in stdlib.glob(pattern):
            files = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
            total += sum(p.stat().st_size for p in files if "__pycache__" not in p.parts)
    return total


# Import the program in a fresh interpreter, so that the modules of this script are not counted
probe = "import sys; " + "; ".join(f"import {n}" for n in sys.argv[2:]) + (
    "; print(*[getattr(m, '__file__', None) or '' for m in sys.modules.values()], sep='\\n')"
)
loaded = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True).stdout
used = set()
for file in loaded.splitlines():
    if file and Path(file).is_relative_to(stdlib):
        used.add(holder(str(Path(file).relative_to(stdlib))))
needed, todo = set(), sorted(used | {"core"})
while todo:
    package = todo.pop()
    if package not in needed:
        needed.add(package)
        todo += manifest[package].get("rdepends", [])
whole = sum(size(p) for p in manifest)
for package in sorted(needed, key=size, reverse=True):
    print(f"python3-{package:<12} {size(package) / 1024:8.0f} KiB")
print(f"{len(needed)} of {len(manifest)} packages, {sum(size(p) for p in needed) / 1024:.0f} KiB of {whole / 1024:.0f} KiB")
