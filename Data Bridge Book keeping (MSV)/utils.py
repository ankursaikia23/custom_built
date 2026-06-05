from datetime import datetime

def format_currency(amount):
    try:
        return f"{float(amount):,.2f}"
    except(
        TypeError,
        ValueError
    ):
        return "0.00"

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
    try:
        parsed=datetime.strptime(
            str(date_value),
            "%Y-%m-%d"
        )
        return parsed.strftime(
            "%Y-%m-%d"
        )
    except(
        TypeError,
        ValueError
    ):
        return str(date_value)

def safe_float(
    value,
    default=0.0
):
    try:
        return float(value)
    except(
        TypeError,
        ValueError
    ):
        return default

def safe_int(
    value,
    default=0
):
    try:
        return int(float(value))
    except(
        TypeError,
        ValueError
    ):
        return default

def generate_timestamp():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

def normalize_text(text):
    if text is None:
        return ""
    return str(text).strip()

def calculate_balance(
    debit,
    credit
):
    return round(
        safe_float(
            debit
        )-
        safe_float(
            credit
        ),
        2
    )