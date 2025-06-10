#!/usr/bin/env python3
"""
Tiger Language Type System

This module defines the type system for the Tiger programming language.
It provides classes representing different types and utilities for type checking
during semantic analysis.

The Tiger type system includes:
- Primitive types: int, string, nil, void
- Composite types: records and arrays
- Named types: user-defined type aliases

Type checking ensures that operations are performed on compatible types
and that the program follows Tiger's type safety rules.

Author: Tiger Compiler Team
"""

from abc import ABC
from typing import List

from dataclasses import dataclass


class Type(ABC):
    """
    Abstract base class for all types in the Tiger type system.
    
    All type representations inherit from this class, providing a common
    interface for type checking and comparison operations.
    """
    pass


class NilType(Type):
    """
    Represents the nil type in Tiger.
    
    The nil type is compatible with all record types and represents
    the absence of a value. It can be assigned to any record variable
    and used in equality comparisons.
    """
    pass


class IntType(Type):
    """
    Represents the integer type in Tiger.
    
    The int type represents signed integers and supports arithmetic
    operations (+, -, *, /) and comparison operations (<, <=, >, >=, =, <>).
    """
    pass


class StringType(Type):
    """
    Represents the string type in Tiger.
    
    The string type represents sequences of characters and supports
    comparison operations (=, <>, <, <=, >, >=) based on lexicographic ordering.
    Strings are immutable in Tiger.
    """
    pass


class VoidType(Type):
    """
    Represents the void type in Tiger.
    
    The void type is used for expressions that do not produce a value,
    such as assignment statements, while loops, and procedures (functions
    without a return type). Also known as the "unit type" in some languages.
    """
    pass


@dataclass
class Field:
    """
    Represents a field in a record type.
    
    Fields have a name and an associated type, and are used to define
    the structure of record types.
    
    Attributes:
        name (str): The name of the field
        type (Type): The type of the field
    """
    name: str
    type: Type


@dataclass
class RecordType(Type):
    """
    Represents a record type in Tiger.
    
    Record types are structured types containing named fields.
    Each field has a name and a type. Records are reference types
    and can be assigned the value nil.
    
    Example: type person = {name: string, age: int}
    
    Attributes:
        fields (List[Field]): List of fields in the record
    """
    fields: List[Field]


@dataclass
class ArrayType(Type):
    """
    Represents an array type in Tiger.
    
    Array types contain elements of a single type. Arrays are reference
    types and can be assigned the value nil. Array elements are accessed
    using integer indices starting from 0.
    
    Example: type intArray = array of int
    
    Attributes:
        type (Type): The type of elements stored in the array
    """
    type: Type


@dataclass
class NameType(Type):
    """
    Represents a named type reference in Tiger.
    
    Named types are aliases for other types, allowing for recursive
    type definitions and improved code readability. During type checking,
    named types are resolved to their underlying types.
    
    Attributes:
        symbol (str): The name of the type being referenced
    """
    symbol: str


def are_types_equal(t1: Type, t2: Type) -> bool:
    """
    Determine if two types are equivalent according to Tiger's type rules.
    
    This function implements Tiger's type compatibility rules:
    - Primitive types are equal if they are the same type
    - nil is compatible with any record type
    - Complex types (records, arrays) are equal if they are the same object
      (structural equivalence is not used in Tiger)
    - Named types are resolved during semantic analysis
    
    Args:
        t1 (Type): First type to compare
        t2 (Type): Second type to compare
        
    Returns:
        bool: True if the types are compatible, False otherwise
        
    Examples:
        >>> are_types_equal(IntType(), IntType())
        True
        >>> are_types_equal(NilType(), RecordType([]))
        True
        >>> are_types_equal(StringType(), IntType())
        False
    """
    return (
            # nil is compatible with nil or any record type
            isinstance(t1, NilType)
            and (isinstance(t2, NilType) or isinstance(t2, RecordType))
            or isinstance(t2, NilType)
            and (isinstance(t1, NilType) or isinstance(t1, RecordType))
            # primitive types must match exactly
            or isinstance(t1, IntType)
            and isinstance(t2, IntType)
            or isinstance(t1, StringType)
            and isinstance(t2, StringType)
            or isinstance(t1, VoidType)
            and isinstance(t2, VoidType)
            # complex types use reference equality (same type declaration)
            or t1 is t2
    )
