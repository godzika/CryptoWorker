import logging
from config import Config
# this class checks if all workers are running and if the database is connected
from web3 import Web3

class Checker:
    def __init__(self, db, eth_service, uni_service, logger=None):
        self.db = db
        self.eth_service = eth_service
        self.uni_service = uni_service
        self.is_running = False
        self.logger = logger or logging.getLogger("SferoWeb3Worker")
        self.error_message = None
    def check_services(self):
        """
        Check if all services are running and connected.
        """
        self.logger.info("Checking if all services are running and connected...")
        self.logger.info("Database connection status: %s", self.db.is_connected())
        self.logger.info("Ethereum node connection status: %s", self.eth_service.is_connected())
        self.logger.info("Uniswap Router connection status: %s", self.uni_service.router is not None)

        if not self.db.is_connected():
            self.error_message = "Database connection failed."
            self.logger.critical(self.error_message)
            return False

        if not self.eth_service.is_connected():
            self.error_message = "Ethereum node connection failed."
            self.logger.critical(self.error_message)
            return False

        if not self.uni_service.router:
            self.error_message = "Uniswap Router connection failed."
            self.logger.critical(self.error_message)
            return False

        self.logger.info("All services are running and connected successfully.")
        return True

    def check_balance_of_main_account(self):
        """
        Check if the main account has enough balance of ETH to cover transaction fees.
        """
        try:
            balance = self.eth_service.get_eth_balance(self.eth_service.account.address)
            if balance < 0.04 * 10**18:  # Check if balance is less than 0.01 ETH
                self.error_message = "Main account balance is too low."
                self.logger.warning(self.error_message + f" Current balance: {balance / 10**18} ETH")
                return False
            self.logger.info(f"Main account balance is sufficient: {balance / 10**18} ETH")
            return True
        except Exception as e:
            self.error_message = f"Error checking main account balance: {e}"
            self.logger.error(self.error_message)
            return False


    def check_balance_of_main_account_token(self):
        contract_address = Config.SFC_CONTRACT  # or any other token contract address you want to check

        try:
            checksum_contract_address = Web3.to_checksum_address(contract_address)
            checksum_account_address = Web3.to_checksum_address(self.eth_service.account.address)
            balance = self.eth_service.get_token_balance(checksum_contract_address, checksum_account_address)
            if balance < 100000 * 10 ** 18:
                self.error_message = f"Main account token balance for {checksum_contract_address} is too low. {balance / 10 ** 18} tokens"
                self.logger.warning(self.error_message)
                return False
            self.logger.info(
                f"Main account token balance is sufficient: {balance / 10 ** 18} tokens")
            return True
        except Exception as e:
            self.error_message = f"Error checking main account token balance for {contract_address}: {e}"
            self.logger.error(self.error_message)
            return False

