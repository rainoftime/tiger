from typing import List, Tuple

from activation_records.temp import TempManager
from intermediate_representation.tree import (
    Statement,
    StatementExpression,
    Constant,
    Expression,
    Name,
    BinaryOperation,
    Memory,
    EvaluateSequence,
    Call,
    Sequence,
    Jump,
    ConditionalJump,
    Move,
    Temporary,
)


def is_noop(statement: Statement) -> bool:
    return isinstance(statement, StatementExpression) and \
        isinstance(statement.expression, Constant)


def commute(statement: Statement, expression: Expression) -> bool:
    """A conversitive strategy for deciding whether
     statement and expression are commutative
    """
    return (
            is_noop(statement)
            or isinstance(expression, Name)
            or isinstance(expression, Constant)
    )


def noop_statement() -> Statement:
    return StatementExpression(Constant(0))


def simplified_sequence(first: Statement, second: Statement) -> Statement:
    if is_noop(first):
        return second
    if is_noop(second):
        return first
    return Sequence([first, second])


def do_expression(expression: Expression) -> Tuple[Statement, Expression]:
    if isinstance(expression, BinaryOperation):
        statement, new_expressions = reorder([expression.left, expression.right])
        return statement, BinaryOperation(
            expression.operator, new_expressions[0], new_expressions[1]
        )

    if isinstance(expression, Memory):
        statement, new_expressions = reorder([expression.expression])
        return statement, Memory(new_expressions[0])

    if isinstance(expression, EvaluateSequence):
        substatement, subexpression = do_expression(expression.expression)
        return (
            simplified_sequence(do_statement(expression.statement), substatement),
            subexpression,
        )

    if isinstance(expression, Call):
        statement, new_expressions = reorder(
            [expression.function] + expression.arguments
        )
        return statement, Call(new_expressions[0], new_expressions[1:])

    return noop_statement(), expression


def do_statement(statement: Statement) -> Statement:
    if isinstance(statement, Sequence):
        substatement_list = []
        for substatement in statement.sequence:
            new_substatement = do_statement(substatement)
            if not is_noop(new_substatement):
                substatement_list.append(new_substatement)
        if not substatement_list:
            return noop_statement()
        return Sequence(substatement_list)

    if isinstance(statement, Jump):
        new_statement, new_expressions = reorder([statement.expression])
        return simplified_sequence(
            new_statement, Jump(new_expressions[0], statement.labels)
        )

    if isinstance(statement, ConditionalJump):
        new_statement, new_expressions = reorder([statement.left, statement.right])
        return simplified_sequence(
            new_statement,
            ConditionalJump(
                statement.operator,
                new_expressions[0],
                new_expressions[1],
                statement.true,
                statement.false,
            ),
        )

    if isinstance(statement, Move):
        if isinstance(statement.temporary, Temporary) and isinstance(
                statement.expression, Call
        ):
            new_statement, new_expressions = reorder(
                [statement.expression.function] + statement.expression.arguments
            )
            return simplified_sequence(
                new_statement,
                Move(
                    statement.temporary, Call(new_expressions[0], new_expressions[1:])
                ),
            )
        if isinstance(statement.temporary, Temporary):
            new_statement, new_expressions = reorder([statement.expression])
            return simplified_sequence(
                new_statement, Move(statement.temporary, new_expressions[0])
            )
        if isinstance(statement.temporary, Memory):
            new_statement, new_expressions = reorder(
                [statement.temporary.expression, statement.expression]
            )
            return simplified_sequence(
                new_statement, Move(Memory(new_expressions[0]), new_expressions[1])
            )
        if isinstance(statement.temporary, EvaluateSequence):
            substatement = statement.temporary.statement
            return do_statement(
                Sequence(
                    [
                        substatement,
                        Move(statement.temporary.expression, statement.expression),
                    ]
                )
            )

    if isinstance(statement, StatementExpression):
        if isinstance(statement.expression, Call):
            new_statement, new_expressions = reorder(
                [statement.expression.function] + statement.expression.arguments
            )
            statement.expression.function = new_expressions[0]
            statement.expression.arguments = new_expressions[1:]
            return simplified_sequence(
                new_statement,
                StatementExpression(Call(new_expressions[0], new_expressions[1:])),
            )
        else:
            new_statement, new_expressions = reorder([statement.expression])
            return simplified_sequence(
                new_statement, StatementExpression(new_expressions[0])
            )

    return statement


def reorder(expression_list: List[Expression]) -> Tuple[Statement, List[Expression]]:
    if not expression_list:
        return noop_statement(), []

    if isinstance(expression_list[0], Call):
        temporary = TempManager.new_temp()
        expression_list[0] = EvaluateSequence(
            Move(Temporary(temporary), expression_list[0]), Temporary(temporary)
        )
        return reorder(expression_list)

    head_statement, head_expression = do_expression(expression_list[0])
    tail_statement, tail_expressions = reorder(expression_list[1:])
    if commute(tail_statement, head_expression):
        return (
            simplified_sequence(head_statement, tail_statement),
            [head_expression] + tail_expressions,
        )

    temporary = TempManager.new_temp()
    return (
        simplified_sequence(
            simplified_sequence(
                head_statement, Move(Temporary(temporary), head_expression)
            ),
            tail_statement,
        ),
        [Temporary(temporary)] + tail_expressions,
    )


def linear(statement: Statement, statement_list: List[Statement]) -> List[Statement]:
    if isinstance(statement, Sequence):
        linear_list = []
        for substatement in statement.sequence:
            linear_list = linear_list + linear(substatement, [])
        return linear_list + statement_list
    return [statement] + statement_list


def linearize(statement: Statement) -> List[Statement]:
    return linear(do_statement(statement), [])
