import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    ETH_NODE_URL = os.getenv('ETH_NODE_URL')
    PRIVATE_KEY = os.getenv('HOT_WALLET_PRIVATE_KEY')
    PUBLIC_ADDRESS = os.getenv('HOT_WALLET_PUBLIC_ADDRESS')
    SFC_CONTRACT = os.getenv('SFC_CONTRACT_ADDRESS')
    USDT_CONTRACT = os.getenv('USDT_CONTRACT_ADDRESS')
    UNISWAP_ROUTER = os.getenv('UNISWAP_ROUTER_ADDRESS')
    NETWORK_ID = int(os.getenv('NETWORK_ID', 1))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
