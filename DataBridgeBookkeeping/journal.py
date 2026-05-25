from datetime import datetime

class JournalManager:
    def __init__(self,db):
        self.db=db

    def create_journal_entry(
        self,
        entry_number,
        entry_date,
        reference,
        description,
        lines
    ):
        total_debit=0
        total_credit=0
        for line in lines:
            total_debit+=float(line["debit"])
            total_credit+=float(line["credit"])
        if round(total_debit,2)!=round(total_credit,2):
            raise ValueError(
                "Journal entry is not balanced"
            )
        cursor=self.db.execute("""
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
        """,(
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
        journal_entry_id=cursor.lastrowid
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
            """,(
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
        return journal_entry_id

    def update_journal_entry(
        self,
        journal_entry_id,
        entry_date,
        reference,
        description,
        lines
    ):
        total_debit=0
        total_credit=0
        for line in lines:
            total_debit+=float(line["debit"])
            total_credit+=float(line["credit"])
        if round(total_debit,2)!=round(total_credit,2):
            raise ValueError(
                "Journal entry is not balanced"
            )
        self.db.execute("""
        UPDATE journal_entries
        SET
            entry_date=?,
            reference=?,
            description=?,
            total_debit=?,
            total_credit=?
        WHERE id=?
        """,(
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
        """,(journal_entry_id,))
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
            """,(
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
            "Updated journal entry"
        )

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
        ORDER BY entry_date DESC,
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
        """,(journal_entry_id,))

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
        """,(journal_entry_id,))

    def delete_journal_entry(
        self,
        journal_entry_id
    ):
        self.db.execute("""
        DELETE FROM journal_lines
        WHERE journal_entry_id=?
        """,(journal_entry_id,))
        self.db.execute("""
        DELETE FROM journal_entries
        WHERE id=?
        """,(journal_entry_id,))
        self.db.log_action(
            "DELETE",
            "journal_entries",
            journal_entry_id,
            "Deleted journal entry"
        )

    def search_journal_entries(
        self,
        keyword
    ):
        keyword=f"%{keyword}%"
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
            OR reference LIKE ?
            OR description LIKE ?
        ORDER BY entry_date DESC
        """,(
            keyword,
            keyword,
            keyword
        ))