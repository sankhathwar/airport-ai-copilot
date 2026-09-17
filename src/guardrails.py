from typing import Any

VALID_AIRPORTS = {"SFO", "LAX", "JFK"}

MAX_SURGE_BY_AIRPORT = {
    "SFO": 1.5,
    "LAX": 1.4,
    "JFK": 1.6,
}

VALID_SEVERITY_LEVELS = {"low", "medium", "high"}

# Project assumptions.
# These thresholds are synthetic and are used only for this project.
INCENTIVE_HIGH_RISK_THRESHOLD = 3000


ACTION_RISK_LEVELS = {
    "get_airport_metrics": {
        "risk_level": "low",
        "approval_required": False,
    },
    "search_policy": {
        "risk_level": "low",
        "approval_required": False,
    },
    "calculate_driver_incentive": {
        "risk_level": "medium",
        "approval_required": False,
    },
    "trigger_surge_override": {
        "risk_level": "high",
        "approval_required": True,
    },
}


def validate_airport_code(airport_code: str) -> dict:
    """Validate airport code."""

    if not airport_code:
        return {
            "valid": False,
            "message": "Airport code is required."
        }

    airport_code = airport_code.strip().upper()

    if airport_code not in VALID_AIRPORTS:
        return {
            "valid": False,
            "message": (
                f"Invalid airport code: {airport_code}. "
                "Valid airports are SFO, LAX, and JFK."
            )
        }

    return {
        "valid": True,
        "airport_code": airport_code
    }


def validate_surge_multiplier(new_multiplier: float) -> dict:
    """Validate surge multiplier."""

    if new_multiplier is None:
        return {
            "valid": False,
            "message": "Surge multiplier is required."
        }

    if not isinstance(new_multiplier, (int, float)):
        return {
            "valid": False,
            "message": "Surge multiplier must be a number."
        }

    if new_multiplier < 1.0:
        return {
            "valid": False,
            "message": "Surge multiplier cannot be less than 1.0x."
        }

    if new_multiplier > 2.0:
        return {
            "valid": False,
            "message": "Surge multiplier cannot exceed the project safety limit of 2.0x."
        }

    return {
        "valid": True,
        "new_multiplier": float(new_multiplier)
    }


def validate_driver_count(driver_count: int) -> dict:
    """Validate driver count."""

    if driver_count is None:
        return {
            "valid": False,
            "message": "Driver count is required."
        }

    if not isinstance(driver_count, int):
        return {
            "valid": False,
            "message": "Driver count must be an integer."
        }

    if driver_count <= 0:
        return {
            "valid": False,
            "message": "Driver count must be greater than 0."
        }

    return {
        "valid": True,
        "driver_count": driver_count
    }


def validate_severity_level(severity_level: str) -> dict:
    """Validate operational severity."""

    if not severity_level:
        return {
            "valid": False,
            "message": "Severity level is required."
        }

    severity_level = severity_level.strip().lower()

    if severity_level not in VALID_SEVERITY_LEVELS:
        return {
            "valid": False,
            "message": (
                "Invalid severity level. "
                "Valid levels are low, medium, and high."
            )
        }

    return {
        "valid": True,
        "severity_level": severity_level
    }


def classify_action(
    action: str,
    new_multiplier: float = None,
    incentive_amount: float = None
) -> dict:
    """
    Classify an action according to project risk assumptions.
    """

    if action not in ACTION_RISK_LEVELS:
        return {
            "status": "error",
            "message": f"Unknown action: {action}"
        }

    risk = ACTION_RISK_LEVELS[action]

    risk_level = risk["risk_level"]
    approval_required = risk["approval_required"]

    # Surge >= 1.3x is explicitly treated as high risk.
    if action == "trigger_surge_override" and new_multiplier is not None:
        if new_multiplier >= 1.3:
            risk_level = "high"
            approval_required = True
        else:
            risk_level = "medium"
            approval_required = True

    # Incentive above the project threshold is high risk.
    if (
        action == "calculate_driver_incentive"
        and incentive_amount is not None
    ):
        if incentive_amount > INCENTIVE_HIGH_RISK_THRESHOLD:
            risk_level = "high"
            approval_required = True

    return {
        "status": "success",
        "action": action,
        "risk_level": risk_level,
        "approval_required": approval_required
    }

