from langgraph.graph import ( #type: ignore
    StateGraph,
    START,
    END,
)

from graph.state import LeaveState
from services.attachment_analyzer import (
    check_attachment_requirement,
    analyze_attachment,
)
from services.policy_retriver import (
    retrieve_policy,
)

from services.evaluator import (
    evaluate_leave_request,
)


# ==================================================
# 1. Validate Request
# ==================================================
from models.leave_request import LeaveRequest


SUPPORTED_COUNTRIES = [
    "KSA",
    "Egypt",
    "Jordan",
    "Qatar",
    "UAE",
    "Lebanon",
]


SUPPORTED_LEAVE_TYPES = [
    "Annual Leave",
    "Sick Leave",
    "Marriage Leave",
    "Maternity / Paternity Leaves",
    "Official and Public Holidays",
    "Unpaid Leave",
    "Compassionate Leave",
    "Hajj Leave",
]


def validate_request(
    state: LeaveState,
) -> LeaveState:

    errors = []

    # ==================================================
    # 1. Validate request structure using Pydantic
    # ==================================================

    try:

        request = LeaveRequest(
            employee_id=state.get("employee_id"),
            country=state.get("country"),
            leave_type=state.get("leave_type"),
            start_date=state.get("start_date"),
            end_date=state.get("end_date"),
            reason=state.get("reason"),
        )

    except Exception as exc:

        errors.append(
            f"Invalid request data: {exc}"
        )

        state["validation_result"] = False
        state["validation_errors"] = errors
        state["decision"] = "INVALID_REQUEST"
        state["evaluation_reason"] = "; ".join(errors)


        return state
    # ==================================================
    # 2. Calculate requested days
    # ==================================================

    if request.end_date >= request.start_date:

        state["requested_days"] = (
            request.end_date - request.start_date
        ).days + 1

    
    # ==================================================
    # 3. Validate country
    # ==================================================

    if request.country not in SUPPORTED_COUNTRIES:

        errors.append(
            f"Unsupported country: {request.country}"
        )

    # ==================================================
    # 4. Validate leave type
    # ==================================================

    if request.leave_type not in SUPPORTED_LEAVE_TYPES:

        errors.append(
            f"Unsupported leave type: "
            f"{request.leave_type}"
        )

    # ==================================================
    # 5. Validate date range
    # ==================================================

    if request.end_date < request.start_date:

        errors.append(
            "End date cannot be before start date."
        )

    # ==================================================
    # 6. Store validation result
    # ==================================================

    state["validation_result"] = len(errors) == 0
    state["validation_errors"] = errors
    if errors:
        state["decision"] = "INVALID_REQUEST"
        state["evaluation_reason"] = "; ".join(errors)
       

    return state

def validation_router(
    state: LeaveState,
) -> str:

    if state.get("validation_result"):

        return "retrieve_policy"

    return "end"
# ==================================================
# 2. Retrieve Relevant Policy
# ==================================================

def retrieve_policy_node(
    state: LeaveState,
) -> LeaveState:

    evidence = retrieve_policy(
        country=state["country"],
        leave_type=state["leave_type"],
        start_date=state["start_date"],
        end_date=state["end_date"],
        reason=state["reason"],
        top_k=5,
    )

    state["policy_evidence"] = evidence
    
    if evidence:
        state["policy_retrieval_status"] = "SUCCESS"
    else:
        state["policy_retrieval_status"] = "NO_EVIDENCE"
        state["decision"] = "REVIEW_REQUIRED"

        state["evaluation_reason"] = (
            "No relevant policy evidence was found "
            "for this country and leave type."
        )

    return state
