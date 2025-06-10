#!/usr/bin/env python3
# coding=utf-8
"""
Tiger Language Lexical Analyzer

This module implements the lexical analyzer (tokenizer) for the Tiger programming language.
It uses the PLY (Python Lex-Yacc) library to define token patterns and lexical rules.

The lexer recognizes:
- Keywords (array, if, then, else, while, for, etc.)
- Identifiers (variable and function names)
- Literals (integers and strings)
- Operators (arithmetic, comparison, logical)
- Punctuation (parentheses, brackets, braces, etc.)
- Comments (nested /* */ style)

Special features:
- Nested comment support
- String literal parsing with escape sequences
- Multi-line string support
- Line number tracking for error reporting

Author: Tiger Compiler Team
"""

# flake8: noqa ANN001

# List of token names that the lexer can produce
# These tokens will be used by the parser to build the syntax tree
tokens = (
    # Literal values
    "INT",      # Integer literals (e.g., 42, 0, 123)
    "STRING",   # String literals (e.g., "hello", "world")
    "ID",       # Identifiers (variable/function names)
    
    # Punctuation symbols for language structure
    "COMMA",     # ,
    "COLON",     # :
    "SEMICOLON", # ;
    "LPAREN",    # (
    "RPAREN",    # )
    "LBRACK",    # [
    "RBRACK",    # ]
    "LBRACE",    # {
    "RBRACE",    # }
    "DOT",       # .
    
    # Arithmetic operators
    "PLUS",      # +
    "MINUS",     # -
    "TIMES",     # *
    "DIVIDE",    # /
    
    # Comparison operators
    "EQ",        # =
    "NEQ",       # <>
    "LT",        # <
    "LE",        # <=
    "GT",        # >
    "GE",        # >=
    
    # Logical operators
    "AND",       # &
    "OR",        # |
    
    # Assignment operator
    "ASSIGN",    # :=
    
    # Reserved keywords (converted to uppercase tokens)
    "ARRAY",
    "IF",
    "THEN",
    "ELSE",
    "WHILE",
    "FOR",
    "TO",
    "DO",
    "LET",
    "IN",
    "END",
    "OF",
    "BREAK",
    "NIL",
    "FUNCTION",
    "VAR",
    "TYPE",
)

# Reserved keywords in Tiger language
# These identifiers have special meaning and cannot be used as variable names
reservedKeywords = (
    "array",
    "if",
    "then",
    "else",
    "while",
    "for",
    "to",
    "do",
    "let",
    "in",
    "end",
    "of",
    "break",
    "nil",
    "function",
    "var",
    "type",
)

# Lexer states for handling complex tokens
# INITIAL is the default state, others are for special parsing contexts
states = (
    ("comment", "exclusive"),      # For parsing nested comments
    ("string", "exclusive"),       # For parsing string literals
    ("escapeString", "exclusive"), # For parsing multi-line strings with escapes
)


# Token recognition functions
# These functions define how to recognize and process different token types

def t_INT(t):
    """
    Recognize integer literals.
    
    Pattern: One or more digits
    Action: Convert string to integer value
    """
    r"\d+"
    t.value = int(t.value)
    return t


def t_string(t):
    """
    Begin string literal parsing.
    
    Pattern: Opening double quote
    Action: Switch to string parsing state and record start position
    """
    r"\""
    t.lexer.string_start = t.lexer.lexpos
    t.lexer.begin("string")


def t_string_word(t):
    """
    Parse regular characters within a string literal.
    
    Pattern: Any character except backslash, quote, or newline
    Action: Accumulate characters (no token returned)
    """
    r"[^\\\"\n]+"


def t_string_notWord(t):
    """
    Parse escape sequences within string literals.
    
    Pattern: Escape sequences like \n, \t, \", \\, \^c, \ddd
    Action: Process escape sequences (no token returned)
    """
    r"((\\n)|(\\t)|(\\\^c)|(\\[0-9][0-9][0-9])|(\\\")|(\\\\))+"


def t_string_specialCase(t):
    """
    Begin multi-line string escape sequence.
    
    Pattern: Backslash at end of line
    Action: Switch to escape string state for multi-line strings
    """
    r"\\"
    t.lexer.special_start = t.lexer.lexpos
    t.lexer.begin("escapeString")


