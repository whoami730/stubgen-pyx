"""
A module for converting Cython module objects to `.pyi` files.
"""

from abc import ABC, abstractmethod
import ast
import dataclasses
import inspect
from textwrap import dedent, indent
from typing import List, Optional

from stubgen_pyx._version import __version__

_INDENT = "    "

# Generally not useful names to include in the stub
_DISALLOWED_NAMES: set[str]  = {
    # Module-level disallowed names
    "__doc__",
    "__file__",
    "__loader__",
    "__name__",
    "__package__",
    "__pyx_capi__",
    "__spec__",
    "__test__",

    # Class-level disallowed names
    "__class__",
    "__dir__",
    "__format__",
    "__getstate__",
    "__hash__",
    "__init_subclass__",
    "__new__",
    "__reduce__",
    "__reduce_ex__",
    "__setstate__",
    "__sizeof__",
    "__subclasshook__",
    "__weakref__",
}

# Useful dunder names for functions (all other dunder names are ignored)
_ALLOWED_DUNDERS: set[str] = {
    "__init__",
    "__len__",
    "__enter__",
    "__exit__",
}

def _is_valid_signature(signature: str) -> bool:
    # Hack: Use the ast module to parse the signature to see if it is valid
    try:
        ast.parse(f"def {signature}: pass")
        return True
    except SyntaxError:
        return False

def _is_function(value) -> bool:
    return inspect.isfunction(value) or value.__class__.__name__ in ("cython_function_or_method", "wrapper_descriptor")

def _is_class(value) -> bool:
    return inspect.isclass(value)

def _unparse_docstring(docstring: str, indentation: int):
    return f"{_INDENT * indentation}\"\"\"\n{indent(dedent(docstring.strip()), _INDENT * indentation)}\n{_INDENT * indentation}\"\"\""


@dataclasses.dataclass
class StubFileSegment(ABC):
    """
    A base class for objects which can be converted to statements in a `.pyi` file.
    """
    
    @abstractmethod
    def key(self) -> tuple:
        """
        Key for sorting the StubFileSegment objects.
        """
        raise NotImplementedError
    
    @abstractmethod
    def to_string(self, indentation: int) -> str:
        """
        Converts the StubFileSegment object to lines of a `.pyi` file.
        """
        raise NotImplementedError
    
    def __str__(self) -> str:
        return self.to_string(0)
    
    def __lt__(self, other: "StubFileSegment") -> bool:
        return self.key() < other.key()
    
    def __eq__(self, other: "StubFileSegment") -> bool:
        return type(self) == type(other) and self.key() == other.key()


@dataclasses.dataclass
class Import(StubFileSegment):
    """
    An import statement in a `.pyi` file.
    """
    module: str
    name: str = ""
    alias: str  = ""
    
    def key(self) -> tuple:
        return 0, self.module, self.name, self.alias
    
    def to_string(self, indentation: int) -> str:
        if not self.name:
            result = f"import {self.module}"
        else:
            result = f"from {self.module} import {self.name}"
        if self.alias:
            result = f"{result} as {self.alias}"
        return f"{_INDENT * indentation}{result}"
    
    @property
    def out_name(self) -> str:
        if self.alias:
            return self.alias
        elif self.name:
            return self.name
        return self.module


@dataclasses.dataclass
class Annotation(StubFileSegment):
    """
    An annotation in a `.pyi` file.
    """
    name: str
    annotation: str
    
    def key(self) -> tuple:
        return 1, self.name, self.annotation
    
    def to_string(self, indentation: int) -> str:
        return f"{_INDENT * indentation}{self.name}: {self.annotation}"


@dataclasses.dataclass
class ClassDefinition(StubFileSegment):
    """
    A class definition in a `.pyi` file.
    """
    name: str
    cls: object
    
    def key(self) -> tuple:
        return 3, self.name
    
    def to_string(self, indentation: int) -> str:
        result: str = f"{_INDENT * indentation}class {self.name}:\n"

        if self.cls.__doc__:
            result = f"{result}{_unparse_docstring(self.cls.__doc__, indentation + 1)}\n"

        members: List[StubFileSegment] = []
        seen_annotations: set[str] = set()

        for name, type_ in inspect.get_annotations(self.cls).items():
            seen_annotations.add(name)
            members.append(Annotation(name, annotation=type_))

        for name, value in inspect.getmembers(self.cls):
            if name in seen_annotations:
                continue
            member = _to_stub_file_segment(name, value)
            if member is not None:
                members.append(member)

        members.sort()

        for member in members:
            result = f"{result}{member.to_string(indentation + 1)}\n"
        
        return result.rstrip("\n")


@dataclasses.dataclass
class FunctionDefinition(StubFileSegment):
    """
    A function definition (or method) in a `.pyi` file.
    """
    name: str
    func: object
    
    def key(self) -> tuple:
        return 4, self.name
    
    def default_definition(self) -> str:
        return f"{self.name}(*args, **kwargs)"

    def to_string(self, indentation: int) -> str:
        definition: str
        docstring: str = ""
        split_docs: list[str] = []

        if self.func.__doc__ and _is_valid_signature((split_docs := self.func.__doc__.split("\n", 1))[0]):
            # Embedded docstring, favorable
            definition = split_docs[0]
            docstring = split_docs[1] if len(split_docs) > 1 else ""
        elif self.func.__doc__:
            # Regular docstring
            try:
                definition = f"{self.name}{inspect.signature(self.func)}"
            except ValueError:
                definition = self.default_definition()
            docstring = self.func.__doc__
        else:
            # No docstring
            try:
                definition = f"{self.name}{inspect.signature(self.func)}"
            except ValueError:
                definition = self.default_definition()
        
        if docstring:
            return f"{_INDENT * indentation}def {definition}: \n{_unparse_docstring(docstring, indentation + 1)}"
        return f"{_INDENT * indentation}def {definition}: ..."


