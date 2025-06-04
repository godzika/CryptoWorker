from models import Transaction
from main import process_transaction

class DummyEthereum:
    def send_token(self, *args, **kwargs): return "0xtesthash"

class DummyUniswap:
    def swap_exact_tokens_for_tokens(self, *args, **kwargs): return "0xtestswaphash"

class DummyDB:
    def fetch_pending_transactions(self): return []
    def update_transaction_status(self, *args, **kwargs): return True

def test_process_transaction_valid(monkeypatch):
    db = DummyDB()
    eth = DummyEthereum()
    uni = DummyUniswap()
    tx = Transaction(
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
    )
    process_transaction(db, eth, uni, tx)
