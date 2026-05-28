from datetime import datetime

def format_currency(amount):
    return f"{float(amount):,.2f}"

def format_date(date_value):
    if not date_value:
        return ""
    if isinstance(
        date_value,
        datetime
    ):
        return date_value.strftime(
            "%Y-%m-%d"
        )
    return str(date_value)

def safe_float(
    value,
    default=0.0
):
    try:
        return float(value)
    except Exception:
        return default

def safe_int(
    value,
    default=0
):
    try:
        return int(value)
    except Exception:
        return default

def generate_timestamp():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

def normalize_text(text):
    return str(text).strip()

def calculate_balance(
    debit,
    credit
):
    return safe_float(
        debit
    )-safe_float(
        credit
    )