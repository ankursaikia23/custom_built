class SettingsManager:
    def __init__(self,db):
        self.db=db

    def set_setting(
        self,
        key,
        value
    ):
        key=str(key).strip()
        if not key:
            raise ValueError(
                "Setting key cannot be empty"
            )
        if value is None:
            value=""
        value=str(value)
        existing=self.db.fetchone("""
        SELECT id
        FROM app_settings
        WHERE setting_key=?
        """,(key,))
        if existing:
            self.db.execute("""
            UPDATE app_settings
            SET setting_value=?
            WHERE setting_key=?
            """,(value,key))
        else:
            self.db.execute("""
            INSERT INTO app_settings(
                setting_key,
                setting_value
            )
            VALUES(?,?)
            """,(key,value))
        self.db.commit_transaction()

    def get_setting(
        self,
        key,
        default_value=None
    ):
        key=str(key).strip()
        if not key:
            return default_value
        row=self.db.fetchone("""
        SELECT setting_value
        FROM app_settings
        WHERE setting_key=?
        """,(key,))
        if row:
            return row["setting_value"]
        return default_value

    def get_all_settings(self):
        rows=self.db.fetchall("""
        SELECT
            setting_key,
            setting_value
        FROM app_settings
        ORDER BY setting_key
        """)
        return [
            dict(row)
            for row in rows
        ]

    def delete_setting(
        self,
        key
    ):
        key=str(key).strip()
        if not key:
            return False
        self.db.execute("""
        DELETE FROM app_settings
        WHERE setting_key=?
        """,(key,))
        self.db.commit_transaction()
        return True

    def setting_exists(
        self,
        key
    ):
        key=str(key).strip()
        if not key:
            return False
        row=self.db.fetchone("""
        SELECT 1
        FROM app_settings
        WHERE setting_key=?
        LIMIT 1
        """,(key,))
        return row is not None