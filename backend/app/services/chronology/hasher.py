import hashlib
import json
from datetime import datetime
from typing import Any, Dict


def json_serial_fallback(obj: Any) -> Any:
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def canonical_json_bytes(payload: Dict[str, Any]) -> bytes:
    """
    Encodes a dictionary into canonical deterministic JSON bytes:
    - Sorted keys
    - No unnecessary whitespace
    - UTF-8 encoding
    - Handled datetime serialization
    """
    serialized = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=json_serial_fallback,
        ensure_ascii=False,
    )
    return serialized.encode("utf-8")


def compute_sha256_hash(data: bytes) -> str:
    """Computes SHA-256 hexadecimal digest from raw bytes."""
    return hashlib.sha256(data).hexdigest()


def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Computes SHA-256 hexadecimal digest of canonical JSON payload."""
    return compute_sha256_hash(canonical_json_bytes(payload))


def compute_chained_record_hash(previous_hash: str, payload_hash: str) -> str:
    """
    Computes current_record_hash from previous_hash and current payload_hash:
    current_hash = SHA256(previous_hash + payload_hash)
    """
    combined = f"{previous_hash}:{payload_hash}".encode("utf-8")
    return compute_sha256_hash(combined)
