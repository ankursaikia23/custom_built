from datetime import datetime

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
        account_code=str(
            account_code
        ).strip()
        if not account_code:
            return False
        return len(account_code)<=20

    @staticmethod
    def validate_account_name(account_name):
        account_name=str(
            account_name
        ).strip()
        if not account_name:
            return False
        return len(account_name)<=100

    @staticmethod
    def validate_account_type(account_type):
        if not account_type:
            return False
        return len(account_type.strip())>0

    @staticmethod
    def validate_date(date_text):
        try:
            datetime.strptime(
                str(date_text),
                "%Y-%m-%d"
            )
            return True
        except:
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
        if not str(entry_number).strip():
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