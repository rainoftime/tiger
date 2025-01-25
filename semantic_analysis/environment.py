from abc import ABC
from typing import List

from dataclasses import dataclass

from activation_records.temp import TempLabel, TempManager
from intermediate_representation.level import Access, outermost_level, RealLevel
from semantic_analysis.table import SymbolTable
from semantic_analysis.types import Type, IntType, StringType, VoidType


class EnvironmentEntry(ABC):
    pass


@dataclass
class VariableEntry(EnvironmentEntry):
    access: Access
    type: Type
    is_editable: bool = True


@dataclass
class FunctionEntry(EnvironmentEntry):
    level: RealLevel
    label: TempLabel
    formals: List[Type]
    result: Type


class BaseEnvironmentManager:
    # Name of every standard library function, along with its argument and return types.
    standard_library_functions = {
        "char_to_num": ([StringType()], IntType()),
        "exit_program": ([IntType()], VoidType()),
        "flush": ([], VoidType()),
        "not": ([IntType()], IntType()),
        "num_to_char": ([IntType()], StringType()),
        "print_num": ([IntType()], VoidType()),
        "print_string": ([StringType()], VoidType()),
        "read_char": ([], StringType()),
        "read_num": ([], IntType()),
        "string_compare": ([StringType(), StringType()], IntType()),
        "string_concat": ([StringType(), StringType()], StringType()),
        "string_equal": ([StringType(), StringType()], IntType()),
        "string_length": ([StringType()], IntType()),
        "string_substring": ([StringType(), IntType(), IntType()], StringType()),
    }

    @classmethod
    def base_type_environment(cls) -> SymbolTable[Type]:
        environment = SymbolTable[Type]()
        environment.add("int", IntType())
        environment.add("string", StringType())
        return environment

    @classmethod
    def base_value_environment(cls) -> SymbolTable[EnvironmentEntry]:
        environment = SymbolTable[EnvironmentEntry]()
        for function_name in cls.standard_library_functions:
            argument_types, return_type = cls.standard_library_functions[function_name]
            environment.add(
                function_name,
                cls._base_function_entry(
                    TempManager.named_label(function_name), argument_types, return_type
                ),
            )
        return environment

    @classmethod
    def _base_function_entry(
            cls, function_label: str, formal_types: List[Type], return_type: Type
    ) -> FunctionEntry:
        function_level = RealLevel(
            outermost_level, function_label, [False for _ in formal_types]
        )
        return FunctionEntry(function_level, function_label, formal_types, return_type)


if __name__ == "__main__":
    # add an example?
    print("env")
