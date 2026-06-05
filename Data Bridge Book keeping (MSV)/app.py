from PyQt5.QtWidgets import(
    QMainWindow, QWidget, QHBoxLayout, QSplitter, QStackedWidget, QTableWidget,
    QTableWidgetItem, QFileDialog, QAbstractItemView, QMessageBox, QHeaderView,
    QInputDialog, QStatusBar, QMenu, QPushButton, QFrame, QVBoxLayout, QAction,
    QComboBox, QToolButton, QDialog, QDateEdit, QFormLayout, QDialogButtonBox,
    QLabel, QLineEdit
)
from PyQt5.QtCore import QDate, Qt
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

class DateFilterDialog(QDialog):
    def __init__(self,parent=None):    
        super().__init__(parent)
        self.setWindowTitle(
            "Custom Date Filter"
        )
        layout=QFormLayout(self)
        self.from_date=QDateEdit()
        self.to_date=QDateEdit()
        self.from_date.setCalendarPopup(
            True
        )
        self.to_date.setCalendarPopup(
            True
        )
        self.from_date.setDate(
            QDate.currentDate().addMonths(-1)
        )
        self.to_date.setDate(
            QDate.currentDate()
        )
        layout.addRow(
            "From",
            self.from_date
        )
        layout.addRow(
            "To",
            self.to_date
        )
        buttons=QDialogButtonBox(
            QDialogButtonBox.Ok|
            QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(
            self.accept
        )
        buttons.rejected.connect(
            self.reject
        )
        layout.addWidget(
            buttons
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
        self.create_session_snapshot()
        self.settings=SettingsManager(
            self.db
        )
        self.setWindowTitle(
            "Bookkeeping System"
        )
        self.unsaved_changes=False
        self.loading_data=False
        self.accounts_filter="all"
        self.current_status_path="Dashboard"
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
        self.accounts_page.setContextMenuPolicy(
            Qt.CustomContextMenu
        )
        self.accounts_page.customContextMenuRequested.connect(
            self.open_accounts_context_menu
        )
        self.journal_page=QTableWidget()
        self.journal_page.setContextMenuPolicy(
            Qt.CustomContextMenu
        )
        self.journal_page.customContextMenuRequested.connect(
            self.open_journal_context_menu
        )
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
        self.action_bar_container.setFixedHeight(95)
        self.action_bar_container.setFixedHeight(140)
        self.navigation_status=QLabel("Dashboard")
        self.navigation_status.setFixedHeight(28)
        self.navigation_status.setStyleSheet("""
        QLabel{
            background:#f5f5f5;
            border-top:1px solid #d0d0d0;
            border-bottom:1px solid #d0d0d0;
            padding-left:10px;
            font-weight:bold;
        }
        """)
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
        
    def update_status_path(self,text):
        self.current_status_path=text
        if hasattr(self,"navigation_status"):
            self.navigation_status.setText(text)
        
    def update_action_bar(self):
        if hasattr(self,"action_buttons"):
            current_page=self.pages.currentIndex()    
            page_config={
                0:["REFRESH","ADD","SELECT","FILTER","DELETE","RESTORE"],
                1:["REFRESH","ADD","SELECT","FILTER","DELETE","RESTORE"],
                2:["REFRESH","ADD","SELECT","FILTER","DELETE","RESTORE"],
                3:["REFRESH"],
                4:["REFRESH"],
                5:["REFRESH"],
                6:["REFRESH"],
                7:["REFRESH"],
                8:["REFRESH"],
                9:["REFRESH","ADD","SELECT"],
                10:["REFRESH","ADD","SELECT"],
                11:["REFRESH","ADD","SELECT"],
                12:["REFRESH"]
            }
            enabled_buttons=page_config.get(
                current_page,
                ["REFRESH"]
            )
            select_pages=[
                0,
                1,
                2,
                9,
                10,
                11
            ]
            for name,button in self.action_buttons.items():
                if name=="FILTER":
                    button.setEnabled(
                        name in enabled_buttons
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
                elif name=="SELECT":
                    button.setEnabled(
                        current_page in select_pages
                    )
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
            "FILTER":self.open_filter_menu,
            "SAVE":self.global_save,
            "DELETE":self.global_delete,
            "RESTORE":self.restore_session_snapshot
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
            layout.update()
            self.action_bar.update()
            self.action_buttons[text]=btn
            if text=="ADD" and "SELECT" not in self.action_buttons:
                select_btn=QToolButton()
                select_btn.setSizePolicy(
                    QPushButton().sizePolicy()
                )
                select_btn.setText("SELECT")
                select_btn.setMinimumHeight(36)
                select_btn.setToolButtonStyle(
                    0
                )
                select_btn.setStyleSheet("""
                QToolButton{
                    background:#1e88e5;
                    color:white;
                    font-weight:bold;
                    padding:8px 16px;
                    border-radius:4px;
                }
                QToolButton:hover{
                    background:#1565c0;
                }
                QToolButton:menu-indicator{
                    image:none;
                }
                """)
                menu=QMenu(self)
                menu.addAction(
                    "Select All",
                    self.select_all_entries
                )
                menu.addAction(
                    "Select None",
                    self.select_none_entries
                )
                menu.addAction(
                    "Select Alternate",
                    self.select_alternate_entries
                )
                select_btn.setMenu(menu)
                select_btn.setPopupMode(
                    QToolButton.InstantPopup
                )
                layout.addWidget(
                    select_btn,
                    1
                )            
                select_btn.setMinimumWidth(
                    btn.minimumWidth()
                )
                self.action_buttons["SELECT"]=select_btn
        container_layout=QVBoxLayout(self.action_bar_container)
        container_layout.setContentsMargins(0,0,0,0)
        container_layout.setSpacing(0)        
        container_layout.addWidget(self.action_bar)
        container_layout.addWidget(self.navigation_status)
        self.search_container=QFrame()
        search_layout=QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(0,0,0,0)
        search_layout.setSpacing(8)        
        self.search_input=QLineEdit()
        self.search_input.setPlaceholderText(
            "Search current page..."
        )
        self.search_input.setMinimumHeight(36)
        self.search_btn=QPushButton("SEARCH")
        self.search_btn.setMinimumHeight(36)
        self.previous_search_btn=QPushButton("PREVIOUS")
        self.previous_search_btn.setMinimumHeight(36)        
        self.next_search_btn=QPushButton("NEXT")
        self.next_search_btn.setMinimumHeight(36)
        self.previous_search_btn.clicked.connect(
            self.previous_search_result
        )
        self.next_search_btn.clicked.connect(
            self.next_search_result
        )
        self.clear_search_btn=QPushButton("CLEAR")
        self.clear_search_btn.setMinimumHeight(36)
        button_style="""
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
        """
        self.search_btn.setStyleSheet(
            button_style
        )        
        self.previous_search_btn.setStyleSheet(
            button_style
        )
        self.next_search_btn.setStyleSheet(
            button_style
        )
        self.clear_search_btn.setStyleSheet(
            button_style
        )
        self.search_btn.setStyleSheet(
            button_style
        )
        self.clear_search_btn.setStyleSheet(
            button_style
        )
        
        self.search_btn.clicked.connect(
            self.perform_search
        )
        self.clear_search_btn.clicked.connect(
            self.clear_search
        )
        search_layout.addWidget(
            self.search_input,
            12
        )
        search_layout.addWidget(
            self.search_btn,
            1
        )
        search_layout.addWidget(
            self.previous_search_btn,
            1
        )
        
        search_layout.addWidget(
            self.next_search_btn,
            1
        )
        search_layout.addWidget(
            self.clear_search_btn,
            1
        )
        container_layout.addWidget(
            self.search_container
        )
        self.right_panel.insertWidget(
            0,
            self.action_bar_container
        )
        self.update_action_bar()
        
    def set_navigation_status(self,text):
        self.current_status_path=text
        if hasattr(self,"navigation_status"):
            self.navigation_status.setText(text)
            
    def perform_search(self):
        search_text=self.search_input.text().strip().lower()
        if not search_text:
            return
        table=self.get_current_table()
        if not table:
            return
        table.clearSelection()
        self.search_matches=[]
        for row in range(table.rowCount()):
            for column in range(table.columnCount()):
                item=table.item(row,column)
                if not item:
                    continue
                if search_text in item.text().lower():
                    self.search_matches.append(row)
                    break
        self.search_matches=list(
            dict.fromkeys(self.search_matches)
        )
        self.current_search_index=0
        if not self.search_matches:
            self.statusbar.showMessage(
                "No matches found"
            )
            return
        table.setSelectionMode(
            QAbstractItemView.MultiSelection
        )
        for row in self.search_matches:
            table.selectRow(row)
    
        table.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )
        first_row=self.search_matches[0]
        first_item=table.item(
            first_row,
            0
        )
        if first_item:
            table.scrollToItem(
                first_item
            )
        self.statusbar.showMessage(
            f"{len(self.search_matches)} matches found"
        )
    
    def clear_search(self):
        if hasattr(self,"search_input"):
            self.search_input.clear()
        self.search_matches=[]
        self.current_search_index=-1
        table=self.get_current_table()
        if table:
            table.clearSelection()
            
    def next_search_result(self):
        if not hasattr(self,"search_matches"):
            return
        if not self.search_matches:
            return
        table=self.get_current_table()
        if not table:
            return
        self.current_search_index+=1
        if self.current_search_index>=len(
            self.search_matches
        ):
            self.current_search_index=0
        row=self.search_matches[
            self.current_search_index
        ]
        item=table.item(
            row,
            0
        )
        if item:
            table.scrollToItem(
                item
            )
        table.setCurrentCell(
            row,
            0
        )
    
    def previous_search_result(self):
        if not hasattr(self,"search_matches"):
            return
        if not self.search_matches:
            return
        table=self.get_current_table()
        if not table:
            return
        self.current_search_index-=1
        if self.current_search_index<0:
            self.current_search_index=(
                len(self.search_matches)-1
            )
        row=self.search_matches[
            self.current_search_index
        ]
        item=table.item(
            row,
            0
        )
        if item:
            table.scrollToItem(
                item
            )
        table.setCurrentCell(
            row,
            0
        )
        
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
        self.set_unsaved_changes(False)
        self.statusbar.showMessage(
            "Changes saved"
        )
            
    def open_filter_menu(self):
        current_page=self.pages.currentIndex()
        menu=QMenu(self)
        if current_page==1:
            menu.addAction(
                "Activated Accounts",
                lambda:self.filter_accounts(True)
            )
            menu.addAction(
                "Deactivated Accounts",
                lambda:self.filter_accounts(False)
            )
            menu.addAction(
                "Show All Accounts",
                self.show_all_accounts
            )
        elif current_page==2:
            menu.addAction(
                "Today",
                lambda:self.filter_journal("today")
            )
            menu.addAction(
                "This Week",
                lambda:self.filter_journal("week")
            )
            menu.addAction(
                "This Month",
                lambda:self.filter_journal("month")
            )
            menu.addAction(
                "This Year",
                lambda:self.filter_journal("year")
            )
            menu.addSeparator()
            menu.addAction(
                "Custom Date Range",
                self.open_custom_date_filter
            )
            menu.addAction(
                "Show All Journal Entries",
                self.show_all_journal_entries
            )
        sender=self.sender()
        if sender:
            menu.exec_(
                sender.mapToGlobal(
                    sender.rect().bottomLeft()
                )
            )

    def global_delete(self):
        index=self.pages.currentIndex()
        if index==0:
            table=self.dashboard_page.recent_entries_table
            selected_rows=table.selectionModel().selectedRows()
            if not selected_rows:
                return
            confirm=QMessageBox.question(
                self,
                "Master Delete",
                f"Delete {len(selected_rows)} selected journal entrie(s)?"
            )
            if confirm!=QMessageBox.Yes:
                return
            entries=self.journal.get_all_journal_entries()
            for selected in selected_rows:
                row=selected.row()
                journal_entry_number=table.item(row,0).text()
                for entry in entries:
                    if str(entry["entry_number"])==journal_entry_number:
                        self.journal.delete_journal_entry(
                            entry["id"]
                        )
            self.load_journal_table()
            self.load_dashboard_recent_entries()
            self.refresh_dashboard()
            self.statusbar.showMessage(
                "Selected journal entries deleted successfully"
            )
        elif index==1:
            table=self.accounts_page
            selected_rows=table.selectionModel().selectedRows()
            if not selected_rows:
                return
            confirm=QMessageBox.question(
                self,
                "Master Delete",
                f"Delete {len(selected_rows)} selected account(s)?"
            )
            if confirm!=QMessageBox.Yes:
                return
            for selected in selected_rows:
                row=selected.row()
                item=table.item(row,0)
                if not item:
                    continue
                account_id=int(
                    item.text()
                )
                self.accounts.delete_account(
                    account_id
                )
            self.load_accounts_table()
            self.refresh_dashboard()
            self.statusbar.showMessage(
                "Selected accounts deleted successfully"
            )
        elif index==2:
            table=self.journal_page
            selected_rows=table.selectionModel().selectedRows()
            if not selected_rows:
                return
            confirm=QMessageBox.question(
                self,
                "Master Delete",
                f"Delete {len(selected_rows)} selected journal entrie(s)?"
            )
            if confirm!=QMessageBox.Yes:
                return
            for selected in selected_rows:
                row=selected.row()
                item=table.item(row,0)
                if not item:
                    continue
                journal_entry_id=int(
                    item.text()
                )
                self.journal.delete_journal_entry(
                    journal_entry_id
                )
            self.load_journal_table()
            self.refresh_dashboard()
            self.statusbar.showMessage(
                "Selected journal entries deleted successfully"
            )
            
    def get_current_table(self):
        current_page=self.pages.currentIndex()
        if current_page==0:
            return self.dashboard_page.recent_entries_table
        if current_page==1:
            return self.accounts_page
        if current_page==2:
            return self.journal_page
        if current_page==9:
            return self.customers_page
        if current_page==10:
            return self.vendors_page
        if current_page==11:
            return self.invoices_page
        return None
    
    def select_all_entries(self):
        table=self.get_current_table()
        if not table:
            return
        table.selectAll()
    
    def select_none_entries(self):
        table=self.get_current_table()
        if not table:
            return
        table.clearSelection()
    
    def select_alternate_entries(self):
        table=self.get_current_table()
        if not table:
            return
        table.clearSelection()
        table.setSelectionMode(
            QAbstractItemView.MultiSelection
        )
        for row in range(0,table.rowCount(),2):
            table.selectRow(row)
        table.setSelectionMode(
            QAbstractItemView.ExtendedSelection
        )

    def activate_selected_accounts(self):    
        selected_rows=self.accounts_page.selectionModel().selectedRows()
        if not selected_rows:
            return
        confirm=QMessageBox.question(
            self,
            "Activate Accounts",
            f"Activate {len(selected_rows)} selected account(s)?"
        )
        if confirm!=QMessageBox.Yes:
            return
        for selected in selected_rows:
            account_id=int(
                self.accounts_page.item(
                    selected.row(),
                    0
                ).text()
            )
            self.accounts.activate_account(
                account_id
            )
        self.load_accounts_table()
        self.refresh_dashboard()
    
    def deactivate_selected_accounts(self):
        selected_rows=self.accounts_page.selectionModel().selectedRows()
        if not selected_rows:
            return
        confirm=QMessageBox.question(
            self,
            "Deactivate Accounts",
            f"Deactivate {len(selected_rows)} selected account(s)?"
        )
        if confirm!=QMessageBox.Yes:
            return
        for selected in selected_rows:
            account_id=int(
                self.accounts_page.item(
                    selected.row(),
                    0
                ).text()
            )
            self.accounts.deactivate_account(
                account_id
            )
        self.load_accounts_table()
        self.refresh_dashboard()
    
    def delete_selected_accounts(self):
        selected_rows=self.accounts_page.selectionModel().selectedRows()
        if not selected_rows:
            return
        confirm=QMessageBox.question(
            self,
            "Delete Accounts",
            f"Delete {len(selected_rows)} selected account(s)?"
        )
        if confirm!=QMessageBox.Yes:
            return
        rows=sorted(
            [r.row() for r in selected_rows],
            reverse=True
        )
        for row in rows:
            account_id=int(
                self.accounts_page.item(
                    row,
                    0
                ).text()
            )
            self.accounts.delete_account(
                account_id
            )
        self.load_accounts_table()
        self.refresh_dashboard()

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
        
    def create_session_snapshot(self):
        self.session_snapshot={}
        tables=[
            "accounts",
            "journal_entries",
            "journal_lines",
            "audit_logs",
            "app_settings",
            "saved_reports",
            "attachments",
            "fiscal_periods",
            "recurring_transactions",
            "bank_accounts",
            "customers",
            "vendors",
            "invoices",
            "invoice_items"
        ]
        for table in tables:
            rows=self.db.fetchall(
                f"SELECT * FROM {table}"
            )
            self.session_snapshot[table]=[
                dict(row)
                for row in rows
            ]
        
    def restore_session_snapshot(self):
        confirm=QMessageBox.question(
            self,
            "Restore Session",
            "Restore application to startup state?"
        )
        if confirm!=QMessageBox.Yes:
            return
        try:
            tables=[
                "invoice_items",
                "invoices",
                "vendors",
                "customers",
                "bank_accounts",
                "recurring_transactions",
                "fiscal_periods",
                "attachments",
                "saved_reports",
                "app_settings",
                "audit_logs",
                "journal_lines",
                "journal_entries",
                "accounts"
            ]
            self.db.begin_transaction()
            cursor=self.db.conn.cursor()
            for table in tables:
                cursor.execute(
                    f"DELETE FROM {table}"
                )
            for table,rows in self.session_snapshot.items():
                if not rows:
                    continue
                columns=list(
                    rows[0].keys()
                )
                column_string=",".join(
                    columns
                )
                placeholders=",".join(
                    ["?"]*len(columns)
                )
                values=[]
                for row in rows:
                    values.append(
                        tuple(
                            row[column]
                            for column in columns
                        )
                    )
                self.db.executemany(
                    f"""
                    INSERT INTO {table}
                    ({column_string})
                    VALUES ({placeholders})
                    """,
                    values
                )
            self.db.commit_transaction()
            self.refresh_all()
            self.statusbar.showMessage(
                "Session restored successfully"
            )
        except Exception as e:
            self.db.rollback_transaction()
            QMessageBox.warning(
                self,
                "Restore Failed",
                str(e)
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
        
    def filter_accounts(self,active_state):
        self.accounts_filter=(
            "active"
            if active_state
            else "inactive"
        )
        self.loading_data=True
        rows=self.accounts.get_all_accounts()
        filtered=[]
        for row in rows:
            status=str(
                row["is_active"]
            )
            if active_state and status=="1":
                filtered.append(row)
            elif not active_state and status!="1":
                filtered.append(row)
        self.accounts_page.setRowCount(
            len(filtered)
        )
        for row_index,row in enumerate(filtered):
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
        if active_state:
            self.set_navigation_status(
                "Chart Of Accounts > Activated Accounts"
            )
        else:
            self.set_navigation_status(
                "Chart Of Accounts > Deactivated Accounts"
            )
    
    def show_all_accounts(self):
        self.accounts_filter="all"
        self.load_accounts_table()
        self.set_navigation_status(
            "Chart Of Accounts > All Accounts"
        )
        
    def filter_journal(self,period):
        rows=self.journal.get_all_journal_entries()
        today=QDate.currentDate()
        filtered=[]
        for row in rows:
            row_date=QDate.fromString(
                str(row["entry_date"]),
                "yyyy-MM-dd"
            )
            include=False
            if period=="today":
                include=row_date==today
            elif period=="week":
                include=(
                    row_date.weekNumber()[0]
                    ==
                    today.weekNumber()[0]
                    and
                    row_date.year()
                    ==
                    today.year()
                )
            elif period=="month":
                include=(
                    row_date.month()
                    ==
                    today.month()
                    and
                    row_date.year()
                    ==
                    today.year()
                )
            elif period=="year":
                include=(
                    row_date.year()
                    ==
                    today.year()
                )
            if include:
                filtered.append(row)
        self.populate_filtered_journal(
            filtered
        )
        self.set_navigation_status(
            f"Journal Entries > {period.title()}"
        )
    
    def open_custom_date_filter(self):
        dialog=DateFilterDialog(self)
        if not dialog.exec_():
            return
        self.filter_journal_range(
            dialog.from_date.date(),
            dialog.to_date.date()
        )
    
    def filter_journal_range(
        self,
        from_date,
        to_date
    ):
        rows=self.journal.get_all_journal_entries()
        filtered=[]
        for row in rows:
            row_date=QDate.fromString(
                str(row["entry_date"]),
                "yyyy-MM-dd"
            )
            if from_date<=row_date<=to_date:
                filtered.append(row)
        self.populate_filtered_journal(
            filtered
        )
        
    def show_all_journal_entries(self):
        self.load_journal_table()
    
    def populate_filtered_journal(
        self,
        rows
    ):
        self.journal_page.setRowCount(
            len(rows)
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
    
    def open_accounts_context_menu(self,position):
        selected_rows=self.accounts_page.selectionModel().selectedRows()
        if len(selected_rows)>1:
            menu=QMenu(self)
            current_filter=getattr(
                self,
                "accounts_filter",
                "all"
            )
            if current_filter=="all":
                QMessageBox.information(
                    self,
                    "Filter Required",
                    "Filter by Activated or Deactivated accounts before performing bulk actions."
                )
                return
            activate_action=None
            deactivate_action=None
            if current_filter=="active":
                deactivate_action=menu.addAction(
                    "Deactivate Selected Accounts"
                )
            elif current_filter=="inactive":
                activate_action=menu.addAction(
                    "Activate Selected Accounts"
                )
            delete_action=menu.addAction(
                "Delete Selected Accounts"
            )
            action=menu.exec_(
                self.accounts_page.viewport().mapToGlobal(
                    position
                )
            )
            if action is None:
                return
            if action==activate_action:
                self.activate_selected_accounts()
            elif action==deactivate_action:
                self.deactivate_selected_accounts()
            elif action==delete_action:
                self.delete_selected_accounts()
                return
            return
        row=self.accounts_page.currentRow()
        if row<0:
            return
        account_id=int(
            self.accounts_page.item(
                row,
                0
            ).text()
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
        menu=QMenu(self)
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
        if action is None:
            return
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
        selected_rows=self.journal_page.selectionModel().selectedRows()
        if len(selected_rows)>1:
            menu=QMenu()
            delete_action=menu.addAction(
                "Delete Selected Journal Entries"
            )
            action=menu.exec_(
                self.journal_page.viewport().mapToGlobal(
                    position
                )
            )
            if action==delete_action:
                self.delete_selected_journal_entries()
            return
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
        date_obj=QDate.fromString(
            str(entry["entry_date"]),
            "yyyy-MM-dd"
        )    
        dialog.entry_year.setCurrentText(
            str(date_obj.year())
        )       
        dialog.entry_month.setCurrentIndex(
            date_obj.month()-1
        )
        dialog.update_day_dropdown()
        dialog.entry_day.setCurrentText(
            str(date_obj.day())
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
            transaction_type_dropdown=QComboBox()
            transaction_type_dropdown.addItems([
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
                "Custom"
            ])
            description_value=str(
                line["description"]
            )
            transaction_index=transaction_type_dropdown.findText(
                description_value
            )
            if transaction_index>=0:
                transaction_type_dropdown.setCurrentIndex(
                    transaction_index
                )
            else:
                transaction_type_dropdown.addItem(
                    description_value
                )
                transaction_type_dropdown.setCurrentText(
                    description_value
                )
            dialog.lines_table.setCellWidget(
                row_index,
                1,
                transaction_type_dropdown
            )
            entry_type_dropdown=QComboBox()
            entry_type_dropdown.addItems([
                "Debit",
                "Credit"
            ])
            if float(line["debit"])>0:
                entry_type_dropdown.setCurrentText(
                    "Debit"
                )
                amount=float(
                    line["debit"]
                )
            else:
                entry_type_dropdown.setCurrentText(
                    "Credit"
                )
                amount=float(
                    line["credit"]
                )
            dialog.lines_table.setCellWidget(
                row_index,
                2,
                entry_type_dropdown
            )
            amount_item=QTableWidgetItem(
                str(amount)
            )
            if entry_type_dropdown.currentText()=="Debit":
                amount_item.setForeground(
                    Qt.red
                )
            else:
                amount_item.setForeground(
                    Qt.darkGreen
                )
            dialog.lines_table.setItem(
                row_index,
                3,
                amount_item
            )
            dialog.lines_table.setItem(
                row_index,
                4,
                QTableWidgetItem("")
            )
            attach_btn=QPushButton(
                "Attach"
            )
            attach_btn.clicked.connect(
                dialog.attachment_placeholder
            )
            dialog.lines_table.setCellWidget(
                row_index,
                5,
                attach_btn
            )
            remove_btn=QPushButton("X")
            remove_btn.clicked.connect(
                lambda _,r=row_index:
                dialog.remove_line(r)
            )
            dialog.lines_table.setCellWidget(
                row_index,
                6,
                remove_btn
            )
        result=dialog.exec_()
        if not result:
            return
        try:
            updated_lines=[]
            total_debit=0
            total_credit=0
            for row in range(
                dialog.lines_table.rowCount()
            ):
                account_widget=dialog.lines_table.cellWidget(
                    row,
                    0
                )
                transaction_type_widget=dialog.lines_table.cellWidget(
                    row,
                    1
                )
                entry_type_widget=dialog.lines_table.cellWidget(
                    row,
                    2
                )
                amount_item=dialog.lines_table.item(
                    row,
                    3
                )
                if not account_widget:
                    continue
                transaction_type=(
                    transaction_type_widget.currentText()
                    if transaction_type_widget
                    else ""
                )
                entry_type=(
                    entry_type_widget.currentText()
                    if entry_type_widget
                    else "Debit"
                )
                try:
                    amount=float(
                        amount_item.text()
                    ) if amount_item and amount_item.text() else 0
                except Exception:
                    amount=0
                debit=amount if entry_type=="Debit" else 0
                credit=amount if entry_type=="Credit" else 0
                total_debit+=debit
                total_credit+=credit
                updated_lines.append({
                    "account_id":
                    account_widget.currentData(),
                    "description":
                    transaction_type,
                    "debit":
                    debit,
                    "credit":
                    credit
                })
            if round(total_debit,2)!=round(total_credit,2):
                raise ValueError(
                    "Journal entry is not balanced."
                )
            self.journal.update_journal_entry(
                journal_entry_id,
                dialog.get_selected_date().toString(
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
            table.setRowCount(0)
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
            total_debit=0
            total_credit=0
            for row in range(
                dialog.lines_table.rowCount()
            ):
                account_widget=dialog.lines_table.cellWidget(
                    row,
                    0
                )
                transaction_type_widget=dialog.lines_table.cellWidget(
                    row,
                    1
                )
                entry_type_widget=dialog.lines_table.cellWidget(
                    row,
                    2
                )
                amount_item=dialog.lines_table.item(
                    row,
                    3
                )
                if not account_widget:
                    continue
                transaction_type=(
                    transaction_type_widget.currentText()
                    if transaction_type_widget
                    else ""
                )
                entry_type=(
                    entry_type_widget.currentText()
                    if entry_type_widget
                    else "Debit"
                )
                try:
                    amount=float(
                        amount_item.text()
                    ) if amount_item and amount_item.text() else 0
                except Exception:
                    amount=0
                debit=amount if entry_type=="Debit" else 0
                credit=amount if entry_type=="Credit" else 0
                total_debit+=debit
                total_credit+=credit
                lines.append({
                    "account_id":
                    account_widget.currentData(),
                    "description":
                    transaction_type,
                    "debit":
                    debit,
                    "credit":
                    credit
                })
            if not entry_number:
                entry_number=self.transactions.generate_entry_number()
            entry_date=dialog.get_selected_date().toString(
                "yyyy-MM-dd"
            )
            if round(total_debit,2)!=round(total_credit,2):
                raise ValueError(
                    "Journal entry is not balanced."
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
            QAbstractItemView.ExtendedSelection
        )
        table.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )
        table.setAlternatingRowColors(
            True
        )
        table.setStyleSheet("""
        QTableView::item:selected{
            background:#1e88e5;
            color:white;
        }
        QTableView::item:selected:!active{
            background:#1e88e5;
            color:white;
        }
        """)
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
            self.set_navigation_status(text.title())
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
        try:
            self.db.close()
        except Exception:
            pass
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