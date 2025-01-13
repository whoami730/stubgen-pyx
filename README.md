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

- `cimport`-ed modules with types that leak into the stub file (by way of function signatures, for example)
  do not have their imports followed in the stub file. As a workaround, you can set a `__cimport_types__` list
  or tuple of module types that you want exposed to the stub file.

- This is only designed to be a _pretty good_ approximation of Python-public members in a Cython module. It's still
  very much a work in progress and may produce inaccurate results. If you notice any bugs or have any suggestions, please
  [open an issue](https://github.com/jon-edward/stubgen-pyx/issues).
