import pandas as pd

class ReportManager:
    def __init__(self,db):
        self.db=db
        
    def normalize_rows(
        self,
        rows
    ):
        normalized=[]
        for row in rows:
            normalized.append(
                dict(row)
            )
        return normalized

    def get_trial_balance(self):
        return self.db.fetchall("""
        SELECT
            a.account_code,
            a.account_name,
            a.account_type,
            COALESCE(SUM(jl.debit),0)
            as total_debit,
            COALESCE(SUM(jl.credit),0)
            as total_credit
        FROM accounts a
        LEFT JOIN journal_lines jl
        ON a.id=jl.account_id
        GROUP BY a.id
        ORDER BY a.account_code
        """)

    def get_profit_and_loss(self):
        return self.db.fetchall("""
        SELECT
            a.account_code,
            a.account_name,
            a.account_type,
            COALESCE(
                SUM(jl.credit-jl.debit),
                0
            ) as balance
        FROM accounts a
        LEFT JOIN journal_lines jl
        ON a.id=jl.account_id
        WHERE a.account_type IN(
            'Revenue',
            'Expense'
        )
        GROUP BY a.id
        ORDER BY a.account_code
        """)

    def get_balance_sheet(self):
        return self.db.fetchall("""
        SELECT
            a.account_code,
            a.account_name,
            a.account_type,
            COALESCE(
                SUM(jl.debit-jl.credit),
                0
            ) as balance
        FROM accounts a
        LEFT JOIN journal_lines jl
        ON a.id=jl.account_id
        WHERE a.account_type IN(
            'Asset',
            'Liability',
            'Equity'
        )
        GROUP BY a.id
        ORDER BY a.account_code
        """)

    def get_general_ledger(self):
        return self.db.fetchall("""
        SELECT
            je.entry_date,
            je.entry_number,
            a.account_code,
            a.account_name,
            jl.description,
            jl.debit,
            jl.credit
        FROM journal_lines jl
        JOIN journal_entries je
        ON jl.journal_entry_id=je.id
        JOIN accounts a
        ON jl.account_id=a.id
        ORDER BY je.entry_date ASC
        """)
        
    def get_general_ledger_by_date(
        self,
        start_date,
        end_date
    ):
        return self.db.fetchall("""
        SELECT
            je.entry_date,
            je.entry_number,
            a.account_code,
            a.account_name,
            jl.description,
            jl.debit,
            jl.credit
        FROM journal_lines jl
        JOIN journal_entries je
        ON jl.journal_entry_id=je.id
        JOIN accounts a
        ON jl.account_id=a.id
        WHERE je.entry_date
        BETWEEN ? AND ?
        ORDER BY je.entry_date ASC
        """,(
            start_date,
            end_date
        ))

    def get_cash_flow_summary(self):
        return self.db.fetchall("""
        SELECT
            a.account_code,
            a.account_name,
            COALESCE(
                SUM(jl.debit),
                0
            ) as cash_in,
            COALESCE(
                SUM(jl.credit),
                0
            ) as cash_out
        FROM journal_lines jl
        JOIN accounts a
        ON jl.account_id=a.id
        WHERE
            a.account_name LIKE '%Cash%'
            OR a.account_name LIKE '%Bank%'
        GROUP BY a.id
        ORDER BY a.account_code
        """)

    def get_account_summary(self):
        return self.db.fetchall("""
        SELECT
            a.account_code,
            a.account_name,
            a.account_type,
            COUNT(jl.id) as transaction_count,
            COALESCE(SUM(jl.debit),0)
            as total_debit,
            COALESCE(SUM(jl.credit),0)
            as total_credit
        FROM accounts a
        LEFT JOIN journal_lines jl
        ON a.id=jl.account_id
        GROUP BY a.id
        ORDER BY a.account_code
        """)

    def get_account_balances(self):
        rows=self.db.fetchall("""
        SELECT
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
        balances=[]
        for row in rows:
            balances.append({
                "account_code":
                row["account_code"],
                "account_name":
                row["account_name"],
                "account_type":
                row["account_type"],
                "balance":
                float(row["total_debit"])-
                float(row["total_credit"])
            })
        return balances

    def get_audit_logs(self):
        return self.db.fetchall("""
        SELECT
            id,
            action_type,
            table_name,
            record_id,
            message,
            created_at
        FROM audit_logs
        ORDER BY id DESC
        """)

    def rows_to_dataframe(
        self,
        rows
    ):
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(
            self.normalize_rows(rows)
        )