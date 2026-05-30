#!/usr/bin/env python3
"""Compile the jvfast C++ acceleration module in place.

Run once after install:  python -m app.native.build  (or python app/native/build.py)

The build is optional. If it fails or is skipped, the application transparently
falls back to the pure-Python implementations — only slower, never broken.
"""
import os
import subprocess
import sys
import sysconfig

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> int:
    try:
        import pybind11
    except ImportError:
        print("pybind11 not installed. Run: pip install pybind11", file=sys.stderr)
        return 1

    src = os.path.join(HERE, "jvfast.cpp")
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
    out = os.path.join(HERE, "jvfast" + ext_suffix)

    include_dirs = [pybind11.get_include(), sysconfig.get_path("include")]
    cxx = os.environ.get("CXX", "c++")

    if sys.platform == "win32":
        # On Windows, prefer building via setuptools (MSVC); see setup.py.
        print("On Windows, build with:  pip install pybind11 && python setup.py build_ext --inplace")
        return 1

    cmd = [
        cxx, "-O3", "-shared", "-std=c++17", "-fPIC", "-fvisibility=hidden",
        *(f"-I{d}" for d in include_dirs),
        src, "-o", out,
    ]
    # macOS needs undefined-symbol leniency for Python symbols.
    if sys.platform == "darwin":
        cmd += ["-undefined", "dynamic_lookup"]

    print("Compiling:", " ".join(cmd))
    proc = subprocess.run(cmd)
    if proc.returncode == 0:
        print(f"Built {out}")
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
