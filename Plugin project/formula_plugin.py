from PyQt6.QtWidgets import QMessageBox
import re
class FormulaPlugin:
    def __init__(self,window):
        self.window=window
    def evaluate(self,value):
        if not isinstance(value,str) or not value.startswith("="):
            return value
        formula=value[1:].upper()
        if formula.startswith("SUM("):
            return self.calculate_range(formula[4:-1],sum)
        if formula.startswith("AVERAGE("):
            return self.calculate_range(formula[8:-1],lambda x:sum(x)/len(x) if x else 0)
        if formula.startswith("MIN("):
            return self.calculate_range(formula[4:-1],min)
        if formula.startswith("MAX("):
            return self.calculate_range(formula[4:-1],max)
        try:
            return eval(formula,{"__builtins__":{}},{})
        except:
            return "#ERROR"
    def calculate_range(self,range_text,operation):
        try:
            start,end=range_text.split(":")
            start_row=int(re.findall(r'\d+',start)[0])-1
            end_row=int(re.findall(r'\d+',end)[0])-1
            start_col=ord(re.findall(r'[A-Z]+',start)[0])-65
            end_col=ord(re.findall(r'[A-Z]+',end)[0])-65
            values=[]
            for row in range(start_row,end_row+1):
                for col in range(start_col,end_col+1):
                    item=self.window.table.item(row,col)
                    if item:
                        try:
                            values.append(float(item.text()))
                        except:
                            pass
            return operation(values)
        except:
            return "#ERROR"
    def apply_formula(self,row,column):
        item=self.window.table.item(row,column)
        if item:
            result=self.evaluate(item.text())
            item.setText(str(result))