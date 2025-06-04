import pytest
from ethereum import EthereumService

class DummyWeb3Provider:
    pass

class DummyAccount:
    address = "0x0000000000000000000000000000000000000000"
    def sign_transaction(self, tx): return type("Signed", (), {"rawTransaction": b"123"})()
    @classmethod
    def from_key(cls, key): return cls()

class DummyEth:
    def getTransactionCount(self, address): return 1
    @property
    def gas_price(self): return 1
    def sendRawTransaction(self, raw): return b"dummy_tx_hash"
    def contract(self, address, abi):
        class DummyContract:
            def functions(self):
                return self
            def transfer(self, to, value):
                class DummyTx:
                    def build_transaction(self, data): return {}
                return DummyTx()
        return DummyContract()
    def get_balance(self, address): return 100
    def __init__(self):
        self.account = DummyAccount

class DummyWeb3:
    HTTPProvider = DummyWeb3Provider
    def __init__(self, *args, **kwargs):
        self.eth = DummyEth()
    def isConnected(self): return True
    def __getattr__(self, item):
        if item == "eth":
            return self.eth
        raise AttributeError(item)
    def contract(self, address, abi): return self.eth.contract(address, abi)
    # Needed for compatibility:
    def __call__(self, *args, **kwargs): return self

@pytest.fixture(autouse=True)
def patch_web3(monkeypatch):
    # Patch ethereum.py-ში გამოყენებული Web3-ს
    import ethereum
    monkeypatch.setattr(ethereum, "Web3", DummyWeb3)
    yield

def test_send_token():
    eth = EthereumService()
    tx_hash = eth.send_token(
        "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        "0x742d35Cc6634C0532925a3b844Bc454e4438f44e",
        1)
    assert isinstance(tx_hash, str)
