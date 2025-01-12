from abc import ABC
from enum import Enum
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class ASTNode(ABC):
    position: int


class Declaration(ASTNode):
    pass


class Type(ASTNode):
    pass


class Expression(ASTNode):
    pass


class Variable(ASTNode):
    pass


class Oper(Enum):
    plus = 1
    minus = 2
    times = 3
    divide = 4
    eq = 5
    neq = 6
    lt = 7
    le = 8
    gt = 9
    ge = 10


# DECLARATION


@dataclass
class DeclarationBlock(ASTNode):
    declaration_list: List[Declaration]


@dataclass
class TypeDec(ASTNode):
    name: str
    type: Type


@dataclass
class TypeDecBlock(Declaration):
    type_dec_list: List[TypeDec]


@dataclass
class NameTy(Type):
    name: str


@dataclass
class Field(ASTNode):
    name: str
    type: str


@dataclass
class RecordTy(Type):
    field_list: List[Field]


@dataclass
class ArrayTy(Type):
    array: str


@dataclass
class VariableDec(Declaration):
    name: str
    type: Optional[str]
    exp: Expression
    escape: bool = False


@dataclass
class FunctionDec(ASTNode):
    name: str
    params: List[Field]
    param_escapes: List[bool]
    return_type: Optional[str]
    body: Expression


@dataclass
class FunctionDecBlock(Declaration):
    function_dec_list: List[FunctionDec]


# EXPRESSION


@dataclass
class VarExp(Expression):
    var: Variable


@dataclass
class NilExp(Expression):
    pass


@dataclass
class IntExp(Expression):
    int: int


@dataclass
class StringExp(Expression):
    string: str


@dataclass
class CallExp(Expression):
    func: str
    args: List[Expression]


@dataclass
class OpExp(Expression):
    oper: Oper
    left: Expression
    right: Expression


@dataclass
class ExpField(ASTNode):
    name: str
    exp: Expression


@dataclass
class RecordExp(Expression):
    type: str
    fields: List[ExpField]


@dataclass
class SeqExp(Expression):
    seq: List[Expression]


@dataclass
class AssignExp(Expression):
    var: Variable
    exp: Expression


@dataclass
class IfExp(Expression):
    test: Expression
    then_do: Expression
    else_do: Optional[Expression]


@dataclass
class WhileExp(Expression):
    test: Expression
    body: Expression


@dataclass
class BreakExp(Expression):
    pass


@dataclass
class ForExp(Expression):
    var: str
    lo: Expression
    hi: Expression
    body: Expression
    escape: bool = False


@dataclass
class LetExp(Expression):
    decs: DeclarationBlock
    body: SeqExp


@dataclass
class ArrayExp(Expression):
    type: str
    size: Expression
    init: Expression


@dataclass
class EmptyExp(Expression):
    pass


# VARIABLE


@dataclass
class SimpleVar(Variable):
    sym: str


@dataclass
class FieldVar(Variable):
    var: Variable
    sym: str


@dataclass
class SubscriptVar(Variable):
    var: Variable
    exp: Expression
