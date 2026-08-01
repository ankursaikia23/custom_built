import json
import os
from PyQt6.QtWidgets import QFileDialog,QLabel,QTableWidgetItem
from PyQt6.QtGui import QPixmap, QTextDocument
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter

class FilePlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table

    def new_file(self):
        self.table.clearContents()
        self.table.setRowCount(100)
        self.table.setColumnCount(26)
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.clear()
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.clear()
        if hasattr(self.spreadsheet,"history_plugin"):
            self.spreadsheet.history_plugin.save_state()
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=False

    def save_file(self):
        file,_=QFileDialog.getSaveFileName(self.spreadsheet,"Save Project","","JSON Files (*.json)")
        if not file:
            return
        data={"rows":self.table.rowCount(),"cols":self.table.columnCount(),"cells":[],"images":[],"pdfs":[]}
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item=self.table.item(r,c)
                if item:
                    data["cells"].append({"row":r,"col":c,"text":item.text()})
        if hasattr(self.spreadsheet,"image_plugin"):
            for (r,c),path in self.spreadsheet.image_plugin.images.items():
                data["images"].append({"row":r,"col":c,"path":path})
        if hasattr(self.spreadsheet,"pdf_plugin"):
            for (r,c),path in self.spreadsheet.pdf_plugin.pdfs.items():
                data["pdfs"].append({"row":r,"col":c,"path":path})
        with open(file,"w") as f:
            json.dump(data,f,indent=4)
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=False

    def open_file(self):
        file,_=QFileDialog.getOpenFileName(self.spreadsheet,"Open Project","","JSON Files (*.json)")
        if not file:
            return
        with open(file,"r") as f:
            data=json.load(f)
        self.new_file()
        self.table.setRowCount(data["rows"])
        self.table.setColumnCount(data["cols"])
        for cell in data["cells"]:
            self.table.setItem(cell["row"],cell["col"],QTableWidgetItem(cell["text"]))
        if hasattr(self.spreadsheet,"image_plugin"):
            for image in data.get("images",[]):
                if os.path.exists(image["path"]):
                    self.spreadsheet.image_plugin.set_image(image["row"],image["col"],image["path"])
        if hasattr(self.spreadsheet,"pdf_plugin"):
            for pdf in data.get("pdfs",[]):
                if os.path.exists(pdf["path"]):
                    self.spreadsheet.pdf_plugin.set_pdf(pdf["row"],pdf["col"],pdf["path"])
        if hasattr(self.spreadsheet,"history_plugin"):
            self.spreadsheet.history_plugin.save_state()
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=False

    def export_pdf(self):
        file,_=QFileDialog.getSaveFileName(self.spreadsheet,"Export PDF","","PDF Files (*.pdf)")
        if not file:
            return
        if not file.lower().endswith(".pdf"):
            file+=".pdf"
        html="<html><body><table border='1' cellspacing='0' cellpadding='4'>"
        for r in range(self.table.rowCount()):
            html+="<tr>"
            for c in range(self.table.columnCount()):
                html+="<td>"
                item=self.table.item(r,c)
                if item:
                    html+=item.text().replace("\n","<br>")
                html+="</td>"
            html+="</tr>"
        html+="</table></body></html>"
        printer=QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file)
        document=QTextDocument()
        document.setHtml(html)
        document.print(printer)
        
    def export_image(self):
        file_name,_=QFileDialog.getSaveFileName(
            self.spreadsheet,
            "Export Image",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        if not file_name:
            return
        pixmap=self.spreadsheet.table.grab()
        pixmap.save(file_name)