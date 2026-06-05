class ReconciliationEngine:
    def __init__(self,db):
        self.db=db

    def get_unbalanced_entries(self):
        return self.db.fetchall("""
        SELECT
            id,
            entry_number,
            total_debit,
            total_credit
        FROM journal_entries
        WHERE ROUND(
            COALESCE(total_debit,0),
            2
        )!=ROUND(
            COALESCE(total_credit,0),
            2
        )
        ORDER BY id
        """)

    def verify_journal_integrity(self):
        invalid_entries=[]
        rows=self.db.fetchall("""
        SELECT
            je.id,
            je.entry_number,
            je.total_debit,
            je.total_credit,
            COALESCE(
                SUM(jl.debit),
                0
            ) as calculated_debit,
            COALESCE(
                SUM(jl.credit),
                0
            ) as calculated_credit
        FROM journal_entries je
        LEFT JOIN journal_lines jl
        ON je.id=jl.journal_entry_id
        GROUP BY je.id
        """)
        for row in rows:
            stored_debit=round(
                float(row["total_debit"] or 0),
                2
            )
            stored_credit=round(
                float(row["total_credit"] or 0),
                2
            )
            calculated_debit=round(
                float(row["calculated_debit"] or 0),
                2
            )
            calculated_credit=round(
                float(row["calculated_credit"] or 0),
                2
            )
            if (
                stored_debit!=stored_credit
                or
                stored_debit!=calculated_debit
                or
                stored_credit!=calculated_credit
            ):
                invalid_entries.append({
                    "id":
                    row["id"],
                    "entry_number":
                    row["entry_number"],
                    "stored_debit":
                    stored_debit,
                    "stored_credit":
                    stored_credit,
                    "calculated_debit":
                    calculated_debit,
                    "calculated_credit":
                    calculated_credit
                })
        return invalid_entries

    def find_duplicate_transactions(self):
        return self.db.fetchall("""
        SELECT
            reference,
            entry_date,
            total_debit,
            COUNT(*) as duplicate_count
        FROM journal_entries
        WHERE
            reference IS NOT NULL
            AND TRIM(reference)<>''
        GROUP BY
            reference,
            entry_date,
            total_debit
        HAVING COUNT(*)>1
        ORDER BY duplicate_count DESC
        """)

    def verify_account_balances(self):
        rows=self.db.fetchall("""
        SELECT
            a.id,
            a.account_code,
            a.account_name,
            a.account_type,
            COALESCE(
                SUM(jl.debit),
                0
            ) as total_debit,
            COALESCE(
                SUM(jl.credit),
                0
            ) as total_credit
        FROM accounts a
        LEFT JOIN journal_lines jl
        ON a.id=jl.account_id
        GROUP BY a.id
        ORDER BY a.account_code
        """)
        results=[]
        for row in rows:
            results.append({
                "account_id":
                row["id"],
                "account_code":
                row["account_code"],
                "account_name":
                row["account_name"],
                "account_type":
                row["account_type"],
                "total_debit":
                float(row["total_debit"] or 0),
                "total_credit":
                float(row["total_credit"] or 0),
                "balance":
                float(row["total_debit"] or 0)-
                float(row["total_credit"] or 0)
            })
        return results