class DashboardManager:
    def __init__(self,db):
        self.db=db

    def get_dashboard_summary(self):
        accounts=self.db.fetchone("""
        SELECT COUNT(*) as total
        FROM accounts
        """)
        journal_entries=self.db.fetchone("""
        SELECT COUNT(*) as total
        FROM journal_entries
        """)
        total_debits=self.db.fetchone("""
        SELECT
            COALESCE(SUM(debit),0)
            as total
        FROM journal_lines
        """)
        total_credits=self.db.fetchone("""
        SELECT
            COALESCE(SUM(credit),0)
            as total
        FROM journal_lines
        """)
        customers=self.db.fetchone("""
        SELECT COUNT(*) as total
        FROM customers
        """)
        vendors=self.db.fetchone("""
        SELECT COUNT(*) as total
        FROM vendors
        """)
        invoices=self.db.fetchone("""
        SELECT COUNT(*) as total
        FROM invoices
        """)
        return{
            "total_accounts":
            int(accounts["total"] or 0),
            "total_journal_entries":
            int(journal_entries["total"] or 0),
            "total_debits":
            float(total_debits["total"] or 0),
            "total_credits":
            float(total_credits["total"] or 0),
            "total_customers":
            int(customers["total"] or 0),
            "total_vendors":
            int(vendors["total"] or 0),
            "total_invoices":
            int(invoices["total"] or 0)
        }

    def get_financial_overview(self):
        income=self.db.fetchone("""
        SELECT
            COALESCE(
                SUM(jl.credit-jl.debit),
                0
            ) as total
        FROM journal_lines jl
        JOIN accounts a
        ON jl.account_id=a.id
        WHERE a.account_type='Revenue'
        """)
        expenses=self.db.fetchone("""
        SELECT
            COALESCE(
                SUM(jl.debit-jl.credit),
                0
            ) as total
        FROM journal_lines jl
        JOIN accounts a
        ON jl.account_id=a.id
        WHERE a.account_type='Expense'
        """)
        assets=self.db.fetchone("""
        SELECT
            COALESCE(
                SUM(jl.debit-jl.credit),
                0
            ) as total
        FROM journal_lines jl
        JOIN accounts a
        ON jl.account_id=a.id
        WHERE a.account_type='Asset'
        """)
        liabilities=self.db.fetchone("""
        SELECT
            COALESCE(
                SUM(jl.credit-jl.debit),
                0
            ) as total
        FROM journal_lines jl
        JOIN accounts a
        ON jl.account_id=a.id
        WHERE a.account_type='Liability'
        """)
        equity=self.db.fetchone("""
        SELECT
            COALESCE(
                SUM(jl.credit-jl.debit),
                0
            ) as total
        FROM journal_lines jl
        JOIN accounts a
        ON jl.account_id=a.id
        WHERE a.account_type='Equity'
        """)
        income_total=float(
            income["total"] or 0
        )
        expense_total=float(
            expenses["total"] or 0
        )
        return{
            "income":
            income_total,
            "expenses":
            expense_total,
            "net_profit":
            income_total-
            expense_total,
            "assets":
            float(
                assets["total"] or 0
            ),
            "liabilities":
            float(
                liabilities["total"] or 0
            ),
            "equity":
            float(
                equity["total"] or 0
            )
        }

    def get_recent_journal_entries(
        self,
        limit=10
    ):
        try:
            limit=max(
                1,
                int(limit)
            )
        except(
            TypeError,
            ValueError
        ):
            limit=10
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
        LIMIT ?
        """,(limit,))

    def get_recent_audit_logs(
        self,
        limit=20
    ):
        try:
            limit=max(
                1,
                int(limit)
            )
        except(
            TypeError,
            ValueError
        ):
            limit=20
        return self.db.fetchall("""
        SELECT
            action_type,
            table_name,
            message,
            created_at
        FROM audit_logs
        ORDER BY id DESC
        LIMIT ?
        """,(limit,))

    def get_recent_activity(
        self,
        limit=15
    ):
        try:
            limit=max(
                1,
                int(limit)
            )
        except(
            TypeError,
            ValueError
        ):
            limit=15
        return self.db.fetchall("""
        SELECT
            action_type,
            table_name,
            message,
            created_at
        FROM audit_logs
        ORDER BY id DESC
        LIMIT ?
        """,(limit,))