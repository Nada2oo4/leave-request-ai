from datetime import date

from pydantic import BaseModel, Field

from models.enums import LeaveType  # type: ignore


class LeaveRequest(BaseModel):
    employee_id: int = Field(gt=0)
    country: str
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str = Field(min_length=1)