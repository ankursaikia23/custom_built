from datetime import datetime

class TransactionValidator:
    VALID_ACCOUNT_TYPES={
        "Asset",
        "Liability",
        "Equity",
        "Revenue",
        "Expense"
    }

    @staticmethod
    def validate_journal_lines(lines):
        if not lines:
            return False
        total_debit=0
        total_credit=0
        try:
            for line in lines:
                debit=float(
                    line.get(
                        "debit",
                        0
                    )
                )
                credit=float(
                    line.get(
                        "credit",
                        0
                    )
                )
                if debit<0 or credit<0:
                    return False
                if debit>0 and credit>0:
                    return False
                if debit==0 and credit==0:
                    return False
                account_id=line.get(
                    "account_id"
                )
                if not account_id:
                    return False
                total_debit+=debit
                total_credit+=credit
            return round(
                total_debit,
                2
            )==round(
                total_credit,
                2
            )
        except (
            TypeError,
            ValueError,
            AttributeError
        ):
            return False

    @staticmethod
    def validate_amount(amount):
        try:
            amount=float(amount)
            return amount>0
        except (
            TypeError,
            ValueError
        ):
            return False

    @staticmethod
    def validate_account_code(account_code):
        account_code=str(
            account_code
        ).strip()
        if not account_code:
            return False
        return len(
            account_code
        )<=20

    @staticmethod
    def validate_account_name(account_name):
        account_name=str(
            account_name
        ).strip()
        if not account_name:
            return False
        return len(
            account_name
        )<=100

    @staticmethod
    def validate_account_type(account_type):
        if not account_type:
            return False
        return (
            account_type.strip()
            in
            TransactionValidator.VALID_ACCOUNT_TYPES
        )

    @staticmethod
    def validate_date(date_text):
        try:
            datetime.strptime(
                str(date_text),
                "%Y-%m-%d"
            )
            return True
        except (
            TypeError,
            ValueError
        ):
            return False

    @staticmethod
    def validate_reference(reference):
        return len(
            str(reference).strip()
        )<=100

    @staticmethod
    def validate_journal_entry(
        entry_number,
        entry_date,
        lines
    ):
        if not str(
            entry_number
        ).strip():
            return False
        if not TransactionValidator.validate_date(
            entry_date
        ):
            return False
        if not lines:
            return False
        return TransactionValidator.validate_journal_lines(
            lines
        )