def _to_import_statement(name: str, value: object) -> Import:
    has_module = hasattr(value, "__module__")
    alias = "" if value.__name__ == name else name
    name_ = value.__name__ if has_module else ""
    module = value.__module__ if has_module else value.__name__
    return Import(module=module, name=name_, alias=alias)


def _to_stub_file_segment(name: str, value: object) -> Optional[StubFileSegment]:
    """
    Converts a module member to an unparsable object. Can return None if the member should not be included in the `.pyi` file.
    """
    if (name in _DISALLOWED_NAMES) or name.startswith("__pyx_"): 
        return
    
    if (name.startswith("__") and name.endswith("__")) and name not in _ALLOWED_DUNDERS:
        return

    if _is_function(value) and (not (name.startswith("__") and name.endswith("__")) or name in _ALLOWED_DUNDERS):
        return FunctionDefinition(name, func=value)
    elif _is_class(value):
        return ClassDefinition(name, cls=value)
    else:
        return Annotation(name, annotation="object")


class AstAnnotationTransformer(ast.NodeTransformer):
    """
    Transforms Cython type names to Python types.
    """

    _cython_ints: tuple[str] = (
        'char',
        'short',
        'Py_UNICODE',
        'Py_UCS4',
        'long',
        'longlong',
        'Py_hash_t',
        'Py_ssize_t',
        'size_t',
        'ssize_t',
        'ptrdiff_t'
    )

    _cython_floats: tuple[str] = (
        'longdouble',
        'double',
    )

    _cython_complex: tuple[str] = (
        'longdoublecomplex',
        'doublecomplex',
        'floatcomplex',
    )

    _cython_translation: dict[str, str] = None

    collected_names: set[str]

    def __init__(self) -> None:
        super().__init__()

        self.collected_names = set()

        self._cython_translation = {
            "bint": "bool",
            "unicode": "str",
        }

        self._cython_translation.update({
            k: "int" for k in self._cython_ints
        })

        self._cython_translation.update({
            k: "float" for k in self._cython_floats
        })

        self._cython_translation.update({
            k: "complex" for k in self._cython_complex
        })
    
    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id in self._cython_translation:
            node.id = self._cython_translation[node.id]
        self.collected_names.add(node.id)
        return node


class ModuleDefinition(StubFileSegment):
    """
    A module definition in a `.pyi` file.
    """
    module: object

    def __init__(self, module: object):
        """
        A module definition in a `.pyi` file.
        """
        self.module = module
    
    def _is_imported(self, value) -> bool:
        """
        Checks if a value is an import. Imports are module members which don't originate from the module itself.
        """
        if inspect.ismodule(value):
            return True
        if not hasattr(value, "__module__") or not hasattr(value, "__name__"):
            return False
        return value.__module__ != self.module.__name__
    
    def key(self) -> tuple:
        raise NotImplemented
    
    def to_string(self, indentation: int) -> str:
        members: List[StubFileSegment] = []
        imports: List[Import] = []
        docstring: str = self.module.__doc__ if self.module.__doc__ else ""

        cimport_members = getattr(self.module, "__cimport_types__", ())

        if isinstance(cimport_members, type):
            cimport_members = (cimport_members,)
        for cimport_member in cimport_members:
            name = cimport_member.__name__
            if self._is_imported(cimport_member):
                imports.append(_to_import_statement(name, cimport_member))
                continue
        
        for name, value in inspect.getmembers(self.module):
            if self._is_imported(value):
                imports.append(_to_import_statement(name, value))
                continue
            member = _to_stub_file_segment(name, value)
            if member is not None:
                members.append(member)
        
        for name, type_ in inspect.get_annotations(self.module).items():
            members.append(Annotation(name, annotation=type_))

        members.sort()

        docs: str = f"{_unparse_docstring(docstring, indentation)}\n\n" if docstring else ""

        previous_member: StubFileSegment = members[0]

        content = previous_member.to_string(indentation)

        for member in members[1:]:
            if type(member) == type(previous_member) == Import:
                content = f"{content}\n{member.to_string(indentation)}"
            else:
                content = f"{content}\n\n{member.to_string(indentation)}"
        
        pyi_ast = ast.parse(content)

        transformer = AstAnnotationTransformer()
        transformer.visit(pyi_ast)
        
        imports = [import_ for import_ in imports if import_.out_name in transformer.collected_names]
        imports.sort()

        content = ast.unparse(pyi_ast)
        import_content = "\n".join([import_.to_string(indentation) for import_ in imports]) + "\n\n" if imports else ""
        content = f"{docs}{import_content}{content}"

        return content


def convert_module(module: object) -> str:
    """
    Converts a Cython module to a `.pyi` file.
    """
    header = f"# This file was generated by stubgen-pyx v{__version__}\n"
    return f"{header}{ModuleDefinition(module).to_string(0)}"
