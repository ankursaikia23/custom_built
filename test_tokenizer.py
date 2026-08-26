from services.formula.tokenizer import Tokenizer

tokenizer=Tokenizer()
tests=[
    "=1+2",
    "=10*5",
    "=A1+B1",
    "=A1*10",
    "=SUM(A1:A5)",
    "=AVERAGE(B1:B10)",
    "=A1+(B1*2)",
]
for formula in tests:
    print(formula)
    print(tokenizer.tokenize(formula))
    print()