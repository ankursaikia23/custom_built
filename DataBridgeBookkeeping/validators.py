class TransactionValidator:
    @staticmethod
    def validate_journal_lines(lines):
        total_debit=0
        total_credit=0
        for line in lines:
            total_debit+=float(line["debit"])
            total_credit+=float(line["credit"])
        return round(
            total_debit,
            2
        )==round(
            total_credit,
            2
        )

    @staticmethod
    def validate_amount(amount):
        try:
            amount=float(amount)
            return amount>0
        except:
            return False

    @staticmethod
    def validate_account_code(account_code):
        return bool(
            str(account_code).strip()
        )

    @staticmethod
    def validate_account_name(account_name):
        return bool(
            str(account_name).strip()
        )

    @staticmethod
    def validate_account_type(account_type):
        valid_types=[
            "Asset",
            "Liability",
            "Equity",
            "Revenue",
            "Expense"
        ]
        return account_type in valid_types

    @staticmethod
    def validate_date(date_text):
        parts=str(date_text).split("-")
        if len(parts)!=3:
            return False
        return True

    @staticmethod
    def validate_reference(reference):
        return len(
            str(reference).strip()
        )<=100