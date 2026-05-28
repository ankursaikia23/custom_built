from PyQt5.QtWidgets import(
    QWidget, QVBoxLayout, QLabel, QTableWidget, QTextEdit, QPushButton, QHBoxLayout, QFrame,
    QLineEdit, QComboBox, QTreeWidgetItem, QTreeWidget
)
#from PyQt5.QtWidgets import(
#    QListWidget
#)
class DashboardWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        layout=QVBoxLayout(self)
        self.summary_frame=QFrame()
        self.summary_layout=QHBoxLayout(
            self.summary_frame
        )
        self.accounts_card=QLabel()
        self.entries_card=QLabel()
        self.debits_card=QLabel()
        self.credits_card=QLabel()
        self.customers_card=QLabel()
        self.vendors_card=QLabel()
        self.invoices_card=QLabel()
        cards=[
            self.accounts_card,
            self.entries_card,
            self.debits_card,
            self.credits_card,
            self.customers_card,
            self.vendors_card,
            self.invoices_card
        ]
        for card in cards:
            card.setMinimumHeight(90)
            card.setStyleSheet("""
            QLabel{
                border:1px solid #cfcfcf;
                border-radius:6px;
                padding:12px;
                font-size:14px;
                font-weight:bold;
                background:white;
            }
            """)
            self.summary_layout.addWidget(
                card
            )
        self.recent_entries_label=QLabel(
            "Recent Journal Entries"
        )
        self.recent_entries_table=QTableWidget()
        layout.addWidget(
            self.summary_frame
        )
        layout.addWidget(
            self.recent_entries_label
        )
        layout.addWidget(
            self.recent_entries_table
        )

class ActivityWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        layout=QVBoxLayout(self)
        self.activity_text=QTextEdit()
        self.activity_text.setReadOnly(
            True
        )
        layout.addWidget(
            self.activity_text
        )

class ReportWidget(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        layout=QVBoxLayout(self)
        self.title_label=QLabel()
        self.toolbar=QHBoxLayout()
        self.search_input=QLineEdit()
        self.filter_combo=QComboBox()
        self.filter_combo.addItems([
            "All",
            "Assets",
            "Liabilities",
            "Equity",
            "Revenue",
            "Expense"
        ])
        self.refresh_btn=QPushButton(
            "Refresh"
        )
        self.export_csv_btn=QPushButton(
            "Export CSV"
        )
        self.export_excel_btn=QPushButton(
            "Export Excel"
        )
        self.export_pdf_btn=QPushButton(
            "Export PDF"
        )
        self.toolbar.addWidget(
            self.search_input
        )
        self.toolbar.addWidget(
            self.filter_combo
        )
        self.toolbar.addWidget(
            self.refresh_btn
        )
        self.toolbar.addWidget(
            self.export_csv_btn
        )
        self.toolbar.addWidget(
            self.export_excel_btn
        )
        self.toolbar.addWidget(
            self.export_pdf_btn
        )
        self.report_table=QTableWidget()
        layout.addWidget(
            self.title_label
        )
        layout.addLayout(
            self.toolbar
        )
        layout.addWidget(
            self.report_table
        )

class NavigationWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        dashboard = QTreeWidgetItem(["DASHBOARD"])
        self.tree.addTopLevelItem(dashboard)
        accounts = QTreeWidgetItem(["ACCOUNTS"])
        self.tree.addTopLevelItem(accounts)
        accounts.addChild(QTreeWidgetItem(["CHART OF ACCOUNTS"]))
        accounts.addChild(QTreeWidgetItem(["NEW ACCOUNT"]))
        accounts.addChild(QTreeWidgetItem(["QUICK ACCOUNT"]))
        journal = QTreeWidgetItem(["JOURNAL"])
        self.tree.addTopLevelItem(journal)
        journal.addChild(QTreeWidgetItem(["JOURNAL ENTRIES"]))
        journal.addChild(QTreeWidgetItem(["NEW JOURNAL ENTRY"]))
        reports = QTreeWidgetItem(["REPORTS"])
        self.tree.addTopLevelItem(reports)
        reports.addChild(QTreeWidgetItem(["TRIAL BALANCE"]))
        reports.addChild(QTreeWidgetItem(["PROFIT & LOSS"]))
        reports.addChild(QTreeWidgetItem(["BALANCE SHEET"]))
        reports.addChild(QTreeWidgetItem(["CASH FLOW"]))
        reports.addChild(QTreeWidgetItem(["EXPORT REPORT"]))
        system = QTreeWidgetItem(["SYSTEM"])
        self.tree.addTopLevelItem(system)
        system.addChild(QTreeWidgetItem(["IMPORT ACCOUNTS"]))
        system.addChild(QTreeWidgetItem(["CREATE BACKUP"]))
        system.addChild(QTreeWidgetItem(["MANAGE BACKUPS"]))
        system.addChild(QTreeWidgetItem(["REFRESH"]))
        layout.addWidget(self.tree)