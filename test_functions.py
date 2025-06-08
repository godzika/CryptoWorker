from web3 import Web3
import secrets
import psycopg2
from config import Config
import uuid
from datetime import datetime
import time
def generate_eth_addresses(n=5, filename="addresses.txt"):
    eth_addresses = []
    # 'a' mode - append, so it doesn't overwrite previous content
    with open(filename, "a") as f:
        for _ in range(n):
            account_private_key = "0x" + secrets.token_hex(32)
            acct = Web3().eth.account.from_key(account_private_key)
            account_public_key = acct.address
            f.write(f"{account_public_key} | {account_private_key}\n")
            eth_addresses.append((account_public_key, account_private_key))
    print(f"Generated {n} addresses in {filename}")
    return eth_addresses

def insert_test_transaction(
    destination_address,
    amount=1.0,
    operation_type='WITHDRAW_SFC',
    asset='SFC',
    status='WAITING'
):
    conn = psycopg2.connect(
        dbname=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        host=Config.DB_HOST,
        port=Config.DB_PORT
    )
    try:
        with conn.cursor() as cur:
            internal_id = str(uuid.uuid4())
            sql = """
            INSERT INTO transactions
                (internal_id, operation_type, asset, amount, source_address, destination_address, status, created_at, updated_at)
            VALUES
                (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            now = datetime.utcnow()
            cur.execute(sql, (
                internal_id,
                operation_type,
                asset,
                amount,
                None,
                destination_address,
                status,
                now,
                now
            ))
            conn.commit()
            print(f"Inserted test transaction {internal_id} to {destination_address} ({amount} {asset})")
    finally:
        conn.close()

if __name__ == '__main__':
    # 1. გენერაცია
    addresses = generate_eth_addresses(1, "addresses.txt")

    # 2. თითო მისამართზე test ტრანზაქცია
    for public_key, private_key in addresses:
        # მაგ: თითო მისამართზე 1 SFC-ი გადაიგზავნოს
        time.sleep(20)
        insert_test_transaction(
            destination_address=public_key,
            amount=1.0,
            operation_type='WITHDRAW_SFC',
            asset='SFC',
            status='WAITING'
        )
