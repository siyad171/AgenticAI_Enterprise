"""
core/events.py — Event type constants (avoids typos)
"""

# HR Agent events
EMPLOYEE_ONBOARDED = "employee_onboarded"
EMPLOYEE_TERMINATED = "employee_terminated"
LEAVE_APPROVED = "leave_approved"

# IT Agent events
ACCESS_PROVISIONED = "access_provisioned"
ACCESS_REVOKED = "access_revoked"
SECURITY_INCIDENT = "security_incident"

# Finance Agent events
EXPENSE_SUBMITTED = "expense_submitted"
EXPENSE_APPROVED = "expense_approved"
BUDGET_ALERT = "budget_alert"
PAYROLL_SETUP_COMPLETE = "payroll_setup_complete"

# Compliance Agent events
VIOLATION_DETECTED = "violation_detected"
TRAINING_OVERDUE = "training_overdue"
POLICY_UPDATED = "policy_updated"
COMPLIANCE_VERIFIED = "compliance_verified"
