from config import Config
from utils import validate_eth_address

class UniswapService:

    def __init__(self, eth_service):
        self.w3 = eth_service.w3
        self.account = eth_service.account
        if not validate_eth_address(Config.UNISWAP_ROUTER):
            raise ValueError("Invalid Uniswap Router address!")
        self.router = self.w3.eth.contract(address=Config.UNISWAP_ROUTER, abi=self._get_router_abi())
        self.nonce_manager = eth_service.nonce_manager

    def swap_exact_tokens_for_tokens(self, amount_in, amount_out_min, path, to_address, deadline, custom_nonce=None):
        # Validate all addresses in path and to_address!
        for addr in path:
            if not validate_eth_address(addr):
                raise ValueError(f"Invalid contract address in path: {addr}")
        if not validate_eth_address(to_address):
            raise ValueError(f"Invalid swap destination address: {to_address}")

        if custom_nonce is None:
            nonce = self.nonce_manager.get_next_nonce()
        else:
            nonce = custom_nonce

        tx = self.router.functions.swapExactTokensForTokens(
            int(amount_in), int(amount_out_min), path, to_address, deadline
        ).build_transaction({
            'from': self.account.address,
            'nonce': nonce,
            'gas': 300000,
            'gasPrice': self.w3.eth.gas_price,
            'chainId': Config.NETWORK_ID,
        })
        signed_tx = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return tx_hash.hex()

    def _get_router_abi(self):
        return [
            {
                "name": "swapExactTokensForTokens",
                "type": "function",
                "inputs": [
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMin", "type": "uint256"},
                    {"name": "path", "type": "address[]"},
                    {"name": "to", "type": "address"},
                    {"name": "deadline", "type": "uint256"}
                ],
                "outputs": [
                    {"name": "amounts", "type": "uint256[]"}
                ]
            }
        ]
