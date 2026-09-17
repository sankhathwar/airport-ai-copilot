import pandas as pd


REQUIRED_COLUMNS = [
    "airport_code",
    "completion_rate",
    "average_eta",
    "active_drivers",
    "driver_cancellation_rate",
    "queue_size",
    "surge_multiplier",
    "request_volume",
    "timestamp",
]

VALID_AIRPORTS = {"SFO", "LAX", "JFK"}


def load_airport_metrics(file_path: str) -> pd.DataFrame:
    """
    Load and validate airport operational metrics.
    """

    df = pd.read_csv(file_path)

    # Check required columns
    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    # Validate airport codes
    invalid_airports = set(df["airport_code"]) - VALID_AIRPORTS

    if invalid_airports:
        raise ValueError(
            f"Invalid airport codes found: {invalid_airports}"
        )

    # Convert timestamp
    df["timestamp"] = pd.to_datetime(
        df["timestamp"],
        errors="raise"
    )

    # Numeric columns
    numeric_columns = [
        "completion_rate",
        "average_eta",
        "active_drivers",
        "driver_cancellation_rate",
        "queue_size",
        "surge_multiplier",
        "request_volume",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="raise"
        )

    # Check for missing values
    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ValueError(
            "Operational dataset contains missing values."
        )

    return df