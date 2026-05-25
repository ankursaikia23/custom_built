from datetime import datetime
import uuid
import os

def format_currency(value):
    return f"{float(value):,.2f}"

def current_timestamp():
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

def current_date():
    return datetime.now().strftime(
        "%Y-%m-%d"
    )

def safe_float(value):
    try:
        return float(value)
    except:
        return 0.0

def safe_int(value):
    try:
        return int(value)
    except:
        return 0

def generate_uuid():
    return str(uuid.uuid4())

def normalize_text(text):
    return str(text).strip()

def ensure_folder(folder_path):
    os.makedirs(
        folder_path,
        exist_ok=True
    )

def file_exists(file_path):
    return os.path.exists(
        file_path
    )