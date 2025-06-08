from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from datetime import datetime

@dataclass
class Transaction:
    tx_id: int
    internal_id: str
    operation_type: str
    asset: str
    amount: Decimal
    source_address: Optional[str]
    destination_address: str
    tx_hash: Optional[str]
    status: str
    confirmations: int
    error_message: Optional[str]
    retries: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    callback_url: Optional[str]
