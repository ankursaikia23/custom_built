from datetime import datetime

class AccountManager:
    VALID_ACCOUNT_TYPES={
        "Asset",
        "Liability",
        "Equity",
        "Revenue",
        "Expense"
    }

    def __init__(self,db):
        self.db=db

    def create_account(
        self,
        account_code,
        account_name,
        account_type,
        parent_id=None
    ):
        if not account_code:
            raise ValueError(
                "Account code is required."
            )
        if not account_name:
            raise ValueError(
                "Account name is required."
            )
        if account_type not in self.VALID_ACCOUNT_TYPES:
            raise ValueError(
                "Invalid account type."
            )
        existing=self.get_account_by_code(
            account_code
        )
        if existing:
            raise ValueError(
                "Account code already exists."
            )
        if parent_id is not None:
            parent=self.get_account_by_id(
                parent_id
            )
            if not parent:
                raise ValueError(
                    "Parent account does not exist."
                )
        self.db.execute("""
        INSERT INTO accounts(
            account_code,
            account_name,
            account_type,
            parent_id,
            created_at
        )
        VALUES(?,?,?,?,?)
        """,(
            account_code,
            account_name,
            account_type,
            parent_id,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))
        self.db.log_action(
            "CREATE",
            "accounts",
            account_code,
            f"Created account: {account_name}"
        )

    def get_all_accounts(self):
        return self.db.fetchall("""
        SELECT
            id,
            account_code,
            account_name,
            account_type,
            parent_id,
            is_active
        FROM accounts
        ORDER BY account_code
        """)

    def get_active_accounts(self):
        return self.db.fetchall("""
        SELECT
            id,
            account_code,
            account_name,
            account_type
        FROM accounts
        WHERE is_active=1
        ORDER BY account_code
        """)

    def get_account_by_id(
        self,
        account_id
    ):
        return self.db.fetchone("""
        SELECT *
        FROM accounts
        WHERE id=?
        """,(account_id,))

    def get_account_by_code(
        self,
        account_code
    ):
        return self.db.fetchone("""
        SELECT *
        FROM accounts
        WHERE account_code=?
        """,(account_code,))

    def update_account(
        self,
        account_id,
        account_code,
        account_name,
        account_type
    ):
        account=self.get_account_by_id(
            account_id
        )
        if not account:
            raise ValueError(
                "Account not found."
            )
        if not account_code:
            raise ValueError(
                "Account code is required."
            )
        if not account_name:
            raise ValueError(
                "Account name is required."
            )
        if account_type not in self.VALID_ACCOUNT_TYPES:
            raise ValueError(
                "Invalid account type."
            )
        existing=self.get_account_by_code(
            account_code
        )
        if existing and existing["id"]!=account_id:
            raise ValueError(
                "Account code already exists."
            )
        self.db.execute("""
        UPDATE accounts
        SET
            account_code=?,
            account_name=?,
            account_type=?
        WHERE id=?
        """,(
            account_code,
            account_name,
            account_type,
            account_id
        ))
        self.db.log_action(
            "UPDATE",
            "accounts",
            account_id,
            f"Updated account: {account_name}"
        )

    def deactivate_account(
        self,
        account_id
    ):
        account=self.get_account_by_id(
            account_id
        )
        if not account:
            raise ValueError(
                "Account not found."
            )
        self.db.execute("""
        UPDATE accounts
        SET is_active=0
        WHERE id=?
        """,(account_id,))
        self.db.log_action(
            "DEACTIVATE",
            "accounts",
            account_id,
            "Account deactivated"
        )

    def activate_account(
        self,
        account_id
    ):
        account=self.get_account_by_id(
            account_id
        )
        if not account:
            raise ValueError(
                "Account not found."
            )
        self.db.execute("""
        UPDATE accounts
        SET is_active=1
        WHERE id=?
        """,(account_id,))
        self.db.log_action(
            "ACTIVATE",
            "accounts",
            account_id,
            "Account activated"
        )

    def delete_account(
        self,
        account_id
    ):
        account=self.get_account_by_id(
            account_id
        )
        if not account:
            raise ValueError(
                "Account not found."
            )
        journal_usage=self.db.fetchone("""
        SELECT id
        FROM journal_lines
        WHERE account_id=?
        LIMIT 1
        """,(account_id,))
        if journal_usage:
            raise ValueError(
                "Account has transactions and cannot be deleted."
            )
        child_account=self.db.fetchone("""
        SELECT id
        FROM accounts
        WHERE parent_id=?
        LIMIT 1
        """,(account_id,))
        if child_account:
            raise ValueError(
                "Account has child accounts and cannot be deleted."
            )
        self.db.execute("""
        DELETE FROM accounts
        WHERE id=?
        """,(account_id,))
        self.db.log_action(
            "DELETE",
            "accounts",
            account_id,
            "Account deleted"
        )

    def account_exists(
        self,
        account_code
    ):
        row=self.db.fetchone("""
        SELECT id
        FROM accounts
        WHERE account_code=?
        """,(account_code,))
        return row is not None