"""
Email Service — Unified SMTP email sender with LLM-generated content
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from core.config import (
    SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD
)


class EmailService:
    """Sends transactional emails (leave notifications, test results, tickets, etc.)"""

    def __init__(self, llm_service=None):
        self.llm = llm_service          # Optional — for AI-generated bodies

    # ── generic send ──────────────────────────────────────────────
    def send_email(self, to: str, subject: str, body: str) -> Dict:
        """Send a plain-text email. Returns {'status': 'success'|'error', 'message': ...}"""
        if not SENDER_EMAIL or not SENDER_PASSWORD:
            return {
                "status": "error",
                "message": "Email credentials not configured in .env",
                "email_content": body
            }
        try:
            msg = MIMEMultipart()
            msg["From"] = SENDER_EMAIL
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                server.send_message(msg)

            return {"status": "success", "message": f"Email sent to {to}"}
        except Exception as e:
            return {"status": "error", "message": str(e), "email_content": body}

    # ── leave notification ────────────────────────────────────────
    def send_leave_email(
        self, employee_name: str, employee_email: str,
        leave_type: str, start_date: str, end_date: str,
        days: int, reason: str, status: str, message: str,
        request_id: str
    ) -> Dict:
        """Send leave request notification — uses LLM body with fallback."""
        subject, body = self._generate_leave_email(
            employee_name, leave_type, start_date, end_date,
            days, reason, status, message, request_id
        )
        return self.send_email(employee_email, subject, body)

    def _generate_leave_email(self, name, leave_type, start, end, days,
                              reason, status, message, req_id):
        """Try LLM, fall back to template."""
        if self.llm:
            try:
                prompt = (
                    f"Generate a professional leave notification email.\n"
                    f"Employee: {name}\nLeave Type: {leave_type}\n"
                    f"Period: {start} to {end} ({days} days)\nReason: {reason}\n"
                    f"Status: {status}\nNote: {message}\nRequest ID: {req_id}\n\n"
                    "Tailor tone to leave type (sick→recovery, annual→enjoy break). "
                    "Return ONLY the email body."
                )
                body = self.llm.ask_question(prompt)
                subj_prompt = (
                    f"Short subject line (<10 words) for leave request {status.lower()}. "
                    f"Type: {leave_type}. Return ONLY the subject."
                )
                subject = self.llm.ask_question(subj_prompt).strip().strip('"\'')
                return subject, body
            except Exception:
                pass

        # ── deterministic fallback ────────────────────────────────
        if status.upper() == "APPROVED":
            tone = {
                "sick": "We wish you a speedy recovery.",
                "annual": "Enjoy your well-deserved break!",
                "unpaid": "We hope everything goes well.",
            }
            closing = tone.get(leave_type.split()[0].lower(), "Have a pleasant time off.")
            subject = f"Leave Request Approved - {leave_type}"
            body = (
                f"Dear {name},\n\nYour leave request has been approved!\n\n"
                f"Request ID: {req_id}\nType: {leave_type}\n"
                f"Period: {start} to {end} ({days} days)\nReason: {reason}\n\n"
                f"Status: APPROVED ✓\n\n{message}\n\n{closing}\n\n"
                "Best regards,\nHR Department"
            )
        elif status.upper() == "REJECTED":
            subject = f"Leave Request Status - {leave_type}"
            body = (
                f"Dear {name},\n\nThank you for submitting your leave request.\n\n"
                f"Request ID: {req_id}\nType: {leave_type}\n"
                f"Period: {start} to {end} ({days} days)\nReason: {reason}\n\n"
                f"Status: NOT APPROVED\n\n{message}\n\n"
                "Please contact HR to discuss alternatives.\n\n"
                "Best regards,\nHR Department"
            )
        else:
            subject = f"Leave Request Under Review - {leave_type}"
            body = (
                f"Dear {name},\n\nYour leave request is under review.\n\n"
                f"Request ID: {req_id}\nType: {leave_type}\n"
                f"Period: {start} to {end} ({days} days)\nReason: {reason}\n\n"
                f"Status: PENDING APPROVAL\n\n{message}\n\n"
                "You will be notified once reviewed.\n\n"
                "Best regards,\nHR Department"
            )
        return subject, body

    # ── test result notification ──────────────────────────────────
    def send_test_result_email(
        self, candidate_email: str, candidate_name: str,
        passed: bool, test_score: float, position: str,
        username: str = None, password: str = None
    ) -> Dict:
        """Send test result email — uses LLM body with fallback."""
        subject, body = self._generate_test_result_email(
            candidate_name, passed, test_score, position, username, password
        )
        return self.send_email(candidate_email, subject, body)

    def _generate_test_result_email(self, name, passed, score, position,
                                     username, password):
        if self.llm:
            try:
                prompt = (
                    f"Professional email for test results.\n"
                    f"Candidate: {name}\nPosition: {position}\n"
                    f"Score: {score:.1f}%\nResult: {'PASSED' if passed else 'FAILED'}\n"
                )
                if passed and username:
                    prompt += f"Include portal credentials — User: {username}, Pass: {password}\n"
                prompt += "Return ONLY the email body."
                body = self.llm.ask_question(prompt)
                subj_prompt = (
                    f"Short subject for test result ({'passed' if passed else 'failed'}) "
                    f"for {position}. Return ONLY subject."
                )
                subject = self.llm.ask_question(subj_prompt).strip().strip('"\'')
                return subject, body
            except Exception:
                pass

        if passed:
            subject = f"Congratulations! Selected for {position}"
            body = (
                f"Dear {name},\n\nCongratulations! You passed the {position} "
                f"assessment with {score:.1f}%.\n\n"
            )
            if username:
                body += f"Portal credentials:\nUsername: {username}\nPassword: {password}\n\n"
            body += "Best regards,\nHR Department"
        else:
            subject = f"Test Results for {position} Position"
            body = (
                f"Dear {name},\n\nThank you for taking the {position} assessment.\n"
                f"Your score of {score:.1f}% did not meet requirements.\n\n"
                "We encourage you to apply for other positions.\n\n"
                "Best regards,\nHR Department"
            )
        return subject, body
