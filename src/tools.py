import pandas as pd

from src.data_preprocessing import load_airport_metrics

from pathlib import Path

from src.guardrails import (
    validate_action_input,
    validate_tool_output,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "airport_metrics.csv"


def get_airport_metrics(airport_code: str) -> dict:
    """
    Return the latest operational metrics for an airport.
    """

    # Validate input
    if not airport_code:
        return {
            "status": "error",
            "message": "Airport code is required."
        }

    airport_code = airport_code.strip().upper()

    # Load validated data
    try:
        df = load_airport_metrics(DATA_PATH)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Unable to load airport metrics: {str(e)}"
        }

    # Check airport exists
    airport_data = df[
        df["airport_code"] == airport_code
    ]

    if airport_data.empty:
        return {
            "status": "error",
            "message": (
                f"Invalid airport code: {airport_code}. "
                "Valid airports are SFO, LAX, and JFK."
            )
        }

    # Get latest record
    latest_record = airport_data.sort_values(
        "timestamp"
    ).iloc[-1]

    # Structured output
    return {
        "status": "success",
        "airport_code": latest_record["airport_code"],
        "completion_rate": float(latest_record["completion_rate"]),
        "average_eta": float(latest_record["average_eta"]),
        "active_drivers": int(latest_record["active_drivers"]),
        "driver_cancellation_rate": float(
            latest_record["driver_cancellation_rate"]
        ),
        "queue_size": int(latest_record["queue_size"]),
        "surge_multiplier": float(latest_record["surge_multiplier"]),
        "request_volume": int(latest_record["request_volume"]),
        "timestamp": str(latest_record["timestamp"])
    }

def calculate_driver_incentive(
    driver_count: int,
    severity_level: str
) -> dict:
    """
    Calculate a recommended driver incentive
    based on operational severity.

    Synthetic project rule:
        low    -> $10 per driver
        medium -> $20 per driver
        high   -> $35 per driver
    """

    # Validate driver count
    if driver_count is None:
        return {
            "status": "error",
            "message": "driver_count is required."
        }

    if driver_count <= 0:
        return {
            "status": "error",
            "message": "driver_count must be greater than 0."
        }

    # Validate severity
    if not severity_level:
        return {
            "status": "error",
            "message": "severity_level is required."
        }

    severity_level = severity_level.strip().lower()

    incentive_rates = {
        "low": 10,
        "medium": 20,
        "high": 35
    }

    if severity_level not in incentive_rates:
        return {
            "status": "error",
            "message": (
                "Invalid severity level. "
                "Valid levels are low, medium, and high."
            )
        }

    incentive_per_driver = incentive_rates[severity_level]

    estimated_total_cost = (
        driver_count * incentive_per_driver
    )

    return {
        "status": "success",
        "driver_count": driver_count,
        "severity_level": severity_level,
        "recommended_incentive_per_driver": incentive_per_driver,
        "estimated_total_cost": estimated_total_cost
    }

def trigger_surge_override(
    airport_code: str,
    new_multiplier: float,
    reason: str
) -> dict:
    """
    Mock execution tool for changing airport surge.

    This is a simulated action for Day 2.
    Real approval and permission controls will be added on Day 4.
    """

    # Validate airport code
    if not airport_code:
        return {
            "status": "error",
            "message": "airport_code is required."
        }

    airport_code = airport_code.strip().upper()

    valid_airports = {"SFO", "LAX", "JFK"}

    if airport_code not in valid_airports:
        return {
            "status": "error",
            "message": (
                f"Invalid airport code: {airport_code}. "
                "Valid airports are SFO, LAX, and JFK."
            )
        }

    # Validate multiplier
    if new_multiplier is None:
        return {
            "status": "error",
            "message": "new_multiplier is required."
        }

    if new_multiplier < 1.0:
        return {
            "status": "error",
            "message": "new_multiplier cannot be less than 1.0."
        }

    # Validate reason
    if not reason or not reason.strip():
        return {
            "status": "error",
            "message": "reason is required."
        }

    # Mock execution
    return {
        "status": "success",
        "action": "surge_override",
        "airport_code": airport_code,
        "new_multiplier": float(new_multiplier),
        "reason": reason.strip(),
        "execution_mode": "mock",
        "message": (
            f"Mock surge override executed for {airport_code} "
            f"at {new_multiplier}x."
        )
    }

TOOL_REGISTRY = {
    "get_airport_metrics": {
        "function": get_airport_metrics,
        "description": (
            "Retrieve the latest operational metrics for an airport, "
            "including completion rate, ETA, active drivers, "
            "driver cancellation rate, queue size, surge multiplier, "
            "request volume, and timestamp."
        ),
        "parameters": {
            "airport_code": {
                "type": "string",
                "description": "Airport code such as SFO, LAX, or JFK.",
                "required": True
            }
        }
    },

    "calculate_driver_incentive": {
        "function": calculate_driver_incentive,
        "description": (
            "Calculate the recommended incentive per driver "
            "and estimated total incentive cost based on "
            "driver count and operational severity."
        ),
        "parameters": {
            "driver_count": {
                "type": "integer",
                "description": "Number of drivers receiving the incentive.",
                "required": True
            },
            "severity_level": {
                "type": "string",
                "description": "Operational severity: low, medium, or high.",
                "required": True
            }
        }
    },

    "trigger_surge_override": {
        "function": trigger_surge_override,
        "description": (
            "Mock execution tool that simulates changing "
            "the surge multiplier for an airport."
        ),
        "parameters": {
            "airport_code": {
                "type": "string",
                "description": "Airport code such as SFO, LAX, or JFK.",
                "required": True
            },
            "new_multiplier": {
                "type": "number",
                "description": "New surge multiplier, such as 1.3 or 1.4.",
                "required": True
            },
            "reason": {
                "type": "string",
                "description": "Operational reason for the surge override.",
                "required": True
            }
        }
    }
}

def execute_tool(tool_name: str, arguments: dict) -> dict:
    """Execute a registered tool after input and output validation."""

    if tool_name not in TOOL_REGISTRY:
        return {
            "status": "error",
            "message": f"Unknown tool: {tool_name}"
        }

    # ---------------------------------------------
    # INPUT GUARDRAIL
    # ---------------------------------------------
    validation = validate_action_input(
        action=tool_name,
        arguments=arguments
    )

    if not validation["valid"]:
        return {
            "status": "blocked",
            "stage": "input_guardrail",
            "tool": tool_name,
            "message": validation["message"]
        }

    validated_arguments = validation["arguments"]

    try:
        # ---------------------------------------------
        # TOOL EXECUTION
        # ---------------------------------------------
        result = TOOL_REGISTRY[tool_name]["function"](**validated_arguments)

        # ---------------------------------------------
        # OUTPUT GUARDRAIL
        # ---------------------------------------------
        output_validation = validate_tool_output(
            action=tool_name,
            result=result
        )

        if not output_validation["valid"]:
            return {
                "status": "blocked",
                "stage": "output_guardrail",
                "tool": tool_name,
                "message": output_validation["message"]
            }

        return result

    except Exception as e:
        return {
            "status": "error",
            "stage": "tool_execution",
            "tool": tool_name,
            "message": f"Tool execution failed: {str(e)}"
        }