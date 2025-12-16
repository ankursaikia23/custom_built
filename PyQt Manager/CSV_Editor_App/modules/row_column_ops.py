import pandas as pd

class RowColumnOps:

    def insert_rows(self, df, selected_row, count=1):
        rows = [{col: "" for col in df.columns} for _ in range(count)]
        new_df = pd.DataFrame(rows)
        return pd.concat([df.iloc[:selected_row], new_df, df.iloc[selected_row:]], ignore_index=True)

    def delete_rows(self, df, rows):
        df = df.drop(rows, axis=0).reset_index(drop=True)
        return df

    def insert_columns(self, df, index, count=1):
        for i in range(count):
            df.insert(index + i, f"New_{index+i+1}", "")
        return df

    def delete_columns(self, df, cols):
        df = df.drop(cols, axis=1)
        return df

    def remove_duplicates(self, df):
        before = len(df)
        df = df.drop_duplicates(subset=["Question"], ignore_index=True)
        return df, before - len(df)

    def missing_only(self, df):
        cols = [c for c in df.columns if c != "Q#"]
        filtered = df[df[cols].isna().any(axis=1)]
        return filtered

    def bulk_find_replace(self, df, columns, find_text, replace_text):
        for col in columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.replace(find_text, replace_text, regex=False)
        return df