# stubgen-pyx

Stub generation for Cython code.

## Installation

Install the package with `pip install stubgen-pyx`.

## Usage

From the command line:

```bash
stubgen-pyx /path/to/package
```

Or from Python:

```python
import stubgen_pyx
stubgen_pyx.stubgen("/path/to/package")
```

## Why?

Cython is a popular Python extension language, but introspection for Cython modules is often
limited. `.pyi` files are a common way to provide type hints for Python code that cannot be
easily analyzed statically.

## Why not mypy?

mypy is a static type checker for Python that can generate `.pyi` files for extension modules
at a pretty good level of accuracy. However, it's not designed to utilize embedded information
about Cython module members - this leaves the `.pyi` files quite limited.

## Limitations

- `cpdef`-ed module and class members are only partially supported. They are included in the
  generated `.pyi` files, but their type hints are incomplete (namely, they're given the type `object`).
  As a workaround, you can set a `__annotations__` dictionary in the module or class definition to
  manually specify the annotations you want to overlay on the stub file.

- `cimport`-ed modules with types that leak into the stub file (by way of function signatures, for example)
  do not have their imports followed in the stub file. As a workaround, you can set a `__cimport_types__` list
  or tuple of module types which you want to import in the stub file.
