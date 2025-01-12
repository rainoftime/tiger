import parser.ast_nodes as Node
import ply.yacc as yacc
from lexer.lex import tokens

# flake8: noqa ANN001

# CONFIGURATION

start = "expression"

precedence = (
    ("nonassoc", "ASSIGN"),
    ("left", "OR"),
    ("left", "AND"),
    ("nonassoc", "EQ", "NEQ", "GT", "LT", "GE", "LE"),
    ("left", "PLUS", "MINUS"),
    ("left", "TIMES", "DIVIDE"),
    ("right", "UMINUS"),  # Unary minus operator
)


# EMPTY


def p_empty(p):
    "empty :"
    pass


def p_empty_list(p):
    "empty_list : empty"
    p[0] = []


# DECLARATION


def p_declaration_block(p):
    """
    declaration_block : empty_declaration_block
                      | ne_declaration_block
    """
    p[0] = p[1]


def p_empty_declaration_block(p):
    "empty_declaration_block : empty_list"
    p[0] = Node.DeclarationBlock(position=p.lexer.lineno - 1, declaration_list=p[1])


def p_ne_declaration_block(p):
    "ne_declaration_block : declaration_list"
    p[0] = Node.DeclarationBlock(
        position=p.slice[1].value[0].position, declaration_list=p[1]
    )


def p_declaration(p):
    """
    declaration : type_dec_block
                | variable_dec
                | function_dec_block
    """
    p[0] = p[1]


# Non-empty declaration list.
def p_declaration_list(p):
    """
    declaration_list : declaration_list_iter
                     | declaration_list_end
    """
    p[0] = p[1]


def p_declaration_list_iter(p):
    "declaration_list_iter : declaration_list declaration"
    p[0] = p[1]
    p[0].append(p[2])


def p_declaration_list_end(p):
    "declaration_list_end : declaration"
    p[0] = [p[1]]


def p_type_dec_block(p):
    """
    type_dec_block : type_dec_list
    """
    p[0] = Node.TypeDecBlock(position=p.slice[1].value[0].position, type_dec_list=p[1])


def p_type_dec(p):
    "type_dec : TYPE ID EQ type"
    p[0] = Node.TypeDec(position=p.lineno(1), name=p[2], type=p[4])


# Non-empty type declaration list.
def p_type_dec_list(p):
    """
    type_dec_list : type_dec_list_iter
                  | type_dec_list_end
    """
    p[0] = p[1]


def p_type_dec_list_iter(p):
    "type_dec_list_iter : type_dec_list type_dec"
    p[0] = p[1]
    p[0].append(p[2])


def p_type_dec_list_end(p):
    "type_dec_list_end : type_dec"
    p[0] = [p[1]]


def p_type(p):
    """
    type : name_ty
         | record_ty
         | array_ty
    """
    p[0] = p[1]


def p_name_ty(p):
    "name_ty : ID"
    p[0] = Node.NameTy(position=p.lineno(1), name=p[1])


def p_record_ty(p):
    """
    record_ty : LBRACE field_list RBRACE
    """
    p[0] = Node.RecordTy(position=p.lineno(1), field_list=p[2])


def p_array_ty(p):
    "array_ty : ARRAY OF ID"
    p[0] = Node.ArrayTy(position=p.lineno(1), array=p[3])


def p_field(p):
    "field : ID COLON ID"
    p[0] = Node.Field(position=p.lineno(1), name=p[1], type=p[3])


def p_field_list(p):
    """
    field_list : empty_list
               | ne_field_list
    """
    p[0] = p[1]


# Non-empty record field or function parameter list.
def p_ne_field_list(p):
    """
    ne_field_list : ne_field_list_end
               | ne_field_list_iter
    """
    p[0] = p[1]


def p_ne_field_list_iter(p):
    "ne_field_list_iter : ne_field_list COMMA field"
    p[0] = p[1]
    p[0].append(p[3])


def p_ne_field_list_end(p):
    "ne_field_list_end : field"
    p[0] = [p[1]]


def p_variable_dec(p):
    """
    variable_dec : variable_dec_no_type
                 | variable_dec_with_type
    """
    p[0] = p[1]


