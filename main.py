import time
import traceback
from config import Config
from database import Database
from ethereum import EthereumService
from uniswap import UniswapService
from models import Transaction
from utils import call_callback_url, validate_eth_address, setup_logger
from checker import Checker
import threading
from monitor import monitor_pending_transactions

logger = setup_logger("web3worker.log")
# logger
def process_transaction(db: Database, eth: EthereumService, uni: UniswapService, tx: Transaction):
    callback_data = {
        "internal_id": tx.internal_id,
        "operation_type": tx.operation_type,
        "status": None,
        "tx_hash": None,
        "error_message": None
    }
    try:
        logger.info(f"START tx_id={tx.internal_id} type={tx.operation_type} amount={tx.amount} dest={tx.destination_address}")
        if not validate_eth_address(tx.destination_address):
            raise ValueError(f"Invalid destination address: {tx.destination_address}")

        nonce = eth.nonce_manager.get_next_nonce()

        if tx.operation_type == "WITHDRAW_SFC":
            tx_hash = eth.send_token(Config.SFC_CONTRACT, tx.destination_address, tx.amount, custom_nonce=nonce)
        elif tx.operation_type == "WITHDRAW_USDT":
            tx_hash = eth.send_token(Config.USDT_CONTRACT, tx.destination_address, tx.amount, decimals=6, custom_nonce=nonce)
        elif tx.operation_type in ["SWAP_TO_SFC", "SWAP_TO_USDT"]:
            path = [Config.USDT_CONTRACT, Config.SFC_CONTRACT] if tx.operation_type == "SWAP_TO_SFC" else [Config.SFC_CONTRACT, Config.USDT_CONTRACT]
            deadline = int(time.time()) + 60 * 10
            amount_out_min = int(tx.amount * 0.97 * (10 ** 18))  # ეს ადგილობრივად დააყენე

            for addr in path:
                if not validate_eth_address(addr):
                    raise ValueError(f"Invalid contract address in path: {addr}")

            tx_hash = uni.swap_exact_tokens_for_tokens(tx.amount, amount_out_min, path, tx.destination_address, deadline, custom_nonce=nonce)
        else:
            raise Exception("Unknown operation_type")

        db.update_transaction_status(tx.internal_id, "PENDING", tx_hash=tx_hash)
        callback_data["status"] = "PENDING"
        callback_data["tx_hash"] = tx_hash
        logger.info(f"SUCCESS tx_id={tx.internal_id} status=PENDING hash={tx_hash}")

    except Exception as e:
        error_msg = f"FAILED tx_id={tx.internal_id} error={str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        db.update_transaction_status(
            tx.internal_id, "FAILED",
            error_message=str(e),
            retries=tx.retries + 1
        )
        callback_data["status"] = "FAILED"
        callback_data["error_message"] = str(e)

    if tx.callback_url:
        try:
            result = call_callback_url(tx.callback_url, callback_data)
            logger.info(f"Callback sent to {tx.callback_url}, result={result}")
        except Exception as cb_e:
            logger.error(f"Callback error: {cb_e}")
            logger.error(traceback.format_exc())

def main():
    db = Database()
    eth = EthereumService()
    uni = UniswapService(eth)

    checker = Checker(db, eth, uni)
    if not checker.check_services():
        logger.critical("Service check failed, exiting.")
        return
    checker.check_balance_of_main_account()
    checker.check_balance_of_main_account_token()

    # Start the monitor thread for pending transactions
    threading.Thread(target=monitor_pending_transactions, args=(db, eth), daemon=True).start()

    try:
        logger.info("Starting main worker loop...")
        # try to process lost transactions first
        logger.info("Processing lost transactions...")
        lost_txs = db.fetch_failed_transactions()
        if not lost_txs:
            logger.info("No lost transactions found.")
        else:
            logger.info(f"Found {len(lost_txs)} lost transactions to process.")
        for tx in lost_txs:
            process_transaction(db, eth, uni, tx)
        # main loop for processing pending transactions
        logger.info("Processing pending transactions...")

        while True:
            txs = db.fetch_waiting_transactions()
            for tx in txs:
                process_transaction(db, eth, uni, tx)
            time.sleep(5)
    except Exception as main_e:
        logger.critical(f"MAIN LOOP CRASH: {main_e}")
        logger.critical(traceback.format_exc())

    except KeyboardInterrupt:
        logger.info("Worker stopped by user.")
    finally:
        db.close()

if __name__ == '__main__':
    main()
