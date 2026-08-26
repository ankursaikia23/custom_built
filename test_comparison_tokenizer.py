from services.formula.tokenizer import Tokenizer

tokenizer = Tokenizer()


# --------------------------------------------------
# Equality
# --------------------------------------------------

tokens = tokenizer.tokenize("=1=1")

assert [
    (token.type, token.value)
    for token in tokens
] == [
    ("NUMBER", "1"),
    ("EQUAL", "="),
    ("NUMBER", "1"),
]

print("Equal: PASS")


# --------------------------------------------------
# Not equal
# --------------------------------------------------

tokens = tokenizer.tokenize("=1<>2")

assert [
    (token.type, token.value)
    for token in tokens
] == [
    ("NUMBER", "1"),
    ("NOT_EQUAL", "<>"),
    ("NUMBER", "2"),
]

print("Not equal: PASS")


# --------------------------------------------------
# Greater than
# --------------------------------------------------

tokens = tokenizer.tokenize("=5>3")

assert [
    (token.type, token.value)
    for token in tokens
] == [
    ("NUMBER", "5"),
    ("GREATER_THAN", ">"),
    ("NUMBER", "3"),
]

print("Greater than: PASS")


# --------------------------------------------------
# Less than
# --------------------------------------------------

tokens = tokenizer.tokenize("=5<10")

assert [
    (token.type, token.value)
    for token in tokens
] == [
    ("NUMBER", "5"),
    ("LESS_THAN", "<"),
    ("NUMBER", "10"),
]

print("Less than: PASS")


# --------------------------------------------------
# Greater or equal
# --------------------------------------------------

tokens = tokenizer.tokenize("=5>=5")

assert [
    (token.type, token.value)
    for token in tokens
] == [
    ("NUMBER", "5"),
    ("GREATER_EQUAL", ">="),
    ("NUMBER", "5"),
]

print("Greater/equal: PASS")


# --------------------------------------------------
# Less or equal
# --------------------------------------------------

tokens = tokenizer.tokenize("=4<=5")

assert [
    (token.type, token.value)
    for token in tokens
] == [
    ("NUMBER", "4"),
    ("LESS_EQUAL", "<="),
    ("NUMBER", "5"),
]

print("Less/equal: PASS")


# --------------------------------------------------
# Cell comparison
# --------------------------------------------------

tokens = tokenizer.tokenize("=A1>B1")

assert [
    (token.type, token.value)
    for token in tokens
] == [
    ("CELL", "A1"),
    ("GREATER_THAN", ">"),
    ("CELL", "B1"),
]

print("Cell comparison: PASS")


# --------------------------------------------------
# Existing arithmetic still works
# --------------------------------------------------

tokens = tokenizer.tokenize("=A1+B1*10")

assert [
    token.type
    for token in tokens
] == [
    "CELL",
    "PLUS",
    "CELL",
    "MULTIPLY",
    "NUMBER",
]

print("Arithmetic regression: PASS")


print("COMPARISON TOKENIZER: PASS")