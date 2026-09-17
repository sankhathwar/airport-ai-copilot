import re

import streamlit as st
import chromadb

from sentence_transformers import SentenceTransformer

from src.config import (
    SUPPORTED_AIRPORTS,
    METRICS_FILE,
    CHROMA_DIR,
)

from src.data_preprocessing import load_airport_metrics
from src.agents import OrchestratorAgent
from src.memory import ConversationMemory
from src.action_controller import execute_guarded_action


# =========================================================
# SURGE ACTION EXTRACTION
# =========================================================

def extract_surge_action(
    user_query: str,
    airport_code: str
):
    """
    Detect a user request to increase/set/override surge
    and extract the requested multiplier.
    """

    query = user_query.lower()

    surge_requested = (
        "surge" in query
        and any(
            keyword in query
            for keyword in [
                "increase",
                "raise",
                "set",
                "override"
            ]
        )
    )

    if not surge_requested:
        return None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*x",
        query
    )

    if not match:
        return None

    new_multiplier = float(
        match.group(1)
    )

    return {
        "action": "trigger_surge_override",
        "arguments": {
            "airport_code": airport_code,
            "new_multiplier": new_multiplier,
            "reason": user_query
        }
    }


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Airport Operations AI Copilot",
    page_icon="✈️",
    layout="wide",
)


# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "approval_pending" not in st.session_state:
    st.session_state.approval_pending = None

if "last_result" not in st.session_state:
    st.session_state.last_result = None

if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = None

if "execution_result" not in st.session_state:
    st.session_state.execution_result = None


# =========================================================
# LOAD RAG COMPONENTS
# =========================================================

@st.cache_resource
def load_rag_components():
    """
    Load ChromaDB collection and embedding model once.
    Streamlit reuses these resources across reruns.
    """

    client = chromadb.PersistentClient(
        path=str(CHROMA_DIR)
    )

    collection = client.get_collection(
        name="airport_policies"
    )

    embedding_model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    return collection, embedding_model


# Load RAG resources
collection, embedding_model = load_rag_components()


# =========================================================
# CREATE ORCHESTRATOR
# =========================================================

if st.session_state.orchestrator is None:

    st.session_state.orchestrator = OrchestratorAgent(
        collection=collection,
        embedding_model=embedding_model,
        max_iterations=5,
        memory=ConversationMemory(
            max_turns=5
        ),
    )


orchestrator = st.session_state.orchestrator


# =========================================================
# LOAD OPERATIONAL DATA
# =========================================================

metrics_df = load_airport_metrics(
    str(METRICS_FILE)
)


# =========================================================
# TITLE
# =========================================================

st.title("✈️ Airport Operations AI Copilot")

