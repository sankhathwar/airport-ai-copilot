from src.tools import get_airport_metrics
from src.rag import create_rag_answer
from src.memory import ConversationMemory


# ============================================================
# 1. OPERATIONS INVESTIGATOR
# ============================================================

class OperationsInvestigator:
    """
    Investigates airport operational conditions using
    airport telemetry data.
    """

    def __init__(self):
        self.name = "Operations Investigator"

    def investigate(self, airport_code: str) -> dict:

        metrics = get_airport_metrics(airport_code)

        if metrics["status"] != "success":

            return {
                "status": "error",
                "agent": self.name,
                "message": metrics["message"]
            }

        findings = []

        completion_rate = metrics["completion_rate"]
        average_eta = metrics["average_eta"]
        driver_cancellation_rate = metrics[
            "driver_cancellation_rate"
        ]
        queue_size = metrics["queue_size"]

        # Completion rate check
        if completion_rate < 0.85:

            findings.append(
                "Completion rate is below the expected "
                "85% threshold."
            )

        # Driver cancellation check
        if driver_cancellation_rate > 0.10:

            findings.append(
                "Driver cancellation rate is elevated."
            )

        # Queue check
        if queue_size > 200:

            findings.append(
                "Airport queue size is high."
            )

        # ETA check
        if average_eta > 10:

            findings.append(
                "Average ETA is elevated."
            )

        # Determine severity
        if not findings:

            severity = "low"
            issue = (
                "No major operational anomaly detected."
            )

        elif len(findings) >= 3:

            severity = "high"
            issue = (
                "Multiple operational indicators show stress."
            )

        else:

            severity = "medium"
            issue = (
                "Operational indicators show potential stress."
            )

        return {
            "status": "success",
            "agent": self.name,
            "airport_code": metrics["airport_code"],
            "severity": severity,
            "issue": issue,
            "findings": findings,
            "metrics": metrics
        }


# ============================================================
# 2. POLICY & COMPLIANCE AGENT
# ============================================================

class PolicyComplianceAgent:
    """
    Retrieves and evaluates airport policies using RAG.
    """

    def __init__(
        self,
        collection,
        embedding_model
    ):

        self.name = "Policy & Compliance Agent"

        self.collection = collection

        self.embedding_model = embedding_model

    def check_policy(
        self,
        query: str
    ) -> dict:

        if not query or not query.strip():

            return {
                "status": "error",
                "agent": self.name,
                "message": "Policy query is required."
            }

        try:

            rag_result = create_rag_answer(
                query=query,
                collection=self.collection,
                embedding_model=self.embedding_model
            )

            return {
                "status": "success",
                "agent": self.name,
                "query": query,
                "policy_result": rag_result.get(
                    "answer",
                    ""
                ),
                "retrieved_documents": rag_result.get(
                    "retrieved_documents",
                    []
                )
            }

        except Exception as e:

            return {
                "status": "error",
                "agent": self.name,
                "message": (
                    f"Policy check failed: {str(e)}"
                )
            }


# ============================================================
# 3. RESOLUTION AGENT
# ============================================================

class ResolutionAgent:
    """
    Generates operational recommendations based on
    investigation findings.
    """

    def __init__(self):

        self.name = "Resolution Agent"

    def recommend(
        self,
        investigation: dict
    ) -> dict:

        if not investigation:

            return {
                "status": "error",
                "agent": self.name,
                "message": (
                    "Investigation result is required."
                )
            }

        if investigation.get("status") != "success":

            return {
                "status": "error",
                "agent": self.name,
                "message": (
                    "Cannot generate recommendation "
                    "from failed investigation."
                )
            }

        severity = investigation["severity"]

        findings = investigation["findings"]

        airport_code = investigation["airport_code"]

        recommendations = []

        # Queue recommendation
        if "Airport queue size is high." in findings:

            recommendations.append(
                "Consider increasing driver availability "
                "through targeted incentives."
            )

        # Cancellation recommendation
        if "Driver cancellation rate is elevated." in findings:

            recommendations.append(
                "Investigate driver cancellation causes "
                "and consider targeted incentives."
            )

        # ETA recommendation
        if "Average ETA is elevated." in findings:

            recommendations.append(
                "Increase available driver capacity "
                "to reduce passenger wait times."
            )

        # Completion recommendation
        if (
            "Completion rate is below the expected "
            "85% threshold."
        ) in findings:

            recommendations.append(
                "Investigate supply-demand imbalance "
                "and operational bottlenecks."
            )

        # No issues
        if not recommendations:

            recommendations.append(
                "Continue monitoring airport operations."
            )

        return {
            "status": "success",
            "agent": self.name,
            "airport_code": airport_code,
            "severity": severity,
            "recommendations": recommendations
        }