def p_variable_dec_no_type(p):
    "variable_dec_no_type : VAR ID ASSIGN expression"
    p[0] = Node.VariableDec(position=p.lineno(1), name=p[2], type=None, exp=p[4])


def p_variable_dec_with_type(p):
    "variable_dec_with_type : VAR ID COLON ID ASSIGN expression"
    p[0] = Node.VariableDec(position=p.lineno(1), name=p[2], type=p[4], exp=p[6])


def p_function_dec_block(p):
    """
    function_dec_block : function_dec_list
    """
    p[0] = Node.FunctionDecBlock(
        position=p.slice[1].value[0].position, function_dec_list=p[1]
    )


def p_function_dec(p):
    """
    function_dec : function_dec_no_type
                 | function_dec_with_type
    """
    p[0] = p[1]


def p_function_dec_no_type(p):
    "function_dec_no_type : FUNCTION ID LPAREN field_list RPAREN EQ expression"
    parameters = p[4]
    p[0] = Node.FunctionDec(
        position=p.lineno(1),
        name=p[2],
        params=parameters,
        param_escapes=[False for _ in parameters],
        return_type=None,
        body=p[7],
    )


def p_function_dec_with_type(p):
    "function_dec_with_type : FUNCTION ID LPAREN field_list RPAREN COLON ID EQ expression"
    parameters = p[4]
    p[0] = Node.FunctionDec(
        position=p.lineno(1),
        name=p[2],
        params=parameters,
        param_escapes=[False for _ in parameters],
        return_type=p[7],
        body=p[9],
    )


# Non-empty function declaration list.
def p_function_dec_list(p):
    """
    function_dec_list : function_dec_list_iter
                      | function_dec_list_end
    """
    p[0] = p[1]


def p_function_dec_list_iter(p):
    "function_dec_list_iter : function_dec_list function_dec"
    p[0] = p[1]
    p[0].append(p[2])


def p_function_dec_list_end(p):
    "function_dec_list_end : function_dec"
    p[0] = [p[1]]


# EXPRESSION


def p_expression(p):
    """
    expression : paren_exp
               | var_exp
               | nil_exp
               | int_exp
               | string_exp
               | call_exp
               | op_exp
               | record_exp
               | seq_exp
               | assign_exp
               | if_then_exp
               | if_then_else_exp
               | while_exp
               | break_exp
               | for_exp
               | let_exp
               | array_exp
               | empty_exp
    """
    p[0] = p[1]


def p_paren_exp(p):
    "paren_exp : LPAREN expression RPAREN"
    p[0] = p[2]


def p_var_exp(p):
    "var_exp : variable"
    p[0] = Node.VarExp(position=p.slice[1].value.position, var=p[1])


def p_nil_exp(p):
    "nil_exp : NIL"
    p[0] = Node.NilExp(position=p.lineno(1))


def p_int_exp(p):
    "int_exp : INT"
    p[0] = Node.IntExp(position=p.lineno(1), int=p[1])


def p_string_exp(p):
    "string_exp : STRING"
    p[0] = Node.StringExp(position=p.lineno(1), string=p[1])


def p_call_exp(p):
    "call_exp : ID LPAREN arg_list RPAREN"
    p[0] = Node.CallExp(position=p.lineno(1), func=p[1], args=p[3])


def p_arg_list(p):
    """
    arg_list : empty_list
             | exp_list
    """
    p[0] = p[1]


# Non-empty expression list.
def p_exp_list(p):
    """
    exp_list : exp_list_iter
             | exp_list_end
    """
    p[0] = p[1]


def p_exp_list_iter(p):
    "exp_list_iter : exp_list COMMA expression"
    p[0] = p[1]
    p[0].append(p[3])


def p_exp_list_end(p):
    "exp_list_end : expression"
    p[0] = [p[1]]


def p_op_exp(p):
    """
    op_exp : unary_minus_exp
           | binary_plus_exp
           | binary_minus_exp
           | binary_times_exp
           | binary_divide_exp
           | binary_eq_exp
           | binary_neq_exp
           | binary_lt_exp
           | binary_le_exp
           | binary_gt_exp
           | binary_ge_exp
           | binary_and_exp
           | binary_or_exp
    """
    p[0] = p[1]


