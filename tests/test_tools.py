from src.tools import (
    get_airport_metrics,
    calculate_driver_incentive,
    trigger_surge_override,
    execute_tool,
)


def test_get_airport_metrics_valid_airport():
    result = get_airport_metrics("SFO")

    assert result["status"] == "success"
    assert result["airport_code"] == "SFO"
    assert result["timestamp"] == "2026-09-15 16:00:00"


def test_get_airport_metrics_invalid_airport():
    result = get_airport_metrics("ABC")

    assert result["status"] == "error"
    assert "Invalid airport code" in result["message"]


def test_calculate_driver_incentive():
    result = calculate_driver_incentive(100, "high")

    assert result["status"] == "success"
    assert result["recommended_incentive_per_driver"] == 35
    assert result["estimated_total_cost"] == 3500


def test_calculate_driver_incentive_invalid_severity():
    result = calculate_driver_incentive(100, "critical")

    assert result["status"] == "error"
    assert "Invalid severity level" in result["message"]


def test_trigger_surge_override():
    result = trigger_surge_override(
        "SFO",
        1.4,
        "High queue size"
    )

    assert result["status"] == "success"
    assert result["airport_code"] == "SFO"
    assert result["new_multiplier"] == 1.4
    assert result["execution_mode"] == "mock"


def test_trigger_surge_override_invalid_multiplier():
    result = trigger_surge_override(
        "SFO",
        0.8,
        "Testing"
    )

    assert result["status"] == "error"
    assert "cannot be less than 1.0" in result["message"]


def test_execute_tool():
    result = execute_tool(
        "get_airport_metrics",
        {"airport_code": "JFK"}
    )

    assert result["status"] == "success"
    assert result["airport_code"] == "JFK"


def test_execute_tool_unknown_tool():
    result = execute_tool(
        "unknown_tool",
        {}
    )

    assert result["status"] == "error"
    assert "Unknown tool" in result["message"]


def test_execute_tool_missing_arguments():
    result = execute_tool(
        "get_airport_metrics",
        None
    )

    assert result["status"] == "error"
    assert "arguments are required" in result["message"]