def validate_required_text(value: str, field_name: str) -> dict:
    """Validate that a required text field is present and non-empty."""
    if value is None:
        return {
            "valid": False,
            "message": f"{field_name} is required."
        }

    if not isinstance(value, str):
        return {
            "valid": False,
            "message": f"{field_name} must be a string."
        }

    if not value.strip():
        return {
            "valid": False,
            "message": f"{field_name} cannot be empty."
        }

    return {
        "valid": True,
        field_name: value.strip()
    }


def validate_action_input(action: str, arguments: dict) -> dict:
    """
    Validate tool inputs before the tool is executed.
    """

    if action not in ACTION_RISK_LEVELS:
        return {
            "valid": False,
            "message": f"Unknown action: {action}"
        }

    if not isinstance(arguments, dict):
        return {
            "valid": False,
            "message": "Tool arguments must be provided as a dictionary."
        }

    # --------------------------------------------------
    # Tool 1: Get airport metrics
    # --------------------------------------------------
    if action == "get_airport_metrics":

        airport_result = validate_airport_code(
            arguments.get("airport_code")
        )

        if not airport_result["valid"]:
            return airport_result

        return {
            "valid": True,
            "arguments": {
                "airport_code": airport_result["airport_code"]
            }
        }

    # --------------------------------------------------
    # Tool 2: Calculate driver incentive
    # --------------------------------------------------
    if action == "calculate_driver_incentive":

        driver_result = validate_driver_count(
            arguments.get("driver_count")
        )

        if not driver_result["valid"]:
            return driver_result

        severity_result = validate_severity_level(
            arguments.get("severity_level")
        )

        if not severity_result["valid"]:
            return severity_result

        return {
            "valid": True,
            "arguments": {
                "driver_count": driver_result["driver_count"],
                "severity_level": severity_result["severity_level"]
            }
        }

    # --------------------------------------------------
    # Tool 3: Trigger surge override
    # --------------------------------------------------
    if action == "trigger_surge_override":

        airport_result = validate_airport_code(
            arguments.get("airport_code")
        )

        if not airport_result["valid"]:
            return airport_result

        surge_result = validate_surge_multiplier(
            arguments.get("new_multiplier")
        )

        if not surge_result["valid"]:
            return surge_result

        reason_result = validate_required_text(
            arguments.get("reason"),
            "reason"
        )

        if not reason_result["valid"]:
            return reason_result

        return {
            "valid": True,
            "arguments": {
                "airport_code": airport_result["airport_code"],
                "new_multiplier": surge_result["new_multiplier"],
                "reason": reason_result["reason"]
            }
        }

    return {
        "valid": False,
        "message": f"No validation rule defined for action: {action}"
    }


