from datetime import datetime

class AccountManager:
    def __init__(self,db):
        self.db=db

    def create_account(
        self,
        account_code,
        account_name,
        account_type,
        parent_id=None
    ):
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