'''
def retrieval_router(
    state: LeaveState,
) -> str:

    if state.get("policy_retrieval_status") == "SUCCESS":
        return "evaluate_request"

    return "no_policy"
'''
# ==================================================
# 3. Attachment Check
# ==================================================
from pathlib import Path
def attachment_check_node(
    state: LeaveState,
) -> LeaveState:
    print("\nDEBUG ATTACHMENT PATH:")
    attachment_path = state.get("attachment_path")

    print("Path from state:", attachment_path)

    print("Path exists:", bool(attachment_path) and Path(attachment_path).exists())

    result = check_attachment_requirement(state)

    state["attachment_required"] = result[
        "attachment_required"
    ]

    state["attachment_present"] = result[
        "attachment_present"
    ]

    state["attachment_type"] = result.get(
        "attachment_type"
    )

    state["attachment_reason"] = result.get(
        "attachment_reason"
    )

    return state

def attachment_router(
    state: LeaveState,
) -> str:

    if not state.get(
        "attachment_required",
        False,
    ):
        return "no_attachment_required"

    if not state.get(
        "attachment_present",
        False,
    ):
        return "attachment_missing"

    return "analyze_attachment"
# ==================================================
# 4. Attachement Analysis
# ==================================================
def analyze_attachment_node(
    state: LeaveState,
) -> LeaveState:

    result = analyze_attachment(
        state
    )

    state["attachment_valid"] = result[
        "attachment_valid"
    ]

    state["attachment_analysis"] = result[
        "analysis"
    ]

    return state
# ==================================================
# 5. Attachment Missing
# ==================================================
def attachment_missing_node(
    state: LeaveState,
) -> LeaveState:

    state["decision"] = "ATTACHMENT_REQUIRED"

    state["evaluation_reason"] = (
        f"An attachment is required for "
        f"{state.get('leave_type')}."
    )

    return state
# ==================================================
# 6. Evaluate Leave Request
# ==================================================

def evaluate_request_node(
    state: LeaveState,
) -> LeaveState:

    policy_evidence = state.get(
        "policy_evidence",
        [],
    )

    # No relevant policy found
    if not policy_evidence:

        state["decision"] = "REVIEW_REQUIRED"

        state["evaluation_reason"] = (
            "No relevant policy evidence was found "
            "for this country and leave type."
        )

        state["requested_days"] = 0

        return state

    # Evaluate request against retrieved policy
    result = evaluate_leave_request(
        leave_request=state,
        policy_evidence=policy_evidence,
    )

    state["decision"] = result.get(
        "decision",
        "REVIEW_REQUIRED",
    )

    state["evaluation_reason"] = result.get(
        "reason",
        "The leave request requires further review.",
    )

    state["requested_days"] = result.get(
        "requested_days",
        0,
    )

    return state


# ==================================================
# Build LangGraph
# ==================================================

graph_builder = StateGraph(LeaveState)


graph_builder.add_node(
    "validate_request",
    validate_request,
)

graph_builder.add_node(
    "retrieve_policy",
    retrieve_policy_node,
)
graph_builder.add_node(
    "attachment_check",
    attachment_check_node,
)

graph_builder.add_node(
    "attachment_missing",
    attachment_missing_node,
) 

graph_builder.add_node(
    "analyze_attachment",
    analyze_attachment_node,
)
graph_builder.add_node(
    "evaluate_request",
    evaluate_request_node,
)


# ==================================================
# Graph Flow
# ==================================================

graph_builder.add_edge(
    START,
    "validate_request",
)

graph_builder.add_conditional_edges(
    "validate_request",
    validation_router,
    {
        "retrieve_policy": "retrieve_policy",
        "end": END,
    },
)

graph_builder.add_edge(
    "retrieve_policy",
    "attachment_check",
)
graph_builder.add_conditional_edges(
    "attachment_check",
    attachment_router,
    {
        "no_attachment_required": "evaluate_request",
        "attachment_missing": "attachment_missing",
        "analyze_attachment": "analyze_attachment",
    },
)
graph_builder.add_edge(
    "analyze_attachment",
    "evaluate_request",
)
graph_builder.add_edge(
    "attachment_missing",
    END,
)

graph_builder.add_edge(
    "evaluate_request",
    END,
)


graph = graph_builder.compile()