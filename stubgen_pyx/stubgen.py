"""
The main function for stubgen-pyx.
"""
from pathlib import Path

from stubgen_pyx.build import build
from stubgen_pyx.convert import convert_module


def stubgen(package_dir: str) -> str:
    """
    Compiles all `.pyx` files in `package_dir` in place and generates a `.pyi` file for each module.
    """

    modules: list[tuple[object, Path]] = build(package_dir)
    for module, file in modules:
        if file.name == "__cinit__.pyx":
            file.with_suffix(".pyi").write_text(convert_module(module, filter_unused_imports=False))
        else:
            file.with_suffix(".pyi").write_text(convert_module(module))