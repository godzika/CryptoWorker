from web3 import Web3
from config import Config
from utils import validate_eth_address
import logging

class EthereumService:
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(Config.ETH_NODE_URL))
        if not self.w3.isConnected():
            raise ConnectionError("Ethereum node not connected")
        self.account = self.w3.eth.account.from_key(Config.PRIVATE_KEY)

    def send_token(self, contract_address, to_address, amount, decimals=18):
        # Validate both contract and to_address!
        if not validate_eth_address(contract_address):
            raise ValueError(f"Invalid contract address: {contract_address}")
        if not validate_eth_address(to_address):
            raise ValueError(f"Invalid destination address: {to_address}")

        contract = self.w3.eth.contract(address=contract_address, abi=self._get_erc20_abi())
        tx = contract.functions.transfer(
            to_address,
            int(amount * (10 ** decimals))
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.getTransactionCount(self.account.address),
            'gas': 120000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': Config.NETWORK_ID,
        })
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return tx_hash.hex()

    def _get_erc20_abi(self):
        return [
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
        ]

    def get_eth_balance(self, address):
        if not validate_eth_address(address):
            raise ValueError(f"Invalid address for balance check: {address}")
        return self.w3.eth.get_balance(address)

    def get_token_balance(self, contract_address, address):
        if not validate_eth_address(contract_address):
            raise ValueError(f"Invalid contract address for balance check: {contract_address}")
        if not validate_eth_address(address):
            raise ValueError(f"Invalid address for token balance check: {address}")
        contract = self.w3.eth.contract(address=contract_address, abi=self._get_erc20_abi())
        return contract.functions.balanceOf(address).call()
