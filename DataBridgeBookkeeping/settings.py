class SettingsManager:
    def __init__(self,db):
        self.db=db

    def set_setting(
        self,
        key,
        value
    ):
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

    def get_setting(
        self,
        key,
        default_value=None
    ):
        row=self.db.fetchone("""
        SELECT setting_value
        FROM app_settings
        WHERE setting_key=?
        """,(key,))

        if row:
            return row["setting_value"]
        return default_value

    def get_all_settings(self):
        return self.db.fetchall("""
        SELECT
            setting_key,
            setting_value
        FROM app_settings
        ORDER BY setting_key
        """)

    def delete_setting(
        self,
        key
    ):
        self.db.execute("""
        DELETE FROM app_settings
        WHERE setting_key=?
        """,(key,))