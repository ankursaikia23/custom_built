from PyQt5.QtWidgets import(
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QTableWidget, QListWidget, QFileDialog, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QDoubleValidator
# from PyQt5.QtWidgets import(
#   QTableWidgetItem)
# from datetime import datetime
class AccountDialog(QDialog):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.setWindowTitle(
            "Account"
        )
        self.resize(500,450)
        layout=QVBoxLayout(self)
        self.account_code=QLineEdit()
        self.account_name=QLineEdit()
        self.account_name.setMaxLength(
            100
        )
        self.description=QTextEdit()
        self.account_type=QComboBox()
        self.account_type.addItems([
            "Asset",
            "Liability",
            "Equity",
            "Revenue",
            "Expense"
        ])
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
            QLabel("Description")
        )
        layout.addWidget(
            self.description
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
        self.lines_table.setRowCount(0)
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
        self.lines_table.setAlternatingRowColors(
            True
        )
        self.lines_table.verticalHeader().setDefaultSectionSize(
            42
        )
        self.lines_table.setSelectionBehavior(
            QTableWidget.SelectRows
        )
        self.lines_table.setShowGrid(
            True
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
            self.validate_and_accept
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
        
    def validate_and_accept(self):
        total_debit=0
        total_credit=0    
        for row in range(
            self.lines_table.rowCount()
        ):
            entry_type_widget=self.lines_table.cellWidget(
                row,
                2
            )
            amount_widget=self.lines_table.cellWidget(
                row,
                3
            )
            if not entry_type_widget:
                continue
            try:
                amount=float(
                    amount_widget.text()
                ) if amount_widget and amount_widget.text() else 0
            except ValueError:
                QMessageBox.warning(
                    self,
                    "Journal Entry",
                    "Invalid amount detected."
                )
                return
            if entry_type_widget.currentText()=="Debit":
                total_debit+=amount
            else:
                total_credit+=amount
        if round(total_debit,2)!=round(total_credit,2):
            QMessageBox.warning(
                self,
                "Journal Entry",
                "Debit and Credit amounts do not match."
            )
            return
        if round(total_debit,2)==0:
            QMessageBox.warning(
                self,
                "Journal Entry",
                "Total amount cannot be zero."
            )
            return
        if self.lines_table.rowCount()<2:
            QMessageBox.warning(
                self,
                "Journal Entry",
                "A journal entry must contain at least two lines."
            )
            return
        if not self.entry_number.text().strip():
            QMessageBox.warning(
                self,
                "Journal Entry",
                "Entry number is required."
            )
            return
        self.accept()
        
    def add_line(self):
        row=self.lines_table.rowCount()
        self.lines_table.insertRow(row)
        account_dropdown=QComboBox()
        account_dropdown.setMinimumHeight(
            32
        )
        account_dropdown.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLengthWithIcon
        )    
        account_dropdown.view().setMinimumWidth(
            300
        )
        if self.parent_app:
            accounts=self.parent_app.accounts.get_active_accounts()
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
        transaction_type_widget.setMinimumHeight(
            32
        )
        transaction_type_widget.setSizeAdjustPolicy(
            QComboBox.AdjustToMinimumContentsLengthWithIcon
        )    
        transaction_type_widget.view().setMinimumWidth(
            180
        )
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
            amount_widget=self.lines_table.cellWidget(
                row,
                3
            )
            if amount_widget:
                if text=="Debit":
                    amount_widget.setStyleSheet(
                        "color:red;"
                    )
                else:
                    amount_widget.setStyleSheet(
                        "color:green;"
                    )
        self.lines_table.setCellWidget(
            row,
            1,
            transaction_type_widget
        )
        entry_type_dropdown=QComboBox()
        entry_type_dropdown.setMinimumHeight(
            32
        )
        entry_type_dropdown.addItems([
            "Debit",
            "Credit"
        ])
        self.lines_table.setCellWidget(
            row,
            2,
            entry_type_dropdown
        )
        amount_input=QLineEdit()
        amount_input.setText(
            "0.00"
        )
        amount_input.setAlignment(
            Qt.AlignRight
        )
        amount_input.setValidator(
            QDoubleValidator(
                0.00,
                999999999999.99,
                2
            )
        )
        self.lines_table.setCellWidget(
            row,
            3,
            amount_input
        )
        entry_type_dropdown.currentTextChanged.connect(
            update_amount_color
        )
        attach_btn=QPushButton(
            "📎 Attach"
        )
        attach_btn.setMinimumHeight(
            32
        )
        attach_btn.clicked.connect(
            self.attachment_placeholder
        )
        self.lines_table.setCellWidget(
            row,
            5,
            attach_btn
        )
        remove_btn=QPushButton("✕")
        remove_btn.setMinimumHeight(
            32
        )
        remove_btn.setStyleSheet("""
        QPushButton{
            color:white;
            background:#c62828;
            border:none;
            border-radius:4px;
            font-weight:bold;
        }
        QPushButton:hover{
            background:#b71c1c;
        }
        """)
        remove_btn.clicked.connect(
            lambda _, btn=remove_btn:
            self.remove_line(
                self.lines_table.indexAt(
                    btn.pos()
                ).row()
            )
        )
        self.lines_table.setCellWidget(
            row,
            6,
            remove_btn
        )
        
    def remove_line(self,row):
        if row<0:
            return
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
            self.accept
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
            "Select File",
            "",
            "Supported Files (*.csv *.xlsx *.xls *.ods)"
        )
        if file_path:
            self.file_path.setText(
                file_path
            )