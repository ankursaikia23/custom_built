from core.formatting import CellFormat

class Cell:
    def __init__(self,reference,value=None):
        self.reference=reference
        self.value=value
        self.format=CellFormat()