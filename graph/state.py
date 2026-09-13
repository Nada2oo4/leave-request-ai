from typing import TypedDict


class LeaveState(TypedDict, total=False):

    # ==================================================
    # Leave Request
    # ==================================================

    employee_id: int
    country: str
    leave_type: str
    start_date: str
    end_date: str
    reason: str
    date_of_joining: str | None

    # ==================================================
    # Validation
    # ==================================================

    validation_result: bool
    validation_errors: list[str]

    # ==================================================
    # Policy Retrieval
    # ==================================================

    policy_evidence: list[dict]
    policy_retrieval_status: str

    # ==================================================
    # ==================================================
    # Attachment Analysis
    # ==================================================

    attachment_required: bool | None
    attachment_present: bool | None
    attachment_type: str | None
    attachment_reason: str | None
    attachment_valid: bool | None
    attachment_analysis: str | None
    attachment_path: str | None

    # ==================================================
    # Evaluation
    # ==================================================

    requested_days: int
    decision: str
    evaluation_reason: str