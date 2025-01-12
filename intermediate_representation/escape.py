from typing import Union

from dataclasses import dataclass

import parser.ast_nodes as ast
from semantic_analysis.table import SymbolTable


@dataclass
class ParameterEscape:
    escape: bool = False


@dataclass
class EscapeEntry:
    depth: int
    variable: Union[ast.ForExp, ast.VariableDec, ParameterEscape]


class EscapeError(Exception):
    def __init__(self, message: str, position: int):
        self.message = message
        self.position = position


def find_escape(expression: ast.Expression):
    traverse_expression(SymbolTable[EscapeEntry](), 0, expression)


def traverse_expression(
        escape_env: SymbolTable[EscapeEntry], depth: int, expression: ast.Expression
):
    if isinstance(
            expression, (ast.NilExp, ast.IntExp, ast.StringExp, ast.BreakExp, ast.EmptyExp)
    ):
        return

    elif isinstance(expression, ast.VarExp):
        traverse_variable(escape_env, depth, expression.var)

    elif isinstance(expression, ast.CallExp):
        for argument_expression in expression.args:
            traverse_expression(escape_env, depth, argument_expression)

    elif isinstance(expression, ast.OpExp):
        traverse_expression(escape_env, depth, expression.left)
        traverse_expression(escape_env, depth, expression.right)

    elif isinstance(expression, ast.RecordExp):
        for field in expression.fields:
            traverse_expression(escape_env, depth, field.exp)

    elif isinstance(expression, ast.SeqExp):
        for sequence_expression in expression.seq:
            traverse_expression(escape_env, depth, sequence_expression)

    elif isinstance(expression, ast.AssignExp):
        traverse_variable(escape_env, depth, expression.var)
        traverse_expression(escape_env, depth, expression.exp)

    elif isinstance(expression, ast.IfExp):
        traverse_expression(escape_env, depth, expression.test)
        traverse_expression(escape_env, depth, expression.then_do)
        if expression.else_do is not None:
            traverse_expression(escape_env, depth, expression.else_do)

    elif isinstance(expression, ast.WhileExp):
        traverse_expression(escape_env, depth, expression.test)
        traverse_expression(escape_env, depth, expression.body)

    elif isinstance(expression, ast.ForExp):
        traverse_expression(escape_env, depth, expression.lo)
        traverse_expression(escape_env, depth, expression.hi)
        escape_env.begin_scope()
        escape_env.add(expression.var, EscapeEntry(depth, expression))
        traverse_expression(escape_env, depth, expression.body)
        escape_env.end_scope()

    elif isinstance(expression, ast.LetExp):
        escape_env.begin_scope()
        for declaration in expression.decs.declaration_list:
            traverse_declaration(escape_env, depth, declaration)
        traverse_expression(escape_env, depth, expression.body)
        escape_env.end_scope()

    elif isinstance(expression, ast.ArrayExp):
        traverse_expression(escape_env, depth, expression.size)
        traverse_expression(escape_env, depth, expression.init)

    else:
        raise EscapeError(
            "Unknown expression kind for escape finding", expression.position
        )


def traverse_declaration(
        escape_env: SymbolTable[EscapeEntry], depth: int, declaration: ast.Declaration
):
    if isinstance(declaration, ast.TypeDecBlock):
        return

    elif isinstance(declaration, ast.VariableDec):
        traverse_expression(escape_env, depth, declaration.exp)
        escape_env.add(declaration.name, EscapeEntry(depth, declaration))

    elif isinstance(declaration, ast.FunctionDecBlock):
        for function_declaration in declaration.function_dec_list:
            escape_env.begin_scope()
            for parameter in function_declaration.params:
                escape_env.add(
                    parameter.name, EscapeEntry(depth + 1, ParameterEscape())
                )
            traverse_expression(escape_env, depth + 1, function_declaration.body)
            for index, parameter in enumerate(function_declaration.params):
                parameter_entry = escape_env.find(parameter.name)
                function_declaration.param_escapes[
                    index
                ] = parameter_entry.variable.escape
            escape_env.end_scope()

    else:
        raise EscapeError(
            "Unknown declaration kind for escape finding", declaration.position
        )


def traverse_variable(
        escape_env: SymbolTable[EscapeEntry], depth: int, variable: ast.Variable
):
    if isinstance(variable, ast.SimpleVar):
        escape_entry = escape_env.find(variable.sym)
        if escape_entry is not None and escape_entry.depth < depth:
            escape_entry.variable.escape = True

    elif isinstance(variable, ast.FieldVar):
        traverse_variable(escape_env, depth, variable.var)

    elif isinstance(variable, ast.SubscriptVar):
        traverse_variable(escape_env, depth, variable.var)
        traverse_expression(escape_env, depth, variable.exp)

    else:
        raise EscapeError("Unknown variable kind for escape finding", variable.position)
