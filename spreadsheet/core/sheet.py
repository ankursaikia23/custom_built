from .cell import Cell

class Sheet:
    def __init__(self,name):
        self.name=name
        self.cells={}
        
    def set_cell(self,reference,value):
        self.cells[reference]=Cell(value)
    
    def get_cell(self,reference):
        return self.cells.get(reference)