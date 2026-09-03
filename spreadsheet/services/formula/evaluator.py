import math
from .ast import (
    NumberNode, ErrorNode, StringNode, CellNode, BinaryOperationNode, FunctionNode, RangeNode,
)

class Evaluator:
    def __init__(
        self,
        sheet=None,
        workbook=None,
    ):
        self.sheet = sheet
        self.workbook = workbook
        self._evaluation_stack = []

    # ERROR HELPER
    @staticmethod
    def _is_error(value):
        return (
            isinstance(value, str)
            and value.startswith("#")
        )

    # AST EVALUATION
    def evaluate(self, node):
        if isinstance(node, ErrorNode):
            return node.error
        if isinstance(node, NumberNode):
            return node.value
        if isinstance(node, StringNode):
            return node.value
        if isinstance(node, CellNode):
            return self.get_cell_value(
                node.reference
            )
        if isinstance(node, RangeNode):
            return self.get_range_values(
                node
            )
        if isinstance(node, BinaryOperationNode):
            left = self.evaluate(
                node.left
            )
            if self._is_error(left):
                return left
            right = self.evaluate(
                node.right
            )
            if self._is_error(right):
                return right
            operator = node.operator

            # ADDITION
            if operator == "+":
                try:
                    return left + right
                except (
                    TypeError,
                    ValueError
                ):
                    return "#VALUE!"

            # SUBSTRACTION
            if operator == "-":
                try:
                    return left - right
                except (
                    TypeError,
                    ValueError
                ):
                    return "#VALUE!"

            # MULTIPLICATION
            if operator == "*":
                try:
                    return left * right
                except (
                    TypeError,
                    ValueError
                ):
                    return "#VALUE!"

            # DIVISION
            if operator == "/":
                # IMPORTANT:
                # CHECK ZERO BEFORE ATTEMPTING DIVISION
                if right == 0:
                    return "#DIV/0!"
                try:
                    return left / right
                except ZeroDivisionError:
                    return "#DIV/0!"
                except (
                    TypeError,
                    ValueError
                ):
                    return "#VALUE!"

            # POWER
            if operator == "^":
                try:
                    return left ** right
                except (
                    TypeError,
                    ValueError,
                    OverflowError
                ):
                    return "#VALUE!"

            # EQUALITY
            if operator == "=":
                return left == right

            # INEQUALITY
            if operator == "<>":
                return left != right

            # COMPARISIONS
            if operator in (
                ">",
                "<",
                ">=",
                "<=",
            ):
                if (
                    isinstance(left, bool)
                    or isinstance(right, bool)
                ):
                    return "#VALUE!"
                try:
                    if operator == ">":
                        return left > right
                    if operator == "<":
                        return left < right
                    if operator == ">=":
                        return left >= right
                    if operator == "<=":
                        return left <= right
                except (
                    TypeError,
                    ValueError
                ):
                    return "#VALUE!"
            return "#VALUE!"
        if isinstance(node, FunctionNode):
            return self.evaluate_function(
                node
            )
        raise ValueError(
            f"Unsupported node: "
            f"{type(node).__name__}"
        )

    # CELL EVALUATION
    def evaluate_cell(self, reference):
        if self.sheet is None:
            raise ValueError(
                "Sheet is required for "
                "cell evaluation"
            )
        target_sheet, cell_reference = (
            self._resolve_reference(
                reference
            )
        )
        if target_sheet is None:
            return "#REF!"
        stack_reference = (
            f"{target_sheet.name}!"
            f"{cell_reference}"
        )
        if stack_reference in self._evaluation_stack:
            return "#CIRC!"
        cell = target_sheet.get_cell(
            cell_reference
        )
        if cell is None:
            return 0
        value = cell.value

        # DIRECT VALUES
        if not isinstance(value, str):
            return value
        
        # PLAIN TEXT
        if not value.startswith("="):
            return value
        from .parser import Parser
        self._evaluation_stack.append(
            stack_reference
        )
        try:
            node = Parser().parse(
                value
            )
            previous_sheet = self.sheet

            # EVALUATE FORMULA IN THE SHEET
            # CONTAINING THE FORMULA
            self.sheet = target_sheet
            try:
                result = self.evaluate(
                    node
                )

                # EXPLICIT ERROR PRESERVATION
                if self._is_error(result):
                    return result
                return result
            finally:
                self.sheet = previous_sheet
        finally:
            self._evaluation_stack.pop()

    # REFEREMCE RESOLUTION
    def _resolve_reference(
        self,
        reference
    ):
        target_sheet = self.sheet
        cell_reference = reference
        if "!" not in reference:
            return (
                target_sheet,
                cell_reference
            )
        if self.workbook is None:
            return (
                None,
                None
            )
        sheet_name, cell_reference = (
            reference.rsplit(
                "!",
                1
            )
        )
        sheet_name = (
            sheet_name
            .strip()
            .strip("'")
        )
        target_sheet = (
            self.workbook.get_sheet(
                sheet_name
            )
        )
        if target_sheet is None:
            return (
                None,
                None
            )
        return (
            target_sheet,
            cell_reference
        )

    # CELL VALUE RESOLUTION
    def get_cell_value(
        self,
        reference
    ):
        if self.sheet is None:
            raise ValueError(
                "Sheet is required for "
                "cell references"
            )
        target_sheet, cell_reference = (
            self._resolve_reference(
                reference
            )
        )
        if target_sheet is None:
            return "#REF!"
        cell = target_sheet.get_cell(
            cell_reference
        )

        # EMPTY / MISSING CELLS ARE ZERO
        if (
            cell is None
            or cell.value in (
                None,
                ""
            )
        ):
            return 0
        value = cell.value

        # DIRECT VALUES
        if isinstance(value, bool):
            return value
        if isinstance(
            value,
            (
                int,
                float
            )
        ):
            return value

        # STRING VALUES
        if isinstance(value, str):

            # FORMULA CELL
            if value.startswith("="):
                qualified_reference = (
                    f"'{target_sheet.name}'!"
                    f"{cell_reference}"
                )
                result = self.evaluate_cell(
                    qualified_reference
                )

                # IMPORTANT:
                # NEVER CONVERT SPREADSHEET ERRORS
                # INTO ORDINARY VALUES
                if self._is_error(result):
                    return result
                return result

            # NUMERIC TEXT
            try:
                return float(value)
            except ValueError:
                return value
        return value

    # RANGE EVALUATION
    def get_range_values(
        self,
        node
    ):
        target_sheet = self.sheet
        if node.sheet_name is not None:
            if self.workbook is None:
                return "#REF!"
            target_sheet = (
                self.workbook.get_sheet(
                    node.sheet_name
                )
            )
            if target_sheet is None:
                return "#REF!"
        start_column, start_row = (
            self.split_reference(
                node.start.reference
            )
        )
        end_column, end_row = (
            self.split_reference(
                node.end.reference
            )
        )
        values = []
        for row in range(
            start_row,
            end_row + 1
        ):
            for column in range(
                start_column,
                end_column + 1
            ):
                reference = (
                    f"{self.column_name(column)}"
                    f"{row}"
                )
                cell = target_sheet.get_cell(
                    reference
                )
                if (
                    cell is None
                    or cell.value in (
                        None,
                        ""
                    )
                ):
                    values.append(0)
                    continue
                value = cell.value
                if isinstance(
                    value,
                    bool
                ):
                    values.append(value)
                    continue
                if isinstance(
                    value,
                    (
                        int,
                        float
                    )
                ):
                    values.append(value)
                    continue
                if isinstance(
                    value,
                    str
                ):
                    if value.startswith("="):
                        qualified_reference = (
                            f"'{target_sheet.name}'!"
                            f"{reference}"
                        )
                        result = (
                            self.evaluate_cell(
                                qualified_reference
                            )
                        )
                        if self._is_error(
                            result
                        ):
                            return result
                        values.append(
                            result
                        )
                        continue
                    try:
                        values.append(
                            float(value)
                        )
                    except ValueError:
                        values.append(
                            value
                        )
                    continue
                values.append(value)
        return values

    # FUNCTION EVALUATION
    def evaluate_function(
        self,
        node
    ):
        name = node.name.upper()
        # IF
        if name == "IF":
            if len(node.args) not in (
                2,
                3
            ):
                return "#VALUE!"
            condition = self.evaluate(
                node.args[0]
            )
            if self._is_error(
                condition
            ):
                return condition
            if condition:
                return self.evaluate(
                    node.args[1]
                )
            if len(node.args) == 3:
                return self.evaluate(
                    node.args[2]
                )
            return False

        # IFERROR
        if name == "IFERROR":
            if len(node.args) != 2:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
            except Exception:
                value = "#VALUE!"
            if self._is_error(value):
                return self.evaluate(
                    node.args[1]
                )
            return value
        
        # ISERROR
        if name == "ISERROR":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
            except Exception:
                return True
            return self._is_error(value)
        
        # ISNUMBER
        if name == "ISNUMBER":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
            except Exception:
                return False
            return (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
            )
        
        # ISTEXT        
        if name == "ISTEXT":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
            except Exception:
                return False
            return isinstance(value, str) and not self._is_error(value)
        
        # ISBLANK
        if name == "ISBLANK":
            if len(node.args) != 1:
                return "#VALUE!"
            argument = node.args[0]
            if isinstance(argument, CellNode):
                target_sheet, cell_reference = (
                    self._resolve_reference(
                        argument.reference
                    )
                )
                if target_sheet is None:
                    return False
                cell = target_sheet.get_cell(
                    cell_reference
                )
                return (
                    cell is None
                    or cell.value in (
                        None,
                        ""
                    )
                )
            return False
        
        # ISLOGICAL        
        if name == "ISLOGICAL":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
            except Exception:
                return False
            return isinstance(value, bool)
        
        # ISNONTEXT
        if name == "ISNONTEXT":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
            except Exception:
                return False
            return not (
                isinstance(value, str)
                and not self._is_error(value)
            )
        
        # ISREF
        if name == "ISREF":
            if len(node.args) != 1:
                return "#VALUE!"
            argument = node.args[0]
            return isinstance(
                argument,
                (CellNode, RangeNode)
            )
        
        # ISERR
        if name == "ISERR":        
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
            except Exception:
                return False
            return (
                self._is_error(value)
                and value != "#N/A"
            )
        
        # ISNA        
        if name == "ISNA":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
            except Exception:
                return False
            return value == "#N/A"
        
        # ISODD  
        if name == "ISODD":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                return int(value) % 2 != 0
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # ISEVEN    
        if name == "ISEVEN":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                return int(value) % 2 == 0
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        
        # SIGN
        if name == "SIGN":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                if value > 0:
                    return 1
                if value < 0:
                    return -1
                return 0
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # POWER    
        if name == "POWER":
            if len(node.args) != 2:
                return "#VALUE!"
            try:
                base = self.evaluate(
                    node.args[0]
                )
                exponent = self.evaluate(
                    node.args[1]
                )
                if self._is_error(base):
                    return base
                if self._is_error(exponent):
                    return exponent
                if (
                    isinstance(base, bool)
                    or isinstance(exponent, bool)
                ):
                    return "#VALUE!"
                return base ** exponent
            except (
                TypeError,
                ValueError,
                OverflowError
            ):
                return "#VALUE!"
            
        # SQRT    
        if name == "SQRT":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"    
                if value < 0:
                    return "#NUM!"
                return math.sqrt(value)
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # PI    
        if name == "PI":
            if len(node.args) != 0:
                return "#VALUE!"
            return math.pi
        
        # EXP        
        if name == "EXP":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                return math.exp(value)
            except (
                TypeError,
                ValueError,
                OverflowError
            ):
                return "#VALUE!"
        
        # LN        
        if name == "LN":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                if value <= 0:
                    return "#NUM!"
                return math.log(value)
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # LOG10    
        if name == "LOG10":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                if value <= 0:
                    return "#NUM!"
                result = math.log10(
                    value
                )
                if math.isclose(
                    result,
                    round(result),
                    rel_tol=1e-12,
                    abs_tol=1e-12
                ):
                    return float(
                        round(result)
                    )
                return result    
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # RADIANS
        if name == "RADIANS":    
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                return math.radians(
                    value
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # DEGREES    
        if name == "DEGREES":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                return math.degrees(
                    value
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # SIN    
        if name == "SIN":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                result = math.sin(
                    value
                )
                if math.isclose(
                    result,
                    round(result),
                    rel_tol=1e-12,
                    abs_tol=1e-12
                ):
                    return float(
                        round(result)
                    )
                return result
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # COS    
        if name == "COS":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                result = math.cos(
                    value
                )    
                if math.isclose(
                    result,
                    round(result),
                    rel_tol=1e-12,
                    abs_tol=1e-12
                ):
                    return float(
                        round(result)
                    )
                return result
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # TAN    
        if name == "TAN":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                result = math.tan(
                    value
                )
                if math.isclose(
                    result,
                    round(result),
                    rel_tol=1e-12,
                    abs_tol=1e-12
                ):
                    return float(
                        round(result)
                    )
                return result
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # ASIN    
        if name == "ASIN":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                if value < -1 or value > 1:
                    return "#NUM!"
                return math.asin(
                    value
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # ACOS    
        if name == "ACOS":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                if value < -1 or value > 1:
                    return "#NUM!"
                return math.acos(
                    value
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # ATAN    
        if name == "ATAN":
            if len(node.args) != 1:
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                return math.atan(
                    value
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # ATAN2    
        if name == "ATAN2":
            if len(node.args) != 2:
                return "#VALUE!"
            try:
                x = self.evaluate(
                    node.args[0]
                )
                y = self.evaluate(
                    node.args[1]
                )
                if self._is_error(x):
                    return x
                if self._is_error(y):
                    return y
                if (
                    isinstance(x, bool)
                    or isinstance(y, bool)
                ):
                    return "#VALUE!"
                if x == 0 and y == 0:
                    return "#DIV/0!"
                return math.atan2(
                    y,
                    x
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            
        # CEILING    
        if name == "CEILING":
            if len(node.args) != 2:
                return "#VALUE!"
            try:
                number = self.evaluate(
                    node.args[0]
                )
                significance = self.evaluate(
                    node.args[1]
                )
                if self._is_error(number):
                    return number
                if self._is_error(significance):
                    return significance
                if (
                    isinstance(number, bool)
                    or isinstance(significance, bool)
                ):
                    return "#VALUE!"
                if significance == 0:
                    return "#DIV/0!"
                if number == 0:
                    return 0
                significance = abs(
                    significance
                )
                if number > 0:
                    return (
                        math.ceil(
                            number / significance
                        )
                        * significance
                    )
                return (
                    math.floor(
                        number / significance
                    )
                    * significance
                )
            except (
                TypeError,
                ValueError,
                OverflowError
            ):
                return "#VALUE!"
            
        # FLOOR    
        if name == "FLOOR":
            if len(node.args) != 2:
                return "#VALUE!"
            try:
                number = self.evaluate(
                    node.args[0]
                )
                significance = self.evaluate(
                    node.args[1]
                )
                if self._is_error(number):
                    return number
                if self._is_error(significance):
                    return significance
                if (
                    isinstance(number, bool)
                    or isinstance(significance, bool)
                ):
                    return "#VALUE!"
                if significance == 0:
                    return "#DIV/0!"
                if number == 0:
                    return 0
                significance = abs(
                    significance
                )
                if number > 0:
                    return (
                        math.floor(
                            number / significance
                        )
                        * significance
                    )
                return (
                    math.ceil(
                        number / significance
                    )
                    * significance
                )
            except (
                TypeError,
                ValueError,
                OverflowError
            ):
                return "#VALUE!"
        
        # LOG    
        if name == "LOG":
            if len(node.args) not in (1, 2):
                return "#VALUE!"
            try:
                value = self.evaluate(
                    node.args[0]
                )
                if self._is_error(value):
                    return value
                if isinstance(value, bool):
                    return "#VALUE!"
                base = (
                    self.evaluate(node.args[1])
                    if len(node.args) == 2
                    else 10
                )
                if self._is_error(base):
                    return base
                if isinstance(base, bool):
                    return "#VALUE!"
                if value <= 0 or base <= 0 or base == 1:
                    return "#NUM!"
                result = math.log(
                    value,
                    base
                )
                if math.isclose(
                    result,
                    round(result),
                    rel_tol=1e-12,
                    abs_tol=1e-12
                ):
                    return float(
                        round(result)
                    )
                return result
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        
        # IFS
        if name == "IFS":
            if (
                len(node.args) == 0
                or len(node.args) % 2 != 0
            ):
                return "#VALUE!"
            for index in range(
                0,
                len(node.args),
                2
            ):
                condition = self.evaluate(
                    node.args[index]
                )
                if self._is_error(
                    condition
                ):
                    return condition
                if condition:
                    return self.evaluate(
                        node.args[index + 1]
                    )
            return "#VALUE!"

        # EVALUATE ARGUMENTS
        values = []
        for argument in node.args:
            result = self.evaluate(
                argument
            )
            if self._is_error(
                result
            ):
                return result
            if isinstance(
                result,
                list
            ):
                values.extend(
                    result
                )
            else:
                values.append(
                    result
                )

        # AGGREGATION
        if name == "SUM":
            if any(
                isinstance(
                    value,
                    str
                )
                for value in values
            ):
                return "#VALUE!"
            try:
                return sum(values)
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        if name == "AVERAGE":
            if not values:
                return "#VALUE!"
            if any(
                isinstance(
                    value,
                    str
                )
                for value in values
            ):
                return "#VALUE!"
            try:
                return (
                    sum(values)
                    / len(values)
                )
            except (
                TypeError,
                ValueError,
                ZeroDivisionError
            ):
                return "#VALUE!"
        if name == "MIN":
            if not values:
                return "#VALUE!"
            if any(
                isinstance(
                    value,
                    str
                )
                for value in values
            ):
                return "#VALUE!"
            try:
                return min(values)
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        if name == "MAX":
            if not values:
                return "#VALUE!"
            if any(
                isinstance(
                    value,
                    str
                )
                for value in values
            ):
                return "#VALUE!"
            try:
                return max(values)
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        if name == "COUNT":
            return len(values)

        # LOGICAL
        if name == "AND":
            try:
                return all(values)
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        if name == "OR":
            try:
                return any(values)
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        if name == "NOT":
            if len(values) != 1:
                return "#VALUE!"
            return not values[0]
        if name == "TRUE":
            if values:
                return "#VALUE!"
            return True
        if name == "FALSE":
            if values:
                return "#VALUE!"
            return False
        if name == "XOR":
            if not values:
                return "#VALUE!"
            return (
                sum(
                    bool(value)
                    for value in values
                )
                % 2
                == 1
            )

        # NUMERIC
        if name == "ABS":
            if len(values) != 1:
                return "#VALUE!"
            try:
                return abs(values[0])
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        if name == "ROUND":
            if len(values) not in (
                1,
                2
            ):
                return "#VALUE!"
            if any(
                isinstance(
                    value,
                    str
                )
                for value in values
            ):
                return "#VALUE!"
            try:

                digits = (
                    int(values[1])
                    if len(values) == 2
                    else 0
                )
                return round(
                    values[0],
                    digits
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        if name == "INT":
            if len(values) != 1:
                return "#VALUE!"
            try:
                return math.floor(
                    values[0]
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
        if name == "MOD":
            if len(values) != 2:
                return "#VALUE!"
            if values[1] == 0:
                return "#DIV/0!"
            try:
                return (
                    values[0]
                    % values[1]
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"

        # TEXT
        if name in (
            "CONCAT",
            "CONCATENATE",
        ):
            return "".join(
                str(value)
                for value in values
            )
        if name == "LEFT":
            if len(values) not in (
                1,
                2
            ):
                return "#VALUE!"
            text = str(
                values[0]
            )
            try:
                count = (
                    int(values[1])
                    if len(values) == 2
                    else 1
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            if count < 0:
                return "#VALUE!"
            return text[:count]
        if name == "RIGHT":
            if len(values) not in (
                1,
                2
            ):
                return "#VALUE!"
            text = str(
                values[0]
            )
            try:
                count = (
                    int(values[1])
                    if len(values) == 2
                    else 1
                )
            except (
                TypeError,
                ValueError
            ):
                return "#VALUE!"
            if count < 0:
                return "#VALUE!"
            if count == 0:
                return ""
            return text[-count:]
        if name == "LEN":
            if len(values) != 1:
                return "#VALUE!"
            return len(
                str(values[0])
            )
        if name == "UPPER":
            if len(values) != 1:
                return "#VALUE!"
            return str(
                values[0]
            ).upper()
        if name == "LOWER":
            if len(values) != 1:
                return "#VALUE!"
            return str(
                values[0]
            ).lower()
        if name == "TRIM":
            if len(values) != 1:
                return "#VALUE!"
            return " ".join(
                str(
                    values[0]
                ).split()
            )
        
        # UNKNOWN FUNCTION
        return "#NAME?"

    # REFERENCE UTILITIES
    def split_reference(
        self,
        reference
    ):
        import re
        match = re.fullmatch(
            r"\$?([A-Za-z]+)\$?(\d+)",
            reference
        )
        if not match:
            raise ValueError(
                f"Invalid cell reference: "
                f"{reference}"
            )
        letters = (
            match.group(1).upper()
        )
        row = int(
            match.group(2)
        )
        column = 0
        for letter in letters:
            column = (
                column * 26
                + ord(letter)
                - 64
            )
        return (
            column,
            row
        )

    def column_name(
        self,
        column
    ):
        result = ""
        while column:
            column, remaining = (
                divmod(
                    column - 1,
                    26
                )
            )
            result = (
                chr(
                    65 + remaining
                )
                + result
            )
        return result