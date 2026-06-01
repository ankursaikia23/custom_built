import os
import shutil
from datetime import datetime

class BackupManager:
    def __init__(
        self,
        db_path="database/bookkeeping.db",
        backup_dir="backups"
    ):
        self.db_path=db_path
        self.backup_dir=backup_dir
        os.makedirs(
            self.backup_dir,
            exist_ok=True
        )
        self.session_backup_file=os.path.join(
            self.backup_dir,
            "_session_start.db"
        )

    def create_backup(self):
        timestamp=datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )
        backup_file=os.path.join(
            self.backup_dir,
            f"backup_{timestamp}.db"
        )
        shutil.copy2(
            self.db_path,
            backup_file
        )
        return backup_file

    def create_session_backup(self):
        wal_file=f"{self.db_path}-wal"
        shm_file=f"{self.db_path}-shm"
        if os.path.exists(wal_file):
            os.remove(wal_file)
        if os.path.exists(shm_file):
            os.remove(shm_file)
        shutil.copy2(
            self.db_path,
            self.session_backup_file
        )
        return self.session_backup_file

    def restore_session_backup(self):
        if not os.path.exists(
            self.session_backup_file
        ):
            raise FileNotFoundError(
                "Session backup not found"
            )
        shutil.copy2(
            self.session_backup_file,
            self.db_path
        )

    def restore_backup(
        self,
        backup_file
    ):
        source=os.path.join(
            self.backup_dir,
            backup_file
        )
        shutil.copy2(
            source,
            self.db_path
        )

    def list_backups(self):
        backups=[]
        for file in os.listdir(
            self.backup_dir
        ):
            if (
                file.endswith(".db")
                and
                file!="_session_start.db"
            ):
                backups.append(file)
        backups.sort(
            reverse=True
        )
        return backups

    def delete_backup(
        self,
        backup_file
    ):
        path=os.path.join(
            self.backup_dir,
            backup_file
        )
        if os.path.exists(path):
            os.remove(path)