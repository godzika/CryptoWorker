import requests
import logging
import time
from typing import Optional
import logging
from logging.handlers import RotatingFileHandler
import threading

def call_callback_url(callback_url: str, data: dict, retries: int = 3, timeout: int = 5) -> bool:
    """
    Callback API-სთვის POST რექვესტი. სთხოვს სერვერს სტატუსის განახლებას.
    """
    for attempt in range(retries):
        try:
            response = requests.post(callback_url, json=data, timeout=timeout)
            if response.status_code in (200, 201, 202):
                logging.info(f"Callback successful to {callback_url}")
                return True
            else:
                logging.warning(f"Callback {callback_url} failed with status {response.status_code}: {response.text}")
        except Exception as e:
            logging.error(f"Callback {callback_url} error: {e}")
        time.sleep(2 ** attempt)  # Exponential backoff
    return False

def validate_eth_address(address: str) -> bool:
    """
    ამოწმებს ethereum მისამართის ვალიდურობას.
    """
    from web3 import Web3
    return Web3.is_address(address)

def to_wei(amount, decimals=18):
    """
    Helper amount-ს Wei-ში გადაყვანისთვის.
    """
    from decimal import Decimal
    return int(Decimal(amount) * (10 ** decimals))

def from_wei(amount, decimals=18):
    """
    Wei-ს human-readable ფორმატში გადაყვანა.
    """
    from decimal import Decimal
    return Decimal(amount) / (10 ** decimals)

def retry_on_exception(func, retries: int = 3, wait: int = 2, exceptions=(Exception,), *args, **kwargs):
    """
    უნივერსალური რეტრი ჰელპერი ნებისმიერი ფუნქციისთვის.
    """
    for attempt in range(retries):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            logging.error(f"Retryable error: {e}")
            time.sleep(wait * (attempt + 1))
    raise Exception(f"Function failed after {retries} retries")


def gas_price_estimate(w3, multiplier: float = 1.2) -> int:
    """
    Gas price-ის შეფასება. გამოიყენება ტრანზაქციისთვის.
    :param w3: Web3 instance
    :param multiplier: გაზის ფასის მულტიპლიკატორი (default: 1.2)
    :return: gas price in wei
    """
    try:
        gas_price = w3.eth.gas_price
        return int(gas_price * multiplier)
    except Exception as e:
        logging.error(f"Gas price estimation error: {e}")
        raise


def setup_logger(logfile="web3worker.log"):
    logger = logging.getLogger("SferoWeb3Worker")
    logger.setLevel(logging.INFO)
    # Check if the logger already has handlers to avoid adding multiple handlers
    if not logger.handlers:
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s (%(filename)s:%(lineno)d)')
        file_handler = RotatingFileHandler(logfile, maxBytes=5*1024*1024, backupCount=5)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    return logger


# utils.py

class NonceManager:
    def __init__(self, w3, address):
        self._lock = threading.Lock()
        self._w3 = w3
        self._address = address
        self._nonce = self._w3.eth.get_transaction_count(self._address, 'pending')

    def get_next_nonce(self):
        with self._lock:
            nonce = self._nonce
            self._nonce += 1
            return nonce

    def set_nonce(self, nonce):
        with self._lock:
            self._nonce = nonce


