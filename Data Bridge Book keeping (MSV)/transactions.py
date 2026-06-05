from datetime import datetime

class TransactionManager:
    def __init__(self,journal_manager):
        self.journal_manager=journal_manager

    def generate_entry_number(self):
        timestamp=datetime.now().strftime(
            "%Y%m%d%H%M%S%f"
        )
        return f"JE-{timestamp}"

    def post_transaction(
        self,
        entry_number,
        entry_date,
        reference,
        description,
        debit_account_id,
        credit_account_id,
        amount
    ):
        if amount is None or amount<=0:
            raise ValueError(
                "Transaction amount must be greater than zero."
            )    
        if debit_account_id is None:
            raise ValueError(
                "Debit account is required."
            )
        if credit_account_id is None:
            raise ValueError(
                "Credit account is required."
            )
        if debit_account_id==credit_account_id:
            raise ValueError(
                "Debit and credit accounts cannot be the same."
            )
        if not entry_number:
            raise ValueError(
                "Entry number is required."
            )
        if not entry_date:
            raise ValueError(
                "Entry date is required."
            )
        lines=[
            {
                "account_id":
                debit_account_id,
                "description":
                description,
                "debit":
                amount,
                "credit":
                0
            },
            {
                "account_id":
                credit_account_id,
                "description":
                description,
                "debit":
                0,
                "credit":
                amount
            }
        ]
        return self.journal_manager.create_journal_entry(
            entry_number,
            entry_date,
            reference,
            description,
            lines
        )

    def post_bulk_transactions(
        self,
        transactions
    ):
        results=[]
        if not transactions:
            return results
        for transaction in transactions:
            required_fields=[
                "entry_number",
                "entry_date",
                "reference",
                "description",
                "debit_account_id",
                "credit_account_id",
                "amount"
            ]        
            for field in required_fields:
                if field not in transaction:
                    raise ValueError(
                        f"Missing required field: {field}"
                    )
            result=self.post_transaction(
                transaction["entry_number"],
                transaction["entry_date"],
                transaction["reference"],
                transaction["description"],
                transaction["debit_account_id"],
                transaction["credit_account_id"],
                transaction["amount"]
            )
            results.append(result)
        return results

    def quick_cash_sale(
        self,
        cash_account_id,
        revenue_account_id,
        amount
    ):
        if amount<=0:
            raise ValueError(
                "Amount must be greater than zero."
            )
        return self.post_transaction(
            self.generate_entry_number(),
            datetime.now().strftime(
                "%Y-%m-%d"
            ),
            "CASHSALE",
            "Cash Sale",
            cash_account_id,
            revenue_account_id,
            amount
        )

    def quick_expense(
        self,
        expense_account_id,
        cash_account_id,
        amount
    ):
        if amount<=0:
            raise ValueError(
                "Amount must be greater than zero."
            )
        return self.post_transaction(
            self.generate_entry_number(),
            datetime.now().strftime(
                "%Y-%m-%d"
            ),
            "EXPENSE",
            "Expense Payment",
            expense_account_id,
            cash_account_id,
            amount
        )

    def quick_bank_deposit(
        self,
        bank_account_id,
        cash_account_id,
        amount
    ):
        if amount<=0:
            raise ValueError(
                "Amount must be greater than zero."
            )
        return self.post_transaction(
            self.generate_entry_number(),
            datetime.now().strftime(
                "%Y-%m-%d"
            ),
            "BANKDEP",
            "Bank Deposit",
            bank_account_id,
            cash_account_id,
            amount
        )