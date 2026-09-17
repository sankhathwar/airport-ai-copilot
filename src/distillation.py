from pathlib import Path
import json


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DISTILLATION_PATH = (
    PROJECT_ROOT / "output" / "distilled_training_data.jsonl"
)


def save_distillation_record(record: dict) -> dict:
    """
    Save a successful AI interaction as a JSONL record.
    """

    if not isinstance(record, dict):
        raise ValueError("Distillation record must be a dictionary.")

    DISTILLATION_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with DISTILLATION_PATH.open(
        "a",
        encoding="utf-8"
    ) as file:
        file.write(
            json.dumps(record)
            + "\n"
        )

    return record