from enum import Enum


class LeaveType(str, Enum):
    ANNUAL = "Annual Leave"
    SICK = "Sick Leave"
    MARRIAGE = "Marriage Leave"
    MATERNITY_PATERNITY = "Maternity / Paternity Leaves"
    OFFICIAL_HOLIDAYS = "Official and Public Holidays"
    UNPAID = "Unpaid Leave"
    COMPASSIONATE = "Compassionate Leave"
    HAJJ = "Hajj Leave"