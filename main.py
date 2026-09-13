from fastapi import FastAPI, UploadFile, File, Form  # type: ignore
from pydantic import BaseModel, Field  # type: ignore
from graph.workflow import graph
from pathlib import Path
from datetime import date
from enum import Enum
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
# ==================================================
# FastAPI App
# ==================================================
app = FastAPI(
    title="Leave Request AI Evaluation System",
    description=(
        "AI-powered leave request evaluation system "
        "using LangGraph, RAG, Pinecone, and GPT-4o."
    ),
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================
# Leave types
# ==================================================
from models.enums import LeaveType  # type: ignore
# ==================================================
# Request Model
# ==================================================
class LeaveRequestInput(BaseModel):
    employee_id: int = Field(gt=0)
    country: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(min_length=1)
    date_of_joining: date | None = None


# ==================================================
# Response Model
# ==================================================
class LeaveRequestResponse(BaseModel):
    decision: str | None = None
    requested_days: int | None = None
    reason: str | None = None
    attachment_required: bool | None = None
    attachment_present: bool | None = None
    attachment_type: str | None = None
    attachment_reason: str | None = None
    attachment_valid: bool | None = None
    attachment_analysis: str | None = None
    policy_evidence: list[dict] = []
# ==================================================
# Health Check
# ==================================================
@app.get("/")
def root():
    return {
        "message": "Leave Request AI Evaluation System is running."
    }
# ==================================================
# Leave Request Endpoint (recives the employee's request)
# ==================================================
@app.post("/leave-request", response_model=LeaveRequestResponse)
async def evaluate_leave(
    employee_id: int = Form(...),
    country: str = Form(...),
    leave_type: LeaveType = Form(...),
    start_date: date = Form(...),
    end_date: date = Form(...),
    reason: str = Form(...),
    date_of_joining: date | None = Form(None),
    attachment: UploadFile | None = File(None),
):


    attachment_path = None

    if attachment is not None:
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        attachment_path = upload_dir / attachment.filename

        with attachment_path.open("wb") as buffer:
            buffer.write(await attachment.read())

    request_data = {
        "employee_id": employee_id,
        "country": country,
        "leave_type": leave_type.value,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "reason": reason,
        "date_of_joining": date_of_joining.isoformat() if date_of_joining else None,
        "attachment_path": str(attachment_path) if attachment_path else None,
    }

    result = graph.invoke(request_data)
    return {
        "decision": result.get("decision"),
        "requested_days": result.get("requested_days"),
        "reason": result.get("evaluation_reason"),
        "attachment_required": result.get(
            "attachment_required"
        ),
        "attachment_present": result.get(
            "attachment_present"
        ),
        "attachment_type": result.get(
            "attachment_type"
        ),
        "attachment_reason": result.get(
            "attachment_reason"
        ),
        "attachment_valid": result.get(
            "attachment_valid"
        ),
        "attachment_analysis": result.get(
            "attachment_analysis"
        ),
        "policy_evidence": result.get(
            "policy_evidence",
            [],
        ),
    }