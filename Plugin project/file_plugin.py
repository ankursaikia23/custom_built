import json
import os
import pandas as pd
from PyQt6.QtWidgets import (
    QFileDialog, QTableWidgetItem, QAbstractItemView, QInputDialog, QMessageBox
)
from grid_plugin import GridPlugin
from PyQt6.QtGui import QImage, QPainter, QPen, QColor, QFont
from PyQt6.QtCore import Qt
from PyQt6.QtPrintSupport import QPrinter

class FilePlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.table=spreadsheet.table
        self.current_file=None
        self.export_scale=100

    def new_file(self):
        before=[]
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                before.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
        self.table.clearContents()
        self.table.clearSpans()
        if hasattr(self.spreadsheet,"border_plugin"):
            self.spreadsheet.border_plugin.border_data={}
            self.spreadsheet.border_plugin.border_data_map[self.table]={}
        if hasattr(self.spreadsheet,"image_plugin"):
            self.spreadsheet.image_plugin.clear()
        if hasattr(self.spreadsheet,"pdf_plugin"):
            self.spreadsheet.pdf_plugin.clear()
        self.table.setRowCount(100)
        self.table.setColumnCount(26)
        after=[]
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                after.append(self.spreadsheet.history_plugin.create_cell_snapshot(r,c))
        self.spreadsheet.history_plugin.push_operation(before,after)
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=False
            
    def save_table(self,table,file):
        rows=table.rowCount()
        cols=table.columnCount()
        data=[]
        for r in range(rows):
            row_data=[]
            for c in range(cols):
                item=table.item(r,c)
                row_data.append(item.text() if item else "")
            data.append(row_data)
        df=pd.DataFrame(data)
        ext=os.path.splitext(file)[1].lower()
        if ext==".csv":
            df.to_csv(file,index=False,header=False,encoding="utf-8-sig")
        elif ext==".xlsx":
            df.to_excel(file,index=False,header=False,engine="openpyxl")
        elif ext==".xls":
            df.to_excel(file,index=False,header=False,engine="xlwt")
        elif ext==".ods":
            df.to_excel(file,index=False,header=False,engine="odf")
            
    def get_metadata_file(self,file):
        base,_=os.path.splitext(os.path.abspath(file))
        return base+".json"
    
    def get_spreadsheet_metadata(self):
        table=self.table
        data={
            "version":4,
            "rows":table.rowCount(),
            "cols":table.columnCount(),
            "images":[],
            "pdfs":[],
            "merged_cells":[],
            "column_widths":{},
            "row_heights":{},
            "hidden_rows":[],
            "hidden_columns":[],
            "cell_formats":{},
            "borders":{},
            "word_wrap":table.wordWrap()
        }
        for (row,col),path in getattr(self.spreadsheet.image_plugin,"images",{}).items():
            if path:
                data["images"].append({
                    "row":row,
                    "col":col,
                    "path":os.path.relpath(
                        os.path.abspath(path),
                        os.path.dirname(os.path.abspath(self.current_file))
                    ) if self.current_file else os.path.abspath(path)
                })
        for (row,col),path in getattr(self.spreadsheet.pdf_plugin,"pdfs",{}).items():
            if path:
                data["pdfs"].append({
                    "row":row,
                    "col":col,
                    "path":os.path.relpath(
                        os.path.abspath(path),
                        os.path.dirname(os.path.abspath(self.current_file))
                    ) if self.current_file else os.path.abspath(path)
                })
        default_row=table.verticalHeader().defaultSectionSize()
        default_col=table.horizontalHeader().defaultSectionSize()
        for row in range(table.rowCount()):
            height=table.rowHeight(row)
            if height!=default_row:
                data["row_heights"][str(row)]=height
            if table.isRowHidden(row):
                data["hidden_rows"].append(row)
        for col in range(table.columnCount()):
            width=table.columnWidth(col)
            if width!=default_col:
                data["column_widths"][str(col)]=width
            if table.isColumnHidden(col):
                data["hidden_columns"].append(col)
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                item=table.item(row,col)
                if item is not None:
                    font=item.font()
                    foreground=item.foreground().color()
                    background=item.background().color()
                    alignment=int(item.textAlignment())
                    data["cell_formats"][f"{row},{col}"]={
                        "font":{
                            "family":font.family(),
                            "point_size":font.pointSizeF(),
                            "bold":font.bold(),
                            "italic":font.italic(),
                            "underline":font.underline(),
                            "strike":font.strikeOut(),
                            "weight":font.weight(),
                            "overline":font.overline()
                        },
                        "foreground":{
                            "name":foreground.name(QColor.NameFormat.HexArgb)
                        },
                        "background":{
                            "name":background.name(QColor.NameFormat.HexArgb)
                        },
                        "alignment":alignment,
                        "user_role":item.data(Qt.ItemDataRole.UserRole),
                        "user_role_1":item.data(Qt.ItemDataRole.UserRole+1)
                    }
                row_span=table.rowSpan(row,col)
                col_span=table.columnSpan(row,col)
                if row_span>1 or col_span>1:
                    data["merged_cells"].append({
                        "row":row,
                        "col":col,
                        "row_span":row_span,
                        "col_span":col_span
                    })
        for (row,col),border in getattr(self.spreadsheet.border_plugin,"border_data",{}).items():
            data["borders"][f"{row},{col}"]=dict(border)
        return data
    
    def apply_spreadsheet_metadata(self,metadata):
        table=self.table
        rows=int(metadata.get("rows",table.rowCount()))
        cols=int(metadata.get("cols",table.columnCount()))
        table.setRowCount(max(1,rows))
        table.setColumnCount(max(1,cols))
        table.clearSpans()
        table.setWordWrap(bool(metadata.get("word_wrap",False)))
        for row in range(table.rowCount()):
            table.setRowHidden(row,False)
            table.setRowHeight(row,table.verticalHeader().defaultSectionSize())
        for col in range(table.columnCount()):
            table.setColumnHidden(col,False)
            table.setColumnWidth(col,table.horizontalHeader().defaultSectionSize())
        for row,height in metadata.get("row_heights",{}).items():
            row=int(row)
            if 0<=row<table.rowCount():
                table.setRowHeight(row,int(height))
        for col,width in metadata.get("column_widths",{}).items():
            col=int(col)
            if 0<=col<table.columnCount():
                table.setColumnWidth(col,int(width))
        for row in metadata.get("hidden_rows",[]):
            row=int(row)
            if 0<=row<table.rowCount():
                table.setRowHidden(row,True)
        for col in metadata.get("hidden_columns",[]):
            col=int(col)
            if 0<=col<table.columnCount():
                table.setColumnHidden(col,True)
        for key,format_data in metadata.get("cell_formats",{}).items():
            try:
                row,col=map(int,key.split(","))
            except (ValueError,AttributeError):
                continue
            if not (0<=row<table.rowCount() and 0<=col<table.columnCount()):
                continue
            item=table.item(row,col)
            if item is None:
                item=QTableWidgetItem()
                table.setItem(row,col,item)
            font_data=format_data.get("font",{})
            font=QFont()
            if font_data.get("family"):
                font.setFamily(str(font_data.get("family")))
            if "point_size" in font_data:
                font.setPointSizeF(float(font_data.get("point_size")))
            font.setBold(bool(font_data.get("bold",False)))
            font.setItalic(bool(font_data.get("italic",False)))
            font.setUnderline(bool(font_data.get("underline",False)))
            font.setStrikeOut(bool(font_data.get("strike",False)))
            font.setOverline(bool(font_data.get("overline",False)))
            if "weight" in font_data:
                font.setWeight(int(font_data.get("weight")))
            item.setFont(font)
            foreground_data=format_data.get("foreground",{})
            foreground_name=foreground_data.get("name")
            if foreground_name:
                foreground=QColor(str(foreground_name))
                if foreground.isValid():
                    item.setForeground(foreground)
            background_data=format_data.get("background",{})
            background_name=background_data.get("name")
            if background_name:
                background=QColor(str(background_name))
                if background.isValid():
                    item.setBackground(background)
            if "alignment" in format_data:
                item.setTextAlignment(Qt.AlignmentFlag(int(format_data.get("alignment"))))
            if "user_role" in format_data:
                item.setData(Qt.ItemDataRole.UserRole,format_data.get("user_role"))
            if "user_role_1" in format_data:
                item.setData(Qt.ItemDataRole.UserRole+1,format_data.get("user_role_1"))
        if hasattr(self.spreadsheet,"border_plugin"):
            border_data={}
            for key,border in metadata.get("borders",{}).items():
                try:
                    row,col=map(int,key.split(","))
                except (ValueError,AttributeError):
                    continue
                if 0<=row<table.rowCount() and 0<=col<table.columnCount():
                    border_data[(row,col)]={
                        "top":bool(border.get("top",False)),
                        "bottom":bool(border.get("bottom",False)),
                        "left":bool(border.get("left",False)),
                        "right":bool(border.get("right",False))
                    }
            self.spreadsheet.border_plugin.border_data=border_data
            self.spreadsheet.border_plugin.border_data_map[table]=border_data
            self.spreadsheet.border_plugin.refresh()
        for merged in metadata.get("merged_cells",[]):
            row=int(merged.get("row",-1))
            col=int(merged.get("col",-1))
            row_span=int(merged.get("row_span",1))
            col_span=int(merged.get("col_span",1))
            if row>=0 and col>=0 and row_span>=1 and col_span>=1:
                if row+row_span<=table.rowCount() and col+col_span<=table.columnCount():
                    table.setSpan(row,col,row_span,col_span)
        table.viewport().update()

    def save_file(self):
        file,_=QFileDialog.getSaveFileName(
            self.spreadsheet,
            "Save Spreadsheet",
            "",
            "CSV Files (*.csv);;Excel Workbook (*.xlsx);;Excel 97-2003 Workbook (*.xls);;OpenDocument Spreadsheet (*.ods)"
        )
        if not file:
            return
        if not os.path.splitext(file)[1]:
            file+=".csv"
        ext=os.path.splitext(file)[1].lower()
        if ext not in [".csv",".xlsx",".xls",".ods"]:
            QMessageBox.warning(self.spreadsheet,"Save File","Please select a valid spreadsheet format.")
            return
        self.current_file=os.path.abspath(file)
        self.save_table(self.table,self.current_file)
        metadata_file=self.get_metadata_file(self.current_file)
        metadata=self.get_spreadsheet_metadata()
        with open(metadata_file,"w",encoding="utf-8") as f:
            json.dump(metadata,f,ensure_ascii=False,indent=2)
        tab_index=self.spreadsheet.tab_plugin.tabs.indexOf(self.table)
        if tab_index>=0:
            self.spreadsheet.tab_plugin.tabs.setTabText(
                tab_index,
                os.path.splitext(os.path.basename(self.current_file))[0]
            )
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=False
        
    def new_tab(self):
        grid=GridPlugin()
        table=grid.widget()
        table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        table.clearSelection()
        table.setCurrentCell(-1,-1)
        index=len(self.spreadsheet.tab_plugin.all_tabs())+1
        self.spreadsheet.tab_plugin.add_tab(table,f"Sheet{index}")
        self.spreadsheet.tab_plugin.tabs.setCurrentIndex(index-1)

    def open_file(self):
        file,_=QFileDialog.getOpenFileName(
            self.spreadsheet,
            "Open Spreadsheet",
            "",
            "Spreadsheet Files (*.csv *.xlsx *.xls *.ods);;CSV Files (*.csv);;Excel Workbook (*.xlsx *.xls);;OpenDocument Spreadsheet (*.ods);;All Files (*)"
        )
        if not file:
            return
        ext=os.path.splitext(file)[1].lower()
        try:
            if ext==".csv":
                try:
                    df=pd.read_csv(file,header=None,dtype=str,keep_default_na=False,encoding="utf-8-sig")
                except (UnicodeDecodeError,pd.errors.ParserError):
                    df=pd.read_csv(file,header=None,dtype=str,keep_default_na=False,encoding="latin-1")
            elif ext==".xlsx":
                df=pd.read_excel(file,header=None,dtype=str,keep_default_na=False,engine="openpyxl")
            elif ext==".xls":
                df=pd.read_excel(file,header=None,dtype=str,keep_default_na=False,engine="xlrd")
            elif ext==".ods":
                df=pd.read_excel(file,header=None,dtype=str,keep_default_na=False,engine="odf")
            else:
                return
        except Exception as error:
            QMessageBox.critical(
                self.spreadsheet,
                "Open File",
                f"Unable to open the selected file.\n\n{error}"
            )
            return
        table=self.table
        table.blockSignals(True)
        try:
            table.clearContents()
            table.clearSpans()
            if hasattr(self.spreadsheet,"border_plugin"):
                self.spreadsheet.border_plugin.border_data={}
                self.spreadsheet.border_plugin.border_data_map[table]={}
            rows=len(df.index)
            cols=len(df.columns)
            table.setRowCount(max(rows,100))
            table.setColumnCount(max(cols,26))
            for r in range(rows):
                for c in range(cols):
                    value=df.iat[r,c]
                    if pd.isna(value):
                        value=""
                    if value!="":
                        table.setItem(r,c,QTableWidgetItem(str(value)))
        finally:
            table.blockSignals(False)
        self.current_file=os.path.abspath(file)
        tab_index=self.spreadsheet.tab_plugin.tabs.indexOf(self.table)
        if tab_index>=0:
            self.spreadsheet.tab_plugin.tabs.setTabText(
                tab_index,os.path.splitext(
                    os.path.basename(self.current_file)
                    )[0]
                )
        tab_index=self.spreadsheet.tab_plugin.tabs.indexOf(table)
        if tab_index>=0:
            self.spreadsheet.tab_plugin.tabs.setTabText(
                tab_index,os.path.splitext(
                    os.path.basename(self.current_file)
                    )[0]
                )
        metadata_file=self.get_metadata_file(self.current_file)
        self.spreadsheet.image_plugin.images_map.setdefault(table,{})
        self.spreadsheet.pdf_plugin.pdfs_map.setdefault(table,{})
        self.spreadsheet.image_plugin.images=self.spreadsheet.image_plugin.images_map[table]
        self.spreadsheet.pdf_plugin.pdfs=self.spreadsheet.pdf_plugin.pdfs_map[table]
        self.spreadsheet.image_plugin.clear()
        self.spreadsheet.pdf_plugin.clear()
        if os.path.isfile(metadata_file):
            try:
                with open(metadata_file,"r",encoding="utf-8") as f:
                    metadata=json.load(f)
                self.apply_spreadsheet_metadata(metadata)
                for image in metadata.get("images",[]):
                    row=int(image.get("row",-1))
                    col=int(image.get("col",-1))
                    path=image.get("path","")
                    if 0<=row<table.rowCount() and 0<=col<table.columnCount() and path:
                        if not os.path.isabs(path):
                            path=os.path.abspath(os.path.join(os.path.dirname(self.current_file),path))
                        if os.path.isfile(path):
                            self.spreadsheet.image_plugin.set_image(row,col,path)
                for pdf in metadata.get("pdfs",[]):
                    row=int(pdf.get("row",-1))
                    col=int(pdf.get("col",-1))
                    path=pdf.get("path","")
                    if 0<=row<table.rowCount() and 0<=col<table.columnCount() and path:
                        if not os.path.isabs(path):
                            path=os.path.abspath(os.path.join(os.path.dirname(self.current_file),path))
                        if os.path.isfile(path):
                            self.spreadsheet.pdf_plugin.set_pdf(row,col,path)
            except Exception as error:
                QMessageBox.warning(
                    self.spreadsheet,
                    "Metadata",
                    f"The spreadsheet was opened, but its JSON metadata could not be restored.\n\n{error}"
                )
        if hasattr(self.spreadsheet,"is_modified"):
            self.spreadsheet.is_modified=False
        self.spreadsheet.statusbar_plugin.show_operation("Opened")
        table.setFocus()
        table.viewport().update()
        
    def set_export_scale(self):
        value,ok=QInputDialog.getInt(
            self.spreadsheet,
            "Scale Up / Down",
            "Export Scale (%):",
            self.export_scale,
            1,
            100,
            1
        )
        if not ok:
            return
        self.export_scale=value
        self.spreadsheet.statusbar_plugin.show_operation(f"Export Scale: {value}%")

    def export_pdf(self):
        file,_=QFileDialog.getSaveFileName(self.spreadsheet,"Export PDF","","PDF Files (*.pdf)")
        if not file:
            return
        if not file.lower().endswith(".pdf"):
            file+=".pdf"
        images=getattr(getattr(self.spreadsheet,"image_plugin",None),"images",{})
        pdfs=getattr(getattr(self.spreadsheet,"pdf_plugin",None),"pdfs",{})
        used_rows=set()
        used_cols=set()
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item=self.table.item(r,c)
                if item and item.text():
                    used_rows.add(r)
                    used_cols.add(c)
        for r,c in images:
            used_rows.add(r)
            used_cols.add(c)
        for r,c in pdfs:
            used_rows.add(r)
            used_cols.add(c)
        if not used_rows or not used_cols:
            used_rows={0}
            used_cols={0}
        min_row=min(used_rows)
        max_row=max(used_rows)
        min_col=min(used_cols)
        max_col=max(used_cols)
        rows=list(range(min_row,max_row+1))
        cols=list(range(min_col,max_col+1))
        printer=QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(file)
        printer.setResolution(300)
        painter=QPainter()
        if not painter.begin(printer):
            return
        page_rect=printer.pageRect(QPrinter.Unit.DevicePixel)
        margin=45
        page_width=int(page_rect.width())-margin*2
        page_height=int(page_rect.height())-margin*2
        dpi_scale=printer.resolution()/96.0
        col_widths={c:max(20,int(self.table.columnWidth(c)*dpi_scale)) for c in cols}
        row_heights={r:max(20,int(self.table.rowHeight(r)*dpi_scale)) for r in rows}
        horizontal_pages=[]
        start_col=0
        while start_col<len(cols):
            width=0
            end_col=start_col
            while end_col<len(cols):
                next_width=width+col_widths[cols[end_col]]
                if width>0 and next_width>page_width:
                    break
                width=next_width
                end_col+=1
            horizontal_pages.append((start_col,end_col))
            start_col=end_col
        vertical_pages=[]
        start_row=0
        while start_row<len(rows):
            height=0
            end_row=start_row
            while end_row<len(rows):
                next_height=height+row_heights[rows[end_row]]
                if height>0 and next_height>page_height:
                    break
                height=next_height
                end_row+=1
            vertical_pages.append((start_row,end_row))
            start_row=end_row
        font=QFont()
        font.setPointSizeF(9)
        painter.setFont(font)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing,True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform,True)
        for vp,(row_start,row_end) in enumerate(vertical_pages):
            for hp,(col_start,col_end) in enumerate(horizontal_pages):
                if vp!=0 or hp!=0:
                    printer.newPage()
                y=margin
                for ri in range(row_start,row_end):
                    r=rows[ri]
                    x=margin
                    cell_height=row_heights[r]
                    for ci in range(col_start,col_end):
                        c=cols[ci]
                        cell_width=col_widths[c]
                        painter.fillRect(x,y,cell_width,cell_height,QColor(255,255,255))
                        painter.setPen(QPen(QColor(120,120,120),1))
                        painter.drawRect(x,y,cell_width,cell_height)
                        image_path=images.get((r,c))
                        if image_path and os.path.exists(image_path):
                            image=QImage(image_path)
                            if not image.isNull():
                                available_width=max(1,cell_width-10)
                                available_height=max(1,cell_height-10)
                                source_width=image.width()
                                source_height=image.height()
                                scale=min(available_width/source_width,available_height/source_height)
                                target_width=max(1,int(source_width*scale))
                                target_height=max(1,int(source_height*scale))
                                target_x=x+(cell_width-target_width)//2
                                target_y=y+(cell_height-target_height)//2
                                painter.drawImage(target_x,target_y,image)
                        elif (r,c) in pdfs:
                            painter.setPen(QColor(80,80,80))
                            painter.drawText(
                                x+5,
                                y+5,
                                cell_width-10,
                                cell_height-10,
                                Qt.AlignmentFlag.AlignCenter,
                                "PDF\n"+os.path.basename(pdfs[(r,c)])
                            )
                        else:
                            item=self.table.item(r,c)
                            if item:
                                painter.setPen(QColor(0,0,0))
                                painter.drawText(
                                    x+5,
                                    y+3,
                                    cell_width-10,
                                    cell_height-6,
                                    Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter,
                                    item.text()
                                )
                        x+=cell_width
                    y+=cell_height
        painter.end()
        self.spreadsheet.statusbar_plugin.show_operation("PDF Exported")
        
    def export_image(self):
        file_name,_=QFileDialog.getSaveFileName(
            self.spreadsheet,
            "Export Image",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg)"
        )
        if not file_name:
            return
        table=self.table
        old_size=table.size()
        old_minimum=table.minimumSize()
        old_maximum=table.maximumSize()
        old_updates=table.updatesEnabled()
        table.setUpdatesEnabled(False)
        try:
            width=table.verticalHeader().width()+table.horizontalHeader().length()+2
            height=table.horizontalHeader().height()+table.verticalHeader().length()+2
            width=max(width,table.sizeHint().width())
            height=max(height,table.sizeHint().height())
            table.setMinimumSize(width,height)
            table.setMaximumSize(width,height)
            table.resize(width,height)
            table.doItemsLayout()
            table.viewport().update()
            image=QImage(width,height,QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.white)
            painter=QPainter(image)
            table.render(painter)
            painter.end()
            scale=self.export_scale/100.0
            target_width=max(1,int(width*scale))
            target_height=max(1,int(height*scale))
            if scale!=1.0:
                image=image.scaled(
                    target_width,
                    target_height,
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            image.save(file_name)
        finally:
            table.setMinimumSize(old_minimum)
            table.setMaximumSize(old_maximum)
            table.resize(old_size)
            table.setUpdatesEnabled(old_updates)
            table.updateGeometry()
            table.viewport().update()
        self.spreadsheet.statusbar_plugin.show_operation("Image Exported")
        
    def export_file(self):
        file,_=QFileDialog.getSaveFileName(
            self.spreadsheet,
            "Export Spreadsheet",
            "",
            "CSV (*.csv);;Excel Workbook (*.xlsx);;Excel 97-2003 (*.xls);;OpenDocument Spreadsheet (*.ods);;TSV (*.tsv)"
        )
        if not file:
            return
        rows=self.table.rowCount()
        cols=self.table.columnCount()
        data=[]
        for r in range(rows):
            row=[]
            for c in range(cols):
                item=self.table.item(r,c)
                row.append(item.text() if item else "")
            data.append(row)
        df=pd.DataFrame(data)
        ext=os.path.splitext(file)[1].lower()
        if ext==".csv":
            df.to_csv(file,index=False,header=False)
        elif ext==".tsv":
            df.to_csv(file,sep="\t",index=False,header=False)
        elif ext==".xlsx":
            df.to_excel(file,index=False,header=False)
        elif ext==".xls":
            df.to_excel(file,index=False,header=False,engine="xlwt")
        elif ext==".ods":
            df.to_excel(file,index=False,header=False,engine="odf")
        else:
            return
        self.spreadsheet.statusbar_plugin.show_operation("Spreadsheet Exported")