def t_escapeString_finish(t):
    """
    End multi-line string escape sequence.
    
    Pattern: Backslash after whitespace
    Action: Return to string parsing state
    """
    r"\\"
    t.lexer.begin("string")


def t_string_STRING(t):
    """
    Complete string literal parsing.
    
    Pattern: Closing double quote
    Action: Extract complete string value and return STRING token
    """
    r"\""
    t.value = t.lexer.lexdata[t.lexer.string_start - 1: t.lexer.lexpos]
    t.type = "STRING"
    t.lexer.begin("INITIAL")
    return t


def t_ID(t):
    """
    Recognize identifiers and keywords.
    
    Pattern: Letter followed by letters, digits, or underscores
    Action: Check if identifier is a reserved keyword and set token type accordingly
    """
    r"[a-zA-Z][a-zA-Z_0-9]*"
    if t.value in reservedKeywords:
        t.type = t.value.upper()  # Convert keyword to uppercase token
    return t


# Comment handling functions
# Tiger supports nested /* */ style comments

def t_comment(t):
    """
    Begin comment parsing.
    
    Pattern: /*
    Action: Switch to comment state and initialize nesting level
    """
    r"\/\*"
    t.lexer.code_start = t.lexer.lexpos
    t.lexer.level = 1
    t.lexer.begin("comment")


def t_comment_begin(t):
    """
    Handle nested comment start.
    
    Pattern: /* within a comment
    Action: Increment nesting level for nested comment support
    """
    r"\/\*"
    t.lexer.level += 1
    pass


def t_comment_COMMENT(t):
    """
    Consume comment content.
    
    Pattern: Any non-comment-delimiter characters
    Action: Ignore comment content (no token returned)
    """
    r"(?!\/\*|\*\/)\S+"
    pass


def t_comment_end(t):
    """
    Handle comment end.
    
    Pattern: */
    Action: Decrement nesting level, return to INITIAL state when level reaches 0
    """
    r"\*\/"
    t.lexer.level -= 1

    if t.lexer.level == 0:
        t.lexer.begin("INITIAL")


# Simple token patterns
# These tokens are recognized by simple regular expressions

# Punctuation tokens
t_COMMA = r","
t_COLON = r":"
t_SEMICOLON = r";"
t_LPAREN = r"\("
t_RPAREN = r"\)"
t_LBRACK = r"\["
t_RBRACK = r"\]"
t_LBRACE = r"\{"
t_RBRACE = r"\}"
t_DOT = r"\."

# Arithmetic operator tokens
t_PLUS = r"\+"
t_MINUS = r"-"
t_TIMES = r"\*"
t_DIVIDE = r"/"

# Comparison operator tokens
t_EQ = r"\="
t_NEQ = r"\<\>"
t_LT = r"\<"
t_LE = r"\<\="
t_GT = r"\>"
t_GE = r"\>\="

# Logical operator tokens
t_AND = r"\&"
t_OR = r"\|"

# Assignment operator token
t_ASSIGN = r"\:\="


def t_INITIAL_comment_escapeString_newline(t):
    """
    Track line numbers across all lexer states.
    
    Pattern: One or more newline characters
    Action: Update line number counter for error reporting
    """
    r"\n+"
    t.lexer.lineno += len(t.value)


# Characters to ignore (whitespace)
# Spaces and tabs are ignored in all lexer states
t_ANY_ignore = " \t"


def t_ANY_error(t):
    """
    Handle lexical errors.
    
    Called when the lexer encounters an unrecognized character.
    Reports the illegal character and its line number.
    """
    print("Illegal character '%s' in line '%s'" % (t.value[0], t.lineno))


# Build the lexer using PLY
from ply import lex as lex
import sys

# Create the lexer instance
lexer = lex.lex()

# Main function for standalone lexer testing
if __name__ == "__main__":
    """
    Standalone lexer testing.
    
    Usage:
        python lex.py [filename]    # Tokenize file
        python lex.py               # Tokenize stdin
    """
    # Read input from file or stdin
    if len(sys.argv) > 1:
        f = open(sys.argv[1], "r")
        data = f.read()
        f.close()
    else:
        # Read from stdin until EOF
        data = ""
        while True:
            try:
                data += raw_input() + "\n"
            except:
                break

    # Tokenize the input
    lex.input(data)

    # Print all tokens
    while True:
        tok = lex.token()
        if not tok:
            break  # No more input
        print(tok)
