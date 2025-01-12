from abc import ABC
from typing import List

from dataclasses import dataclass


class Type(ABC):
    pass


class NilType(Type):
    pass


class IntType(Type):
    pass


class StringType(Type):
    pass


class VoidType(Type):
    pass


@dataclass
class Field:
    name: str
    type: Type


@dataclass
class RecordType(Type):
    fields: List[Field]


@dataclass
class ArrayType(Type):
    type: Type


@dataclass
class NameType(Type):
    symbol: str


def are_types_equal(t1: Type, t2: Type) -> bool:
    """Sees if two types are of the same basic type or if they reference the same complex type."""

    return (
            isinstance(t1, NilType)
            and (isinstance(t2, NilType) or isinstance(t2, RecordType))
            or isinstance(t2, NilType)
            and (isinstance(t1, NilType) or isinstance(t1, RecordType))
            or isinstance(t1, IntType)
            and isinstance(t2, IntType)
            or isinstance(t1, StringType)
            and isinstance(t2, StringType)
            or isinstance(t1, VoidType)
            and isinstance(t2, VoidType)
            or t1 is t2
    )
