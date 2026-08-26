from .tokenizer import Tokenizer
from .ast import (
    NumberNode,
    CellNode,
    BinaryOperationNode,
    FunctionNode,
    RangeNode,
)


class Parser:
    def parse(self, formula):
        self.tokens = Tokenizer().tokenize(formula)
        self.position = 0

        node = self.parse_expression()

        if self.position != len(self.tokens):
            raise ValueError("Unexpected token")

        return node

    def current(self):
        if self.position >= len(self.tokens):
            return None

        return self.tokens[self.position]

    def advance(self):
        token = self.current()
        self.position += 1
        return token

    def parse_expression(self):
        node = self.parse_comparison()
    
        return node
    
    
    def parse_comparison(self):
        node = self.parse_addition()
    
        if self.current() and self.current().type in (
            "EQUAL",
            "NOT_EQUAL",
            "GREATER_THAN",
            "LESS_THAN",
            "GREATER_EQUAL",
            "LESS_EQUAL",
        ):
            operator = self.advance().value
            right = self.parse_addition()
    
            node = BinaryOperationNode(
                operator,
                node,
                right,
            )
    
        return node
    
    
    def parse_addition(self):
        node = self.parse_term()
    
        while self.current() and self.current().type in (
            "PLUS",
            "MINUS",
        ):
            operator = self.advance().value
            right = self.parse_term()
    
            node = BinaryOperationNode(
                operator,
                node,
                right,
            )
    
        return node
    
    
    def parse_term(self):
        node = self.parse_power()
    
        while self.current() and self.current().type in (
            "MULTIPLY",
            "DIVIDE",
        ):
            operator = self.advance().value
            right = self.parse_power()
    
            node = BinaryOperationNode(
                operator,
                node,
                right,
            )
    
        return node

    def parse_power(self):
        node = self.parse_primary()

        while self.current() and self.current().type == "POWER":
            operator = self.advance().value
            right = self.parse_primary()

            node = BinaryOperationNode(
                operator,
                node,
                right,
            )

        return node

    def parse_primary(self):
        token = self.current()

        if token is None:
            raise ValueError(
                "Unexpected end of formula"
            )
        if token.type == "MINUS":
            self.advance()
        
            operand = self.parse_primary()
        
            return BinaryOperationNode(
                "-",
                NumberNode(0),
                operand,
            )
        if token.type == "NUMBER":
            self.advance()

            value = (
                float(token.value)
                if "." in token.value
                else int(token.value)
            )

            return NumberNode(value)

        if token.type == "CELL":
            self.advance()

            if (
                self.current()
                and self.current().type == "COLON"
            ):
                self.advance()

                end = self.advance()

                if (
                    end is None
                    or end.type != "CELL"
                ):
                    raise ValueError(
                        "Invalid range"
                    )

                return RangeNode(
                    CellNode(token.value),
                    CellNode(end.value),
                )

            return CellNode(token.value)

        if token.type == "FUNCTION":
            name = self.advance().value

            if (
                not self.current()
                or self.current().type != "LPAREN"
            ):
                raise ValueError(
                    "Expected '(' after function"
                )

            self.advance()

            args = []

            if (
                self.current()
                and self.current().type != "RPAREN"
            ):
                args.append(
                    self.parse_expression()
                )

                while (
                    self.current()
                    and self.current().type == "COMMA"
                ):
                    self.advance()

                    args.append(
                        self.parse_expression()
                    )

            if (
                not self.current()
                or self.current().type != "RPAREN"
            ):
                raise ValueError(
                    "Expected ')'"
                )

            self.advance()

            return FunctionNode(
                name,
                args,
            )

        if token.type == "LPAREN":
            self.advance()

            node = self.parse_expression()

            if (
                not self.current()
                or self.current().type != "RPAREN"
            ):
                raise ValueError(
                    "Expected ')'"
                )

            self.advance()

            return node

        raise ValueError(
            f"Unexpected token: {token.value}"
        )