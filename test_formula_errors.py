from services.formula.errors import (
    FormulaError,
    DivisionByZeroError,
    InvalidReferenceError,
    InvalidFunctionError,
    InvalidArgumentError,
)


# --------------------------------------------------
# 1. Error hierarchy
# --------------------------------------------------

assert issubclass(
    DivisionByZeroError,
    FormulaError
)

assert issubclass(
    InvalidReferenceError,
    FormulaError
)

assert issubclass(
    InvalidFunctionError,
    FormulaError
)

assert issubclass(
    InvalidArgumentError,
    FormulaError
)

print("Error hierarchy: PASS")


# --------------------------------------------------
# 2. Errors can carry messages
# --------------------------------------------------

error = DivisionByZeroError(
    "Cannot divide by zero"
)

assert str(error) == "Cannot divide by zero"

print("Error messages: PASS")


# --------------------------------------------------
# 3. Errors are catchable through FormulaError
# --------------------------------------------------

try:
    raise InvalidReferenceError(
        "Invalid cell reference"
    )

except FormulaError as error:
    assert str(error) == "Invalid cell reference"

print("FormulaError catching: PASS")


# --------------------------------------------------
# 4. Individual errors remain distinct
# --------------------------------------------------

try:
    raise InvalidFunctionError(
        "Unknown function"
    )

except InvalidFunctionError:
    print("Specific error catching: PASS")


print("FORMULA ERROR FOUNDATION: PASS")