def validate_tool_output(action: str, result: dict) -> dict:
    """
    Validate the structure and basic values of a tool response
    before it is passed to the agent.
    """

    if not isinstance(result, dict):
        return {
            "valid": False,
            "message": "Tool output must be a dictionary."
        }

    if result.get("status") != "success":
        return {
            "valid": False,
            "message": "Tool did not return a successful result."
        }

    # --------------------------------------------------
    # Tool 1: Get airport metrics
    # --------------------------------------------------
    if action == "get_airport_metrics":

        required_fields = [
            "airport_code",
            "completion_rate",
            "average_eta",
            "active_drivers",
            "driver_cancellation_rate",
            "queue_size",
            "surge_multiplier",
            "request_volume",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in result
        ]

        if missing_fields:
            return {
                "valid": False,
                "message": f"Missing fields in tool output: {missing_fields}"
            }

        if result["airport_code"] not in VALID_AIRPORTS:
            return {
                "valid": False,
                "message": "Tool returned an invalid airport code."
            }

        numeric_fields = [
            "completion_rate",
            "average_eta",
            "active_drivers",
            "driver_cancellation_rate",
            "queue_size",
            "surge_multiplier",
            "request_volume",
        ]

        for field in numeric_fields:
            if not isinstance(result[field], (int, float)):
                return {
                    "valid": False,
                    "message": f"{field} must be numeric."
                }

        if result["completion_rate"] < 0 or result["completion_rate"] > 1:
            return {
                "valid": False,
                "message": "Completion rate must be between 0 and 1."
            }

        if result["driver_cancellation_rate"] < 0 or result["driver_cancellation_rate"] > 1:
            return {
                "valid": False,
                "message": "Driver cancellation rate must be between 0 and 1."
            }

        if result["average_eta"] < 0:
            return {
                "valid": False,
                "message": "Average ETA cannot be negative."
            }

        if result["active_drivers"] < 0:
            return {
                "valid": False,
                "message": "Active drivers cannot be negative."
            }

        if result["queue_size"] < 0:
            return {
                "valid": False,
                "message": "Queue size cannot be negative."
            }

        return {
            "valid": True,
            "message": "Tool output passed validation."
        }

    # --------------------------------------------------
    # Tool 2: Calculate driver incentive
    # --------------------------------------------------
    if action == "calculate_driver_incentive":

        required_fields = [
            "driver_count",
            "severity_level",
            "recommended_incentive_per_driver",
            "estimated_total_cost",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in result
        ]

        if missing_fields:
            return {
                "valid": False,
                "message": f"Missing fields in tool output: {missing_fields}"
            }

        if result["driver_count"] <= 0:
            return {
                "valid": False,
                "message": "Driver count must be greater than 0."
            }

        if result["recommended_incentive_per_driver"] < 0:
            return {
                "valid": False,
                "message": "Recommended incentive cannot be negative."
            }

        if result["estimated_total_cost"] < 0:
            return {
                "valid": False,
                "message": "Estimated total cost cannot be negative."
            }

        return {
            "valid": True,
            "message": "Tool output passed validation."
        }

    # --------------------------------------------------
    # Tool 3: Trigger surge override
    # --------------------------------------------------
    if action == "trigger_surge_override":

        required_fields = [
            "airport_code",
            "new_multiplier",
            "reason",
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in result
        ]

        if missing_fields:
            return {
                "valid": False,
                "message": f"Missing fields in tool output: {missing_fields}"
            }

        if result["airport_code"] not in VALID_AIRPORTS:
            return {
                "valid": False,
                "message": "Tool returned an invalid airport code."
            }

        if result["new_multiplier"] < 1.0:
            return {
                "valid": False,
                "message": "Returned surge multiplier cannot be less than 1.0x."
            }

        if result["new_multiplier"] > 2.0:
            return {
                "valid": False,
                "message": "Returned surge multiplier exceeds safety limit."
            }

        if not isinstance(result["reason"], str) or not result["reason"].strip():
            return {
                "valid": False,
                "message": "Tool must return a valid reason."
            }

        return {
            "valid": True,
            "message": "Tool output passed validation."
        }

    return {
        "valid": False,
        "message": f"No output validation rule defined for action: {action}"
    }

def validate_policy_action(action: str, arguments: dict) -> dict:
    """
    Validate whether a proposed action complies with
    the synthetic airport policy limits.
    """

    if action != "trigger_surge_override":
        return {
            "valid": True,
            "message": "No policy restriction defined for this action."
        }

    airport_code = arguments.get("airport_code")
    new_multiplier = arguments.get("new_multiplier")

    if airport_code not in MAX_SURGE_BY_AIRPORT:
        return {
            "valid": False,
            "message": f"No surge policy found for airport: {airport_code}"
        }

    max_allowed = MAX_SURGE_BY_AIRPORT[airport_code]

    if new_multiplier > max_allowed:
        return {
            "valid": False,
            "policy_violation": True,
            "message": (
                f"Policy violation: {airport_code} maximum surge is "
                f"{max_allowed}x, but {new_multiplier}x was requested."
            )
        }

    return {
        "valid": True,
        "policy_violation": False,
        "message": (
            f"Requested surge of {new_multiplier}x is within the "
            f"{airport_code} policy limit of {max_allowed}x."
        )
    }