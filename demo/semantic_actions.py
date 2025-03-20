import sys
sys.path.append('/Users/rainoftime/Work/teaching')
from tiger.ply import lex
from tiger.ply import yacc

# ---- Lexer ----
tokens = (
    'NUMBER',
    'PLUS',
    'MINUS',
    'TIMES',
    'DIVIDE',
    'LPAREN',
    'RPAREN',
)

# Token rules
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'
t_LPAREN  = r'\('
t_RPAREN  = r'\)'
t_ignore  = ' \t'

def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Illegal character '{t.value[0]}'")
    t.lexer.skip(1)

# Build the lexer
lexer = lex.lex()

# ---- Parser with AST generation ----
class Node:
    def __init__(self, type, children=None, value=None):
        self.type = type
        self.children = children if children else []
        self.value = value
    
    def __str__(self, level=0):
        result = "  " * level + f"{self.type}"
        if self.value is not None:
            result += f": {self.value}"
        result += "\n"
        for child in self.children:
            result += child.__str__(level + 1)
        return result

# Precedence rules
precedence = (
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE'),
)

# Grammar rules with semantic actions
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression'''
    # Create an AST node for the binary operation
    p[0] = Node(p[2], [p[1], p[3]])

def p_expression_group(p):
    'expression : LPAREN expression RPAREN'
    # Just pass up the expression
    p[0] = p[2]

def p_expression_number(p):
    'expression : NUMBER'
    # Create a leaf node for the number
    p[0] = Node('NUM', value=p[1])

def p_error(p):
    if p:
        print(f"Syntax error at '{p.value}'")
    else:
        print("Syntax error at EOF")

# Build the parser
parser = yacc.yacc()

# ---- Evaluator for the AST ----
def evaluate_ast(node):
    if node.type == 'NUM':
        return node.value
    
    left = evaluate_ast(node.children[0])
    right = evaluate_ast(node.children[1])
    
    if node.type == '+':
        return left + right
    elif node.type == '-':
        return left - right
    elif node.type == '*':
        return left * right
    elif node.type == '/':
        return left / right
    
    raise ValueError(f"Unknown operator: {node.type}")

# ---- Demo function ----
def parse_and_evaluate(expression):
    print(f"\nExpression: {expression}")
    
    # Generate AST
    ast = parser.parse(expression)
    print("\nAbstract Syntax Tree:")
    print(ast)
    
    # Evaluate expression
    result = evaluate_ast(ast)
    print(f"Evaluation result: {result}")
    
    return ast, result

# Test with some expressions
if __name__ == "__main__":
    expressions = [
       # "2 + 3",
        "4 * 5 - 6",
        "1 + 2 * 3",
       # "(1 + 2) * 3",
       # "10 / 2 + 3 * 4"
    ]
    
    for expr in expressions:
        parse_and_evaluate(expr)