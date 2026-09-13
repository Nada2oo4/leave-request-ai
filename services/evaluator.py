from datetime import date, timedelta
from typing import Any, cast
from pydantic import BaseModel, Field  # type: ignore
from openai import OpenAI
import httpx
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    http_client=cast(Any, httpx.Client())
)

# ==================================================
# LLM Evaluation Output
# ==================================================
class LeaveEvaluation(BaseModel):
    decision: str = Field(
        description=(
            "Final decision: APPROVED, DENIED, or REVIEW_REQUIRED."
        )
    )
    reason: str = Field(
        description="Clear explanation for the final decision."
    )
    policy_basis: str = Field(
        description=(
            "The specific policy rule or evidence used "
            "to support the decision."
        )
    )
# ==================================================
# Leave Days Calculation
# ==================================================
def calculate_leave_days(
    start_date: str,
    end_date: str,
) -> int:
    """
    Calculate the number of calendar days requested.
    """
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError(
            "End date cannot be before start date."
        )
    return (end - start).days + 1

def calculate_working_days(start_date: str, end_date: str) -> int:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    if end < start:
        raise ValueError("End date cannot be before start date.")

    working_days = 0
    current = start

    while current <= end:
        # Friday = 4, Saturday = 5
        if current.weekday() not in (4, 5):
            working_days += 1

        current += timedelta(days=1)

    return working_days
def calculate_service_duration(
    date_of_joining: str,
    reference_date: str,
) -> tuple[int, int]:
    joining = date.fromisoformat(date_of_joining)
    reference = date.fromisoformat(reference_date)

    if reference < joining:
        raise ValueError("Reference date cannot be before date of joining.")

    years = reference.year - joining.year
    months = reference.month - joining.month

    if reference.day < joining.day:
        months -= 1

    if months < 0:
        years -= 1
        months += 12

    total_months = years * 12 + months

    return years, total_months

def get_annual_leave_entitlement(
    country: str,
    date_of_joining: str,
    leave_start_date: str,
) -> int | None:

    if country != "Egypt":
        return None

    _, total_months = calculate_service_duration(
        date_of_joining,
        leave_start_date,
    )

    if total_months < 6:
        return 0

    if total_months < 12:
        return 15

    return 21

# ==================================================
# Final LLM Evaluation
# ==================================================
def evaluate_leave_request(
    leave_request: dict[str, Any],
    policy_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    if not policy_evidence:
        return {
            "decision": "REVIEW_REQUIRED",
            "reason": "No relevant policy evidence was found.",
            "policy_basis": "",
            "requested_days": calculate_leave_days(
                leave_request["start_date"],
                leave_request["end_date"],
            ),
            "evidence": [],
        }
    if leave_request.get("leave_type") == "Annual Leave":
        requested_days = calculate_working_days(
            leave_request["start_date"],
            leave_request["end_date"],
        )
    else:
        requested_days = calculate_leave_days(
            leave_request["start_date"],
            leave_request["end_date"],
        )
    working_days = None
    annual_leave_entitlement = None
    service_months = None

    if leave_request.get("leave_type") == "Annual Leave":
        working_days = calculate_working_days(
        leave_request["start_date"],
        leave_request["end_date"],
    )

    sick_leave_entitlement = None
    if leave_request.get("leave_type") == "Sick Leave":
        sick_leave_entitlement = 14

    date_of_joining = leave_request.get("date_of_joining")

    if date_of_joining:
        _, service_months = calculate_service_duration(
            date_of_joining,
            leave_request["start_date"],
        )

        annual_leave_entitlement = get_annual_leave_entitlement(
            leave_request["country"],
            date_of_joining,
            leave_request["start_date"],
        )
    policy_text = "\n\n".join(
        [
            f"Page {evidence.get('page')}:\n"
            f"{evidence.get('text', '')}"
            for evidence in policy_evidence
        ]
    )
    attachment_analysis = leave_request.get(
        "attachment_analysis",
        "No attachment analysis available.",
    )
    attachment_required = leave_request.get(
        "attachment_required",
        False,
    )
    attachment_present = leave_request.get(
        "attachment_present",
        False,
    )
    prompt = f"""
You are a Leave Request Evaluation Agent.
Your task is to evaluate an employee's leave request
using ONLY the provided company policy evidence.
Do not invent policy rules.
Employee Request:
- Employee ID: {leave_request.get("employee_id")}
- Country: {leave_request.get("country")}
- Leave Type: {leave_request.get("leave_type")}
- Start Date: {leave_request.get("start_date")}
- End Date: {leave_request.get("end_date")}
- Requested Days: {requested_days}
- Day Calculation Type: {
    "working days"
    if leave_request.get("leave_type") == "Annual Leave"
    else "calendar days"
}
- Reason: {leave_request.get("reason")}
- Date of Joining: {leave_request.get("date_of_joining")}
- Service Duration: {service_months} months
- Requested Working Days: {working_days}
- Annual Leave Entitlement: {annual_leave_entitlement} working days
- Sick Leave Annual Entitlement: {sick_leave_entitlement} calendar days
Attachment Information:
- Attachment Required: {attachment_required}
- Attachment Present: {attachment_present}
- Attachment Analysis:
{attachment_analysis}
Retrieved Company Policy:
{policy_text}
Rules:
1. Base the decision only on the provided policy evidence.
2. If the request clearly satisfies the policy, return APPROVED.
3. If the request clearly violates the policy, return DENIED.
4. If the evidence is insufficient to make a confident decision,
   return REVIEW_REQUIRED.
5. If a required attachment is missing or invalid,
   take that into consideration when making the decision.
6. Do not create or assume requirements that are not stated
   in the provided policy.
7. Explain the decision clearly.
8. Mention the relevant policy rule in policy_basis.
9. For Annual Leave, use the calculated working days provided above.
   Do not recalculate the number of days as calendar days.
10. For Sick Leave, the policy states an annual entitlement of 14 days
   at full pay once the leave is verified by a medical certificate.
11. Do not assume the employee has the full 14 days available if
    previous sick leave usage is not provided.
Return only the structured evaluation.
"""
    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a company leave policy evaluation agent. "
                    "Evaluate requests strictly using the supplied "
                    "policy evidence."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        response_format=LeaveEvaluation,
    )
    evaluation = response.choices[0].message.parsed
    if evaluation is None:
        return {
            "decision": "REVIEW_REQUIRED",
            "reason": "The LLM could not produce a valid evaluation.",
            "policy_basis": "",
            "requested_days": requested_days,
            "evidence": policy_evidence,
        }
    return {
        "decision": evaluation.decision,
        "reason": evaluation.reason,
        "policy_basis": evaluation.policy_basis,
        "requested_days": requested_days,
        "evidence": policy_evidence,
    }