from src.guardrails import (
    validate_action_input,
    validate_policy_action,
    classify_action,
    validate_tool_output,
)
from src.approval import evaluate_approval
from src.tools import execute_tool
from src.audit import log_interaction

def execute_guarded_action(
    action: str,
    arguments: dict,
    human_approved: bool | None = None,
    user_request: str = ""
) -> dict:
    """
    Execute an action through the complete Day 4 safety pipeline.
    """

    # --------------------------------------------------
    # 1. INPUT GUARDRAIL
    # --------------------------------------------------

    input_validation = validate_action_input(
        action=action,
        arguments=arguments
    )

    if not input_validation["valid"]:

        result = {
            "status": "blocked",
            "stage": "input_guardrail",
            "action": action,
            "message": input_validation["message"]
        }

        log_interaction({
            "user_request": user_request,
            "agents_invoked": [],
            "tools_called": [action],
            "retrieved_policies": [],
            "recommendation": arguments,
            "risk_level": "unknown",
            "approval_decision": "not_required",
            "final_action": "blocked",
            "execution_result": result
        })

        return result

    validated_arguments = input_validation["arguments"]

    # --------------------------------------------------
    # 2. POLICY GUARDRAIL
    # --------------------------------------------------

    policy_validation = validate_policy_action(
        action=action,
        arguments=validated_arguments
    )

    if not policy_validation["valid"]:

        result = {
            "status": "blocked",
            "stage": "policy_guardrail",
            "action": action,
            "message": policy_validation["message"]
        }

        log_interaction({
            "user_request": user_request,
            "agents_invoked": [],
            "tools_called": [action],
            "retrieved_policies": [action],
            "recommendation": validated_arguments,
            "risk_level": "unknown",
            "approval_decision": "not_required",
            "final_action": "blocked",
            "execution_result": result
        })

        return result

    # --------------------------------------------------
    # 3. RISK CLASSIFICATION
    # --------------------------------------------------

    risk_info = classify_action(
        action=action,
        new_multiplier=validated_arguments.get("new_multiplier")
    )

    if risk_info["status"] != "success":

        result = {
            "status": "error",
            "stage": "risk_classification",
            "action": action,
            "message": risk_info["message"]
        }

        log_interaction({
            "user_request": user_request,
            "agents_invoked": [],
            "tools_called": [action],
            "retrieved_policies": [],
            "recommendation": validated_arguments,
            "risk_level": "unknown",
            "approval_decision": "not_required",
            "final_action": "error",
            "execution_result": result
        })

        return result

    # --------------------------------------------------
    # 4. HUMAN APPROVAL
    # --------------------------------------------------

    approval = evaluate_approval(
        risk_info=risk_info,
        human_approved=human_approved
    )

    if approval["status"] in {"pending", "rejected"}:

        result = {
            "status": "blocked",
            "stage": "human_approval",
            "action": action,
            "risk_level": risk_info["risk_level"],
            "approval": approval,
            "message": approval["message"]
        }

        log_interaction({
            "user_request": user_request,
            "agents_invoked": [],
            "tools_called": [action],
            "retrieved_policies": [action],
            "recommendation": validated_arguments,
            "risk_level": risk_info["risk_level"],
            "approval_decision": approval["status"],
            "final_action": "blocked",
            "execution_result": result
        })

        return result

    # --------------------------------------------------
    # 5. EXECUTE TOOL
    # --------------------------------------------------

    execution_result = execute_tool(
        tool_name=action,
        arguments=validated_arguments
    )

    # --------------------------------------------------
    # 6. AUDIT SUCCESSFUL EXECUTION
    # --------------------------------------------------

    log_interaction({
        "user_request": user_request,
        "agents_invoked": [],
        "tools_called": [action],
        "retrieved_policies": [action],
        "recommendation": validated_arguments,
        "risk_level": risk_info["risk_level"],
        "approval_decision": approval["status"],
        "final_action": action,
        "execution_result": execution_result
    })

    return {
        "status": execution_result.get("status"),
        "action": action,
        "risk_level": risk_info["risk_level"],
        "approval": approval,
        "execution_result": execution_result
    }