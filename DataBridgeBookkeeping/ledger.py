class LedgerManager:
    def __init__(self,db):
        self.db=db

    def get_account_ledger(
        self,
        account_id
    ):
        rows=self.db.fetchall("""
        SELECT
            je.entry_date,
            je.entry_number,
            je.reference,
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
        WHERE jl.account_id=?
        ORDER BY je.entry_date ASC,
        je.id ASC
        """,(account_id,))
        balance=0
        ledger=[]
        for row in rows:
            balance+=(
                float(row["debit"])-
                float(row["credit"])
            )
            item=dict(row)
            item["running_balance"]=balance
            ledger.append(item)
        return ledger

    def get_account_balance(
        self,
        account_id
    ):
        row=self.db.fetchone("""
        SELECT
            COALESCE(SUM(debit),0) as total_debit,
            COALESCE(SUM(credit),0) as total_credit
        FROM journal_lines
        WHERE account_id=?
        """,(account_id,))
        return(
            float(row["total_debit"])-
            float(row["total_credit"])
        )
    
    def get_account_balance_by_date(
        self,
        account_id,
        start_date,
        end_date
    ):
        row=self.db.fetchone("""
        SELECT
            COALESCE(
                SUM(debit),
                0
            ) as total_debit,
            COALESCE(
                SUM(credit),
                0
            ) as total_credit
        FROM journal_lines jl
        JOIN journal_entries je
        ON jl.journal_entry_id=je.id
        WHERE
            jl.account_id=?
            AND je.entry_date
            BETWEEN ? AND ?
        """,(
            account_id,
            start_date,
            end_date
        ))
        return(
            float(row["total_debit"])-
            float(row["total_credit"])
        )

    def get_all_balances(self):
        return self.db.fetchall("""
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

    def get_cashbook(self):
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
        WHERE a.account_name LIKE '%Cash%'
        OR a.account_name LIKE '%Bank%'
        ORDER BY je.entry_date ASC
        """)

    def get_transactions_by_date(
        self,
        start_date,
        end_date
    ):
        return self.db.fetchall("""
        SELECT
            je.entry_date,
            je.entry_number,
            je.reference,
            jl.description,
            jl.debit,
            jl.credit,
            a.account_code,
            a.account_name
        FROM journal_lines jl
        JOIN journal_entries je
        ON jl.journal_entry_id=je.id
        JOIN accounts a
        ON jl.account_id=a.id
        WHERE je.entry_date
        BETWEEN ? AND ?
        ORDER BY je.entry_date ASC
        """,(start_date,end_date))
        
    def format_ledger_rows(
        self,
        rows
    ):
        formatted=[]
        for row in rows:
            formatted.append({
                "Date":
                row["entry_date"],
                "Entry":
                row["entry_number"],
                "Reference":
                row.get(
                    "reference",
                    ""
                ),
                "Account":
                f"{row['account_code']} - "
                f"{row['account_name']}",
                "Description":
                row["description"],
                "Debit":
                float(row["debit"]),
                "Credit":
                float(row["credit"])
            })
        return formatted