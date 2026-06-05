from datetime import datetime

class JournalManager:
    def __init__(self, db):
        self.db = db

    def create_journal_entry(
        self,
        entry_number,
        entry_date,
        reference,
        description,
        lines
    ):
        if not lines:
            raise ValueError(
                "Journal entry requires at least one line"
            )
        total_debit = 0
        total_credit = 0
        for line in lines:
            account_id = line.get("account_id")
            debit = float(line.get("debit", 0))
            credit = float(line.get("credit", 0))
            if not account_id:
                raise ValueError(
                    "Account is required"
                )
            if debit > 0 and credit > 0:
                raise ValueError(
                    "Line cannot contain both debit and credit"
                )
            if debit == 0 and credit == 0:
                raise ValueError(
                    "Line amount cannot be zero"
                )
            total_debit += debit
            total_credit += credit
        if total_debit <= 0:
            raise ValueError(
                "Journal entry amount must be greater than zero"
            )
        if round(total_debit, 2) != round(total_credit, 2):
            raise ValueError(
                "Journal entry is not balanced"
            )
        self.db.begin_transaction()
        try:
            cursor = self.db.execute("""
            INSERT INTO journal_entries(
                entry_number,
                entry_date,
                reference,
                description,
                total_debit,
                total_credit,
                created_at
            )
            VALUES(?,?,?,?,?,?,?)
            """, (
                entry_number,
                entry_date,
                reference,
                description,
                total_debit,
                total_credit,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            ))
            journal_entry_id = cursor.lastrowid
            for line in lines:
                self.db.execute("""
                INSERT INTO journal_lines(
                    journal_entry_id,
                    account_id,
                    description,
                    debit,
                    credit
                )
                VALUES(?,?,?,?,?)
                """, (
                    journal_entry_id,
                    line["account_id"],
                    line["description"],
                    line["debit"],
                    line["credit"]
                ))
            self.db.log_action(
                "CREATE",
                "journal_entries",
                journal_entry_id,
                f"Created journal entry {entry_number}"
            )
            self.db.commit_transaction()
            return journal_entry_id
        except Exception:
            self.db.rollback_transaction()
            raise

    def update_journal_entry(
        self,
        journal_entry_id,
        entry_date,
        reference,
        description,
        lines
    ):
        existing = self.get_journal_entry_by_id(
            journal_entry_id
        )
        if not existing:
            raise ValueError(
                "Journal entry not found"
            )
        if not lines:
            raise ValueError(
                "Journal entry requires at least one line"
            )
        total_debit = 0
        total_credit = 0
        for line in lines:
            account_id = line.get("account_id")
            debit = float(line.get("debit", 0))
            credit = float(line.get("credit", 0))
            if not account_id:
                raise ValueError(
                    "Account is required"
                )
            if debit > 0 and credit > 0:
                raise ValueError(
                    "Line cannot contain both debit and credit"
                )
            if debit == 0 and credit == 0:
                raise ValueError(
                    "Line amount cannot be zero"
                )
            total_debit += debit
            total_credit += credit
        if total_debit <= 0:
            raise ValueError(
                "Journal entry amount must be greater than zero"
            )
        if round(total_debit, 2) != round(total_credit, 2):
            raise ValueError(
                "Journal entry is not balanced"
            )
        self.db.begin_transaction()
        try:
            self.db.execute("""
            UPDATE journal_entries
            SET
                entry_date=?,
                reference=?,
                description=?,
                total_debit=?,
                total_credit=?
            WHERE id=?
            """, (
                entry_date,
                reference,
                description,
                total_debit,
                total_credit,
                journal_entry_id
            ))
            self.db.execute("""
            DELETE FROM journal_lines
            WHERE journal_entry_id=?
            """, (
                journal_entry_id,
            ))
            for line in lines:
                self.db.execute("""
                INSERT INTO journal_lines(
                    journal_entry_id,
                    account_id,
                    description,
                    debit,
                    credit
                )
                VALUES(?,?,?,?,?)
                """, (
                    journal_entry_id,
                    line["account_id"],
                    line["description"],
                    line["debit"],
                    line["credit"]
                ))
            self.db.log_action(
                "UPDATE",
                "journal_entries",
                journal_entry_id,
                f"Updated journal entry {journal_entry_id}"
            )
            self.db.commit_transaction()
        except Exception:
            self.db.rollback_transaction()
            raise

    def get_all_journal_entries(self):
        return self.db.fetchall("""
        SELECT
            id,
            entry_number,
            entry_date,
            reference,
            description,
            total_debit,
            total_credit
        FROM journal_entries
        ORDER BY
            entry_date DESC,
            id DESC
        """)

    def get_journal_entry_by_id(
        self,
        journal_entry_id
    ):
        return self.db.fetchone("""
        SELECT *
        FROM journal_entries
        WHERE id=?
        """, (
            journal_entry_id,
        ))

    def get_journal_entry_lines(
        self,
        journal_entry_id
    ):
        return self.db.fetchall("""
        SELECT
            jl.id,
            jl.description,
            jl.debit,
            jl.credit,
            a.account_code,
            a.account_name,
            a.id as account_id
        FROM journal_lines jl
        JOIN accounts a
        ON jl.account_id=a.id
        WHERE jl.journal_entry_id=?
        ORDER BY jl.id
        """, (
            journal_entry_id,
        ))

    def delete_journal_entry(
        self,
        journal_entry_id
    ):
        existing = self.get_journal_entry_by_id(
            journal_entry_id
        )
        if not existing:
            raise ValueError(
                "Journal entry not found"
            )
        self.db.begin_transaction()
        try:
            self.db.execute("""
            DELETE FROM journal_lines
            WHERE journal_entry_id=?
            """, (
                journal_entry_id,
            ))
            self.db.execute("""
            DELETE FROM journal_entries
            WHERE id=?
            """, (
                journal_entry_id,
            ))
            self.db.log_action(
                "DELETE",
                "journal_entries",
                journal_entry_id,
                f"Deleted journal entry {journal_entry_id}"
            )
            self.db.commit_transaction()
        except Exception:
            self.db.rollback_transaction()
            raise

    def search_journal_entries(
        self,
        keyword
    ):
        keyword = f"%{keyword}%"
        return self.db.fetchall("""
        SELECT
            id,
            entry_number,
            entry_date,
            reference,
            description,
            total_debit,
            total_credit
        FROM journal_entries
        WHERE
            entry_number LIKE ?
            OR entry_date LIKE ?
            OR reference LIKE ?
            OR description LIKE ?
        ORDER BY
            entry_date DESC,
            id DESC
        """, (
            keyword,
            keyword,
            keyword,
            keyword
        ))