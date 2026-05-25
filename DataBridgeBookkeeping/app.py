from PyQt5.QtWidgets import(
    QMainWindow, QWidget, QHBoxLayout, QSplitter, QStackedWidget, QTableWidget,
    QTableWidgetItem, QAction, QFileDialog, QAbstractItemView, QMessageBox, QHeaderView,
    QInputDialog, QToolBar, QStatusBar
)
# from PyQt5.QtWidgets import QVBoxLayout
from database import DatabaseManager
from accounts import AccountManager
from journal import JournalManager
from transactions import TransactionManager
from reports import ReportManager
from ledger import LedgerManager
from dashboard import DashboardManager
from imports import ImportManager
from exports import ExportManager
from dialogs import(
    AccountDialog, JournalEntryDialog, BackupDialog, ImportDialog
)
from reconciliation import ReconciliationEngine
from backup import BackupManager
from settings import SettingsManager
from widgets import(
    DashboardWidget, NavigationWidget, ReportWidget
)

class BookkeepingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db=DatabaseManager()
        self.accounts=AccountManager(
            self.db
        )
        self.journal=JournalManager(
            self.db
        )
        self.transactions=TransactionManager(
            self.journal
        )
        self.reports=ReportManager(
            self.db
        )
        self.ledger=LedgerManager(
            self.db
        )
        self.dashboard=DashboardManager(
            self.db
        )
        self.imports=ImportManager(
            self.db
        )
        self.exports=ExportManager()
        self.reconciliation=ReconciliationEngine(
            self.db
        )
        self.backups=BackupManager()
        self.settings=SettingsManager(
            self.db
        )
        self.setWindowTitle(
            "Bookkeeping System"
        )
        self.resize(1600,900)
        self.init_ui()
        self.initialize_demo_data()
        self.refresh_dashboard()
        self.load_dashboard_recent_entries()
        self.load_accounts_table()
        self.load_journal_table()
        self.load_audit_logs()
        self.load_trial_balance_report()
        self.load_profit_loss_report()
        self.load_balance_sheet_report()
        self.load_cash_flow_report()
        self.setup_report_exports()
        self.connect_navigation_signals()

    def init_ui(self):
        self.central_widget=QWidget()
        self.setCentralWidget(
            self.central_widget
        )
        self.main_layout=QHBoxLayout(
            self.central_widget
        )
        self.splitter=QSplitter()
        self.navigation=NavigationWidget()
        self.pages=QStackedWidget()
        self.dashboard_page=DashboardWidget()
        self.accounts_page=QTableWidget()
        self.journal_page=QTableWidget()
        self.ledger_page=QTableWidget()
        self.trial_balance_page=ReportWidget()
        self.pnl_page=ReportWidget()
        self.balance_sheet_page=ReportWidget()
        self.cash_flow_page=ReportWidget()
        self.audit_page=QTableWidget()
        self.trial_balance_page.title_label.setText(
            "Trial Balance"
        )        
        self.pnl_page.title_label.setText(
            "Profit & Loss"
        )
        self.balance_sheet_page.title_label.setText(
            "Balance Sheet"
        )
        self.cash_flow_page.title_label.setText(
            "Cash Flow"
        )
        self.customers_page=QTableWidget()
        self.vendors_page=QTableWidget()
        self.invoices_page=QTableWidget()
        self.settings_page=QTableWidget()
        self.pages.addWidget(
            self.dashboard_page
        )
        self.pages.addWidget(
            self.accounts_page
        )
        self.pages.addWidget(
            self.journal_page
        )
        self.pages.addWidget(
            self.ledger_page
        )
        self.pages.addWidget(
            self.trial_balance_page
        )
        self.pages.addWidget(
            self.pnl_page
        )
        self.pages.addWidget(
            self.balance_sheet_page
        )
        self.pages.addWidget(
            self.cash_flow_page
        )
        self.pages.addWidget(
            self.audit_page
        )
        self.pages.addWidget(
            self.customers_page
        )        
        self.pages.addWidget(
            self.vendors_page
        )
        self.pages.addWidget(
            self.invoices_page
        )
        self.pages.addWidget(
            self.settings_page
        )
        self.splitter.addWidget(
            self.navigation
        )
        self.splitter.addWidget(
            self.pages
        )
        self.main_layout.addWidget(
            self.splitter
        )
        self.create_menu()
        self.create_toolbar()
        self.create_statusbar()
        self.navigation.navigation_list.currentRowChanged.connect(
            self.pages.setCurrentIndex
        )

    def create_menu(self):
        menubar=self.menuBar()
        file_menu=menubar.addMenu(
            "File"
        )
        import_action=QAction(
            "Import Accounts",
            self
        )
        export_action=QAction(
            "Export Report",
            self
        )
        backup_action=QAction(
            "Create Backup",
            self
        )
        new_account_action=QAction(
            "New Account",
            self
        )     
        new_journal_action=QAction(
            "New Journal Entry",
            self
        )
        view_backups_action=QAction(
            "Manage Backups",
            self
        )
        file_menu.addAction(
            import_action
        )
        file_menu.addAction(
            export_action
        )
        file_menu.addAction(
            backup_action
        )
        file_menu.addSeparator()
        file_menu.addAction(
            new_account_action
        )
        file_menu.addAction(
            new_journal_action
        )
        file_menu.addAction(
            view_backups_action
        )
        import_action.triggered.connect(
            self.import_accounts
        )
        export_action.triggered.connect(
            self.export_trial_balance
        )
        backup_action.triggered.connect(
            self.create_backup
        )
        new_account_action.triggered.connect(
            self.open_account_dialog
        )        
        new_journal_action.triggered.connect(
            self.open_journal_dialog
        )
        view_backups_action.triggered.connect(
            self.open_backup_dialog
        )
        
    def create_toolbar(self):
        self.toolbar=QToolBar()
        self.addToolBar(
            self.toolbar
        )
        refresh_action=QAction(
            "Refresh",
            self
        )
        dashboard_action=QAction(
            "Dashboard",
            self
        )
        accounts_action=QAction(
            "Accounts",
            self
        )
        journal_action=QAction(
            "Journal",
            self
        )
        reports_action=QAction(
            "Reports",
            self
        )       
        backup_toolbar_action=QAction(
            "Backup",
            self
        )
        import_toolbar_action=QAction(
            "Import",
            self
        )
        quick_account_action=QAction(
            "Quick Account",
            self
        )
        self.toolbar.addAction(
            refresh_action
        )
        self.toolbar.addAction(
            dashboard_action
        )
        self.toolbar.addAction(
            accounts_action
        )
        self.toolbar.addAction(
            journal_action
        )
        self.toolbar.addAction(
            reports_action
        )       
        self.toolbar.addAction(
            import_toolbar_action
        )
        self.toolbar.addAction(
            quick_account_action
        )
        self.toolbar.addAction(
            backup_toolbar_action
        )
        refresh_action.triggered.connect(
            self.refresh_all
        )
        dashboard_action.triggered.connect(
            lambda:self.pages.setCurrentIndex(0)
        )
        accounts_action.triggered.connect(
            lambda:self.pages.setCurrentIndex(1)
        )
        journal_action.triggered.connect(
            lambda:self.pages.setCurrentIndex(2)
        )
        reports_action.triggered.connect(
            lambda:self.pages.setCurrentIndex(4)
        )       
        import_toolbar_action.triggered.connect(
            self.open_import_dialog
        )
        quick_account_action.triggered.connect(
            self.quick_create_account
        )
        backup_toolbar_action.triggered.connect(
            self.open_backup_dialog
        )

    def create_statusbar(self):
        self.statusbar=QStatusBar()
        self.setStatusBar(
            self.statusbar
        )
        self.statusbar.showMessage(
            "Ready"
        )

    def initialize_demo_data(self):
        existing=self.accounts.get_all_accounts()
        if existing:
            return
        sample_accounts=[
            ("1000","Cash","Asset"),
            ("1100","Bank","Asset"),
            (
                "1200",
                "Accounts Receivable",
                "Asset"
            ),
            (
                "2000",
                "Accounts Payable",
                "Liability"
            ),
            (
                "3000",
                "Owner Equity",
                "Equity"
            ),
            (
                "4000",
                "Sales Revenue",
                "Revenue"
            ),
            (
                "5000",
                "Office Expense",
                "Expense"
            )
        ]
        for code,name,acc_type in sample_accounts:
            self.accounts.create_account(
                code,
                name,
                acc_type
            )
        accounts=self.accounts.get_all_accounts()
        account_map={}
        for account in accounts:
            account_map[
                account["account_code"]
            ]=account["id"]
        self.transactions.post_transaction(
            "JE-0001",
            "2026-01-01",
            "OPENING",
            "Opening Balance",
            account_map["1000"],
            account_map["3000"],
            50000
        )

    def refresh_dashboard(self):
        summary=self.dashboard.get_dashboard_summary()
        self.dashboard_page.accounts_card.setText(
            f"Accounts\n{summary['total_accounts']}"
        )
        self.dashboard_page.entries_card.setText(
            f"Entries\n{summary['total_journal_entries']}"
        )
        self.dashboard_page.debits_card.setText(
            f"Debits\n{summary['total_debits']}"
        )
        self.dashboard_page.credits_card.setText(
            f"Credits\n{summary['total_credits']}"
        )
        self.dashboard_page.customers_card.setText(
            f"Customers\n{summary['total_customers']}"
        )       
        self.dashboard_page.vendors_card.setText(
            f"Vendors\n{summary['total_vendors']}"
        )
        self.dashboard_page.invoices_card.setText(
            f"Invoices\n{summary['total_invoices']}"
        )
        
    def load_dashboard_recent_entries(self):
        rows=self.dashboard.get_recent_journal_entries()
        table=self.dashboard_page.recent_entries_table
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Entry No",
            "Date",
            "Reference",
            "Description",
            "Debit",
            "Credit"
        ])
        table.setRowCount(
            len(rows)
        )
        for row_index,row in enumerate(rows):
            table.setItem(
                row_index,
                0,
                QTableWidgetItem(
                    str(row["entry_number"])
                )
            )
            table.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    str(row["entry_date"])
                )
            )
            table.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    str(row["reference"])
                )
            )
            table.setItem(
                row_index,
                3,
                QTableWidgetItem(
                    str(row["description"])
                )
            )
            table.setItem(
                row_index,
                4,
                QTableWidgetItem(
                    str(row["total_debit"])
                )
            )
            table.setItem(
                row_index,
                5,
                QTableWidgetItem(
                    str(row["total_credit"])
                )
            )
        self.apply_table_styling(
            table
        )
        
    def refresh_all(self):
        self.refresh_dashboard()
        self.load_dashboard_recent_entries()
        self.load_accounts_table()
        self.load_journal_table()
        self.load_audit_logs()
        self.load_trial_balance_report()
        self.load_profit_loss_report()
        self.load_balance_sheet_report()
        self.load_cash_flow_report()
        self.statusbar.showMessage(
            "Data refreshed"
        )

    def load_accounts_table(self):
        rows=self.accounts.get_all_accounts()
        self.accounts_page.setColumnCount(4)
        self.accounts_page.setHorizontalHeaderLabels([
            "Code",
            "Name",
            "Type",
            "Status"
        ])
        self.accounts_page.setRowCount(
            len(rows)
        )
        self.apply_table_styling(
            self.accounts_page
        )
        for row_index,row in enumerate(rows):
            self.accounts_page.setItem(
                row_index,
                0,
                QTableWidgetItem(
                    str(row["account_code"])
                )
            )
            self.accounts_page.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    str(row["account_name"])
                )
            )
            self.accounts_page.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    str(row["account_type"])
                )
            )
            self.accounts_page.setItem(
                row_index,
                3,
                QTableWidgetItem(
                    str(row["is_active"])
                )
            )
            
    def load_journal_table(self):
        rows=self.journal.get_all_journal_entries()
        self.journal_page.setColumnCount(6)
        self.journal_page.setHorizontalHeaderLabels([
            "Entry No",
            "Date",
            "Reference",
            "Description",
            "Debit",
            "Credit"
        ])
        self.journal_page.setRowCount(
            len(rows)
        )
        self.apply_table_styling(
            self.journal_page
        )
        for row_index,row in enumerate(rows):
            self.journal_page.setItem(
                row_index,
                0,
                QTableWidgetItem(
                    str(row["entry_number"])
                )
            )
            self.journal_page.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    str(row["entry_date"])
                )
            )
            self.journal_page.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    str(row["reference"])
                )
            )
            self.journal_page.setItem(
                row_index,
                3,
                QTableWidgetItem(
                    str(row["description"])
                )
            )
            self.journal_page.setItem(
                row_index,
                4,
                QTableWidgetItem(
                    str(row["total_debit"])
                )
            )
            self.journal_page.setItem(
                row_index,
                5,
                QTableWidgetItem(
                    str(row["total_credit"])
                )
            )

    def load_audit_logs(self):
        rows=self.reports.get_audit_logs()
        self.audit_page.setColumnCount(5)
        self.audit_page.setHorizontalHeaderLabels([
            "Action",
            "Table",
            "Record ID",
            "Message",
            "Created"
        ])
        self.audit_page.setRowCount(
            len(rows)
        )
        for row_index,row in enumerate(rows):
            self.audit_page.setItem(
                row_index,
                0,
                QTableWidgetItem(
                    str(row["action_type"])
                )
            )
            self.audit_page.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    str(row["table_name"])
                )
            )
            self.audit_page.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    str(row["record_id"])
                )
            )
            self.audit_page.setItem(
                row_index,
                3,
                QTableWidgetItem(
                    str(row["message"])
                )
            )
            self.audit_page.setItem(
                row_index,
                4,
                QTableWidgetItem(
                    str(row["created_at"])
                )
            )
            
    def load_trial_balance_report(self):
        rows=self.reports.get_trial_balance()
        self.trial_balance_page.title_label.setText(
            f"Trial Balance ({len(rows)} Accounts)"
        )
        self.populate_report_table(
            self.trial_balance_page.report_table,
            rows
        )

    def load_profit_loss_report(self):
        rows=self.reports.get_profit_and_loss()
        self.pnl_page.title_label.setText(
            f"Profit & Loss ({len(rows)} Rows)"
        )
        self.populate_report_table(
            self.pnl_page.report_table,
            rows
        )

    def load_balance_sheet_report(self):
        rows=self.reports.get_balance_sheet()
        self.balance_sheet_page.title_label.setText(
            f"Balance Sheet ({len(rows)} Rows)"
        )
        self.populate_report_table(
            self.balance_sheet_page.report_table,
            rows
        )

    def load_cash_flow_report(self):
        rows=self.reports.get_cash_flow_summary()
        self.cash_flow_page.title_label.setText(
            f"Cash Flow ({len(rows)} Accounts)"
        )
        self.populate_report_table(
            self.cash_flow_page.report_table,
            rows
        )

    def populate_report_table(
        self,
        table,
        rows
    ):
        if not rows:
            table.clear()
            return
        headers=list(
            rows[0].keys()
        )
        table.setColumnCount(
            len(headers)
        )
        table.setHorizontalHeaderLabels(
            headers
        )
        table.setRowCount(
            len(rows)
        )
        for row_index,row in enumerate(rows):
            for column_index,header in enumerate(headers):
                table.setItem(
                    row_index,
                    column_index,
                    QTableWidgetItem(
                        str(row[header])
                    )
                )
        self.apply_table_styling(
            table
        )

    def import_accounts(self):
        file_path,_=QFileDialog.getOpenFileName(
            self,
            "Import Accounts"
        )
        if not file_path:
            return
        imported=self.imports.import_chart_of_accounts(
            file_path
        )
        self.load_accounts_table()
        QMessageBox.information(
            self,
            "Import Complete",
            f"Imported {imported} accounts"
        )

    def export_trial_balance(self):
        rows=self.reports.get_trial_balance()
        dataframe=self.reports.rows_to_dataframe(
            rows
        )
        file_path,_=QFileDialog.getSaveFileName(
            self,
            "Export Trial Balance",
            "",
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return
        self.exports.export_dataframe_pdf(
            dataframe,
            file_path,
            "Trial Balance"
        )
        QMessageBox.information(
            self,
            "Export Complete",
            "Report exported successfully"
        )

    def create_backup(self):
        backup_file=self.backups.create_backup()
        QMessageBox.information(
            self,
            "Backup Created",
            backup_file
        )
        
    def open_account_dialog(self):
        dialog=AccountDialog(self)
        result=dialog.exec_()
        if not result:
            return
        code=dialog.account_code.text().strip()
        name=dialog.account_name.text().strip()
        account_type=dialog.account_type.currentText()
        if not code or not name:
            QMessageBox.warning(
                self,
                "Validation",
                "Account code and name required"
            )
            return
        self.accounts.create_account(
            code,
            name,
            account_type
        )
        self.load_accounts_table()
        self.refresh_dashboard()

    def open_journal_dialog(self):
        dialog=JournalEntryDialog(self)
        dialog.lines_table.setRowCount(2)
        result=dialog.exec_()
        if not result:
            return
        try:
            entry_number=dialog.entry_number.text().strip()
            reference=dialog.reference.text().strip()
            description=dialog.description.toPlainText().strip()
            lines=[]
            for row in range(
                dialog.lines_table.rowCount()
            ):
                account_item=dialog.lines_table.item(
                    row,
                    0
                )
                description_item=dialog.lines_table.item(
                    row,
                    1
                )
                debit_item=dialog.lines_table.item(
                    row,
                    2
                )
                credit_item=dialog.lines_table.item(
                    row,
                    3
                )
                if not account_item:
                    continue
                lines.append({
                    "account_id":
                    int(account_item.text()),
                    "description":
                    description_item.text()
                    if description_item
                    else "",
                    "debit":
                    float(debit_item.text())
                    if debit_item
                    else 0,
                    "credit":
                    float(credit_item.text())
                    if credit_item
                    else 0
                })
            if not entry_number:
                entry_number=self.transactions.generate_entry_number()        
            entry_date=dialog.entry_date.date().toString(
                "yyyy-MM-dd"
            )        
            self.journal.create_journal_entry(
                entry_number,
                entry_date,
                reference,
                description,
                lines
            )
            self.load_journal_table()
            self.refresh_dashboard()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                str(e)
            )

    def open_backup_dialog(self):
        dialog=BackupDialog(self)
        backups=self.backups.list_backups()
        dialog.backup_list.addItems(
            backups
        )
        dialog.exec_()
        
    def open_import_dialog(self):
        dialog=ImportDialog(self)
        result=dialog.exec_()
        if not result:
            return
        file_path=dialog.file_path.text().strip()
        if not file_path:
            return
        try:
            imported=self.imports.import_chart_of_accounts(
                file_path
            )
            self.load_accounts_table()
            self.refresh_dashboard()
            QMessageBox.information(
                self,
                "Import Complete",
                f"Imported {imported} accounts"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Import Failed",
                str(e)
            )
            
    def export_current_report(
        self,
        report_type
    ):
        report_map={
            "trial_balance":
            self.reports.get_trial_balance,
            "profit_loss":
            self.reports.get_profit_and_loss,
            "balance_sheet":
            self.reports.get_balance_sheet,
            "cash_flow":
            self.reports.get_cash_flow_summary
        }
        if report_type not in report_map:
            return
        rows=report_map[
            report_type
        ]()
        dataframe=self.reports.rows_to_dataframe(
            rows
        )
        file_path,_=QFileDialog.getSaveFileName(
            self,
            "Export Report",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx);;PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            if file_path.endswith(".csv"):
                self.exports.export_dataframe_csv(
                    dataframe,
                    file_path
                )
            elif file_path.endswith(".xlsx"):
                self.exports.export_dataframe_excel(
                    dataframe,
                    file_path
                )
            elif file_path.endswith(".pdf"):
                self.exports.export_dataframe_pdf(
                    dataframe,
                    file_path,
                    report_type
                )
            QMessageBox.information(
                self,
                "Export Complete",
                "Report exported successfully"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Export Failed",
                str(e)
            )

    def setup_report_exports(self):
        self.trial_balance_page.export_csv_btn.clicked.connect(
            lambda:self.export_current_report(
                "trial_balance"
            )
        )
        self.trial_balance_page.export_excel_btn.clicked.connect(
            lambda:self.export_current_report(
                "trial_balance"
            )
        )
        self.trial_balance_page.export_pdf_btn.clicked.connect(
            lambda:self.export_current_report(
                "trial_balance"
            )
        )
        self.pnl_page.export_csv_btn.clicked.connect(
            lambda:self.export_current_report(
                "profit_loss"
            )
        )
        self.pnl_page.export_excel_btn.clicked.connect(
            lambda:self.export_current_report(
                "profit_loss"
            )
        )
        self.pnl_page.export_pdf_btn.clicked.connect(
            lambda:self.export_current_report(
                "profit_loss"
            )
        )
        self.balance_sheet_page.export_csv_btn.clicked.connect(
            lambda:self.export_current_report(
                "balance_sheet"
            )
        )
        self.balance_sheet_page.export_excel_btn.clicked.connect(
            lambda:self.export_current_report(
                "balance_sheet"
            )
        )
        self.balance_sheet_page.export_pdf_btn.clicked.connect(
            lambda:self.export_current_report(
                "balance_sheet"
            )
        )
        self.cash_flow_page.export_csv_btn.clicked.connect(
            lambda:self.export_current_report(
                "cash_flow"
            )
        )
        self.cash_flow_page.export_excel_btn.clicked.connect(
            lambda:self.export_current_report(
                "cash_flow"
            )
        )
        self.cash_flow_page.export_pdf_btn.clicked.connect(
            lambda:self.export_current_report(
                "cash_flow"
            )
        )

    def quick_create_account(self):
        code,ok=QInputDialog.getText(
            self,
            "Account Code",
            "Enter account code"
        )
        if not ok or not code:
            return
        name,ok=QInputDialog.getText(
            self,
            "Account Name",
            "Enter account name"
        )
        if not ok or not name:
            return
        account_type,ok=QInputDialog.getItem(
            self,
            "Account Type",
            "Select account type",
            [
                "Asset",
                "Liability",
                "Equity",
                "Revenue",
                "Expense"
            ],
            0,
            False
        )
        if not ok:
            return
        self.accounts.create_account(
            code,
            name,
            account_type
        )
        self.load_accounts_table()
        self.refresh_dashboard()
        
    def apply_table_styling(self,table):
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        table.setAlternatingRowColors(
            True
        )
        table.setSortingEnabled(
            True
        )
        
    def connect_navigation_signals(self):
        self.trial_balance_page.refresh_btn.clicked.connect(
            self.load_trial_balance_report
        )
        self.pnl_page.refresh_btn.clicked.connect(
            self.load_profit_loss_report
        )
        self.balance_sheet_page.refresh_btn.clicked.connect(
            self.load_balance_sheet_report
        )
        self.cash_flow_page.refresh_btn.clicked.connect(
            self.load_cash_flow_report
        )