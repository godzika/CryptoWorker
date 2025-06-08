import time
from web3.exceptions import TransactionNotFound
import logging
# შენი მოდულები
from ethereum import EthereumService
from database import Database

# პარამეტრები (გადაიტანე config-იდან თუ გაქვს სურვილი)
CONFIRMATION_TARGET = 3   # მინიმალური კონფირმაცია
RETRY_ATTEMPTS = 10       # მაქს. ცდების რაოდენობა receipt-ის მისაღებად
RETRY_DELAY = 5           # წამები ცდებს შორის

loger = logging.getLogger("SferoWeb3Worker")

def get_transaction_receipt_with_retries(eth: EthereumService, tx_hash: str, max_attempts=RETRY_ATTEMPTS, delay=RETRY_DELAY):
    """
    Retrieves the transaction receipt with retries in case of TransactionNotFound error.
    Attempts to fetch the receipt multiple times if it is not found immediately.
    :param eth:
    :param tx_hash:
    :param max_attempts:
    :param delay:
    :return:
    """
    attempts = 0
    while attempts < max_attempts:
        try:
            receipt = eth.w3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                return receipt
        except TransactionNotFound:
            loger.info(f"Receipt for tx {tx_hash} not found, attempt {attempts+1}/{max_attempts}")
            time.sleep(delay)
            attempts += 1
            continue
        except Exception as e:
            loger.error(f"Unexpected error fetching tx {tx_hash}: {e}")
            break
    return None


def monitor_pending_transactions(db, eth):
    """
    Monitors pending transactions, checks for receipt and updates status in the DB.
    """

    loger.info("Monitor started. Checking for pending transactions...")


    try:
        while True:
            pending_txs = db.fetch_pending_transactions()
            if not pending_txs:
                loger.info("No pending transactions found. Sleeping 10 seconds...")
                time.sleep(10)
                continue

            for tx in pending_txs:
                tx_hash = tx.tx_hash
                if not tx_hash or not isinstance(tx_hash, str) or not tx_hash.startswith('0x'):
                    loger.warning(f"Invalid tx_hash in DB for tx_id={tx.internal_id}: {tx_hash}")
                    db.update_transaction_status(
                        tx.internal_id,
                        status="INVALID_HASH",
                        error_message="Invalid transaction hash in database."
                    )
                    continue

                loger.info(f"Checking transaction {tx_hash} (tx_id={tx.internal_id})")
                receipt = get_transaction_receipt_with_retries(eth, tx_hash)

                if receipt is None:
                    loger.warning(f"Receipt not found for tx_id={tx.internal_id} after {RETRY_ATTEMPTS} attempts. Marking as STALE_PENDING.")
                    db.update_transaction_status(
                        tx.internal_id,
                        status="STALE_PENDING",
                        error_message="Receipt not found after retries."
                    )
                    continue

                confirmations = eth.w3.eth.block_number - receipt.blockNumber + 1
                status_str = "SUCCESSFUL" if receipt.status == 1 and confirmations >= CONFIRMATION_TARGET else "PENDING"

                loger.info(
                    f"tx_id={tx.internal_id}: status={status_str}, confirmations={confirmations}"
                )

                db.update_transaction_status(
                    tx.internal_id,
                    status=status_str,
                    tx_hash=tx_hash,
                    confirmations=confirmations,
                    retries=tx.retries + 1 if status_str == "PENDING" else tx.retries
                )

                if status_str == "SUCCESSFUL":
                    loger.info(f"Transaction {tx_hash} confirmed successfully.")
            #       delete error message if it was set
                    db.update_transaction_status(
                        tx.internal_id,
                        error_message=None
                    )

            # ყოველი ციკლის ბოლოს დაელოდე 5 წამი
            time.sleep(5)

    except KeyboardInterrupt:
        loger.info("Monitor stopped by user.")
    except Exception as ex:
        loger.critical(f"Monitor crashed: {ex}", exc_info=True)
    finally:
        db.close()

