import psycopg2
import psycopg2.extras
from typing import List
from models import Transaction
from config import Config

class Database:
    # is connected?
    def is_connected(self) -> bool:
        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False

    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            connect_timeout=5
        )

    def fetch_pending_transactions(self) -> List[Transaction]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT * FROM transactions 
                WHERE status = 'PENDING' OR (status = 'WAITING' AND retries < %s)
                ORDER BY created_at ASC
                FOR UPDATE SKIP LOCKED
                """, (Config.MAX_RETRIES,))
            rows = cur.fetchall()
            return [Transaction(**row) for row in rows]

    def fetch_waiting_transactions(self) -> List[Transaction]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT * FROM transactions 
                WHERE status = 'WAITING' OR (status = 'FAILED' AND retries < %s)
                ORDER BY created_at ASC
                FOR UPDATE SKIP LOCKED
                """, (Config.MAX_RETRIES,))
            rows = cur.fetchall()
            return [Transaction(**row) for row in rows]

    def update_transaction_status(self, internal_id: str, status: str = None, tx_hash: str = None,
                                  error_message: str = None, confirmations: int = None, retries: int = None):
        updates = []
        values = []
        if status is not None:
            updates.append("status = %s")
            values.append(status)
        if tx_hash is not None:
            updates.append("tx_hash = %s")
            values.append(tx_hash)
        if error_message is not None:
            updates.append("error_message = %s")
            values.append(error_message)
        if confirmations is not None:
            updates.append("confirmations = %s")
            values.append(confirmations)
        if retries is not None:
            updates.append("retries = %s")
            values.append(retries)

        updates.append("updated_at = NOW()")
        values.append(internal_id)

        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE transactions
                SET {', '.join(updates)}
                WHERE internal_id = %s
            """, values)
            self.conn.commit()

    def fetch_failed_transactions(self) -> List[Transaction]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute("""
                SELECT * FROM transactions 
                WHERE status = 'FAILED' AND retries >= %s
                ORDER BY created_at ASC
            """, (Config.MAX_RETRIES,))
            rows = cur.fetchall()
            return [Transaction(**row) for row in rows]

    def close(self):
        self.conn.close()
