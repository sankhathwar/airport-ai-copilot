def evaluate_approval(
    risk_info: dict,
    human_approved: bool | None = None
) -> dict:
    """
    Determine whether an action can proceed based on
    its risk level and human approval.
    """

    if not risk_info or risk_info.get("status") != "success":
        return {
            "status": "error",
            "message": "Valid risk information is required."
        }

    approval_required = risk_info.get("approval_required", False)
    risk_level = risk_info.get("risk_level", "unknown")

    # Low/medium action where approval is not required
    if not approval_required:
        return {
            "status": "not_required",
            "approved": True,
            "risk_level": risk_level,
            "message": "Human approval is not required."
        }

    # High-risk action but no decision has been provided
    if human_approved is None:
        return {
            "status": "pending",
            "approved": False,
            "risk_level": risk_level,
            "message": "Human approval is required before execution."
        }

    # Human explicitly approved
    if human_approved is True:
        return {
            "status": "approved",
            "approved": True,
            "risk_level": risk_level,
            "message": "Human approval received. Action may proceed."
        }

    # Human explicitly rejected
    return {
        "status": "rejected",
        "approved": False,
        "risk_level": risk_level,
        "message": "Human approval rejected. Action must not execute."
    }