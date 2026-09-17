from datetime import datetime, timezone
from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
AUDIT_LOG_PATH = PROJECT_ROOT / "output" / "audit_log.jsonl"


def log_interaction(record: dict) -> dict:
    """
    Append one AI interaction to the audit log.
    """

    if not isinstance(record, dict):
        raise ValueError("Audit record must be a dictionary.")

    AUDIT_LOG_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    audit_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **record
    }

    with AUDIT_LOG_PATH.open(
        "a",
        encoding="utf-8"
    ) as file:
        file.write(
            json.dumps(audit_record)
            + "\n"
        )

    return audit_record