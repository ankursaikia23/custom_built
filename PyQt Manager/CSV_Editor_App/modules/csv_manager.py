import pandas as pd
from PyQt5.QtWidgets import QTableWidgetItem
import os

class CSVManager:
    def __init__(self):
        self.df = None
        self.filtered_df = None
        self.csv_filename = ""
        self.current_csv_path = ""

    def load_csv_file(self, file_path):
        try:
            if file_path.lower().endswith((".xlsx", ".xls", ".ods")):
                excel_df = pd.read_excel(file_path)
                temp_csv_path = file_path.rsplit(".", 1)[0] + "_converted.csv"
                excel_df.to_csv(temp_csv_path, index=False)
                self.df = pd.read_csv(temp_csv_path)
                self.current_csv_path = temp_csv_path
            else:
                self.df = pd.read_csv(file_path)
                self.current_csv_path = file_path
            self.df = self.df.loc[:, ~self.df.columns.duplicated()].copy()
            self.df = self.df.drop(columns=["Q#"], errors="ignore")
            self.df.insert(0, "Q#", range(1, len(self.df) + 1))
            self.csv_filename = os.path.basename(file_path)
            return True
        except Exception:
            self.df = None
            return False

    def save(self):
        if self.df is None or not self.current_csv_path: return False
        try:
            self.df.to_csv(self.current_csv_path, index=False)
            return True
        except:
            return False

    def rename(self, new_filename):
        if not self.current_csv_path: return False
        new_path = os.path.join(os.path.dirname(self.current_csv_path), new_filename)
        try:
            os.rename(self.current_csv_path, new_path)
            self.current_csv_path = new_path
            self.csv_filename = new_filename
            return True
        except:
            return False

    def populate_table(self, table_widget, dataframe):
        table_widget.clear()
        table_widget.setRowCount(len(dataframe))
        table_widget.setColumnCount(len(dataframe.columns))
        table_widget.setHorizontalHeaderLabels(dataframe.columns.tolist())
        for row in range(len(dataframe)):
            for col in range(len(dataframe.columns)):
                val = "" if pd.isna(dataframe.iat[row, col]) else str(dataframe.iat[row, col])
                table_widget.setItem(row, col, QTableWidgetItem(val))
        table_widget.resizeColumnsToContents()
        table_widget.resizeRowsToContents()

    def show_all(self, table_widget):
        self.filtered_df = None
        if self.df is not None:
            self.populate_table(table_widget, self.df)

    def search(self, table_widget, text):
        if self.df is None: return
        if not text.strip(): self.show_all(table_widget); return
        filtered = self.df[self.df.apply(lambda r: r.astype(str).str.contains(text, case=False).any(), axis=1)]
        self.filtered_df = filtered
        self.populate_table(table_widget, filtered)

    def update_from_table(self, table_widget):
        if self.df is None: return
        rows, cols = table_widget.rowCount(), table_widget.columnCount()
        new_data = []
        for r in range(rows):
            row_values = []
            for c in range(cols):
                item = table_widget.item(r, c)
                value = "" if not item or not item.text().strip() else item.text().strip()
                row_values.append(value)
            new_data.append(row_values)
        new_df = pd.DataFrame(new_data, columns=self.df.columns)
        new_df.replace({"": pd.NA, "nan": pd.NA}, inplace=True)
        self.df = new_df

    def export(self, path, ext):
        if self.df is None: return
        if ext == "xlsx": self.df.to_excel(path, index=False)
        elif ext == "json": self.df.to_json(path, orient="records", indent=4)
        elif ext == "md": self.df.to_markdown(path, index=False)