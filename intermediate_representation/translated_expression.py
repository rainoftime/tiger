from abc import ABC
from typing import List

from dataclasses import dataclass

from activation_records.temp import TempLabel, TempManager

from intermediate_representation import tree
from intermediate_representation.tree import (
    EvaluateSequence,
    Constant,
    Move,
    Temporary,
    Label,
    StatementExpression,
    Sequence,
    ConditionalJump,
    RelationalOperator,
)


def patch_true_labels(condition_list: List[ConditionalJump], label: TempLabel):
    for condition in condition_list:
        condition.true = label


def patch_false_labels(condition_list: List[ConditionalJump], label: TempLabel):
    for condition in condition_list:
        condition.false = label


class TranslatedExpression(ABC):
    pass


@dataclass
class Expression(TranslatedExpression):
    expression: tree.Expression


@dataclass
class NoResult(TranslatedExpression):
    statement: tree.Statement


@dataclass
class Conditional(TranslatedExpression):
    condition: tree.Condition


def convert_to_expression(exp: TranslatedExpression) -> tree.Expression:
    if isinstance(exp, Expression):
        return exp.expression

    if isinstance(exp, NoResult):
        return EvaluateSequence(exp.statement, Constant(0))

    if isinstance(exp, Conditional):
        temporary_value = TempManager.new_temp()
        true = TempManager.new_label()
        false = TempManager.new_label()
        patch_true_labels(exp.condition.trues, true)
        patch_false_labels(exp.condition.falses, false)
        return EvaluateSequence(
            Move(Temporary(temporary_value), Constant(1)),
            EvaluateSequence(
                exp.condition.statement,
                EvaluateSequence(
                    Label(false),
                    EvaluateSequence(
                        Move(Temporary(temporary_value), Constant(0)),
                        EvaluateSequence(Label(true), Temporary(temporary_value)),
                    ),
                ),
            ),
        )


def convert_to_statement(exp: TranslatedExpression) -> tree.Statement:
    if isinstance(exp, Expression):
        return StatementExpression(exp.expression)

    if isinstance(exp, NoResult):
        return exp.statement

    if isinstance(exp, Conditional):
        true = TempManager.new_label()
        false = TempManager.new_label()
        patch_true_labels(exp.condition.trues, true)
        patch_false_labels(exp.condition.falses, false)
        return Sequence([exp.condition.statement, Label(true), Label(false)])


def convert_to_condition(exp: TranslatedExpression) -> tree.Condition:
    if isinstance(exp, Expression):
        jump = ConditionalJump(RelationalOperator.ne, exp.expression, Constant(0))
        return tree.Condition(jump, [jump], [jump])

    if isinstance(exp, NoResult):
        raise Exception("Trying to remove_conditional from a NoResult expression.")

    if isinstance(exp, Conditional):
        return exp.condition


def no_op_expression() -> TranslatedExpression:
    return Expression(Constant(0))
