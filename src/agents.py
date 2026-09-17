from src.tools import get_airport_metrics
from src.rag import create_rag_answer
from src.memory import ConversationMemory

class OperationsInvestigator:
    """
    Investigates airport operational conditions using telemetry tools.
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
        driver_cancellation_rate = metrics["driver_cancellation_rate"]
        queue_size = metrics["queue_size"]

        if completion_rate < 0.85:
            findings.append(
                "Completion rate is below the expected 85% threshold."
            )

        if driver_cancellation_rate > 0.10:
            findings.append(
                "Driver cancellation rate is elevated."
            )

        if queue_size > 200:
            findings.append(
                "Airport queue size is high."
            )

        if average_eta > 10:
            findings.append(
                "Average ETA is elevated."
            )

        if not findings:
            severity = "low"
            issue = "No major operational anomaly detected."
        elif len(findings) >= 3:
            severity = "high"
            issue = "Multiple operational indicators show stress."
        else:
            severity = "medium"
            issue = "Operational indicators show potential stress."

        return {
            "status": "success",
            "agent": self.name,
            "airport_code": metrics["airport_code"],
            "severity": severity,
            "issue": issue,
            "findings": findings,
            "metrics": metrics
        }




class PolicyComplianceAgent:
    """
    Searches the policy knowledge base and evaluates
    policy-related questions.
    """

    def __init__(self, collection, embedding_model):
        self.name = "Policy & Compliance Agent"
        self.collection = collection
        self.embedding_model = embedding_model

    def check_policy(self, query: str) -> dict:

        if not query or not query.strip():
            return {
                "status": "error",
                "agent": self.name,
                "message": "Policy query is required."
            }

        try:
            answer = create_rag_answer(
                query=query,
                collection=self.collection,
                embedding_model=self.embedding_model
            )

            return {
                "status": "success",
                "agent": self.name,
                "query": query,
                "policy_result": answer
            }

        except Exception as e:
            return {
                "status": "error",
                "agent": self.name,
                "message": f"Policy check failed: {str(e)}"
            }


class ResolutionAgent:
    """
    Generates operational recommendations based on
    investigation findings.
    """

    def __init__(self):
        self.name = "Resolution Agent"

    def recommend(self, investigation: dict) -> dict:

        if not investigation:
            return {
                "status": "error",
                "agent": self.name,
                "message": "Investigation result is required."
            }

        if investigation.get("status") != "success":
            return {
                "status": "error",
                "agent": self.name,
                "message": "Cannot generate recommendation from failed investigation."
            }

        severity = investigation["severity"]
        findings = investigation["findings"]
        airport_code = investigation["airport_code"]

        recommendations = []

        if "Airport queue size is high." in findings:
            recommendations.append(
                "Consider increasing driver availability through targeted incentives."
            )

        if "Driver cancellation rate is elevated." in findings:
            recommendations.append(
                "Investigate driver cancellation causes and consider targeted incentives."
            )

        if "Average ETA is elevated." in findings:
            recommendations.append(
                "Increase available driver capacity to reduce passenger wait times."
            )

        if "Completion rate is below the expected 85% threshold." in findings:
            recommendations.append(
                "Investigate supply-demand imbalance and operational bottlenecks."
            )

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

class OrchestratorAgent:
    """
    Coordinates the airport operations agents
    using a controlled ReAct-style workflow.
    """

    def __init__(self, collection, embedding_model, max_iterations: int = 5,memory=None):
        self.name = "Orchestrator Agent"

        self.investigator = OperationsInvestigator()

        self.policy_agent = PolicyComplianceAgent(
            collection=collection,
            embedding_model=embedding_model
        )

        self.resolution_agent = ResolutionAgent()

        self.max_iterations = max_iterations

        self.memory = memory or ConversationMemory(max_turns=5)

    def run(self, airport_code: str = None, policy_query: str = "") -> dict:
        if not airport_code:
            history = self.memory.get_history()

            if history:
                last_user_message = history[-1]["user"]

                for airport in ["SFO", "LAX", "JFK"]:
                    if airport in last_user_message.upper():
                        airport_code = airport
                        break

        if not airport_code:
            return {
            "status": "error",
            "agent": self.name,
            "message": "Airport code could not be determined."
        }


        steps = []
        iteration = 0

        # -----------------------------
        # STEP 1: PLAN
        # -----------------------------

        iteration += 1

        steps.append({
            "iteration": iteration,
            "action": "PLAN",
            "description": (
                "Determine operational condition, "
                "check applicable policy, and generate resolution."
            )
        })

        # -----------------------------
        # STEP 2: INVESTIGATE
        # -----------------------------

        if iteration >= self.max_iterations:
            return {
                "status": "error",
                "message": "Maximum iterations reached."
            }

        iteration += 1

        steps.append({
            "iteration": iteration,
            "action": "INVESTIGATE",
            "description": f"Retrieve operational metrics for {airport_code}."
        })

        investigation = self.investigator.investigate(airport_code)

        if investigation["status"] != "success":
            return {
                "status": "error",
                "agent": self.name,
                "stage": "investigation",
                "steps": steps,
                "message": investigation["message"]
            }

        # -----------------------------
        # STEP 3: POLICY CHECK
        # -----------------------------

        if iteration >= self.max_iterations:
            return {
                "status": "error",
                "message": "Maximum iterations reached."
            }

        iteration += 1

        steps.append({
            "iteration": iteration,
            "action": "CHECK_POLICY",
            "description": "Retrieve and evaluate the applicable airport policy."
        })

        policy_result = self.policy_agent.check_policy(policy_query)

        if policy_result["status"] != "success":
            return {
                "status": "error",
                "agent": self.name,
                "stage": "policy",
                "steps": steps,
                "message": policy_result["message"]
            }

        # -----------------------------
        # STEP 4: RESOLUTION
        # -----------------------------

        if iteration >= self.max_iterations:
            return {
                "status": "error",
                "message": "Maximum iterations reached."
            }

        iteration += 1

        steps.append({
            "iteration": iteration,
            "action": "GENERATE_RESOLUTION",
            "description": "Generate possible operational interventions."
        })

        resolution = self.resolution_agent.recommend(
            investigation
        )

        if resolution["status"] != "success":
            return {
                "status": "error",
                "agent": self.name,
                "stage": "resolution",
                "steps": steps,
                "message": resolution["message"]
            }

        # -----------------------------
        # STEP 5: COMPLETE
        # -----------------------------

        iteration += 1

        steps.append({
            "iteration": iteration,
            "action": "COMPLETE",
            "description": "Investigation, policy check, and resolution completed."
        })

        self.memory.add_turn(
            user_message=policy_query,
            assistant_message=str(resolution)
            )

        return {
            "status": "success",
            "agent": self.name,
            "airport_code": airport_code,
            "iterations": iteration,
            "steps": steps,
            "investigation": investigation,
            "policy": policy_result,
            "resolution": resolution
        }

    def run_query(self, user_query: str) -> dict:
        """
        Accept a natural-language operational query,identify the airport, and run the agent workflow.
        """

        if not user_query or not user_query.strip():
            return {
            "status": "error",
            "agent": self.name,
            "message": "User query is required."
        }

        query = user_query.strip()

        # Identify airport from the user's query
        airport_code = None

        for airport in ["SFO", "LAX", "JFK"]:
            if airport in query.upper():
                airport_code = airport
                break

        if not airport_code:
            return {
            "status": "error",
            "agent": self.name,
            "message": "Please specify a supported airport: SFO, LAX, or JFK."
            }

        # Use the complete user query as the policy question
        result = self.run(
            airport_code=airport_code,
            policy_query=query
        )

        return result

