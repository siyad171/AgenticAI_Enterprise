"""Prompts for leave notification emails"""

SYSTEM_PROMPT = "You are an HR email assistant. Write professional, empathetic emails."

def leave_body_prompt(name, leave_type, start, end, days, reason, status, msg, req_id):
    return (
        f"Generate a leave notification email.\n"
        f"Employee: {name}\nType: {leave_type}\n"
        f"Period: {start} to {end} ({days} days)\nReason: {reason}\n"
        f"Status: {status}\nNote: {msg}\nRequest ID: {req_id}\n"
        "Tailor tone to leave type. Return ONLY the body."
    )

def leave_subject_prompt(leave_type, status):
    return f"Short subject (<10 words) for leave {status.lower()}, type: {leave_type}. Return ONLY subject."
