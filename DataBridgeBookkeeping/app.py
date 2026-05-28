from PyQt5.QtWidgets import(
    QMainWindow, QWidget, QHBoxLayout, QSplitter, QStackedWidget, QTableWidget,
    QTableWidgetItem, QFileDialog, QAbstractItemView, QMessageBox, QHeaderView,
    QInputDialog, QStatusBar, QMenu, QPushButton, QFrame, QVBoxLayout, QAction,
    QComboBox
)
from PyQt5.QtGui import QKeySequence
# from PyQt5.QtWidgets import QVBoxLayout, QAction, QToolBar
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
from validators import TransactionValidator

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
        self.unsaved_changes=False
        self.loading_data=False
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
        self.setCentralWidget(self.central_widget)
        self.main_layout=QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0,0,0,0)
        self.main_layout.setSpacing(0)
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
        self.trial_balance_page.title_label.setText("Trial Balance")
        self.pnl_page.title_label.setText("Profit & Loss")
        self.balance_sheet_page.title_label.setText("Balance Sheet")
        self.cash_flow_page.title_label.setText("Cash Flow")
        self.customers_page=QTableWidget()
        self.vendors_page=QTableWidget()
        self.invoices_page=QTableWidget()
        self.settings_page=QTableWidget()
        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(self.accounts_page)
        self.pages.addWidget(self.journal_page)
        self.pages.addWidget(self.ledger_page)
        self.pages.addWidget(self.trial_balance_page)
        self.pages.addWidget(self.pnl_page)
        self.pages.addWidget(self.balance_sheet_page)
        self.pages.addWidget(self.cash_flow_page)
        self.pages.addWidget(self.audit_page)
        self.pages.addWidget(self.customers_page)
        self.pages.addWidget(self.vendors_page)
        self.pages.addWidget(self.invoices_page)
        self.pages.addWidget(self.settings_page)
        self.action_bar_container=QFrame()
        self.action_bar_container.setFixedHeight(50)
        self.statusbar=QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Ready")
        self.right_panel=QVBoxLayout()
        self.right_panel.setContentsMargins(0,0,0,0)
        self.right_panel.setSpacing(0)
        self.right_container=QWidget()
        self.right_container.setLayout(self.right_panel)
        self.right_panel.addWidget(self.pages)
        self.splitter.addWidget(self.navigation)
        self.splitter.addWidget(self.right_container)
        self.main_layout.addWidget(self.splitter)
        self.navigation.tree.itemClicked.connect(self.handle_sidebar_click)
        self.accounts_page.doubleClicked.connect(
            lambda: self.open_accounts_context_menu(
                self.accounts_page.viewport().rect().center()
            )
        )        
        self.journal_page.doubleClicked.connect(
            lambda: self.open_journal_context_menu(
                self.journal_page.viewport().rect().center()
            )
        )
        self.pages.currentChanged.connect(
            lambda _: self.update_action_bar()
        )
        self.update_action_bar()
        self.save_shortcut=QAction(self)
        self.save_shortcut.setShortcut(QKeySequence("Ctrl+S"))
        self.save_shortcut.triggered.connect(self.global_save)
        self.addAction(self.save_shortcut)
        
    def update_action_bar(self):
        if hasattr(self,"action_buttons"):
            current_page=self.pages.currentIndex()    
            page_config={
                0:["REFRESH","ADD","DELETE"],
                1:["REFRESH","ADD","DELETE"],
                2:["REFRESH","ADD","DELETE"],
                3:["REFRESH"],
                4:["REFRESH"],
                5:["REFRESH"],
                6:["REFRESH"],
                7:["REFRESH"],
                8:["REFRESH"],
                9:["REFRESH","ADD","DELETE"],
                10:["REFRESH","ADD","DELETE"],
                11:["REFRESH","ADD","DELETE"],
                12:["REFRESH"]
            }
            enabled_buttons=page_config.get(
                current_page,
                ["REFRESH"]
            )
            has_rows=False
            current_widget=self.pages.currentWidget()
            if hasattr(current_widget,"rowCount"):
                has_rows=current_widget.rowCount()>0
            for name,button in self.action_buttons.items():
                if name=="DELETE":
                    button.setEnabled(
                        name in enabled_buttons and has_rows
                    )
                elif name=="SAVE":
                    save_allowed=name in enabled_buttons
                    button.setEnabled(
                        save_allowed and self.unsaved_changes
                    )
                    if self.unsaved_changes:
                        button.setText("SAVE *")
                    else:
                        button.setText("SAVE")
                else:
                    button.setEnabled(
                        name in enabled_buttons
                    )
            return
        self.action_bar=QFrame()
        layout=QHBoxLayout(self.action_bar)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(8)
        button_map={
            "REFRESH":self.refresh_all,
            "ADD":self.global_add,
            "SAVE":self.global_save,
            "DELETE":self.global_delete
        }
        self.action_buttons={}
        for text,func in button_map.items():
            btn=QPushButton(text)
            btn.setMinimumHeight(36)
            btn.setStyleSheet("""
            QPushButton{
                background:#1e88e5;
                color:white;
                font-weight:bold;
                padding:8px 16px;
                border-radius:4px;
            }
            QPushButton:hover:enabled{
                background:#1565c0;
            }
            QPushButton:disabled{
                background:#9e9e9e;
                color:#e0e0e0;
            }
            """)
            btn.clicked.connect(func)
            layout.addWidget(btn,1)
            self.action_buttons[text]=btn
        container_layout=QVBoxLayout(self.action_bar_container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.addWidget(self.action_bar)
        self.right_panel.insertWidget(
            0,
            self.action_bar_container
        )
        self.update_action_bar()
        
    def set_unsaved_changes(self,state=True):
        if self.loading_data:
            return
        self.unsaved_changes=state
        self.update_action_bar()
        
    def global_add(self):
        index=self.pages.currentIndex()    
        if index==0:
            self.open_journal_dialog()    
        elif index==1:
            self.open_account_dialog()
        elif index==2:
            self.open_journal_dialog()
        elif index in [9,10,11]:
            QMessageBox.information(self,"Info","Module not implemented yet")
            
    def global_save(self):
        if not self.unsaved_changes:
            return
        confirm=QMessageBox.question(
            self,
            "Confirm Save",
            "Are you sure you want to save changes?",
            QMessageBox.Ok|QMessageBox.Cancel
        )
        if confirm!=QMessageBox.Ok:
            return
        try:
            self.statusbar.showMessage("CHANGES SAVED")
            self.set_unsaved_changes(False)
            self.refresh_dashboard()
        except Exception as e:
            QMessageBox.warning(self,"Save Error",str(e))

    def global_delete(self):
        index=self.pages.currentIndex()
        if index==0:
            table=self.dashboard_page.recent_entries_table
            row=table.currentRow()        
            if row<0:
                row=0
            journal_entry_number=table.item(row,0).text()
            entries=self.journal.get_all_journal_entries()
            for entry in entries:
                if str(entry["entry_number"])==journal_entry_number:
                    confirm=QMessageBox.question(
                        self,
                        "Delete Journal Entry",
                        "Delete selected journal entry?"
                    )
                    if confirm!=QMessageBox.Yes:
                        return
                    self.journal.delete_journal_entry(
                        entry["id"]
                    )
                    self.load_journal_table()
                    self.load_dashboard_recent_entries()
                    self.refresh_dashboard()
        
                    self.statusbar.showMessage(
                        "Journal entry deleted successfully"
                    )
                    return
        if index==1:
            row=self.accounts_page.currentRow()
            if row<0:
                return
            account_id=int(
                self.accounts_page.item(row,0).text()
            )
            confirm=QMessageBox.question(
                self,
                "Delete Account",
                "Delete selected account?"
            )
            if confirm!=QMessageBox.Yes:
                return
            self.accounts.delete_account(
                account_id
            )
            self.load_accounts_table()
            self.refresh_dashboard()
            self.statusbar.showMessage(
                "Account deleted successfully"
            )
        elif index==2:
            row=self.journal_page.currentRow()
            if row<0:
                return
            journal_entry_id=int(
                self.journal_page.item(row,0).text()
            )
            confirm=QMessageBox.question(
                self,
                "Delete Journal Entry",
                "Delete selected journal entry?"
            )
            if confirm!=QMessageBox.Yes:
                return
            self.journal.delete_journal_entry(
                journal_entry_id
            )
            self.load_journal_table()
            self.refresh_dashboard()
            self.statusbar.showMessage(
                "Journal entry deleted successfully"
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
        self.loading_data=True
        rows=self.accounts.get_all_accounts()
        self.accounts_page.setColumnCount(5)
        self.accounts_page.setHorizontalHeaderLabels([
            "ID",
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
        self.accounts_page.setContextMenuPolicy(
            3
        )
        self.accounts_page.customContextMenuRequested.connect(
            self.open_accounts_context_menu
        )
        for row_index,row in enumerate(rows):
            self.accounts_page.setItem(
                row_index,
                0,
                QTableWidgetItem(
                    str(row["id"])
                )
            )
            self.accounts_page.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    str(row["account_code"])
                )
            )
            self.accounts_page.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    str(row["account_name"])
                )
            )
            self.accounts_page.setItem(
                row_index,
                3,
                QTableWidgetItem(
                    str(row["account_type"])
                )
            )
            self.accounts_page.setItem(
                row_index,
                4,
                QTableWidgetItem(
                    str(row["is_active"])
                )
            )
        self.loading_data=False
        self.update_action_bar()
    
    def open_accounts_context_menu(self,position):
        row=self.accounts_page.currentRow()
        if row<0:
            return
        account_id=int(
            self.accounts_page.item(row,0).text()
        )
        account_code=self.accounts_page.item(
            row,
            1
        ).text()
        account_name=self.accounts_page.item(
            row,
            2
        ).text()
        account_type=self.accounts_page.item(
            row,
            3
        ).text()
        status=self.accounts_page.item(
            row,
            4
        ).text()
        menu=QMenu()
        edit_action=menu.addAction(
            "Edit Account"
        )
        if status=="1":
            toggle_action=menu.addAction(
                "Deactivate Account"
            )
        else:
            toggle_action=menu.addAction(
                "Activate Account"
            )
        delete_action=menu.addAction(
            "Delete Account"
        )
        action=menu.exec_(
            self.accounts_page.viewport().mapToGlobal(
                position
            )
        )
        if action==edit_action:
            dialog=AccountDialog(self)
            dialog.account_code.setText(
                account_code
            )
            dialog.account_name.setText(
                account_name
            )
            if account_type in [
                "Asset",
                "Liability",
                "Equity",
                "Revenue",
                "Expense"
            ]:
                dialog.account_type.setCurrentText(
                    account_type
                )
            else:
                dialog.account_type.setCurrentText(
                    "Custom"
                )
                dialog.custom_account_type.setText(
                    account_type
                )
                dialog.custom_account_type.show()
            result=dialog.exec_()
            if not result:
                return
            code=dialog.account_code.text().strip()
            name=dialog.account_name.text().strip()
            acc_type=dialog.account_type.currentText()
            if acc_type=="Custom":
                acc_type=dialog.custom_account_type.text().strip()
            if not code or not name:
                QMessageBox.warning(
                    self,
                    "Validation",
                    "Account code and name required"
                )
                return
            self.accounts.update_account(
                account_id,
                code,
                name,
                acc_type
            )
            self.load_accounts_table()
            self.refresh_dashboard()
        elif action==toggle_action:
            if status=="1":
                self.accounts.deactivate_account(
                    account_id
                )
            else:
                self.accounts.activate_account(
                    account_id
                )
            self.load_accounts_table()
            self.refresh_dashboard()
        elif action==delete_action:
            confirm=QMessageBox.question(
                self,
                "Delete Account",
                "Delete selected account?"
            )
            if confirm!=QMessageBox.Yes:
                return
            self.accounts.delete_account(
                account_id
            )
            self.load_accounts_table()
            self.refresh_dashboard()
            
    def load_journal_table(self):
        self.loading_data=True
        rows=self.journal.get_all_journal_entries()
        self.journal_page.setColumnCount(7)
        self.journal_page.setHorizontalHeaderLabels([
            "ID",
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
        self.journal_page.setContextMenuPolicy(
            3
        )
        self.journal_page.customContextMenuRequested.connect(
            self.open_journal_context_menu
        )
        for row_index,row in enumerate(rows):
            self.journal_page.setItem(
                row_index,
                0,
                QTableWidgetItem(
                    str(row["id"])
                )
            )
            self.journal_page.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    str(row["entry_number"])
                )
            )
            self.journal_page.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    str(row["entry_date"])
                )
            )
            self.journal_page.setItem(
                row_index,
                3,
                QTableWidgetItem(
                    str(row["reference"])
                )
            )
            self.journal_page.setItem(
                row_index,
                4,
                QTableWidgetItem(
                    str(row["description"])
                )
            )
            self.journal_page.setItem(
                row_index,
                5,
                QTableWidgetItem(
                    str(row["total_debit"])
                )
            )
            self.journal_page.setItem(
                row_index,
                6,
                QTableWidgetItem(
                    str(row["total_credit"])
                )
            )
        self.loading_data=False
        self.update_action_bar()
            
    def open_journal_context_menu(self,position):
        row=self.journal_page.currentRow()
        if row<0:
            return
        journal_entry_id=int(
            self.journal_page.item(
                row,
                0
            ).text()
        )
        menu=QMenu()
        edit_action=menu.addAction(
            "Edit Journal Entry"
        )
        delete_action=menu.addAction(
            "Delete Journal Entry"
        )
        action=menu.exec_(
            self.journal_page.viewport().mapToGlobal(
                position
            )
        )
        if action==edit_action:
            self.edit_journal_entry(
                journal_entry_id
            )
        elif action==delete_action:
            confirm=QMessageBox.question(
                self,
                "Delete Journal Entry",
                "Delete selected journal entry?"
            )
            if confirm!=QMessageBox.Yes:
                return
            self.journal.delete_journal_entry(
                journal_entry_id
            )
            self.load_journal_table()
            self.refresh_dashboard()
            self.statusbar.showMessage(
                "Journal entry deleted successfully"
            )
            
    def edit_journal_entry(self,journal_entry_id):
        entry=self.journal.get_journal_entry_by_id(
            journal_entry_id
        )
        if not entry:
            return
        lines=self.journal.get_journal_entry_lines(
            journal_entry_id
        )
        dialog=JournalEntryDialog(self)
        dialog.entry_number.setText(
            str(entry["entry_number"])
        )
        dialog.entry_number.setReadOnly(
            True
        )
        dialog.reference.setText(
            str(entry["reference"])
        )
        dialog.description.setPlainText(
            str(entry["description"])
        )
        dialog.entry_date.setDate(
            dialog.entry_date.date().fromString(
                str(entry["entry_date"]),
                "yyyy-MM-dd"
            )
        )
        dialog.lines_table.setRowCount(
            len(lines)
        )
        for row_index,line in enumerate(lines):
            account_dropdown=QComboBox()
            accounts=self.accounts.get_all_accounts()
            selected_index=0
            for index,account in enumerate(accounts):
                account_dropdown.addItem(
                    f"{account['id']} - {account['account_name']}",
                    account["id"]
                )
                if account["id"]==line["account_id"]:
                    selected_index=index
            account_dropdown.setCurrentIndex(
                selected_index
            )
            dialog.lines_table.setCellWidget(
                row_index,
                0,
                account_dropdown
            )
            dialog.lines_table.setItem(
                row_index,
                1,
                QTableWidgetItem(
                    str(line["description"])
                )
            )
            dialog.lines_table.setItem(
                row_index,
                2,
                QTableWidgetItem(
                    str(line["debit"])
                )
            )
            dialog.lines_table.setItem(
                row_index,
                3,
                QTableWidgetItem(
                    str(line["credit"])
                )
            )
        result=dialog.exec_()
        if not result:
            return
        try:
            updated_lines=[]
            for row in range(
                dialog.lines_table.rowCount()
            ):
                account_widget=dialog.lines_table.cellWidget(
                    row,
                    0
                )
                if not account_widget:
                    continue
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
                updated_lines.append({
                    "account_id":
                    account_widget.currentData(),
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
            self.journal.update_journal_entry(
                journal_entry_id,
                dialog.entry_date.date().toString(
                    "yyyy-MM-dd"
                ),
                dialog.reference.text().strip(),
                dialog.description.toPlainText().strip(),
                updated_lines
            )
            self.load_journal_table()
            self.refresh_dashboard()
            self.statusbar.showMessage(
                "Journal entry updated successfully"
            )
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                str(e)
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
        if account_type=="Custom":
            account_type=dialog.custom_account_type.text().strip()
        if not TransactionValidator.validate_account_code(
            code
        ):
            QMessageBox.warning(
                self,
                "Validation",
                "Invalid account code"
            )
            return
        if not TransactionValidator.validate_account_name(
            name
        ):
            QMessageBox.warning(
                self,
                "Validation",
                "Invalid account name"
            )
            return
        if not TransactionValidator.validate_account_type(
            account_type
        ):
            QMessageBox.warning(
                self,
                "Validation",
                "Invalid account type"
            )
            return
        if self.accounts.account_exists(
            code
        ):
            QMessageBox.warning(
                self,
                "Duplicate Account",
                "Account code already exists"
            )
            return
        self.accounts.create_account(
            code,
            name,
            account_type
        )
        self.load_accounts_table()
        self.refresh_dashboard()
        self.statusbar.showMessage(
            "Account created successfully"
        )

    def open_journal_dialog(self):
        dialog=JournalEntryDialog(self)
        dialog.add_line()
        dialog.add_line()
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
                account_widget=dialog.lines_table.cellWidget(
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
                if not account_widget:
                    continue
                lines.append({
                    "account_id":
                    account_widget.currentData(),
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
        if self.accounts.account_exists(
            code.strip()
        ):
            QMessageBox.warning(
                self,
                "Duplicate Account",
                "Account code already exists"
            )
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
            code.strip(),
            name.strip(),
            account_type
        )
        self.load_accounts_table()
        self.refresh_dashboard()
        self.statusbar.showMessage(
            "Account created successfully"
        )
        
    def apply_table_styling(self,table):
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch
        )
        table.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )
        table.setSelectionMode(
            QAbstractItemView.SingleSelection
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
        table.verticalHeader().setVisible(
            False
        )
        
    def handle_navigation_click(self,item,column):
        text=item.text(0).strip().upper()
        mapping={
            "DASHBOARD":0,
            "CHART OF ACCOUNTS":1,
            "JOURNAL ENTRIES":2,
            "GENERAL LEDGER":3,
            "TRIAL BALANCE":4,
            "PROFIT & LOSS":5,
            "BALANCE SHEET":6,
            "CASH FLOW":7,
            "AUDIT LOGS":8,
            "CUSTOMERS":9,
            "VENDORS":10,
            "INVOICES":11,
            "SETTINGS":12
        }
        if text in mapping:
            self.pages.setCurrentIndex(mapping[text])
            
    def handle_sidebar_click(self,item,column):
        text=item.text(0).strip().upper()
        nav_map={
            "DASHBOARD":0,
            "CHART OF ACCOUNTS":1,
            "JOURNAL ENTRIES":2,
            "GENERAL LEDGER":3,
            "TRIAL BALANCE":4,
            "PROFIT & LOSS":5,
            "BALANCE SHEET":6,
            "CASH FLOW":7,
            "AUDIT LOGS":8,
            "CUSTOMERS":9,
            "VENDORS":10,
            "INVOICES":11,
            "SETTINGS":12
        }
        if text in nav_map:
            self.pages.setCurrentIndex(nav_map[text])
            self.update_action_bar()
            return
        action_map={
            "NEW ACCOUNT":self.open_account_dialog,
            "QUICK ACCOUNT":self.quick_create_account,
            "NEW JOURNAL ENTRY":self.open_journal_dialog,
            "IMPORT ACCOUNTS":self.import_accounts,
            "EXPORT REPORT":self.export_trial_balance,
            "CREATE BACKUP":self.create_backup,
            "MANAGE BACKUPS":self.open_backup_dialog,
            "REFRESH":self.refresh_all
        }
        action=action_map.get(text)
        if action:
            action()
            self.update_action_bar()
        
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
    
    def closeEvent(self,event):
        if self.unsaved_changes:
            reply=QMessageBox.question(
                self,
                "Unsaved Changes",
                "Exit without saving?",
                QMessageBox.Ok|QMessageBox.Cancel
            )
            if reply!=QMessageBox.Ok:
                event.ignore()
                return
        event.accept()