def p_unary_minus_exp(p):
    "unary_minus_exp : MINUS expression %prec UMINUS"
    p[0] = Node.OpExp(
        position=p.lineno(1),
        oper=Node.Oper.minus,
        left=Node.IntExp(position=p.lineno(1), int=0),
        right=p[2],
    )


def p_binary_plus_exp(p):
    "binary_plus_exp : expression PLUS expression"
    p[0] = Node.OpExp(position=p.lineno(2), oper=Node.Oper.plus, left=p[1], right=p[3])


def p_binary_minus_exp(p):
    "binary_minus_exp : expression MINUS expression"
    p[0] = Node.OpExp(position=p.lineno(2), oper=Node.Oper.minus, left=p[1], right=p[3])


def p_binary_times_exp(p):
    "binary_times_exp : expression TIMES expression"
    p[0] = Node.OpExp(position=p.lineno(2), oper=Node.Oper.times, left=p[1], right=p[3])


def p_binary_divide_exp(p):
    "binary_divide_exp : expression DIVIDE expression"
    p[0] = Node.OpExp(
        position=p.lineno(2), oper=Node.Oper.divide, left=p[1], right=p[3]
    )


def p_binary_eq_exp(p):
    "binary_eq_exp : expression EQ expression"
    p[0] = Node.OpExp(position=p.lineno(2), oper=Node.Oper.eq, left=p[1], right=p[3])


def p_binary_neq_exp(p):
    "binary_neq_exp : expression NEQ expression"
    p[0] = Node.OpExp(position=p.lineno(2), oper=Node.Oper.neq, left=p[1], right=p[3])


def p_binary_lt_exp(p):
    "binary_lt_exp : expression LT expression"
    p[0] = Node.OpExp(position=p.lineno(2), oper=Node.Oper.lt, left=p[1], right=p[3])


def p_binary_le_exp(p):
    "binary_le_exp : expression LE expression"
    p[0] = Node.OpExp(position=p.lineno(2), oper=Node.Oper.le, left=p[1], right=p[3])


def p_binary_gt_exp(p):
    "binary_gt_exp : expression GT expression"
    p[0] = Node.OpExp(position=p.lineno(2), oper=Node.Oper.gt, left=p[1], right=p[3])


def p_binary_ge_exp(p):
    "binary_ge_exp : expression GE expression"
    p[0] = Node.OpExp(position=p.lineno(2), oper=Node.Oper.ge, left=p[1], right=p[3])


def p_binary_and_exp(p):
    "binary_and_exp : expression AND expression"
    p[0] = Node.IfExp(
        position=p.lineno(2),
        test=p[1],
        then_do=p[3],
        else_do=Node.IntExp(position=p.lineno(2), int=0),
    )


def p_binary_or_exp(p):
    "binary_or_exp : expression OR expression"
    p[0] = Node.IfExp(
        position=p.lineno(2),
        test=p[1],
        then_do=Node.IntExp(position=p.lineno(2), int=1),
        else_do=p[3],
    )


def p_record_exp(p):
    "record_exp : ID LBRACE exp_field_list RBRACE"
    p[0] = Node.RecordExp(position=p.lineno(1), type=p[1], fields=p[3])


def p_exp_field(p):
    "exp_field : ID EQ expression"
    p[0] = Node.ExpField(position=p.lineno(1), name=p[1], exp=p[3])


def p_exp_field_list(p):
    """
    exp_field_list : empty_list
                   | ne_exp_field_list
    """
    p[0] = p[1]


# Non-empty expression list.
def p_ne_exp_field_list(p):
    """
    ne_exp_field_list : ne_exp_field_list_iter
                      | ne_exp_field_list_end
    """
    p[0] = p[1]


def p_ne_exp_field_list_iter(p):
    "ne_exp_field_list_iter : ne_exp_field_list COMMA exp_field"
    p[0] = p[1]
    p[0].append(p[3])


def p_ne_exp_field_list_end(p):
    "ne_exp_field_list_end : exp_field"
    p[0] = [p[1]]


