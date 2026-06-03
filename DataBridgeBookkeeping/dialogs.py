from PyQt5.QtWidgets import(
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QTableWidget, QListWidget, QFileDialog, QHeaderView, QMessageBox, QTableWidgetItem
)
from PyQt5.QtCore import Qt, QDate
# from PyQt5.QtWidgets import(
#)
# from datetime import datetime
class AccountDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            "Account"
        )
        self.resize(400,300)
        layout=QVBoxLayout(self)
        self.account_code=QLineEdit()
        self.account_name=QLineEdit()
        self.account_type=QComboBox()
        self.account_type.addItems([
            "Asset",
            "Liability",
            "Equity",
            "Revenue",
            "Expense",
            "Custom"
        ])
        self.custom_account_type=QLineEdit()
        self.custom_account_type.setPlaceholderText(
            "Enter custom account type"
        )
        self.custom_account_type.hide()
        layout.addWidget(self.custom_account_type)
        self.account_type.currentTextChanged.connect(
            self.toggle_custom_account_type
        )
        layout.addWidget(
            QLabel("Account Code")
        )
        layout.addWidget(
            self.account_code
        )
        layout.addWidget(
            QLabel("Account Name")
        )
        layout.addWidget(
            self.account_name
        )
        layout.addWidget(
            QLabel("Account Type")
        )
        layout.addWidget(
            self.account_type
        )
        buttons=QHBoxLayout()
        self.save_btn=QPushButton(
            "Save"
        )
        self.cancel_btn=QPushButton(
            "Cancel"
        )
        buttons.addWidget(
            self.save_btn
        )
        buttons.addWidget(
            self.cancel_btn
        )        
        layout.addLayout(buttons)
        self.save_btn.clicked.connect(
            self.accept
        )
        self.cancel_btn.clicked.connect(
            self.reject
        )
        
    def toggle_custom_account_type(self,text):
        if text=="Custom":
            self.custom_account_type.show()
        else:
            self.custom_account_type.hide()

class JournalEntryDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.parent_app=parent
        self.setWindowTitle(
            "Journal Entry"
        )
        self.resize(1000,650)
        layout=QVBoxLayout(self)
        self.entry_number=QLineEdit()
        self.reference=QLineEdit()
        current_date=QDate.currentDate()
        self.entry_day=QComboBox()
        self.entry_month=QComboBox()
        self.entry_year=QComboBox()
        self.entry_day.setMaxVisibleItems(10)
        self.entry_month.setMaxVisibleItems(10)
        self.entry_year.setMaxVisibleItems(10)
        for day in range(1,32):
            self.entry_day.addItem(str(day))
        months=[
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ]
        self.entry_month.addItems(months)
        for year in range(1901,current_date.year()+1):
            self.entry_year.addItem(str(year))
        self.entry_day.setCurrentText(
            str(current_date.day())
        )
        self.entry_month.setCurrentIndex(
            current_date.month()-1
        )
        self.entry_year.setCurrentText(
            str(current_date.year())
        )
        date_layout=QHBoxLayout()
        date_layout.addWidget(
            self.entry_day
        )
        date_layout.addWidget(
            self.entry_month
        )
        date_layout.addWidget(
            self.entry_year
        )
        self.entry_month.currentIndexChanged.connect(
            self.update_day_dropdown
        )
        self.entry_year.currentIndexChanged.connect(
            self.update_day_dropdown
        )
        self.update_day_dropdown()
        self.description=QTextEdit()
        self.lines_table=QTableWidget()
        self.lines_table.setColumnCount(7)
        self.lines_table.setHorizontalHeaderLabels([
            "Account",
            "Transaction Type",
            "Type",
            "Amount",
            "Notes",
            "Attachments",
            "Remove"
        ])
        self.lines_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        header_layout=QHBoxLayout()
        entry_number_layout=QVBoxLayout()
        entry_number_layout.addWidget(
            QLabel("Entry Number")
        )
        entry_number_layout.addWidget(
            self.entry_number
        )
        reference_layout=QVBoxLayout()
        reference_layout.addWidget(
            QLabel("Reference")
        )
        reference_layout.addWidget(
            self.reference
        )
        date_container_layout=QVBoxLayout()
        date_container_layout.addWidget(
            QLabel("Entry Date")
        )
        date_container_layout.addLayout(
            date_layout
        )
        header_layout.addLayout(
            entry_number_layout,
            2
        )
        header_layout.addLayout(
            reference_layout,
            3
        )
        header_layout.addLayout(
            date_container_layout,
            4
        )
        layout.addLayout(
            header_layout
        )
        layout.addWidget(
            QLabel("Description")
        )
        layout.addWidget(
            self.description
        )
        layout.addWidget(
            self.lines_table
        )
        buttons=QHBoxLayout()
        self.add_line_btn=QPushButton(
            "Add Line"
        )
        self.add_line_btn.clicked.connect(
            self.add_line
        )
        self.save_btn=QPushButton(
            "Post Entry"
        )
        self.cancel_btn=QPushButton(
            "Cancel"
        )
        buttons.addWidget(
            self.add_line_btn
        )
        buttons.addWidget(
            self.save_btn
        )
        buttons.addWidget(
            self.cancel_btn
        )
        layout.addLayout(
            buttons
        )
        self.save_btn.clicked.connect(
            self.accept
        )
        self.cancel_btn.clicked.connect(
            self.reject
        )
        
    def get_selected_date(self):
        month_names=[
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ]
        day=int(
            self.entry_day.currentText()
        )
        month=month_names.index(
            self.entry_month.currentText()
        )+1
        year=int(
            self.entry_year.currentText()
        )
        return QDate(
            year,
            month,
            day
        )
    
    def update_day_dropdown(self):
        month_names=[
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ]    
        current_day=min(
            int(self.entry_day.currentText()),
            31
        )
        month=month_names.index(
            self.entry_month.currentText()
        )+1
        year=int(
            self.entry_year.currentText()
        )
        if month in [1,3,5,7,8,10,12]:
            max_days=31
        elif month in [4,6,9,11]:
            max_days=30
        else:
            if (year%400==0) or (year%4==0 and year%100!=0):
                max_days=29
            else:
                max_days=28
        self.entry_day.blockSignals(True)
        self.entry_day.clear()
        for day in range(1,max_days+1):
            self.entry_day.addItem(str(day))
        self.entry_day.setCurrentText(
            str(min(current_day,max_days))
        )
        self.entry_day.blockSignals(False)
        
    def add_line(self):
        row=self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        account_dropdown=QComboBox()
        if self.parent_app:
            accounts=self.parent_app.accounts.get_all_accounts()
            for account in accounts:
                account_dropdown.addItem(
                    f"{account['id']} - {account['account_name']}",
                    account["id"]
                )
        self.lines_table.setCellWidget(
            row,
            0,
            account_dropdown
        )
        transaction_type_widget=QComboBox()
        transaction_type_widget.addItems([
            "Cash",
            "UPI",
            "Online Banking",
            "Cheque",
            "NEFT",
            "RTGS",
            "IMPS",
            "Card",
            "Wallet",
            "Adjustment",
        ])

        def update_amount_color(text):
            if self.lines_table.item(row,3):
                if text=="Debit":
                    self.lines_table.item(
                        row,
                        3
                    ).setForeground(Qt.red)
                else:
                    self.lines_table.item(
                        row,
                        3
                    ).setForeground(Qt.darkGreen)
    
        self.lines_table.setCellWidget(
            row,
            1,
            transaction_type_widget
        )
        entry_type_dropdown=QComboBox()
        entry_type_dropdown.addItems([
            "Debit",
            "Credit"
        ])
        self.lines_table.setCellWidget(
            row,
            2,
            entry_type_dropdown
        )
        amount_item=QTableWidgetItem(
            "0.00"
        )
        amount_item.setForeground(
            Qt.red
        )
        self.lines_table.setItem(
            row,
            3,
            amount_item
        )
        entry_type_dropdown.currentTextChanged.connect(
            update_amount_color
        )
        attach_btn=QPushButton(
            "Attach"
        )    
        attach_btn.clicked.connect(
            self.attachment_placeholder
        )
        self.lines_table.setCellWidget(
            row,
            5,
            attach_btn
        )
        remove_btn=QPushButton("X")
        remove_btn.clicked.connect(
            lambda _, r=row: self.remove_line(r)
        )
        self.lines_table.setCellWidget(
            row,
            6,
            remove_btn
        )
        
    def remove_line(self,row):
        if self.lines_table.rowCount()<=2:
            QMessageBox.information(
                self,
                "Journal Entry",
                "A journal entry must contain at least two lines."
            )
            return
        self.lines_table.removeRow(row)
        
    def attachment_placeholder(self):
        QMessageBox.information(
            self,
            "Attachments",
            "Attachment functionality will be added later."
        )

class BackupDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)

        self.setWindowTitle(
            "Database Backups"
        )
        self.resize(500,400)
        layout=QVBoxLayout(self)
        self.backup_list=QListWidget()
        self.create_backup_btn=QPushButton(
            "Create Backup"
        )
        self.restore_backup_btn=QPushButton(
            "Restore Backup"
        )
        self.delete_backup_btn=QPushButton(
            "Delete Backup"
        )
        layout.addWidget(
            self.backup_list
        )
        layout.addWidget(
            self.create_backup_btn
        )
        layout.addWidget(
            self.restore_backup_btn
        )
        layout.addWidget(
            self.delete_backup_btn
        )
        self.create_backup_btn.clicked.connect(
            self.accept
        )       
        self.restore_backup_btn.clicked.connect(
            self.accept
        )
        self.delete_backup_btn.clicked.connect(
            self.reject
        )

class ImportDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            "Import Data"
        )
        self.resize(500,200)
        layout=QVBoxLayout(self)
        self.file_path=QLineEdit()
        self.browse_btn=QPushButton(
            "Browse"
        )
        self.import_btn=QPushButton(
            "Import"
        )
        layout.addWidget(
            QLabel("File Path")
        )
        layout.addWidget(
            self.file_path
        )
        layout.addWidget(
            self.browse_btn
        )
        layout.addWidget(
            self.import_btn
        )   
        self.browse_btn.clicked.connect(
            self.select_file
        )
        self.import_btn.clicked.connect(
            self.accept
        )

    def select_file(self):
        file_path,_=QFileDialog.getOpenFileName(
            self,
            "Select File"
        )
        if file_path:
            self.file_path.setText(
                file_path
            )