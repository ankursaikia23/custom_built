import pandas as pd

class Validator:

    def validate_answers(self, df):
        if df is None or df.empty:
            return "No data to validate"
        missing = df.isna().sum().sum()
        empty_cells = missing
        total_cells = df.size
        percent_missing = (empty_cells / total_cells) * 100 if total_cells else 0
        return f"Validation complete: {empty_cells} missing cells ({percent_missing:.2f}%)"

    def validate_structure(self, df):
        if df is None or df.empty:
            return "No data to validate"
        issues = []
        if "Q#" not in df.columns:
            issues.append("Missing column Q#")
        duplicates = df.duplicated(subset=["Question"]).sum() if "Question" in df.columns else 0
        if duplicates:
            issues.append(f"{duplicates} duplicate questions")
        return "Structure OK" if not issues else "; ".join(issues)