def p_seq_exp(p):
    "seq_exp : LPAREN ne_exp_seq SEMICOLON expression RPAREN"
    p[2].append(p[4])
    p[0] = Node.SeqExp(position=p.lineno(1), seq=p[2])


# Non-empty expression sequence.
def p_ne_exp_seq(p):
    """
    ne_exp_seq : ne_exp_seq_iter
               | ne_exp_seq_end
    """
    p[0] = p[1]


def p_ne_exp_seq_iter(p):
    "ne_exp_seq_iter : ne_exp_seq SEMICOLON expression"
    p[0] = p[1]
    p[0].append(p[3])


def p_ne_exp_seq_end(p):
    "ne_exp_seq_end : expression"
    p[0] = [p[1]]


def p_assign_exp(p):
    "assign_exp : variable ASSIGN expression"
    p[0] = Node.AssignExp(position=p.lineno(2), var=p[1], exp=p[3])


def p_if_then_exp(p):
    "if_then_exp : IF expression THEN expression"
    p[0] = Node.IfExp(position=p.lineno(1), test=p[2], then_do=p[4], else_do=None)


def p_if_then_else_exp(p):
    "if_then_else_exp : IF expression THEN expression ELSE expression"
    p[0] = Node.IfExp(position=p.lineno(1), test=p[2], then_do=p[4], else_do=p[6])


def p_while_exp(p):
    "while_exp : WHILE expression DO expression"
    p[0] = Node.WhileExp(position=p.lineno(1), test=p[2], body=p[4])


def p_break_exp(p):
    "break_exp : BREAK"
    p[0] = Node.BreakExp(position=p.lineno(1))


def p_for_exp(p):
    "for_exp : FOR ID ASSIGN expression TO expression DO expression"
    p[0] = Node.ForExp(position=p.lineno(1), var=p[2], lo=p[4], hi=p[6], body=p[8])


def p_let_exp(p):
    """
    let_exp : empty_let_exp
            | ne_let_exp
    """
    p[0] = p[1]


def p_empty_let_exp(p):
    "empty_let_exp : LET declaration_block IN empty_list END"
    p[0] = Node.LetExp(
        position=p.lineno(1),
        decs=p[2],
        body=Node.SeqExp(position=p.lineno(3), seq=p[4]),
    )


def p_ne_let_exp(p):
    "ne_let_exp : LET declaration_block IN ne_exp_seq END"
    p[0] = Node.LetExp(
        position=p.lineno(1),
        decs=p[2],
        body=Node.SeqExp(position=p.slice[4].value[0].position, seq=p[4]),
    )


def p_array_exp(p):
    "array_exp : ID LBRACK expression RBRACK OF expression"
    p[0] = Node.ArrayExp(position=p.lineno(1), type=p[1], size=p[3], init=p[6])


def p_empty_exp(p):
    "empty_exp : empty"
    p[0] = Node.EmptyExp(position=p.lexer.lineno - 1)


# VARIABLE


def p_variable(p):
    """
    variable : simple_var
             | field_var
             | subscript_var
             | subscript_var_aux
    """
    p[0] = p[1]


def p_simple_var(p):
    "simple_var : ID"
    p[0] = Node.SimpleVar(position=p.lineno(1), sym=p[1])


def p_field_var(p):
    "field_var : variable DOT ID"
    p[0] = Node.FieldVar(position=p.lineno(2), var=p[1], sym=p[3])


def p_subscript_var(p):
    "subscript_var : variable LBRACK expression RBRACK"
    p[0] = Node.SubscriptVar(position=p.lineno(2), var=p[1], exp=p[3])


def p_subscript_var_aux(p):
    "subscript_var_aux : ID LBRACK expression RBRACK"
    p[0] = Node.SubscriptVar(
        position=p.lineno(2),
        var=Node.SimpleVar(position=p.lineno(1), sym=p[1]),
        exp=p[3],
    )


# ERROR
class SyntacticError(Exception):
    def __init__(self, value: str, position: int):
        self.value = value
        self.position = position

    def __str__(self):
        return f"Syntax error in input! Unexpected value {self.value} in line {self.position}"


def p_error(p):
    raise SyntacticError(p.value, p.lexer.lineno)


# Build the parser
parser = yacc.yacc()
