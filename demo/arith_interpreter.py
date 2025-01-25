from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


# Token types
class TokenType(Enum):
    NUMBER = 'NUMBER'
    PLUS = '+'
    MINUS = '-'
    MULTIPLY = '*'
    DIVIDE = '/'
    EOF = 'EOF'
    LPAREN = '('
    RPAREN = ')'


@dataclass
class Token:
    type: TokenType
    value: Optional[str] = None


# AST nodes
@dataclass
class Node:
    pass


@dataclass
class NumberNode(Node):
    value: float


@dataclass
class BinOpNode(Node):
    left: Node
    operator: Token
    right: Node


class Lexer:
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.current_char = self.text[0] if text else None

    def advance(self):
        self.pos += 1
        self.current_char = self.text[self.pos] if self.pos < len(self.text) else None

    def skip_whitespace(self):
        while self.current_char and self.current_char.isspace():
            self.advance()

    def number(self):
        result = ''
        while self.current_char and self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return float(result)

    def get_next_token(self):
        while self.current_char:
            if self.current_char.isspace():
                self.skip_whitespace()
                continue

            if self.current_char.isdigit():
                return Token(TokenType.NUMBER, str(self.number()))

            if self.current_char == '+':
                self.advance()
                return Token(TokenType.PLUS)

            if self.current_char == '-':
                self.advance()
                return Token(TokenType.MINUS)

            if self.current_char == '*':
                self.advance()
                return Token(TokenType.MULTIPLY)

            if self.current_char == '/':
                self.advance()
                return Token(TokenType.DIVIDE)

            if self.current_char == '(':
                self.advance()
                return Token(TokenType.LPAREN)

            if self.current_char == ')':
                self.advance()
                return Token(TokenType.RPAREN)

            raise SyntaxError(f'Invalid character: {self.current_char}')

        return Token(TokenType.EOF)


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token()

    def eat(self, token_type: TokenType):
        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token()
        else:
            raise SyntaxError(f'Expected {token_type}, got {self.current_token.type}')

    def number(self):
        token = self.current_token
        self.eat(TokenType.NUMBER)
        return NumberNode(float(token.value))

    def factor(self):
        token = self.current_token
        if token.type == TokenType.LPAREN:
            self.eat(TokenType.LPAREN)
            node = self.expr()
            self.eat(TokenType.RPAREN)
            return node
        else:
            return self.number()

    def term(self):
        node = self.factor()
        while self.current_token.type == TokenType.MULTIPLY:
            token = self.current_token
            self.eat(TokenType.MULTIPLY)
            node = BinOpNode(node, token, self.factor())
        return node

    def expr(self):
        node = self.term()
        while self.current_token.type in (TokenType.PLUS, TokenType.MINUS):
            token = self.current_token
            if token.type == TokenType.PLUS:
                self.eat(TokenType.PLUS)
            else:
                self.eat(TokenType.MINUS)
            node = BinOpNode(node, token, self.term())
        return node


class Interpreter:
    def visit(self, node: Node):
        if isinstance(node, NumberNode):
            return node.value
        elif isinstance(node, BinOpNode):
            if node.operator.type == TokenType.PLUS:
                return self.visit(node.left) + self.visit(node.right)
            elif node.operator.type == TokenType.MINUS:
                return self.visit(node.left) - self.visit(node.right)
            elif node.operator.type == TokenType.MULTIPLY:
                return self.visit(node.left) * self.visit(node.right)
            elif node.operator.type == TokenType.DIVIDE:
                right_val = self.visit(node.right)
                if right_val == 0:
                    raise ZeroDivisionError("Division by zero")
                return self.visit(node.left) / right_val

    def interpret(self, text: str):
        lexer = Lexer(text)
        parser = Parser(lexer)
        tree = parser.expr()
        return self.visit(tree)


# Example usage
def main():
    interpreter = Interpreter()
    while True:
        try:
            text = input('calc> ')
            if not text:
                continue
            result = interpreter.interpret(text)
            print(result)
        except (SyntaxError, ZeroDivisionError) as e:
            print(f'Error: {e}')
        except KeyboardInterrupt:
            break


if __name__ == '__main__':
    main()
