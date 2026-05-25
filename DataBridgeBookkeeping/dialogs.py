from PyQt5.QtWidgets import(
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QTableWidget, QListWidget, QFileDialog, QDateEdit
)

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
        self.setWindowTitle(
            "Journal Entry"
        )
        self.resize(1000,650)
        layout=QVBoxLayout(self)
        self.entry_number=QLineEdit()
        self.reference=QLineEdit()
        self.entry_date=QDateEdit()
        self.entry_date.setCalendarPopup(
            True
        )
        self.description=QTextEdit()
        self.lines_table=QTableWidget()
        self.lines_table.setColumnCount(5)
        self.lines_table.setHorizontalHeaderLabels([
            "Account ID",
            "Description",
            "Debit",
            "Credit",
            "Notes"
        ])
        layout.addWidget(
            QLabel("Entry Number")
        )
        layout.addWidget(
            self.entry_number
        )
        layout.addWidget(
            QLabel("Reference")
        )
        layout.addWidget(
            self.reference
        )
        layout.addWidget(
            QLabel("Entry Date")
        )       
        layout.addWidget(
            self.entry_date
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
        layout.addLayout(buttons)
        self.save_btn.clicked.connect(
            self.accept
        )     
        self.cancel_btn.clicked.connect(
            self.reject
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