st.markdown(
    """
    Analyze airport operations, investigate anomalies,
    retrieve applicable policies, and generate operational
    recommendations.
    """
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("✈️ Airport Selection")

airport_code = st.sidebar.selectbox(
    "Select Airport",
    SUPPORTED_AIRPORTS,
)


# Get latest metrics for selected airport
airport_metrics = (
    metrics_df[
        metrics_df["airport_code"] == airport_code
    ]
    .sort_values("timestamp")
    .iloc[-1]
)


st.sidebar.markdown("---")

st.sidebar.write(
    f"**Selected Airport:** {airport_code}"
)


# =========================================================
# CLEAR CONVERSATION
# =========================================================

if st.sidebar.button("Clear Conversation"):

    st.session_state.messages = []
    st.session_state.last_result = None
    st.session_state.approval_pending = None
    st.session_state.execution_result = None

    orchestrator.memory.clear()

    st.rerun()


# =========================================================
# OPERATIONAL METRICS
# =========================================================

st.subheader("📊 Operational Metrics")

col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.metric(
        "Completion Rate",
        f"{airport_metrics['completion_rate']:.0%}",
    )


with col2:

    st.metric(
        "Average ETA",
        f"{airport_metrics['average_eta']:.1f} min",
    )


with col3:

    st.metric(
        "Driver Cancellation",
        f"{airport_metrics['driver_cancellation_rate']:.0%}",
    )


with col4:

    st.metric(
        "Queue Size",
        int(airport_metrics["queue_size"]),
    )


with col5:

    st.metric(
        "Surge",
        f"{airport_metrics['surge_multiplier']:.1f}x",
    )


# =========================================================
# CHAT INTERFACE
# =========================================================

st.subheader("💬 Ask the AI Copilot")


# Display previous conversation
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.write(message["content"])


# Chat input
user_query = st.chat_input(
    "Ask about airport operations..."
)


# =========================================================
# PROCESS USER QUERY
# =========================================================

if user_query:

    # -----------------------------------------------------
    # Store user message
    # -----------------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_query,
        }
    )


    # -----------------------------------------------------
    # Display user message
    # -----------------------------------------------------

    with st.chat_message("user"):

        st.write(user_query)


    # -----------------------------------------------------
    # Run orchestrator
    # -----------------------------------------------------

    with st.chat_message("assistant"):

        with st.spinner(
            "Processing your request..."
        ):

            result = orchestrator.run_query(
                user_query
            )


        # Store result
        st.session_state.last_result = result


        # -------------------------------------------------
        # Detect possible surge action
        # -------------------------------------------------

        surge_action = extract_surge_action(
            user_query=user_query,
            airport_code=airport_code
        )


        if (
            result.get("status") == "success"
            and result.get("query_type") == "action"
            and surge_action is not None
        ):

            st.session_state.approval_pending = {
                "action": surge_action["action"],
                "arguments": surge_action["arguments"],
                "user_request": user_query
            }


        # -------------------------------------------------
        # Handle error
        # -------------------------------------------------

        if result["status"] != "success":

            error_message = result.get(
                "message",
                "Unable to process the request.",
            )

            st.error(error_message)

            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": error_message,
                }
            )


        # -------------------------------------------------
        # Handle successful result
        # -------------------------------------------------

        else:

            query_type = result.get(
                "query_type"
            )


            # =============================================
            # POLICY RESPONSE
            # =============================================

            if query_type == "policy":

                policy = result.get(
                    "policy"
                )

                if policy:

                    assistant_answer = policy.get(
                        "policy_result",
                        "Policy information was retrieved."
                    )

                else:

                    assistant_answer = (
                        "Policy information was retrieved."
                    )


                st.write(assistant_answer)


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_answer,
                    }
                )


            # =============================================
            # OPERATIONAL RESPONSE
            # =============================================

            elif query_type == "operational":

                investigation = result.get(
                    "investigation"
                )

                if investigation:

                    assistant_summary = (
                        f"Investigation completed for "
                        f"{result['airport_code']}. "
                        f"Severity: "
                        f"{investigation['severity'].upper()}."
                    )

                else:

                    assistant_summary = (
                        "Operational investigation completed."
                    )


                st.write(assistant_summary)


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": assistant_summary,
                    }
                )


            # =============================================
            # ACTION RESPONSE
            # =============================================

            elif query_type == "action":

                policy = result.get(
                    "policy"
                )

                if policy:

                    action_message = (
                        "I evaluated the requested action "
                        "against the applicable airport policy."
                    )

                else:

                    action_message = (
                        "The requested operational action "
                        "has been evaluated."
                    )


                st.write(action_message)


                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": action_message,
                    }
                )


# =========================================================
# SHOW RESULTS FROM LAST QUERY
# =========================================================

result = st.session_state.last_result


