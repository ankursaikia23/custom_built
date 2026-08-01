from PyQt6.QtCore import Qt

class AlignmentPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def selected_items(self):
        return self.table.selectedItems()

    def align_left(self):
        for item in self.selected_items():
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

    def align_center(self):
        for item in self.selected_items():
            item.setTextAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignVCenter)

    def align_right(self):
        for item in self.selected_items():
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

    def align_top(self):
        for item in self.selected_items():
            item.setTextAlignment((item.textAlignment()&Qt.AlignmentFlag.AlignHorizontal_Mask)|Qt.AlignmentFlag.AlignTop)

    def align_middle(self):
        for item in self.selected_items():
            item.setTextAlignment((item.textAlignment()&Qt.AlignmentFlag.AlignHorizontal_Mask)|Qt.AlignmentFlag.AlignVCenter)

    def align_bottom(self):
        for item in self.selected_items():
            item.setTextAlignment((item.textAlignment()&Qt.AlignmentFlag.AlignHorizontal_Mask)|Qt.AlignmentFlag.AlignBottom)