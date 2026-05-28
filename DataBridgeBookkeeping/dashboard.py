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
            accounts["total"],
            "total_journal_entries":
            journal_entries["total"],
            "total_debits":
            float(total_debits["total"]),
            "total_credits":
            float(total_credits["total"]),
            "total_customers":
            customers["total"],
            "total_vendors":
            vendors["total"],
            "total_invoices":
            invoices["total"]
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
        return{
            "income":
            float(income["total"]),
            "expenses":
            float(expenses["total"]),
            "net_profit":
            float(income["total"])-
            float(expenses["total"]),
            "assets":
            float(assets["total"])
        }

    def get_recent_journal_entries(
        self,
        limit=10
    ):
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
        ORDER BY id DESC
        LIMIT ?
        """,(limit,))

    def get_recent_audit_logs(
        self,
        limit=20
    ):
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