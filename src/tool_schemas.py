"""
Gemini tool schemas for the Airport Operations AI Copilot.

These schemas describe the available Python tools to Gemini.
They do not execute the tools themselves.
"""

TOOL_SCHEMAS = [
    {
        "name": "get_airport_metrics",
        "description": (
            "Retrieve the latest operational metrics for an airport. "
            "Use this when the user asks about current airport "
            "operational conditions or metrics."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "airport_code": {
                    "type": "string",
                    "description": (
                        "Airport code. Supported airports are "
                        "SFO, LAX, and JFK."
                    )
                }
            },
            "required": ["airport_code"]
        }
    },

    {
        "name": "calculate_driver_incentive",
        "description": (
            "Calculate the recommended driver incentive and "
            "estimated total cost based on driver count and "
            "operational severity."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "driver_count": {
                    "type": "integer",
                    "description": (
                        "Number of drivers receiving the incentive."
                    )
                },
                "severity_level": {
                    "type": "string",
                    "description": (
                        "Operational severity level: "
                        "low, medium, or high."
                    )
                }
            },
            "required": [
                "driver_count",
                "severity_level"
            ]
        }
    },

    {
        "name": "trigger_surge_override",
        "description": (
            "Mock execution tool that simulates changing "
            "the surge multiplier at an airport. "
            "This is a simulated action and does not change "
            "a real pricing system."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "airport_code": {
                    "type": "string",
                    "description": (
                        "Airport code. Supported airports are "
                        "SFO, LAX, and JFK."
                    )
                },
                "new_multiplier": {
                    "type": "number",
                    "description": (
                        "New surge multiplier, such as 1.2 or 1.4."
                    )
                },
                "reason": {
                    "type": "string",
                    "description": (
                        "Operational reason for the requested "
                        "surge override."
                    )
                }
            },
            "required": [
                "airport_code",
                "new_multiplier",
                "reason"
            ]
        }
    }
]