import enum


class UserRole(str, enum.Enum):
    OPERATOR = "Operator"
    SUPERVISOR = "Supervisor"
    MANAGEMENT = "Management"
