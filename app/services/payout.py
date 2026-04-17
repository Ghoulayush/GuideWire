from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict
from uuid import uuid4
from urllib.parse import quote_plus


DEFAULT_PAYEE_UPI = "gigshield@upi"
DEFAULT_PAYEE_NAME = "GigShield Insurance"
AUTO_COMPLETE_SECONDS = 8


_PAYOUTS: Dict[str, Dict[str, Any]] = {}


def generate_transaction_id() -> str:
    now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    token = uuid4().hex[:10].upper()
    return f"TXN-{now}-{token}"


def build_upi_uri(
    *,
    amount: float,
    transaction_id: str,
    payee_upi: str = DEFAULT_PAYEE_UPI,
    payee_name: str = DEFAULT_PAYEE_NAME,
    note: str = "GigShield instant payout",
) -> str:
    encoded_name = quote_plus(payee_name)
    encoded_note = quote_plus(note)
    return (
        f"upi://pay?pa={payee_upi}&pn={encoded_name}&am={amount:.2f}&cu=INR"
        f"&tr={transaction_id}&tn={encoded_note}"
    )


def _qr_image_url(payload: str) -> str:
    encoded = quote_plus(payload)
    return f"https://quickchart.io/qr?size=240&text={encoded}"


def _derive_status(record: Dict[str, Any]) -> str:
    if record["status"] == "completed":
        return "completed"

    created_at = record.get("created_at")
    if not isinstance(created_at, datetime):
        return "pending"

    if datetime.utcnow() >= created_at + timedelta(seconds=AUTO_COMPLETE_SECONDS):
        record["status"] = "completed"
        record["completed_at"] = datetime.utcnow()
        record["confirmation_message"] = "Money credited"
        return "completed"

    return "pending"


def initiate_payout(
    *,
    worker_id: str,
    amount: float,
    claim_id: str | None = None,
    payee_upi: str | None = None,
) -> Dict[str, Any]:
    transaction_id = generate_transaction_id()
    safe_amount = max(0.0, float(amount or 0.0))
    upi_uri = build_upi_uri(
        amount=safe_amount,
        transaction_id=transaction_id,
        payee_upi=payee_upi or DEFAULT_PAYEE_UPI,
    )

    record: Dict[str, Any] = {
        "transaction_id": transaction_id,
        "worker_id": worker_id,
        "claim_id": claim_id,
        "amount": round(safe_amount, 2),
        "status": "pending",
        "upi_uri": upi_uri,
        "qr_image_url": _qr_image_url(upi_uri),
        "created_at": datetime.utcnow(),
        "completed_at": None,
        "confirmation_message": "Payment is being processed",
    }

    _PAYOUTS[transaction_id] = record
    return serialize_payout(record)


def get_payout(transaction_id: str) -> Dict[str, Any] | None:
    record = _PAYOUTS.get(transaction_id)
    if not record:
        return None

    _derive_status(record)
    return serialize_payout(record)


def serialize_payout(record: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "transaction_id": record["transaction_id"],
        "worker_id": record.get("worker_id"),
        "claim_id": record.get("claim_id"),
        "amount": record.get("amount", 0.0),
        "status": record.get("status", "pending"),
        "upi_uri": record.get("upi_uri", ""),
        "qr_image_url": record.get("qr_image_url", ""),
        "confirmation_message": record.get("confirmation_message", ""),
        "created_at": record.get("created_at").isoformat()
        if record.get("created_at")
        else None,
        "completed_at": record.get("completed_at").isoformat()
        if record.get("completed_at")
        else None,
    }
