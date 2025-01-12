from typing import Optional, List

import parser.ast_nodes as ast
import activation_records.frame as frame
from activation_records.temp import TempManager, TempLabel
from intermediate_representation.fragment import (
    StringFragment,
    FragmentManager,
    ProcessFragment,
)
from intermediate_representation.level import Access, Level, RealLevel
from intermediate_representation.translated_expression import (
    TranslatedExpression,
    Expression,
    convert_to_expression,
    Conditional,
    convert_to_condition,
    patch_true_labels,
    patch_false_labels,
    convert_to_statement,
    NoResult,
)
from intermediate_representation.tree import (
    BinaryOperator,
    BinaryOperation,
    RelationalOperator,
    Condition,
    ConditionalJump,
    Constant,
    Temporary,
    Jump,
    Name,
    Sequence,
    Label,
    Move,
    EvaluateSequence,
    Memory,
    StatementExpression,
    Call,
)
from semantic_analysis.environment import BaseEnvironmentManager


def simple_variable(access: Access, level: Level) -> TranslatedExpression:
    result = Temporary(frame.frame_pointer())
    current_level = level
    while current_level is not access.level:
        static_link_access = current_level.formals()[0]
        result = frame.access_to_exp(static_link_access.access, result)
        current_level = current_level.parent
    return Expression(frame.access_to_exp(access.access, result))


def field_variable(
        variable: TranslatedExpression, field_index: int
) -> TranslatedExpression:
    return Expression(
        Memory(
            BinaryOperation(
                BinaryOperator.plus,
                convert_to_expression(variable),
                BinaryOperation(
                    BinaryOperator.mul,
                    Constant(field_index),
                    Constant(frame.word_size),
                ),
            )
        )
    )


def subscript_variable(
        variable: TranslatedExpression, subscript: TranslatedExpression
) -> TranslatedExpression:
    return Expression(
        Memory(
            BinaryOperation(
                BinaryOperator.plus,
                convert_to_expression(variable),
                BinaryOperation(
                    BinaryOperator.mul,
                    convert_to_expression(subscript),
                    Constant(frame.word_size),
                ),
            )
        )
    )


def nil_expression() -> TranslatedExpression:
    return Expression(Constant(0))


def integer_expression(integer: int) -> TranslatedExpression:
    return Expression(Constant(integer))


def string_expression(string: str) -> TranslatedExpression:
    string_label = TempManager.new_label()
    FragmentManager.add_fragment(StringFragment(string_label, string))
    return Expression(Name(string_label))


def call_expression(
        function_label: TempLabel,
        function_level: RealLevel,
        caller_level: RealLevel,
        argument_list: List[TranslatedExpression],
) -> TranslatedExpression:
    argument_expressions = [
        convert_to_expression(argument) for argument in argument_list
    ]

    if function_label in BaseEnvironmentManager.standard_library_functions:
        return Expression(frame.external_call(function_label, argument_expressions))

    static_link_expression = Temporary(frame.frame_pointer())
    current_level = caller_level
    while current_level is not function_level.parent:
        current_static_link = current_level.formals()[0]
        static_link_expression = frame.access_to_exp(
            current_static_link.access, static_link_expression
        )
        current_level = current_level.parent
    return Expression(
        Call(Name(function_label), [static_link_expression] + argument_expressions)
    )


def arithmetic_operation_expression(
        operator: ast.Oper, left: TranslatedExpression, right: TranslatedExpression
) -> TranslatedExpression:
    return Expression(
        BinaryOperation(
            convert_arithmetic_operator(operator),
            convert_to_expression(left),
            convert_to_expression(right),
        )
    )


def conditional_operation_expression(
        operator: ast.Oper, left: TranslatedExpression, right: TranslatedExpression
) -> TranslatedExpression:
    jump_expression = ConditionalJump(
        convert_conditional_operator(operator),
        convert_to_expression(left),
        convert_to_expression(right),
    )
    return Conditional(Condition(jump_expression, [jump_expression], [jump_expression]))


def string_conditional_operation_expression(
        operator: ast.Oper, left: TranslatedExpression, right: TranslatedExpression
) -> TranslatedExpression:
    jump_expression = ConditionalJump(
        convert_conditional_operator(operator),
        frame.external_call(
            "string_compare",
            [convert_to_expression(left), convert_to_expression(right)],
        ),
        Constant(0),
    )
    return Conditional(Condition(jump_expression, [jump_expression], [jump_expression]))


def record_expression(field_list: List[TranslatedExpression]) -> TranslatedExpression:
    result = TempManager.new_temp()
    creation_sequence = [
        Move(
            Temporary(result),
            frame.external_call(
                "init_record", [Constant(len(field_list) * frame.word_size)]
            ),
        )
    ]

    for index, field_expression in enumerate(field_list):
        field_allocation = Move(
            Memory(
                BinaryOperation(
                    BinaryOperator.plus,
                    Temporary(result),
                    Constant(index * frame.word_size),
                )
            ),
            convert_to_expression(field_expression),
        )
        creation_sequence.append(field_allocation)

    return Expression(EvaluateSequence(Sequence(creation_sequence), Temporary(result)))


