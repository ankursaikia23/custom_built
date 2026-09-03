class FormulaError(Exception):
    """Base class for formula evaluation errors."""

class DivisionByZeroError(FormulaError):
    pass

class InvalidReferenceError(FormulaError):
    pass

class InvalidFunctionError(FormulaError):
    pass

class InvalidArgumentError(FormulaError):
    pass