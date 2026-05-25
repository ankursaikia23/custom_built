import os
import pandas as pd

class ImportManager:
    def __init__(self,db):
        self.db=db

    def load_dataframe(
        self,
        file_path
    ):
        extension=os.path.splitext(
            file_path
        )[1].lower()
        if extension==".csv":
            return pd.read_csv(file_path)
        if extension in[
            ".xlsx",
            ".xls"
        ]:
            return pd.read_excel(file_path)
        if extension==".ods":
            return pd.read_excel(
                file_path,
                engine="odf"
            )

        raise ValueError(
            "Unsupported file format"
        )

    def import_chart_of_accounts(
        self,
        file_path
    ):
        df=self.load_dataframe(
            file_path
        )
        imported=0
        for _,row in df.iterrows():
            existing=self.db.fetchone("""
            SELECT id
            FROM accounts
            WHERE account_code=?
            """,(str(row["account_code"]),))
            if existing:
                continue
            self.db.execute("""
            INSERT INTO accounts(
                account_code,
                account_name,
                account_type,
                created_at
            )
            VALUES(
                ?,
                ?,
                ?,
                datetime('now')
            )
            """,(
                str(row["account_code"]),
                str(row["account_name"]),
                str(row["account_type"])
            ))
            imported+=1
        self.db.log_action(
            "IMPORT",
            "accounts",
            imported,
            f"Imported {imported} accounts"
        )
        return imported

    def import_customers(
        self,
        file_path
    ):
        df=self.load_dataframe(
            file_path
        )
        imported=0
        for _,row in df.iterrows():
            self.db.execute("""
            INSERT INTO customers(
                customer_name,
                phone,
                email,
                address,
                created_at
            )
            VALUES(
                ?,
                ?,
                ?,
                ?,
                datetime('now')
            )
            """,(
                str(row.get(
                    "customer_name",
                    ""
                )),
                str(row.get(
                    "phone",
                    ""
                )),
                str(row.get(
                    "email",
                    ""
                )),
                str(row.get(
                    "address",
                    ""
                ))
            ))
            imported+=1
        return imported

    def import_vendors(
        self,
        file_path
    ):
        df=self.load_dataframe(
            file_path
        )
        imported=0
        for _,row in df.iterrows():
            self.db.execute("""
            INSERT INTO vendors(
                vendor_name,
                phone,
                email,
                address,
                created_at
            )
            VALUES(
                ?,
                ?,
                ?,
                ?,
                datetime('now')
            )
            """,(
                str(row.get(
                    "vendor_name",
                    ""
                )),
                str(row.get(
                    "phone",
                    ""
                )),
                str(row.get(
                    "email",
                    ""
                )),
                str(row.get(
                    "address",
                    ""
                ))
            ))
            imported+=1
        return imported