from .ast import NumberNode, CellNode, BinaryOperationNode, FunctionNode, RangeNode

class Evaluator:
    def __init__(self,sheet=None):
        self.sheet=sheet

    def evaluate(self,node):
        if isinstance(node,NumberNode):
            return node.value
        if isinstance(node,CellNode):
            return self.get_cell_value(node.reference)
        if isinstance(node,BinaryOperationNode):
            left=self.evaluate(node.left)
            right=self.evaluate(node.right)
            if node.operator=="+":
                return left+right
            if node.operator=="-":
                return left-right
            if node.operator=="*":
                return left*right
            if node.operator=="/":
                if right==0:
                    raise ZeroDivisionError("Division by zero")
                return left/right
            if node.operator=="^":
                return left**right
            raise ValueError(f"Unsupported operator: {node.operator}")
        if isinstance(node,RangeNode):
            return self.get_range_values(node)
        if isinstance(node,FunctionNode):
            return self.evaluate_function(node)
        raise ValueError(f"Unsupported node: {type(node).__name__}")

    def get_cell_value(self,reference):
        if self.sheet is None:
            raise ValueError("Sheet is required for cell references")
        cell=self.sheet.get_cell(reference)
        if cell is None or cell.value in (None,""):
            return 0
        try:
            return float(cell.value)
        except (TypeError,ValueError):
            raise ValueError(f"Cell {reference} does not contain a numeric value")

    def get_range_values(self,node):
        start_column,start_row=self.split_reference(node.start.reference)
        end_column,end_row=self.split_reference(node.end.reference)
        values=[]
        for row in range(start_row,end_row+1):
            for column in range(start_column,end_column+1):
                reference=f"{self.column_name(column)}{row}"
                values.append(self.get_cell_value(reference))
        return values
  
    def evaluate_function(self,node):
        values=[]
        for argument in node.args:
            result=self.evaluate(argument)
            if isinstance(result,list):
                values.extend(result)
            else:
                values.append(result)
        name=node.name.upper()
        if name=="SUM":
            return sum(values)
        if name=="AVERAGE":
            if not values:
                raise ValueError("AVERAGE requires at least one value")
            return sum(values)/len(values)
        if name=="MIN":
            if not values:
                raise ValueError("MIN requires at least one value")
            return min(values)
        if name=="MAX":
            if not values:
                raise ValueError("MAX requires at least one value")
            return max(values)
        if name=="COUNT":
            return len(values)
        raise ValueError(f"Unsupported function: {node.name}")
    
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