if result and result.get("status") == "success":

    query_type = result.get(
        "query_type"
    )

    investigation = result.get(
        "investigation"
    )

    policy = result.get(
        "policy"
    )

    resolution = result.get(
        "resolution"
    )


    # =====================================================
    # AGENT ACTIVITY
    # =====================================================

    st.subheader("🤖 Agent Activity")


    for step in result.get("steps", []):

        action = step["action"]
        description = step["description"]


        if action == "PLAN":

            st.write(
                f"🧠 **Orchestrator** — {description}"
            )


        elif action == "INVESTIGATE":

            st.write(
                f"🔎 **Operations Investigator** — "
                f"{description}"
            )


        elif action == "CHECK_POLICY":

            st.write(
                f"📚 **Policy Agent** — {description}"
            )


        elif action == "GENERATE_RESOLUTION":

            st.write(
                f"💡 **Resolution Agent** — "
                f"{description}"
            )


        elif action == "COMPLETE":

            st.write(
                f"✅ **Orchestrator** — {description}"
            )


        else:

            st.write(
                f"• **{action}** — {description}"
            )


    # =====================================================
    # POLICY QUERY DISPLAY
    # =====================================================

    if query_type == "policy":

        # -------------------------------------------------
        # Actual Answer
        # -------------------------------------------------

        st.subheader("💬 Answer")


        if policy:

            st.write(
                policy.get(
                    "policy_result",
                    "No policy response available."
                )
            )

        else:

            st.info(
                "No policy response available."
            )


        # -------------------------------------------------
        # RAG TRACE
        # -------------------------------------------------

        st.subheader("📚 RAG Trace")


        with st.expander(
            "View Retrieved Policy Information"
        ):

            if policy:

                # Policy Agent Query
                st.write(
                    "**Policy Agent Query:**"
                )

                st.code(
                    policy.get(
                        "query",
                        ""
                    )
                )


                # -------------------------------------------------
                # IMPORTANT:
                # Do NOT display policy_result here.
                # The actual answer is already shown above.
                # RAG Trace should only show retrieval evidence.
                # -------------------------------------------------

                st.write(
                    "**Retrieved Documents:**"
                )


                retrieved_documents = policy.get(
                    "retrieved_documents",
                    []
                )


                if retrieved_documents:

                    for index, document in enumerate(
                        retrieved_documents,
                        start=1
                    ):

                        st.markdown(
                            f"### {index}. "
                            f"{document.get('source', 'Unknown source')}"
                        )


                        st.write(
                            f"**Airport:** "
                            f"{document.get('airport', 'Unknown')}"
                        )


                        if document.get(
                            "distance"
                        ) is not None:

                            st.write(
                                f"**Retrieval Distance:** "
                                f"{document['distance']:.4f}"
                            )


                        st.write(
                            "**Retrieved Policy Chunk:**"
                        )


                        st.code(
                            document.get(
                                "content",
                                ""
                            )
                        )


                else:

                    st.info(
                        "No policy documents were retrieved."
                    )


            else:

                st.info(
                    "No policy information available."
                )


    # =====================================================
    # OPERATIONAL QUERY DISPLAY
    # =====================================================

    elif query_type == "operational":

        # -------------------------------------------------
        # Investigation
        # -------------------------------------------------

        if investigation:

            st.subheader("🔎 Investigation")


            col1, col2, col3 = st.columns(3)


            with col1:

                st.write(
                    f"**Airport:** "
                    f"{investigation['airport_code']}"
                )

                st.write(
                    f"**Severity:** "
                    f"{investigation['severity'].upper()}"
                )


            with col2:

                st.write(
                    f"**Completion Rate:** "
                    f"{investigation['metrics']['completion_rate']:.0%}"
                )

                st.write(
                    f"**Average ETA:** "
                    f"{investigation['metrics']['average_eta']:.1f} min"
                )


            with col3:

                st.write(
                    f"**Driver Cancellation:** "
                    f"{investigation['metrics']['driver_cancellation_rate']:.0%}"
                )

                st.write(
                    f"**Queue Size:** "
                    f"{investigation['metrics']['queue_size']}"
                )


            st.write(
                f"**Issue:** "
                f"{investigation['issue']}"
            )


            if investigation["findings"]:

                st.write(
                    "**Contributing Factors:**"
                )


                for finding in investigation[
                    "findings"
                ]:

                    st.write(
                        f"- {finding}"
                    )

            else:

                st.write(
                    "No major operational anomalies detected."
                )


        # -------------------------------------------------
        # Resolution
        # -------------------------------------------------

        if resolution:

            st.subheader(
                "💡 Resolution Recommendation"
            )


            st.write(
                f"**Severity:** "
                f"{resolution['severity'].upper()}"
            )


            for recommendation in resolution[
                "recommendations"
            ]:

                st.write(
                    f"- {recommendation}"
                )


    # =====================================================
    # ACTION QUERY DISPLAY
    # =====================================================

    elif query_type == "action":

        # -------------------------------------------------
        # Investigation
        # -------------------------------------------------

        if investigation:

            st.subheader("🔎 Investigation")


            col1, col2, col3 = st.columns(3)


            with col1:

                st.write(
                    f"**Airport:** "
                    f"{investigation['airport_code']}"
                )

                st.write(
                    f"**Severity:** "
                    f"{investigation['severity'].upper()}"
                )


            with col2:

                st.write(
                    f"**Completion Rate:** "
                    f"{investigation['metrics']['completion_rate']:.0%}"
                )

                st.write(
                    f"**Average ETA:** "
                    f"{investigation['metrics']['average_eta']:.1f} min"
                )


            with col3:

                st.write(
                    f"**Driver Cancellation:** "
                    f"{investigation['metrics']['driver_cancellation_rate']:.0%}"
                )

                st.write(
                    f"**Queue Size:** "
                    f"{investigation['metrics']['queue_size']}"
                )


            st.write(
                f"**Issue:** "
                f"{investigation['issue']}"
            )


            if investigation["findings"]:

                st.write(
                    "**Contributing Factors:**"
                )


                for finding in investigation[
                    "findings"
                ]:

                    st.write(
                        f"- {finding}"
                    )


        # -------------------------------------------------
        # Policy
        # -------------------------------------------------

        if policy:

            st.subheader("📚 Policy Check")


            st.write(
                policy.get(
                    "policy_result",
                    "No policy response available."
                )
            )


            with st.expander(
                "View Retrieved Policy Information"
            ):

                retrieved_documents = policy.get(
                    "retrieved_documents",
                    []
                )


                for index, document in enumerate(
                    retrieved_documents,
                    start=1
                ):

                    st.markdown(
                        f"### {index}. "
                        f"{document.get('source', 'Unknown source')}"
                    )


                    st.write(
                        f"**Airport:** "
                        f"{document.get('airport', 'Unknown')}"
                    )


                    if document.get(
                        "distance"
                    ) is not None:

                        st.write(
                            f"**Retrieval Distance:** "
                            f"{document['distance']:.4f}"
                        )


                    st.code(
                        document.get(
                            "content",
                            ""
                        )
                    )


        # -------------------------------------------------
        # Resolution
        # -------------------------------------------------

        if resolution:

            st.subheader(
                "💡 Resolution Recommendation"
            )


            for recommendation in resolution[
                "recommendations"
            ]:

                st.write(
                    f"- {recommendation}"
                )


        # =================================================
        # HUMAN APPROVAL
        # =================================================

        st.subheader("⚠️ Human Approval")


        pending = st.session_state.approval_pending


        if pending:

            st.warning(
                "⚠️ HUMAN APPROVAL REQUIRED"
            )


            st.write(
                "**Proposed Action:** "
                "Trigger Surge Override"
            )


            st.write(
                f"**Airport:** "
                f"{pending['arguments']['airport_code']}"
            )


            st.write(
                f"**Requested Surge:** "
                f"{pending['arguments']['new_multiplier']:.1f}x"
            )


            st.write(
                f"**Reason:** "
                f"{pending['arguments']['reason']}"
            )


            st.write(
                "**Risk Level:** HIGH"
            )


            st.write(
                "This action cannot execute without "
                "human approval."
            )


            approve_col, reject_col = st.columns(2)


            with approve_col:

                if st.button(
                    "✅ Approve Action",
                    key="approve_action"
                ):

                    execution = execute_guarded_action(
                        action=pending["action"],
                        arguments=pending["arguments"],
                        human_approved=True,
                        user_request=pending["user_request"]
                    )


                    st.session_state.execution_result = (
                        execution
                    )


                    st.session_state.approval_pending = None

                    st.rerun()


            with reject_col:

                if st.button(
                    "❌ Reject Action",
                    key="reject_action"
                ):

                    execution = execute_guarded_action(
                        action=pending["action"],
                        arguments=pending["arguments"],
                        human_approved=False,
                        user_request=pending["user_request"]
                    )


                    st.session_state.execution_result = (
                        execution
                    )


                    st.session_state.approval_pending = None

                    st.rerun()


        else:

            st.info(
                "No operational action is currently "
                "awaiting human approval."
            )


        # =================================================
        # EXECUTION RESULT
        # =================================================

        execution_result = (
            st.session_state.execution_result
        )


        if execution_result:

            st.subheader(
                "⚡ Execution Result"
            )


            if execution_result.get(
                "status"
            ) == "success":

                st.success(
                    "✅ Action executed successfully "
                    "(mock execution)."
                )


                st.json(
                    execution_result
                )


            elif execution_result.get(
                "status"
            ) == "blocked":

                st.error(
                    "🚫 Action was blocked."
                )


                st.json(
                    execution_result
                )


            else:

                st.error(
                    "Action execution returned an error."
                )


                st.json(
                    execution_result
                )