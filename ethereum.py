import time

from web3 import Web3
from web3.exceptions import TransactionNotFound

from config import Config
from utils import validate_eth_address, NonceManager
import logging
import json
import requests

class EthereumService:

    # check if all works correctly
    def is_connected(self) -> bool:
        """
        Checks if the Ethereum node is connected.
        Validates the connection by attempting to call a simple method.
        :raises ConnectionError: If the Ethereum node is not connected.
        :return:
        """
        try:
            return self.w3.is_connected()
        except Exception as e:
            logging.error(f"Ethereum node connection error: {e}")
            return False

    def __init__(self):
        """
        Initializes the EthereumService with a connection to the Ethereum node.
        Validates the connection and sets up the main account using the private key from the configuration.
        :raises ConnectionError: If the Ethereum node is not connected.
        """
        self.w3 = Web3(Web3.HTTPProvider(Config.ETH_NODE_URL))
        if not self.w3.is_connected():
            raise ConnectionError("Ethereum node not connected")
        self.account = self.w3.eth.account.from_key(Config.PRIVATE_KEY)
        self.nonce_manager = NonceManager(self.w3, self.account.address)

    def send_token(self, contract_address, to_address, amount, decimals=18, custom_nonce=None):
        """
        Sends an ERC20 token from the main account to a specified address.
        Uses get_gas_fee to determine optimal gas params.
        """
        # Validate both contract and to_address!
        if not validate_eth_address(contract_address):
            raise ValueError(f"Invalid contract address: {contract_address}")
        if not validate_eth_address(to_address):
            raise ValueError(f"Invalid destination address: {to_address}")

        if custom_nonce is None:
            nonce = self.nonce_manager.get_next_nonce()
        else:
            nonce = custom_nonce

        contract = self.w3.eth.contract(address=contract_address, abi=self._get_erc20_abi())

        tx_params = {
            'from': self.account.address,
            'nonce': nonce,
            'gas': 300000,  # აქ შეგიძლია გონივრული ლიმიტი დააყენო
            'chainId': Config.NETWORK_ID,
        }

        # თუ გაზის ფასები არ გაქვს, აიღე მაღალი გაზის ფასები
        gas_fees = self.get_gas_fee("high")
        tx = contract.functions.transfer(
            to_address,
            int(amount * (10 ** decimals))
        ).build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'gas': 300000,
            'maxFeePerGas': gas_fees["maxFeePerGas"],
            'maxPriorityFeePerGas': gas_fees["maxPriorityFeePerGas"],
            'chainId': Config.NETWORK_ID,
        })


        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return self.w3.to_hex(tx_hash)

    def _get_erc20_abi(self):
        """
        Retrieves the ABI for the ERC20 token contract.
        Reads from a local JSON file named contract_abi.json.
        :raises FileNotFoundError: If the contract_abi.json file is not found.
        :raises ValueError: If the JSON file is not properly formatted.
        :return:
        """
        #    get abi from contract_abi.json file
        try:
            with open('contract_abi.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("contract_abi.json file not found. Please provide the correct path.")
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON from contract_abi.json: {e}")

    def get_eth_balance(self, address):
        """
        Retrieves the ETH balance of a specific address.
        Validates the address before proceeding.
        :param address:
        :return:
        """
        if not validate_eth_address(address):
            raise ValueError(f"Invalid address for balance check: {address}")
        return self.w3.eth.get_balance(address)

    def get_token_balance(self, contract_address, address):
        """
        Retrieves the token balance of a specific address for a given ERC20 contract.
        :param contract_address:
        :param address:
        :return:
        """
        if not validate_eth_address(contract_address):
            raise ValueError(f"Invalid contract address for balance check: {contract_address}")
        if not validate_eth_address(address):
            raise ValueError(f"Invalid address for token balance check: {address}")
        contract = self.w3.eth.contract(address=contract_address, abi=self._get_erc20_abi())
        return contract.functions.balanceOf(address).call()

    def send_eth(self, to_address, amount):
        """
        Sends ETH from the main account to a specified address.
        Validates the destination address before proceeding.
        :param to_address:
        :param amount:
        :return:
        """
        if not validate_eth_address(to_address):
            raise ValueError(f"Invalid destination address: {to_address}")
        tx = {
            'to': to_address,
            'value': int(amount * (10 ** 18)),  # Convert ETH to Wei
            'gas': 21000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'chainId': Config.NETWORK_ID,
        }
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def send_eth_from_user_to_destination(self, user_address, user_private_key, destination_address, amount):
        """
        Sends ETH from a user's address to a destination address.
        Validates both user and destination addresses before proceeding.
        :param user_address:
        :param user_private_key:
        :param destination_address:
        :param amount:
        :return:
        """
        if not validate_eth_address(user_address):
            raise ValueError(f"Invalid user address: {user_address}")
        if not validate_eth_address(destination_address):
            raise ValueError(f"Invalid destination address: {destination_address}")

        tx = {
            'to': destination_address,
            'value': int(amount * (10 ** 18)),  # Convert ETH to Wei
            'gas': 21000,
            'gasPrice': self.w3.eth.gas_price,
            'nonce': self.w3.eth.get_transaction_count(user_address),
            'chainId': Config.NETWORK_ID,
        }
        signed_tx = self.w3.eth.account.sign_transaction(tx, user_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def send_sfc_from_user_to_destination(self, user_address, user_private_key, destination_address, amount):
        """
        Sends SFC from a user's address to a destination address.
        Validates both user and destination addresses before proceeding.
        :param user_address:
        :param user_private_key:
        :param destination_address:
        :param amount:
        :return:
        """
        if not validate_eth_address(user_address):
            raise ValueError(f"Invalid user address: {user_address}")
        if not validate_eth_address(destination_address):
            raise ValueError(f"Invalid destination address: {destination_address}")

        contract = self.w3.eth.contract(address=Config.SFC_CONTRACT, abi=self._get_erc20_abi())
        tx = contract.functions.transfer(
            destination_address,
            int(amount * (10 ** 18))  # Convert SFC to Wei
        ).build_transaction({
            'from': user_address,
            'nonce': self.w3.eth.get_transaction_count(user_address),
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': Config.NETWORK_ID,
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, user_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def send_usdt_from_user_to_destination(self, user_address, user_private_key, destination_address, amount):
        """
        Sends USDT from a user's address to a destination address.
        Validates both user and destination addresses before proceeding.
        :param user_address:
        :param user_private_key:
        :param destination_address:
        :param amount:
        :return:
        """
        if not validate_eth_address(user_address):
            raise ValueError(f"Invalid user address: {user_address}")
        if not validate_eth_address(destination_address):
            raise ValueError(f"Invalid destination address: {destination_address}")

        contract = self.w3.eth.contract(address=Config.USDT_CONTRACT, abi=self._get_erc20_abi())
        tx = contract.functions.transfer(
            destination_address,
            int(amount * (10 ** 6))  # Convert USDT to Wei (6 decimals)
        ).build_transaction({
            'from': user_address,
            'nonce': self.w3.eth.get_transaction_count(user_address),
            'gas': 120000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': Config.NETWORK_ID,
        })
        signed_tx = self.w3.eth.account.sign_transaction(tx, user_private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()

    def get_transaction_receipt(self, tx_hash, max_attempts=10, delay=5):
        if not isinstance(tx_hash, str) or not tx_hash.startswith('0x'):
            raise ValueError(f"Invalid transaction hash: {tx_hash}")
        attempts = 0
        while attempts < max_attempts:
            try:
                receipt = self.w3.eth.get_transaction_receipt(tx_hash)
                if receipt:
                    return receipt
            except TransactionNotFound:
                time.sleep(delay)
                attempts += 1
                continue
            except Exception as e:
                raise RuntimeError(f"Error fetching transaction receipt: {e}")
        # ბოლოს თუ ისევ ვერ ვიპოვეთ
        return None

    def get_transaction_status(self, tx_hash):
        """
        Retrieves the status of a transaction by its hash.
        :param tx_hash:
        :return:
        """
        if not isinstance(tx_hash, str) or not tx_hash.startswith('0x'):
            raise ValueError(f"Invalid transaction hash: {tx_hash}")
        try:
            receipt = self.get_transaction_receipt(tx_hash)
            return receipt.status  # 1 for success, 0 for failure
        except Exception as e:
            raise RuntimeError(f"Error fetching transaction status: {e}")

    def check_if_account_has_enough_balance_for_transaction_gas(self, address, amount):
        """
        Checks if the account has enough ETH balance to cover the transaction gas.
        :param address: Ethereum address to check
        :param amount: Amount in ETH to check against
        :return: True if balance is sufficient, False otherwise
        """
        try:
            balance = self.get_eth_balance(address)
            required_balance = int(amount * (10 ** 18))  # Convert ETH to Wei
            return balance >= required_balance
        except Exception as e:
            logging.error(f"Error checking account balance: {e}")
            return False

    def get_gas_fee(self, urgency="high"):
        url = f"https://gas.api.infura.io/networks/{Config.NETWORK_ID}/suggestedGasFees"

        headers = {"Authorization": f"Basic {Config.INFURA_API_KEY}"} if Config.INFURA_API_KEY else {}
        r = requests.get(url, headers=headers)
        r.raise_for_status()
        fees = r.json()[urgency]
        return {
            "maxFeePerGas": Web3.to_wei(float(fees["suggestedMaxFeePerGas"]), "gwei"),
            "maxPriorityFeePerGas": Web3.to_wei(float(fees["suggestedMaxPriorityFeePerGas"]), "gwei"),
        }