# ============================================================
# 4. QUERY CLASSIFIER
# ============================================================

def classify_query(query: str) -> str:
    """
    Classify the user's request into one of three categories:

    - policy
    - operational
    - action
    """

    query_lower = query.lower()

    # --------------------------------------------------------
    # Action requests
    # --------------------------------------------------------

    action_keywords = [
        "increase",
        "decrease",
        "raise",
        "lower",
        "set",
        "change",
        "override",
        "execute",
        "trigger",
        "apply"
    ]

    # --------------------------------------------------------
    # Policy questions
    # --------------------------------------------------------

    policy_keywords = [
        "policy",
        "allowed",
        "maximum",
        "max",
        "limit",
        "permitted",
        "rule",
        "rules",
        "approval",
        "can drivers",
        "are drivers allowed",
        "what is the surge"
    ]

    # --------------------------------------------------------
    # Action has priority
    # --------------------------------------------------------

    if any(
        word in query_lower
        for word in action_keywords
    ):

        return "action"

    # --------------------------------------------------------
    # Policy
    # --------------------------------------------------------

    if any(
        word in query_lower
        for word in policy_keywords
    ):

        return "policy"

    # --------------------------------------------------------
    # Default
    # --------------------------------------------------------

    return "operational"


# ============================================================
# 5. ORCHESTRATOR AGENT
# ============================================================

