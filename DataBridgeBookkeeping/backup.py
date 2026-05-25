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
            if file.endswith(".db"):
                backups.append(file)
        backups.sort(reverse=True)
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