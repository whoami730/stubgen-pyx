"""
A module for building Cython modules in place.
"""
import importlib
from pathlib import Path
import sys

from Cython.Build import cythonize
from setuptools import setup, Extension

# See https://cython.readthedocs.io/en/latest/src/userguide/source_files_and_compilation.html#compiler-directives
# 
# These are friendly defaults for building most modern Cython, and should be modified if needed.
# To get the most out of this tool, it is recommended to use the `embedsignature` directive with 
# the `python` format. Embedded signatures will be used to generate stubs.
compiler_directives = {
    "embedsignature": True,
    "embedsignature.format": "python",
    "language_level": "3",
}

def _path_as_module(path: Path) -> str:
    return path.with_suffix("").as_posix().replace("/", ".")

def build(package_dir: str) -> list[tuple[object, Path]]:
    """
    Compiles all `.pyx` files in `package_dir` in place.
    """

    cy_files = list(Path(package_dir).glob("**/*.pyx"))
    cy_names = [_path_as_module(file) for file in cy_files]

    extensions = [
        Extension(
            name=name,
            sources=[str(file)],
        ) for name, file in zip(cy_names, cy_files)
    ]

    ext_modules = cythonize(
        extensions,
        compiler_directives=compiler_directives,
    )

    setup(
        ext_modules=ext_modules,
        script_args=[
            "build_ext",
            "--inplace",
        ] 
    )

    sys.path.insert(0, str(Path(".").absolute()))

    try:
        return [
            (importlib.import_module(name), file)
            for name, file in zip(cy_names, cy_files)
        ]
    finally:
        sys.path.pop(0)
