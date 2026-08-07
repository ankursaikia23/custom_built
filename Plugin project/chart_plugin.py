from PyQt6.QtWidgets import QInputDialog
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

class ChartPlugin:
    def __init__(self,window):
        self.window=window
        
    def get_data(self):
        data=[]
        for row in range(self.window.table.rowCount()):
            item=self.window.table.item(row,0)
            if item:
                try:
                    data.append(float(item.text()))
                except:
                    pass
        return data
    
    def create_chart(self,chart_type="line"):
        data=self.get_data()
        figure=Figure()
        canvas=FigureCanvasQTAgg(figure)
        axis=figure.add_subplot(111)
        if chart_type=="bar":
            axis.bar(range(len(data)),data)
        elif chart_type=="pie":
            axis.pie(data)
        else:
            axis.plot(data)
        return canvas