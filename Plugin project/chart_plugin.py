from PyQt6.QtWidgets import QInputDialog
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
import math

class ChartPlugin:
    def __init__(self,window):
        self.window=window

    def get_data(self):
        data=[]
        selection=self.window.table.selectedRanges()
        columns=[]
        if selection:
            for selected_range in selection:
                for column in range(selected_range.leftColumn(),selected_range.rightColumn()+1):
                    if column not in columns:
                        columns.append(column)
        if not columns:
            columns=[0]
        column=columns[0]
        for row in range(self.window.table.rowCount()):
            item=self.window.table.item(row,column)
            if item:
                try:
                    value=float(item.text())
                    if math.isfinite(value):
                        data.append(value)
                except (ValueError,TypeError):
                    continue
        return data

    def create_chart(self,chart_type="line"):
        data=self.get_data()
        if not data:
            return None
        if chart_type=="pie" and any(value<0 for value in data):
            return None
        figure=Figure()
        canvas=FigureCanvasQTAgg(figure)
        axis=figure.add_subplot(111)
        if chart_type=="bar":
            axis.bar(range(len(data)),data)
        elif chart_type=="pie":
            axis.pie(data)
        else:
            axis.plot(data)
        figure.tight_layout()
        return canvas