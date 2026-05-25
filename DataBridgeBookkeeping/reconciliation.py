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
        WHERE ROUND(total_debit,2)!=ROUND(total_credit,2)
        """)

    def verify_journal_integrity(self):
        invalid_entries=[]
        rows=self.db.fetchall("""
        SELECT
            id,
            entry_number,
            total_debit,
            total_credit
        FROM journal_entries
        """)
        for row in rows:
            if round(
                float(row["total_debit"]),
                2
            )!=round(
                float(row["total_credit"]),
                2
            ):
                invalid_entries.append(
                    dict(row)
                )
        return invalid_entries

    def find_duplicate_transactions(self):
        return self.db.fetchall("""
        SELECT
            reference,
            entry_date,
            total_debit,
            COUNT(*) as duplicate_count
        FROM journal_entries
        GROUP BY
            reference,
            entry_date,
            total_debit
        HAVING COUNT(*)>1
        """)

    def verify_account_balances(self):
        rows=self.db.fetchall("""
        SELECT
            a.account_code,
            a.account_name,
            COALESCE(SUM(jl.debit),0) as total_debit,
            COALESCE(SUM(jl.credit),0) as total_credit
        FROM accounts a
        LEFT JOIN journal_lines jl
        ON a.id=jl.account_id
        GROUP BY a.id
        """)
        results=[]
        for row in rows:
            results.append({
                "account_code":row["account_code"],
                "account_name":row["account_name"],
                "balance":float(
                    row["total_debit"]
                )-float(
                    row["total_credit"]
                )
            })
        return results