class OrchestratorAgent:
    """
    Coordinates the airport operations agents using
    a controlled workflow based on query type.
    """

    def __init__(
        self,
        collection,
        embedding_model,
        max_iterations: int = 5,
        memory=None
    ):

        self.name = "Orchestrator Agent"

        self.investigator = OperationsInvestigator()

        self.policy_agent = PolicyComplianceAgent(
            collection=collection,
            embedding_model=embedding_model
        )

        self.resolution_agent = ResolutionAgent()

        self.max_iterations = max_iterations

        self.memory = memory or ConversationMemory(
            max_turns=5
        )

    # ========================================================
    # MAIN QUERY ENTRY POINT
    # ========================================================

    def run_query(
        self,
        user_query: str
    ) -> dict:
        """
        Accept a natural-language query, identify the airport,
        classify the query, and run the appropriate workflow.

        Query types:

        policy
            Policy and compliance questions.

        operational
            Questions about airport operational conditions.

        action
            Requests to change or execute an operational action.
        """

        # ----------------------------------------------------
        # 1. Validate query
        # ----------------------------------------------------

        if not user_query or not user_query.strip():

            return {
                "status": "error",
                "agent": self.name,
                "message": "User query is required."
            }

        query = user_query.strip()

        # ----------------------------------------------------
        # 2. Identify airport
        # ----------------------------------------------------

        airport_code = None

        for airport in ["SFO", "LAX", "JFK"]:

            if airport in query.upper():

                airport_code = airport
                break

        if not airport_code:

            return {
                "status": "error",
                "agent": self.name,
                "message": (
                    "Please specify a supported airport: "
                    "SFO, LAX, or JFK."
                )
            }

        # ----------------------------------------------------
        # 3. Classify query
        # ----------------------------------------------------

        query_type = classify_query(query)

        # ====================================================
        # POLICY QUERY
        # ====================================================

        if query_type == "policy":

            steps = [
                {
                    "iteration": 1,
                    "action": "PLAN",
                    "description": (
                        "Identify the request as a policy "
                        "question."
                    )
                },
                {
                    "iteration": 2,
                    "action": "CHECK_POLICY",
                    "description": (
                        "Retrieve and evaluate the applicable "
                        "airport policy."
                    )
                }
            ]

            # ----------------------------------------------
            # RAG / Policy Agent
            # ----------------------------------------------

            policy_result = (
                self.policy_agent.check_policy(query)
            )

            if policy_result["status"] != "success":

                return {
                    "status": "error",
                    "agent": self.name,
                    "stage": "policy",
                    "steps": steps,
                    "message": policy_result["message"]
                }

            # ----------------------------------------------
            # Memory
            # ----------------------------------------------

            self.memory.add_turn(
                user_message=query,
                assistant_message=(
                    policy_result["policy_result"]
                )
            )

            # ----------------------------------------------
            # Return
            # ----------------------------------------------

            return {
                "status": "success",
                "agent": self.name,
                "airport_code": airport_code,
                "query_type": "policy",
                "iterations": len(steps),
                "steps": steps,
                "investigation": None,
                "policy": policy_result,
                "resolution": None
            }

        # ====================================================
        # OPERATIONAL QUERY
        # ====================================================

        if query_type == "operational":

            steps = [
                {
                    "iteration": 1,
                    "action": "PLAN",
                    "description": (
                        "Identify the request as an "
                        "operational investigation."
                    )
                },
                {
                    "iteration": 2,
                    "action": "INVESTIGATE",
                    "description": (
                        f"Retrieve operational metrics "
                        f"for {airport_code}."
                    )
                },
                {
                    "iteration": 3,
                    "action": "GENERATE_RESOLUTION",
                    "description": (
                        "Generate possible operational "
                        "interventions."
                    )
                }
            ]

            # ----------------------------------------------
            # Investigation
            # ----------------------------------------------

            investigation = (
                self.investigator.investigate(
                    airport_code
                )
            )

            if investigation["status"] != "success":

                return {
                    "status": "error",
                    "agent": self.name,
                    "stage": "investigation",
                    "steps": steps,
                    "message": investigation["message"]
                }

            # ----------------------------------------------
            # Resolution
            # ----------------------------------------------

            resolution = (
                self.resolution_agent.recommend(
                    investigation
                )
            )

            if resolution["status"] != "success":

                return {
                    "status": "error",
                    "agent": self.name,
                    "stage": "resolution",
                    "steps": steps,
                    "message": resolution["message"]
                }

            # ----------------------------------------------
            # Memory
            # ----------------------------------------------

            self.memory.add_turn(
                user_message=query,
                assistant_message=str(resolution)
            )

            # ----------------------------------------------
            # Return
            # ----------------------------------------------

            return {
                "status": "success",
                "agent": self.name,
                "airport_code": airport_code,
                "query_type": "operational",
                "iterations": len(steps),
                "steps": steps,
                "investigation": investigation,
                "policy": None,
                "resolution": resolution
            }

        # ====================================================
        # ACTION QUERY
        # ====================================================

        if query_type == "action":

            steps = [
                {
                    "iteration": 1,
                    "action": "PLAN",
                    "description": (
                        "Identify the request as an "
                        "operational action."
                    )
                },
                {
                    "iteration": 2,
                    "action": "INVESTIGATE",
                    "description": (
                        f"Retrieve operational metrics "
                        f"for {airport_code}."
                    )
                },
                {
                    "iteration": 3,
                    "action": "CHECK_POLICY",
                    "description": (
                        "Retrieve and evaluate the applicable "
                        "airport policy."
                    )
                },
                {
                    "iteration": 4,
                    "action": "GENERATE_RESOLUTION",
                    "description": (
                        "Evaluate the proposed operational "
                        "intervention."
                    )
                }
            ]

            # ----------------------------------------------
            # Investigation
            # ----------------------------------------------

            investigation = (
                self.investigator.investigate(
                    airport_code
                )
            )

            if investigation["status"] != "success":

                return {
                    "status": "error",
                    "agent": self.name,
                    "stage": "investigation",
                    "steps": steps,
                    "message": investigation["message"]
                }

            # ----------------------------------------------
            # Policy
            # ----------------------------------------------

            policy_result = (
                self.policy_agent.check_policy(
                    query
                )
            )

            if policy_result["status"] != "success":

                return {
                    "status": "error",
                    "agent": self.name,
                    "stage": "policy",
                    "steps": steps,
                    "message": policy_result["message"]
                }

            # ----------------------------------------------
            # Resolution
            # ----------------------------------------------

            resolution = (
                self.resolution_agent.recommend(
                    investigation
                )
            )

            if resolution["status"] != "success":

                return {
                    "status": "error",
                    "agent": self.name,
                    "stage": "resolution",
                    "steps": steps,
                    "message": resolution["message"]
                }

            # ----------------------------------------------
            # Return
            # ----------------------------------------------

            return {
                "status": "success",
                "agent": self.name,
                "airport_code": airport_code,
                "query_type": "action",
                "iterations": len(steps),
                "steps": steps,
                "investigation": investigation,
                "policy": policy_result,
                "resolution": resolution
            }

        # ====================================================
        # FALLBACK
        # ====================================================

        return {
            "status": "error",
            "agent": self.name,
            "message": (
                "Unable to classify the user request."
            )
        }