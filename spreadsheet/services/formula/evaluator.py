import math
from .ast import (
    NumberNode,
    ErrorNode,
    CellNode,
    BinaryOperationNode,
    FunctionNode,
    RangeNode,
)

class Evaluator:
    def __init__(self, sheet=None, workbook=None):
        self.sheet = sheet
        self.workbook = workbook
        self._evaluation_stack = []

    def evaluate(self,node):
        if isinstance(node, ErrorNode):
            return node.error
        if isinstance(node,NumberNode):
            return node.value
        if isinstance(node, CellNode):
            return self.get_cell_value(
                node.reference
            )
        if isinstance(node,BinaryOperationNode):
            left=self.evaluate(node.left)
            right=self.evaluate(node.right)
            if isinstance(left, str) and left.startswith("#"):
                return left
            
            if isinstance(right, str) and right.startswith("#"):
                return right
            if node.operator == "+":
                try:
                    return left + right
                except (TypeError, ValueError):
                    return "#VALUE!"
            
            if node.operator == "-":
                try:
                    return left - right
                except (TypeError, ValueError):
                    return "#VALUE!"
            
            if node.operator == "*":
                try:
                    return left * right
                except (TypeError, ValueError):
                    return "#VALUE!"
            
            if node.operator == "/":
                if right == 0:
                    return "#DIV/0!"
            
                try:
                    return left / right
                except (TypeError, ValueError):
                    return "#VALUE!"
            
            if node.operator == "^":
                try:
                    return left ** right
                except (TypeError, ValueError):
                    return "#VALUE!"
            
            if node.operator == "=":
                return left == right
            
            if node.operator == "<>":
                return left != right
            
            if node.operator in (
                ">",
                "<",
                ">=",
                "<=",
            ):
                if isinstance(left, bool) or isinstance(right, bool):
                    raise ValueError(
                        "Boolean values only support "
                        "equality comparisons"
                    )
            
                if node.operator == ">":
                    return left > right
            
                if node.operator == "<":
                    return left < right
            
                if node.operator == ">=":
                    return left >= right
            
                if node.operator == "<=":
                    return left <= right
            raise ValueError(f"Unsupported operator: {node.operator}")
        if isinstance(node,RangeNode):
            return self.get_range_values(node)
        if isinstance(node,FunctionNode):
            return self.evaluate_function(node)
        raise ValueError(f"Unsupported node: {type(node).__name__}")
        
    def evaluate_cell(self, reference):
        if self.sheet is None:
            raise ValueError(
                "Sheet is required for cell evaluation"
            )
    
        stack_reference = reference
    
        if "!" in reference:
            sheet_name, cell_reference = reference.rsplit(
                "!",
                1
            )
    
            sheet_name = sheet_name.strip("'")
    
            if self.workbook is None:
                return "#REF!"
    
            target_sheet = self.workbook.get_sheet(
                sheet_name
            )
    
            if target_sheet is None:
                return "#REF!"
    
            stack_reference = (
                f"{sheet_name}!{cell_reference}"
            )
    
            cell = target_sheet.get_cell(
                cell_reference
            )
        else:
            cell = self.sheet.get_cell(reference)
    
        if stack_reference in self._evaluation_stack:
            return "#CIRC!"
    
        if cell is None:
            return 0
    
        value = cell.value
    
        if not isinstance(value, str):
            return value
    
        if not value.startswith("="):
            return self.get_cell_value(
                reference
            )
    
        from .parser import Parser
    
        self._evaluation_stack.append(
            stack_reference
        )
    
        try:
            node = Parser().parse(value)
            return self.evaluate(node)
    
        finally:
            self._evaluation_stack.pop()

    def get_cell_value(self, reference):
        if self.sheet is None:
            raise ValueError(
                "Sheet is required for cell references"
            )
    
        target_sheet = self.sheet
        cell_reference = reference
    
        if "!" in reference:
            sheet_name, cell_reference = reference.rsplit(
                "!",
                1
            )
    
            sheet_name = sheet_name.strip("'")
    
            if self.workbook is None:
                raise ValueError(
                    "Workbook is required for "
                    "cross-sheet references"
                )
    
            target_sheet = self.workbook.get_sheet(
                sheet_name
            )
    
            if target_sheet is None:
                return "#REF!"
    
        cell = target_sheet.get_cell(
            cell_reference
        )
    
        if cell is None or cell.value in (None, ""):
            return 0
    
        value = cell.value
    
        if isinstance(value, bool):
            return value
    
        if isinstance(value, (int, float)):
            return value
    
        if isinstance(value, str):
            if value.startswith("="):
                if target_sheet is self.sheet:
                    return self.evaluate_cell(
                        cell_reference
                    )
        
                qualified_reference = (
                    f"'{target_sheet.name}'!"
                    f"{cell_reference}"
                )
        
                return self.evaluate_cell(
                    qualified_reference
                )
        
            try:
                return float(value)
            except ValueError:
                return value
    
        return value

    def get_range_values(self, node):
        target_sheet = self.sheet
    
        if node.sheet_name is not None:
            if self.workbook is None:
                raise ValueError(
                    "Workbook is required for "
                    "cross-sheet ranges"
                )
    
            target_sheet = self.workbook.get_sheet(
                node.sheet_name
            )
    
            if target_sheet is None:
                return "#REF!"
    
        start_column, start_row = self.split_reference(
            node.start.reference
        )
    
        end_column, end_row = self.split_reference(
            node.end.reference
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
                    f"{self.column_name(column)}{row}"
                )
    
                cell = target_sheet.get_cell(
                    reference
                )
    
                if (
                    cell is None
                    or cell.value in (None, "")
                ):
                    values.append(0)
                    continue
    
                value = cell.value
    
                if isinstance(value, bool):
                    values.append(value)
                    continue
    
                if isinstance(value, (int, float)):
                    values.append(value)
                    continue
    
                if isinstance(value, str):
                    try:
                        values.append(float(value))
                    except ValueError:
                        raise ValueError(
                            f"Cell {reference} does not "
                            "contain a numeric value"
                        )
                    continue
    
                values.append(value)
    
        return values
  
    def evaluate_function(self, node):
        values = []
    
        for argument in node.args:
            result = self.evaluate(argument)
    
            if isinstance(result, str) and result.startswith("#"):
                return result
    
            if isinstance(result, list):
                for value in result:
                    if isinstance(value, str) and value.startswith("#"):
                        return value
    
                values.extend(result)
            else:
                values.append(result)
    
        name = node.name.upper()
    
        if name == "SUM":
            if any(
                isinstance(value, str)
                for value in values
            ):
                return "#VALUE!"
    
            try:
                return sum(values)
            except (TypeError, ValueError):
                return "#VALUE!"
    
        if name == "AVERAGE":
            if not values:
                return "#VALUE!"
    
            if any(
                isinstance(value, str)
                for value in values
            ):
                return "#VALUE!"
    
            try:
                return sum(values) / len(values)
            except (TypeError, ValueError, ZeroDivisionError):
                return "#VALUE!"
    
        if name == "MIN":
            if not values:
                return "#VALUE!"
    
            if any(
                isinstance(value, str)
                for value in values
            ):
                return "#VALUE!"
    
            try:
                return min(values)
            except (TypeError, ValueError):
                return "#VALUE!"
    
        if name == "MAX":
            if not values:
                return "#VALUE!"
    
            if any(
                isinstance(value, str)
                for value in values
            ):
                return "#VALUE!"
    
            try:
                return max(values)
            except (TypeError, ValueError):
                return "#VALUE!"
    
        if name == "COUNT":
            return len(values)
    
        if name == "AND":
            try:
                return all(values)
            except (TypeError, ValueError):
                return "#VALUE!"
    
        if name == "OR":
            try:
                return any(values)
            except (TypeError, ValueError):
                return "#VALUE!"
    
        if name == "NOT":
            if len(values) != 1:
                return "#VALUE!"
    
            return not values[0]
    
        if name == "ABS":
            if len(values) != 1:
                return "#VALUE!"
    
            try:
                return abs(values[0])
            except (TypeError, ValueError):
                return "#VALUE!"
    
        if name == "ROUND":
            if len(values) not in (1, 2):
                return "#VALUE!"
    
            if any(
                isinstance(value, str)
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
    
            except (TypeError, ValueError):
                return "#VALUE!"
    
        if name == "INT":
            if len(values) != 1:
                return "#VALUE!"
    
            try:
                return math.floor(values[0])
            except (TypeError, ValueError):
                return "#VALUE!"
    
        if name == "MOD":
            if len(values) != 2:
                return "#VALUE!"
    
            if values[1] == 0:
                return "#DIV/0!"
    
            try:
                return values[0] % values[1]
            except (TypeError, ValueError):
                return "#VALUE!"
    
        return "#NAME?"
    
    def split_reference(self,reference):
        import re
        match=re.fullmatch(r"\$?([A-Za-z]+)\$?(\d+)",reference)
        if not match:
            raise ValueError(f"Invalid cell reference: {reference}")
        letters=match.group(1).upper()
        row=int(match.group(2))
        column=0
        for letter in letters:
            column=column*26+(ord(letter)-64)
        return column,row
    
    def column_name(self,column):
        result=""
        while column:
            column,remaining=divmod(column-1,26)
            result=chr(65+remaining)+result
        return result