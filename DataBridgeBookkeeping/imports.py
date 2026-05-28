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
        
    def validate_columns(
        self,
        dataframe,
        required_columns
    ):
        missing=[]
        for column in required_columns:
            if column not in dataframe.columns:
                missing.append(column)
        if missing:
            raise ValueError(
                "Missing required columns: "
                + ", ".join(missing)
            )
            
    def get_supported_formats(self):
        return[
            ".csv",
            ".xlsx",
            ".xls",
            ".ods"
        ]

    def import_chart_of_accounts(
        self,
        file_path
    ):
        df=self.load_dataframe(
            file_path
        )
        self.validate_columns(
            df,
            [
                "account_code",
                "account_name",
                "account_type"
            ]
        )
        imported=0
        for _,row in df.iterrows():
            account_code=str(
                row["account_code"]
            ).strip()
            account_name=str(
                row["account_name"]
            ).strip()
            account_type=str(
                row["account_type"]
            ).strip()
            if not account_code:
                continue
            existing=self.db.fetchone("""
            SELECT id
            FROM accounts
            WHERE account_code=?
            """,(account_code,))
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
                account_code,
                account_name,
                account_type
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
            customer_name=str(row.get(
                "customer_name",
                ""
            )).strip()
            email=str(row.get(
                "email",
                ""
            )).strip()
            existing=self.db.fetchone("""
            SELECT id
            FROM customers
            WHERE customer_name=?
            AND email=?
            """,(
                customer_name,
                email
            ))
            if existing:
                continue
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
                customer_name,
                str(row.get(
                    "phone",
                    ""
                )).strip(),
                email,
                str(row.get(
                    "address",
                    ""
                )).strip()
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
            vendor_name=str(row.get(
                "vendor_name",
                ""
            )).strip()
            email=str(row.get(
                "email",
                ""
            )).strip()
            existing=self.db.fetchone("""
            SELECT id
            FROM vendors
            WHERE vendor_name=?
            AND email=?
            """,(
                vendor_name,
                email
            ))
            if existing:
                continue
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
                vendor_name,
                str(row.get(
                    "phone",
                    ""
                )).strip(),
                email,
                str(row.get(
                    "address",
                    ""
                )).strip()
            ))
            imported+=1
        return imported