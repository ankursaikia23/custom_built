import re

class Token:
    def __init__(self, token_type, value):
        self.type = token_type
        self.value = value

    def __repr__(self):
        return f"Token({self.type!r},{self.value!r})"

class Tokenizer:
    TOKEN_SPECIFICATION = [
        ("NUMBER", r"\d+(?:\.\d+)?"),
        ("SHEET_CELL", r"'[^']+'![A-Za-z]+\$?\d+|[A-Za-z_][A-Za-z0-9_ ]*![A-Za-z]+\$?\d+"),
        ("STRING", r'"(?:[^"]|"")*"'),
        ("CELL", r"\$?[A-Za-z]+\$?\d+"),
        ("FUNCTION", r"[A-Za-z_][A-Za-z0-9_]*"),

        # Comparison operators must come before single-character
        # operators so >=, <= and <> are matched as one token.
        ("COMPARISON", r"<>|>=|<=|=|>|<"),

        ("OPERATOR", r"[+\-*/^]"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("COMMA", r","),
        ("COLON", r":"),
        ("WHITESPACE", r"\s+"),
    ]

    def tokenize(self, formula):
        if not isinstance(formula, str):
            raise TypeError("Formula must be a string")

        if formula.startswith("="):
            formula = formula[1:]

        pattern = "|".join(
            f"(?P<{name}>{regex})"
            for name, regex in self.TOKEN_SPECIFICATION
        )

        tokens = []
        position = 0

        while position < len(formula):
            match = re.match(
                pattern,
                formula[position:]
            )

            if not match:
                raise ValueError(
                    f"Invalid character at position "
                    f"{position}: {formula[position]}"
                )

            token_type = match.lastgroup
            value = match.group()

            position += len(value)

            if token_type == "WHITESPACE":
                continue

            if token_type == "OPERATOR":
                token_type = {
                    "+": "PLUS",
                    "-": "MINUS",
                    "*": "MULTIPLY",
                    "/": "DIVIDE",
                    "^": "POWER",
                }[value]

            elif token_type == "COMPARISON":
                token_type = {
                    "=": "EQUAL",
                    "<>": "NOT_EQUAL",
                    ">": "GREATER_THAN",
                    "<": "LESS_THAN",
                    ">=": "GREATER_EQUAL",
                    "<=": "LESS_EQUAL",
                }[value]

            tokens.append(
                Token(token_type, value)
            )

        return tokens