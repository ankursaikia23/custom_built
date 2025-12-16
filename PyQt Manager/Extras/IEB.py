import sys, os, shutil
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QFileDialog, QComboBox, QDateEdit,
    QInputDialog
)
from PyQt5.QtCore import Qt, QDate

from PyQt5.QtGui import QKeyEvent

class ExpenseTable(QTableWidget):
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter):
            current = self.currentItem()
            if current:
                if self.state() != self.EditingState:
                    self.editItem(current)
                else:
                    self.closePersistentEditor(current)
            return
        if event.modifiers() == Qt.ControlModifier:
            current = self.currentItem()
            if current:
                if key == Qt.Key_Up:
                    self.editItem(current)
                    editor = self.focusWidget()
                    if hasattr(editor, "setCursorPosition"):
                        editor.setCursorPosition(0)
                    return
                elif key == Qt.Key_Down:
                    self.editItem(current)
                    editor = self.focusWidget()
                    if hasattr(editor, "setCursorPosition"):
                        text = editor.text() if hasattr(editor, "text") else editor.toPlainText()
                        editor.setCursorPosition(len(text))
                    return
        super().keyPressEvent(event)

class ExpenseManager(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expense Manager")
        self.resize(1100, 650)
        self.accounts = []
        self.df = pd.DataFrame(columns=["Date", "Description", "Category", "Amount", "Type", "Account"])
        self.image_folder = os.path.join(os.getcwd(), "receipts")
        os.makedirs(self.image_folder, exist_ok=True)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        top_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load")
        self.save_btn = QPushButton("Save")
        self.add_btn = QPushButton("Add Entry")
        self.account_btn = QPushButton("Select/Add Account")
        self.balance_label = QLabel("Balance: 0.00")
        self.balance_label.setStyleSheet("font-size: 24px; font-weight: bold; color: darkgreen;")
        top_layout.addWidget(self.load_btn)
        top_layout.addWidget(self.save_btn)
        top_layout.addWidget(self.add_btn)
        top_layout.addWidget(self.account_btn)
        self.image_btn = QPushButton("Add Image(s)")
        top_layout.addWidget(self.image_btn)
        top_layout.addWidget(self.balance_label)
        self.image_btn.clicked.connect(self.add_images)
        layout.addLayout(top_layout)
        self.account_balances_label = QLabel("")
        layout.addWidget(self.account_balances_label)
        self.table = ExpenseTable(0, len(self.df.columns))
        self.table.setHorizontalHeaderLabels(self.df.columns)
        layout.addWidget(self.table)
        self.load_btn.clicked.connect(self.load_data)
        self.save_btn.clicked.connect(self.save_data)
        self.add_btn.clicked.connect(self.add_entry)
        self.account_btn.clicked.connect(self.manage_accounts)
        self.table.cellChanged.connect(self.update_balance)

    def add_entry(self):
        r = self.table.rowCount()
        self.table.insertRow(r)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.currentDate())
        date_edit.dateChanged.connect(self.sort_by_date)
        self.table.setCellWidget(r, 0, date_edit)
        self.table.setItem(r, 1, QTableWidgetItem(""))
        cat_box = QComboBox()
        cat_box.addItems(["Income", "Expense", "Transfer"])
        self.table.setCellWidget(r, 2, cat_box)
        self.table.setItem(r, 3, QTableWidgetItem(""))
        type_box = QComboBox()
        type_box.addItems(["Online", "Cash"])
        type_box.setEditable(True)
        self.table.setCellWidget(r, 4, type_box)
        acc_box = QComboBox()
        acc_box.addItems(self.accounts)
        acc_box.setEditable(False)
        self.table.setCellWidget(r, 5, acc_box)

    def sort_by_date(self):
        data = []
        for i in range(self.table.rowCount()):
            d = self.table.cellWidget(i, 0).date().toPyDate()
            desc = self.table.item(i, 1).text() if self.table.item(i, 1) else ""
            cat = self.table.cellWidget(i, 2).currentText()
            amt = self.table.item(i, 3).text() if self.table.item(i, 3) else ""
            typ = self.table.cellWidget(i, 4).currentText()
            acc = self.table.cellWidget(i, 5).currentText() if self.table.cellWidget(i, 5) else ""
            data.append([d, desc, cat, amt, typ, acc])
        data.sort(key=lambda x: x[0])
        self.table.blockSignals(True)
        self.table.setRowCount(0)
        for row in data:
            r = self.table.rowCount()
            self.table.insertRow(r)
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDate(QDate(row[0].year, row[0].month, row[0].day))
            date_edit.dateChanged.connect(self.sort_by_date)
            self.table.setCellWidget(r, 0, date_edit)
            self.table.setItem(r, 1, QTableWidgetItem(row[1]))
            cat_box = QComboBox()
            cat_box.addItems(["Income", "Expense", "Transfer"])
            cat_box.setCurrentText(row[2])
            self.table.setCellWidget(r, 2, cat_box)
            self.table.setItem(r, 3, QTableWidgetItem(row[3]))
            type_box = QComboBox()
            type_box.addItems(["Online", "Cash"])
            type_box.setEditable(True)
            type_box.setCurrentText(row[4])
            self.table.setCellWidget(r, 4, type_box)
            acc_box = QComboBox()
            acc_box.addItems(self.accounts)
            acc_box.setCurrentText(row[5])
            self.table.setCellWidget(r, 5, acc_box)
        self.table.blockSignals(False)
        self.update_balance()

    def load_data(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        self.df = pd.read_csv(path)
        self.table.setRowCount(0)
        for _, row in self.df.iterrows():
            r = self.table.rowCount()
            self.table.insertRow(r)
            d = datetime.strptime(row["Date"], "%Y-%m-%d").date()
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDate(QDate(d.year, d.month, d.day))
            date_edit.dateChanged.connect(self.sort_by_date)
            self.table.setCellWidget(r, 0, date_edit)
            self.table.setItem(r, 1, QTableWidgetItem(str(row["Description"])))
            cat_box = QComboBox()
            cat_box.addItems(["Income", "Expense", "Transfer"])
            cat_box.setCurrentText(str(row["Category"]))
            self.table.setCellWidget(r, 2, cat_box)
            self.table.setItem(r, 3, QTableWidgetItem(str(row["Amount"])))
            type_box = QComboBox()
            type_box.addItems(["Online", "Cash"])
            type_box.setEditable(True)
            type_box.setCurrentText(str(row["Type"]))
            self.table.setCellWidget(r, 4, type_box)
            acc_box = QComboBox()
            acc_box.addItems(self.accounts)
            acc_box.setCurrentText(str(row["Account"]))
            self.table.setCellWidget(r, 5, acc_box)
        self.update_balance()

    def save_data(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        rows = self.table.rowCount()
        data = []
        for i in range(rows):
            d = self.table.cellWidget(i, 0).date().toString("yyyy-MM-dd")
            desc = self.table.item(i, 1).text() if self.table.item(i, 1) else ""
            cat = self.table.cellWidget(i, 2).currentText()
            amt = self.table.item(i, 3).text() if self.table.item(i, 3) else ""
            typ = self.table.cellWidget(i, 4).currentText()
            acc = self.table.cellWidget(i, 5).currentText()
            data.append([d, desc, cat, amt, typ, acc])
        pd.DataFrame(data, columns=self.df.columns).to_csv(path, index=False)

    def manage_accounts(self):
        text, ok = QInputDialog.getText(self, "Add or Select Account", "Enter account name:")
        if ok and text.strip():
            if text not in self.accounts:
                self.accounts.append(text)
            for i in range(self.table.rowCount()):
                acc_box = self.table.cellWidget(i, 5)
                if acc_box and text not in [acc_box.itemText(j) for j in range(acc_box.count())]:
                    acc_box.addItem(text)

    def update_balance(self):
        total = 0
        account_balances = {}
        for i in range(self.table.rowCount()):
            amt_item = self.table.item(i, 3)
            if not amt_item:
                continue
            try:
                amt = float(amt_item.text())
            except:
                amt = 0
            cat = self.table.cellWidget(i, 2).currentText()
            acc = self.table.cellWidget(i, 5).currentText()
            if cat == "Income":
                total += amt
                account_balances[acc] = account_balances.get(acc, 0) + amt
            elif cat == "Expense":
                total -= amt
                account_balances[acc] = account_balances.get(acc, 0) - amt
        self.balance_label.setText(f"Balance: {total:.2f}")
        text = "\n".join([f"{k}: {v:.2f}" for k, v in account_balances.items()])
        self.account_balances_label.setText(text)
        
    def table_key_press(self, event):
        key = event.key()
        current = self.table.currentItem()
        if not current:
            return
        if key in (Qt.Key_Return, Qt.Key_Enter):
            if self.table.state() != self.table.EditingState:
                self.table.editItem(current)
            else:
                self.table.closePersistentEditor(current)
            return
        if event.modifiers() == Qt.ControlModifier:
            if key == Qt.Key_Up:
                current.setSelected(True)
                cursor = self.table.item(current.row(), current.column())
                if cursor:
                    self.table.editItem(cursor)
                    editor = self.table.focusWidget()
                    if hasattr(editor, 'setCursorPosition'):
                        editor.setCursorPosition(0)
                return
            elif key == Qt.Key_Down:
                current.setSelected(True)
                cursor = self.table.item(current.row(), current.column())
                if cursor:
                    self.table.editItem(cursor)
                    editor = self.table.focusWidget()
                    if hasattr(editor, 'setCursorPosition'):
                        text = editor.text() if hasattr(editor, 'text') else editor.toPlainText()
                        editor.setCursorPosition(len(text))
                return
        self.table.keyPressEvent = QTableWidget.keyPressEvent
        QTableWidget.keyPressEvent(self.table, event)

    def add_images(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if not paths:
            return
        date_widget = self.table.cellWidget(current_row, 0)
        if date_widget:
            date_str = date_widget.date().toString("MM-dd-yyyy_")
        else:
            date_str = datetime.now().strftime("%m-%d-%Y_")
        image_names = []
        for p in paths:
            base = os.path.basename(p)
            new_name = date_str + base
            shutil.copy(p, os.path.join(self.image_folder, new_name))
            image_names.append(new_name)
        current_images = self.table.item(current_row, 1)
        if current_images:
            existing_text = current_images.text()
            if existing_text.strip():
                current_images.setText(existing_text + " | " + " , ".join(image_names))
            else:
                current_images.setText(" , ".join(image_names))
        else:
            self.table.setItem(current_row, 1, QTableWidgetItem(" , ".join(image_names)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ExpenseManager()
    w.show()
    sys.exit(app.exec_())