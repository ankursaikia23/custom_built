import json
from datetime import datetime

class QueueManager:
    def __init__(self,db):
        self.db=db

    def add_change(
        self,
        change_type,
        target_table,
        payload,
        target_id=None
    ):
        self.db.execute("""
        INSERT INTO pending_changes(
            change_type,
            target_table,
            target_id,
            payload,
            created_at
        )
        VALUES(?,?,?,?,?)
        """,(
            change_type,
            target_table,
            str(target_id)
            if target_id is not None
            else "",
            json.dumps(payload),
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        ))

    def get_pending_changes(self):
        return self.db.fetchall("""
        SELECT *
        FROM pending_changes
        ORDER BY id
        """)

    def remove_change(
        self,
        queue_id
    ):
        self.db.execute("""
        DELETE FROM pending_changes
        WHERE id=?
        """,(queue_id,))

    def clear_queue(self):
        self.db.execute("""
        DELETE FROM pending_changes
        """)