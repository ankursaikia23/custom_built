import re
from PyQt6.QtCore import Qt

class FormulaPlugin:
    def __init__(self,window):
        self.window=window
        self.evaluating=set()

    def column_to_number(self,column):
        result=0
        
        for char in column:
            result=result*26+(ord(char)-64)
        return result-1

    def get_cell_value(self,reference):
        reference=reference.upper()
        if reference in self.evaluating:
            return 0
        match=re.fullmatch(r"([A-Z]+)(\d+)",reference.upper())
        if not match:
            return 0
    
        column,row=match.groups()
        row=int(row)-1
        column=self.column_to_number(column)
    
        if row<0 or column<0:
            return 0
        if row>=self.window.table.rowCount():
            return 0
        if column>=self.window.table.columnCount():
            return 0
    
        item=self.window.table.item(row,column)
        if item is None:
            return 0
    
        formula=item.data(Qt.ItemDataRole.UserRole)
    
        if isinstance(formula,str) and formula.startswith("="):
            if reference in self.evaluating:
                return 0
            self.evaluating.add(reference)
            try:
                value=self.evaluate(formula)
                try:
                    return float(value)
                except (ValueError,TypeError):
                    return 0
            finally:
                self.evaluating.discard(reference)
    
        text=item.text().strip()
    
        try:
            return float(text)
        except:
            return 0

    def get_range_values(self,range_text):
        if ":" not in range_text:
            return [self.get_cell_value(range_text)]
        start,end=range_text.upper().split(":")
        start_match=re.fullmatch(r"([A-Z]+)(\d+)",start)
        end_match=re.fullmatch(r"([A-Z]+)(\d+)",end)
        if not start_match or not end_match:
            return []
        start_col,start_row=start_match.groups()
        end_col,end_row=end_match.groups()
        start_col=self.column_to_number(start_col)
        end_col=self.column_to_number(end_col)
        start_row=int(start_row)-1
        end_row=int(end_row)-1
        values=[]
        for row in range(min(start_row,end_row),max(start_row,end_row)+1):
            for col in range(min(start_col,end_col),max(start_col,end_col)+1):
                if row<0 or col<0:
                    continue
                if row>=self.window.table.rowCount():
                    continue
                if col>=self.window.table.columnCount():
                    continue
                item=self.window.table.item(row,col)
                if item is None:
                    values.append(None)
                    continue
                formula=item.data(Qt.ItemDataRole.UserRole)
                if isinstance(formula,str) and formula.startswith("="):
                    value=self.evaluate(formula)
                else:
                    text=item.text().strip()
                    if text=="":
                        values.append(None)
                        continue
                    try:
                        value=float(text)
                    except:
                        value=0
                try:
                    values.append(float(value))
                except:
                    values.append(None)
        return values
    
    def sum_function(self,range_text):
        values=self.get_range_values(range_text)
        return sum(value for value in values if value is not None)
    
    def count_function(self,range_text):
        values=self.get_range_values(range_text)
        return sum(1 for value in values if value is not None)
    
    def average_function(self,range_text):
        values=[value for value in self.get_range_values(range_text) if value is not None]
        if not values:
            return 0
        return sum(values)/len(values)
    
    def min_function(self,range_text):
        values=[value for value in self.get_range_values(range_text) if value is not None]
        if not values:
            return 0
        return min(values)
    
    def max_function(self,range_text):
        values=[value for value in self.get_range_values(range_text) if value is not None]
        if not values:
            return 0
        return max(values)
    
    def replace_functions(self,formula):
        while True:
            match=re.search(r"SUM\(([A-Z0-9:]+)\)",formula)
            if not match:
                break
            formula=formula.replace(match.group(0),str(self.sum_function(match.group(1))),1)
        while True:
            match=re.search(r"COUNT\(([A-Z0-9:]+)\)",formula)
            if not match:
                break
            formula=formula.replace(match.group(0),str(self.count_function(match.group(1))),1)
        while True:
            match=re.search(r"AVERAGE\(([A-Z0-9:]+)\)",formula)
            if not match:
                break
            formula=formula.replace(match.group(0),str(self.average_function(match.group(1))),1)
        while True:
            match=re.search(r"MIN\(([A-Z0-9:]+)\)",formula)
            if not match:
                break
            formula=formula.replace(match.group(0),str(self.min_function(match.group(1))),1)
        while True:
            match=re.search(r"MAX\(([A-Z0-9:]+)\)",formula)
            if not match:
                break
            formula=formula.replace(match.group(0),str(self.max_function(match.group(1))),1)
        return formula
    
    def replace_cell_references(self,formula):
        pattern=r"\b([A-Z]+[0-9]+)\b"
    
        while True:
            match=re.search(pattern,formula)
            if not match:
                break
    
            reference=match.group(1)
            value=self.get_cell_value(reference)
    
            formula=(
                formula[:match.start()]
                +str(value)
                +formula[match.end():]
            )
    
        return formula
    
    def evaluate(self,value):
        if not isinstance(value,str):
            return value
    
        if not value.startswith("="):
            return value
    
        formula=value[1:].strip().upper()
    
        formula=self.replace_functions(formula)
        formula=self.replace_cell_references(formula)
    
        try:
            result=eval(
                formula,
                {"__builtins__":None},
                {}
            )
    
            if isinstance(result,float):
                if result.is_integer():
                    return int(result)
    
            return result
    
        except:
            return "#ERROR"
        
    def apply_formula(self,row,column):
        item=self.window.table.item(row,column)
        if item is None:
            return
        text=item.text()
        if not isinstance(text,str):
            return
        if text.strip()=="":
            item.setData(Qt.ItemDataRole.UserRole,None)
            self.window.is_modified=True
            return
        if not text.startswith("="):
            item.setData(Qt.ItemDataRole.UserRole,None)
            self.window.is_modified=True
            return
        formula=text
        result=self.evaluate(formula)
        item.setData(Qt.ItemDataRole.UserRole,formula)
        self.window.table.blockSignals(True)
        item.setText(str(result))
        self.window.table.blockSignals(False)
        self.window.is_modified=True

    def recalculate(self):
        table=self.window.table
        formulas=[]
        for row in range(table.rowCount()):
            for column in range(table.columnCount()):
                item=table.item(row,column)
                if item is None:
                    continue
                formula=item.data(Qt.ItemDataRole.UserRole)
                if isinstance(formula,str) and formula.startswith("="):
                    formulas.append((item,formula))
        table.blockSignals(True)
        try:
            for item,formula in formulas:
                item.setText(str(self.evaluate(formula)))
        finally:
            table.blockSignals(False)
        
        
    def insert_function(self,function_name):
        table=self.window.table
        item=table.currentItem()
    
        if item is None:
            from PyQt6.QtWidgets import QTableWidgetItem
            row=table.currentRow()
            column=table.currentColumn()
            if row<0 or column<0:
                return
            item=QTableWidgetItem("")
            table.setItem(row,column,item)
    
        item.setText(f"={function_name}()")
        table.editItem(item)