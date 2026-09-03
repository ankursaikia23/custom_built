from core.formatting import CellFormat

class Cell:
    def __init__(
        self,
        reference,
        value=None
    ):
        self.reference = reference
        self.value = value
        self.format = CellFormat()

        # CACHED RESULT OF FORMULA EVALUATION
        # THE ORIGINAL FORMULA REMIANS IN "VALUE"
        self.calculated_value = None