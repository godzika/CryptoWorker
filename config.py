import os
from dotenv import load_dotenv
from web3 import Web3
load_dotenv()
# check if all required environment variables are set
required_vars = [
    'DB_HOST', 'DB_PORT', 'DB_NAME', 'DB_USER', 'DB_PASSWORD',
    'ETH_NODE_URL', 'HOT_WALLET_PRIVATE_KEY', 'HOT_WALLET_PUBLIC_ADDRESS',
    'SFC_CONTRACT_ADDRESS', 'USDT_CONTRACT_ADDRESS', 'UNISWAP_ROUTER_ADDRESS',
    'NETWORK_ID', 'MAX_RETRIES', 'INFURA_API_KEY'
]
for var in required_vars:
    if not os.getenv(var):
        raise EnvironmentError(f"Required environment variable {var} is not set.")

class Config:
    DB_HOST = os.getenv('DB_HOST')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    ETH_NODE_URL = os.getenv('ETH_NODE_URL')
    PRIVATE_KEY = os.getenv('HOT_WALLET_PRIVATE_KEY')
    PUBLIC_ADDRESS = os.getenv('HOT_WALLET_PUBLIC_ADDRESS')
    SFC_CONTRACT = Web3.to_checksum_address(os.getenv('SFC_CONTRACT_ADDRESS'))
    USDT_CONTRACT = os.getenv('USDT_CONTRACT_ADDRESS')
    UNISWAP_ROUTER = os.getenv('UNISWAP_ROUTER_ADDRESS')
    NETWORK_ID = int(os.getenv('NETWORK_ID', 1))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    INFURA_API_KEY = os.getenv('INFURA_API_KEY', None)
    INFURA_API_SECRET = os.getenv('INFURA_API_SECRET', None)
