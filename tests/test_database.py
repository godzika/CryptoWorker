import pytest
from database import Database
from models import Transaction

class DummyDB(Database):
    def __init__(self):
        pass
    def fetch_waiting_transactions(self):
        return [Transaction(
            tx_id=1,
            internal_id="abc123",
            operation_type="WITHDRAW_SFC",
            asset="SFC",
            amount=1,
            source_address=None,
            destination_address="0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
            tx_hash=None,
            status="WAITING",
            confirmations=0,
            error_message=None,
            retries=0,
            callback_url=None
        )]
    def update_transaction_status(self, *args, **kwargs):
        return True

def test_fetch_and_update():
    db = DummyDB()
    txs = db.fetch_waiting_transactions()
    assert len(txs) == 1
    assert txs[0].status == "WAITING"
    assert db.update_transaction_status("abc123", "PENDING") is True
