import psycopg2
import psycopg2.extras
from typing import List
from models import Transaction
from config import Config

class Database:
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
                WHERE status = 'WAITING' OR (status = 'FAILED' AND retries < %s)
                ORDER BY created_at ASC
                FOR UPDATE SKIP LOCKED
                """, (Config.MAX_RETRIES,))
            rows = cur.fetchall()
            return [Transaction(**row) for row in rows]

    def update_transaction_status(self, internal_id: str, status: str, tx_hash: str = None, error_message: str = None, confirmations: int = 0, retries: int = 0):
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE transactions
                SET status = %s, tx_hash = %s, error_message = %s, confirmations = %s, retries = %s, updated_at = NOW()
                WHERE internal_id = %s
            """, (status, tx_hash, error_message, confirmations, retries, internal_id))
            self.conn.commit()

    def close(self):
        self.conn.close()
