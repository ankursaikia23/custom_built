import os
import sqlite3
import json
from datetime import datetime

class DatabaseManager:
    def __init__(self,db_path="database/bookkeeping.db"):
        self.db_path=db_path
        self.conn=None
        self.connect()
        self.enable_foreign_keys()
        self.create_tables()

    def connect(self):
        os.makedirs(
            os.path.dirname(self.db_path),
            exist_ok=True
        )
        self.conn=sqlite3.connect(
            self.db_path
        )
        self.conn.row_factory=sqlite3.Row

    def enable_foreign_keys(self):
        self.conn.execute(
            "PRAGMA foreign_keys=ON"
        )

    def execute(
        self,
        query,
        params=()
    ):
        cursor=self.conn.cursor()
        cursor.execute(
            query,
            params
        )
        self.conn.commit()
        return cursor

    def executemany(
        self,
        query,
        rows
    ):
        cursor=self.conn.cursor()
        cursor.executemany(
            query,
            rows
        )
        self.conn.commit()
        return cursor

    def fetchone(
        self,
        query,
        params=()
    ):
        cursor=self.conn.cursor()
        cursor.execute(
            query,
            params
        )
        return cursor.fetchone()

    def fetchall(
        self,
        query,
        params=()
    ):
        cursor=self.conn.cursor()
        cursor.execute(
            query,
            params
        )
        return cursor.fetchall()

    def begin_transaction(self):
        self.conn.execute(
            "BEGIN"
        )

    def commit_transaction(self):
        self.conn.commit()

    def rollback_transaction(self):
        self.conn.rollback()

    def database_exists(self):
        return os.path.exists(
            self.db_path
        )

    def vacuum_database(self):
        self.execute(
            "VACUUM"
        )

    def export_database_metadata(self):
        metadata={
            "database_path":self.db_path,
            "generated_at":datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        }
        return json.dumps(
            metadata,
            indent=4
        )

    def create_tables(self):
        self.execute("""
        CREATE TABLE IF NOT EXISTS accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_code TEXT UNIQUE NOT NULL,
            account_name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            parent_id INTEGER,
            is_active INTEGER DEFAULT 1,
            created_at TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_number TEXT UNIQUE NOT NULL,
            entry_date TEXT NOT NULL,
            reference TEXT,
            description TEXT,
            total_debit REAL DEFAULT 0,
            total_credit REAL DEFAULT 0,
            created_at TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS journal_lines(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            journal_entry_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            FOREIGN KEY(journal_entry_id)
            REFERENCES journal_entries(id)
            ON DELETE CASCADE,
            FOREIGN KEY(account_id)
            REFERENCES accounts(id)
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT,
            table_name TEXT,
            record_id TEXT,
            message TEXT,
            created_at TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS app_settings(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE,
            setting_value TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS saved_reports(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_name TEXT,
            report_type TEXT,
            filters TEXT,
            created_at TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS attachments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            related_table TEXT,
            related_id INTEGER,
            file_name TEXT,
            file_path TEXT,
            created_at TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS fiscal_periods(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_name TEXT,
            start_date TEXT,
            end_date TEXT,
            is_closed INTEGER DEFAULT 0
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS recurring_transactions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_name TEXT,
            frequency TEXT,
            next_run_date TEXT,
            transaction_data TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS bank_accounts(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_name TEXT,
            bank_name TEXT,
            account_number TEXT,
            opening_balance REAL DEFAULT 0,
            current_balance REAL DEFAULT 0,
            created_at TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS customers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_at TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS vendors(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT,
            phone TEXT,
            email TEXT,
            address TEXT,
            created_at TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS invoices(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE,
            customer_id INTEGER,
            invoice_date TEXT,
            due_date TEXT,
            subtotal REAL DEFAULT 0,
            tax_amount REAL DEFAULT 0,
            total_amount REAL DEFAULT 0,
            status TEXT,
            created_at TEXT
        )
        """)
        self.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER,
            item_description TEXT,
            quantity REAL DEFAULT 0,
            unit_price REAL DEFAULT 0,
            total_price REAL DEFAULT 0
        )
        """)

    def log_action(
        self,
        action_type,
        table_name,
        record_id,
        message
    ):
        self.execute("""
        INSERT INTO audit_logs(
            action_type,
            table_name,
            record_id,
            message,
            created_at
        )
        VALUES(?,?,?,?,?)
        """,(
            action_type,
            table_name,
            str(record_id),
            message,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

    def close(self):
        if self.conn:
            self.conn.close()