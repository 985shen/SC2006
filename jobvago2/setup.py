"""Build the optional jvfast C++ acceleration module.

The extension is OPTIONAL. If it isn't built, jobvago falls back to pure-Python
keyword matching automatically (slower, never broken). Build it for the fast
path with either:

    python -m app.native.build            # quick, uses g++/clang directly
    pip install pybind11 && python setup.py build_ext --inplace   # portable

On Windows, the second form is recommended (uses the MSVC toolchain).
"""
from setuptools import setup, Extension

try:
    from pybind11.setup_helpers import Pybind11Extension, build_ext
    ext_modules = [
        Pybind11Extension(
            "app.native.jvfast",
            ["app/native/jvfast.cpp"],
            cxx_std=17,
        )
    ]
    cmdclass = {"build_ext": build_ext}
except ImportError:
    # pybind11 not installed yet — fall back to a plain Extension so that
    # `pip install pybind11` followed by a rebuild works.
    ext_modules = [Extension("app.native.jvfast", ["app/native/jvfast.cpp"])]
    cmdclass = {}

setup(
    name="jobvago-native",
    version="1.0.0",
    description="Native Aho-Corasick keyword matcher for jobvago",
    ext_modules=ext_modules,
    cmdclass=cmdclass,
    zip_safe=False,
)