def sequence_expression(sequence: List[TranslatedExpression]) -> TranslatedExpression:
    result = convert_to_expression(sequence[0])
    for line in sequence[1:]:
        result = EvaluateSequence(
            StatementExpression(result), convert_to_expression(line)
        )
    return Expression(result)


def assignment_expression(
        variable: TranslatedExpression, expression: TranslatedExpression
) -> TranslatedExpression:
    return NoResult(
        Move(convert_to_expression(variable), convert_to_expression(expression))
    )


def if_expression(
        test: TranslatedExpression,
        then: TranslatedExpression,
        else_do: Optional[TranslatedExpression],
) -> TranslatedExpression:
    test_condition = convert_to_condition(test)
    then_expression = convert_to_expression(then)
    else_expression = (
        convert_to_expression(else_do) if else_do is not None else Constant(0)
    )

    true_label = TempManager.new_label()
    false_label = TempManager.new_label()
    join_label = TempManager.new_label()

    result = TempManager.new_temp()

    patch_true_labels(test_condition.trues, true_label)
    patch_false_labels(test_condition.trues, false_label)

    sequence = Sequence(
        [
            test_condition.statement,
            Label(true_label),
            Move(Temporary(result), then_expression),
            Jump(Name(join_label), [join_label]),
            Label(false_label),
            Move(Temporary(result), else_expression),
            Label(join_label),
        ]
    )

    return Expression(EvaluateSequence(sequence, Temporary(result)))


def while_expression(
        test: TranslatedExpression, body: TranslatedExpression, break_label: TempLabel
) -> TranslatedExpression:
    test_label = TempManager.new_label()
    body_label = TempManager.new_label()

    sequence = Sequence(
        [
            Label(test_label),
            ConditionalJump(
                RelationalOperator.ne,
                convert_to_expression(test),
                Constant(0),
                body_label,
                break_label,
            ),
            Label(body_label),
            convert_to_statement(body),
            Jump(Name(test_label), [test_label]),
            Label(break_label),
        ]
    )

    return NoResult(sequence)


def break_expression(break_label: TempLabel) -> TranslatedExpression:
    return NoResult(Jump(Name(break_label), [break_label]))


def for_expression(
        variable: TranslatedExpression,
        lo: TranslatedExpression,
        hi: TranslatedExpression,
        body: TranslatedExpression,
        break_label: TempLabel,
) -> TranslatedExpression:
    test_label = TempManager.new_label()
    body_label = TempManager.new_label()
    limit = TempManager.new_temp()
    variable_expression = convert_to_expression(variable)

    sequence = Sequence(
        [
            Move(variable_expression, convert_to_expression(lo)),
            Move(Temporary(limit), convert_to_expression(hi)),
            Label(test_label),
            ConditionalJump(
                RelationalOperator.le,
                variable_expression,
                Temporary(limit),
                body_label,
                break_label,
            ),
            Label(body_label),
            convert_to_statement(body),
            Move(
                variable_expression,
                BinaryOperation(BinaryOperator.plus, variable_expression, Constant(1)),
            ),
            Jump(Name(test_label), [test_label]),
            Label(break_label),
        ]
    )

    return NoResult(sequence)


def let_expression(
        declaration_list: List[TranslatedExpression], body_expression: TranslatedExpression
) -> TranslatedExpression:
    declaration_sequence = [
        convert_to_statement(declaration) for declaration in declaration_list
    ]
    return Expression(
        EvaluateSequence(
            Sequence(declaration_sequence), convert_to_expression(body_expression)
        )
    )


def array_expression(
        size: TranslatedExpression, initial_value: TranslatedExpression
) -> TranslatedExpression:
    return Expression(
        frame.external_call(
            "init_array",
            [convert_to_expression(size), convert_to_expression(initial_value)],
        )
    )


def empty_expression() -> TranslatedExpression:
    return NoResult(StatementExpression(Constant(0)))


def proc_entry_exit(function_level: RealLevel, body: TranslatedExpression):
    body_statement = Move(Temporary(frame.return_value()), convert_to_expression(body))
    proc_statement = frame.preserve_callee_registers(
        function_level.frame, frame.shift_view(function_level.frame, body_statement)
    )
    FragmentManager.add_fragment(ProcessFragment(proc_statement, function_level.frame))


def convert_arithmetic_operator(operator: ast.Oper) -> BinaryOperator:
    conversion_dictionary = {
        ast.Oper.plus: BinaryOperator.plus,
        ast.Oper.minus: BinaryOperator.minus,
        ast.Oper.times: BinaryOperator.mul,
        ast.Oper.divide: BinaryOperator.div,
    }
    return conversion_dictionary[operator]


def convert_conditional_operator(operator: ast.Oper) -> RelationalOperator:
    conversion_dictionary = {
        ast.Oper.eq: RelationalOperator.eq,
        ast.Oper.neq: RelationalOperator.ne,
        ast.Oper.lt: RelationalOperator.lt,
        ast.Oper.le: RelationalOperator.le,
        ast.Oper.gt: RelationalOperator.gt,
        ast.Oper.ge: RelationalOperator.ge,
    }
    return conversion_dictionary[operator]
