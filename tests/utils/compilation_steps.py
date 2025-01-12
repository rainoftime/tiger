import os
from activation_records.frame import TempMap
from lexer import lex as le
from parser import parser as p
from ply import lex

import parser.ast_nodes as ast
from semantic_analysis.analyzers import TypedExpression, translate_program


def parse_program(file_name: str) -> ast.Expression:
    cur_file_dir = os.path.dirname(os.path.realpath(__file__))
    upper_of_upper_dir = os.path.dirname(os.path.dirname(cur_file_dir))
    with open(upper_of_upper_dir + "/examples/" + file_name, "r") as file:
        data = file.read()

    # Both the lexer cloning and the parser restart are necessary
    # in order to be able to parse files from successive test cases.
    lexer_clone = le.lexer.clone()
    lex.input(data)
    parse_result = p.parser.parse(data, lexer_clone)
    p.parser.restart()
    return parse_result


def semantic_analysis(file_name: str) -> TypedExpression:
    TempMap.initialize()
    return translate_program(parse_program(file_name))
