"""
HR Agent — Leave processing, onboarding, policy Q&A, audit, candidate evaluation, resume parsing
"""
import datetime, re, json, random, string, os
from typing import Dict, List, Optional
from core.base_agent import BaseAgent
from core.config import CANDIDATE_REVIEW_THRESHOLD as SKILL_MATCH_THRESHOLD, CANDIDATE_ACCEPT_THRESHOLD as AUTO_ACCEPT_THRESHOLD
from tools.email_service import EmailService


class HRAgent(BaseAgent):
    """
    Capabilities:
      1. process_leave_request   — validate balance, approve/reject, send email
      2. handle_employee_onboarding — create profile, credentials, welcome email
      3. ask_hr_policy_question  — LLM answer with DB context
      4. generate_audit_report   — date-filtered activity report
      5. evaluate_candidate      — skill/experience/education scoring
      6. parse_resume_text       — LLM parse with pattern-matching fallback
      + send_test_result_email   — delegated to EmailService
    """

    def __init__(self, db, llm_service, event_bus=None):
        super().__init__(agent_name="HR Agent", database=db, llm_service=llm_service, event_bus=event_bus)
        self.email = EmailService(llm_service)

    # ── BaseAgent abstract ────────────────────────────────────────
    def get_capabilities(self) -> List[str]:
        return [
            "process_leave_request", "handle_employee_onboarding",
            "ask_hr_policy_question", "generate_audit_report",
            "evaluate_candidate", "parse_resume_text",
            "send_test_result_email"
        ]

    def handle_event(self, event_type: str, data: dict):
        if event_type == "new_candidate_applied":
            cid = data.get("candidate_id")
            candidate = self.db.get_candidate(cid)
            job = self.db.get_job_position(
                self.db.get_job_id_by_title(candidate.applied_position)
            )
            if candidate and job:
                self.evaluate_candidate(candidate, job)
        elif event_type == "employee_offboarded":
            self.log_action("Employee Offboarded", data)

    # ══════════════════════════════════════════════════════════════
    #  1.  PROCESS LEAVE REQUEST
    # ══════════════════════════════════════════════════════════════
    def process_leave_request(self, employee_id: str, leave_type: str,
                              start_date: str, end_date: str, reason: str) -> Dict:
        employee = self.db.get_employee(employee_id)
        if not employee:
            return {"status": "error", "message": "Employee not found"}

        # Date conflict check
        conflict = self.db.check_leave_date_conflict(employee_id, start_date, end_date)
        if conflict:
            msg = (f"Dates conflict with approved leave {conflict.request_id} "
                   f"({conflict.start_date} to {conflict.end_date})")
            self._send_leave_notification(employee, leave_type, start_date,
                                          end_date, 0, reason, "Rejected", msg, "N/A")
            return {"status": "error", "message": msg, "decision": "Rejected"}

        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days + 1
        balance = employee.leave_balance.get(leave_type, 0)

        if days > balance:
            status, msg = "Rejected", f"Insufficient balance ({balance} avail, {days} requested)"
        elif days > 10:
            status, msg = "Pending", "Requires manager approval (>10 days)"
        else:
            status, msg = "Approved", "Auto-approved"
            self.db.update_leave_balance(employee_id, leave_type, days)

        request_id = f"LR{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"

        from core.database import LeaveRequest
        self.db.add_leave_request(LeaveRequest(
            request_id=request_id, employee_id=employee_id,
            employee_name=employee.name, leave_type=leave_type,
            start_date=start_date, end_date=end_date, days=days,
            reason=reason, status=status,
            submitted_date=datetime.datetime.now().isoformat(),
            processed_date=datetime.datetime.now().isoformat() if status == "Approved" else None
        ))

        email_result = self._send_leave_notification(
            employee, leave_type, start_date, end_date,
            days, reason, status, msg, request_id
        )

        # Publish event
        if self.event_bus:
            self.event_bus.publish("leave_processed", {
                "employee_id": employee_id, "request_id": request_id,
                "status": status, "days": days
            })

        result = {"status": "success", "request_id": request_id,
                  "decision": status, "message": msg, "email_result": email_result}
        self.log_action("Process Leave Request", result, employee_id)
        return result

    def _send_leave_notification(self, employee, leave_type, start, end,
                                  days, reason, status, msg, req_id):
        return self.email.send_leave_email(
            employee.name, employee.email, leave_type,
            start, end, days, reason, status, msg, req_id
        )

    # ══════════════════════════════════════════════════════════════
    #  2.  HANDLE EMPLOYEE ONBOARDING
    # ══════════════════════════════════════════════════════════════
    def handle_employee_onboarding(self, name: str, email: str,
                                    department: str, position: str,
                                    join_date: str) -> Dict:
        from core.database import Employee
        emp_count = len(self.db.employees) + 1
        emp_id = f"EMP{emp_count:03d}"

        employee = Employee(
            employee_id=emp_id, name=name, email=email,
            department=department, position=position, join_date=join_date,
            leave_balance={"Casual Leave": 12, "Sick Leave": 15, "Annual Leave": 20}
        )
        self.db.add_employee(employee)

        creds = {
            "username": email.split('@')[0],
            "temp_password": f"Welcome@{emp_id}",
            "portal_url": "https://company.portal.com"
        }
        documents = ["Employee Handbook", "Company Policies",
                     "IT Security Guidelines", "Benefits Information", "Tax Forms"]

        # Publish event for other agents
        if self.event_bus:
            self.event_bus.publish("employee_onboarded", {
                "employee_id": emp_id, "name": name,
                "department": department, "position": position
            })

        result = {"status": "success", "employee_id": emp_id,
                  "credentials": creds, "documents": documents}
        self.log_action("Employee Onboarding", result, emp_id)
        return result

    # ══════════════════════════════════════════════════════════════
    #  3.  ASK HR POLICY QUESTION (with DB access)
    # ══════════════════════════════════════════════════════════════
    def ask_hr_policy_question(self, question: str, employee_id: str = "GUEST") -> Dict:
        all_policies = self.db.get_all_policies()

        system_prompt = (
            "You are an HR assistant. Use these policies:\n\n"
            f"{all_policies}\n\n"
            "You also have access to the employee database. "
            "When asked about specific employees provide their details. "
            "Be professional and concise."
        )

        answer = self.llm.generate_response(question, system_prompt,
                                             include_employee_data=True)
        relevant = self._find_relevant_policies(question)
        emp = self._extract_employee_from_question(question)

        result = {"status": "success", "question": question, "answer": answer,
                  "relevant_policies": relevant,
                  "employee_data_accessed": emp is not None}
        self.log_action("HR Policy Question",
                        {"question": question, "db_access": emp is not None},
                        employee_id)
        return result

    def _extract_employee_from_question(self, question: str):
        q = question.lower()
        m = re.search(r'EMP\d{3}', question, re.IGNORECASE)
        if m:
            return self.db.get_employee(m.group(0).upper())
        for emp in self.db.employees.values():
            if emp.name.lower() in q or emp.name.split()[0].lower() in q:
                return emp
        return None

    def _find_relevant_policies(self, question: str) -> List[str]:
        q = question.lower()
        policies = []
        if any(w in q for w in ["leave", "vacation", "time off"]):
            policies.append("Leave Policy")
        if any(w in q for w in ["onboard", "joining", "new employee"]):
            policies.append("Onboarding Policy")
        if any(w in q for w in ["hours", "timing", "schedule", "remote"]):
            policies.append("Working Hours Policy")
        if any(w in q for w in ["conduct", "behavior", "dress"]):
            policies.append("Code of Conduct")
        return policies

    # ══════════════════════════════════════════════════════════════
    #  4.  GENERATE AUDIT REPORT
    # ══════════════════════════════════════════════════════════════
    def generate_audit_report(self, start_date: str = None,
                               end_date: str = None) -> Dict:
        now = datetime.datetime.now()
        if not start_date:
            start_date = (now - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = now.strftime("%Y-%m-%d")

        try:
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59)
        except ValueError:
            return {"status": "error", "message": "Invalid date format"}

        filtered = []
        for log in self.db.audit_logs:
            try:
                log_dt = datetime.datetime.fromisoformat(log.timestamp)
                if start_dt <= log_dt <= end_dt:
                    filtered.append(log)
            except Exception:
                continue

        leave_logs = [l for l in filtered if l.action == "Process Leave Request"]
        onboard_logs = [l for l in filtered if l.action == "Employee Onboarding"]
        policy_logs = [l for l in filtered if l.action == "HR Policy Question"]
        compliance_issues = self._check_compliance()

        report = {
            "report_id": f"AUDIT{now.strftime('%Y%m%d%H%M%S')}",
            "generated_date": now.isoformat(),
            "period": {"start": start_date, "end": end_date},
            "summary": {
                "total_activities": len(filtered),
                "leave_requests": {
                    "total": len(leave_logs),
                    "approved": sum(1 for l in leave_logs if l.details.get('decision') == 'Approved'),
                    "rejected": sum(1 for l in leave_logs if l.details.get('decision') == 'Rejected'),
                    "pending": sum(1 for l in leave_logs if l.details.get('decision') == 'Pending'),
                },
                "onboarding": len(onboard_logs),
                "policy_questions": len(policy_logs),
            },
            "detailed_logs": [
                {"log_id": l.log_id, "timestamp": l.timestamp, "agent": l.agent,
                 "action": l.action, "user": l.user, "details": l.details}
                for l in filtered
            ],
            "compliance_status": "COMPLIANT" if not compliance_issues else "ISSUES_FOUND",
            "compliance_issues": compliance_issues,
        }
        self.log_action("Generate Audit Report", {"report_id": report["report_id"]}, "Admin")
        return report

    def _check_compliance(self) -> List[str]:
        issues = []
        for rid, req in self.db.leave_requests.items():
            if req.status == "Pending":
                submitted = datetime.datetime.fromisoformat(req.submitted_date)
                if (datetime.datetime.now() - submitted).days > 7:
                    issues.append(f"Leave request {rid} pending >7 days")
        return issues

    # ══════════════════════════════════════════════════════════════
    #  5.  EVALUATE CANDIDATE
    # ══════════════════════════════════════════════════════════════
    def _normalize_education_level(self, education_text: str) -> int:
        """Extract education level from text and return hierarchy value (higher = more qualified)"""
        text = education_text.lower()
        if any(x in text for x in ['phd', 'ph.d', 'doctorate']):
            return 5
        elif any(x in text for x in ['master', "master's", 'm.sc', 'm.s.', 'mba', 'mca']):
            return 4
        elif any(x in text for x in ['bachelor', "bachelor's", 'b.sc', 'b.s.', 'b.tech', 'b.e.', 'bca']):
            return 3
        elif any(x in text for x in ['diploma', 'associate']):
            return 2
        elif any(x in text for x in ['high school', 'secondary', '12th', 'hsc']):
            return 1
        return 0  # Not specified or unknown

    def evaluate_candidate(self, candidate, job_position) -> Dict:
        criteria = self.db.eligibility_criteria
        required = {s.lower() for s in job_position.required_skills}
        candidate_sk = {s.lower() for s in candidate.extracted_skills}
        matched = required & candidate_sk
        skill_pct = (len(matched) / len(required) * 100) if required else 0

        exp_met = candidate.experience_years >= job_position.min_experience
        # Use normalized education level comparison instead of simple substring match
        candidate_edu_level = self._normalize_education_level(candidate.education)
        required_edu_level = self._normalize_education_level(job_position.min_education)
        edu_met = candidate_edu_level >= required_edu_level

        score = skill_pct
        if criteria.get('experience_required', True) and not exp_met:
            score *= 0.7
        if criteria.get('education_required', True) and not edu_met:
            score *= 0.8

        auto_thr = criteria.get('auto_accept_threshold', AUTO_ACCEPT_THRESHOLD)
        skill_thr = criteria.get('skill_match_threshold', SKILL_MATCH_THRESHOLD)

        if score >= auto_thr:
            decision, msg = "Accepted", f"Score {score:.1f}% meets threshold"
        elif score >= skill_thr:
            decision, msg = "Pending Review", f"Score {score:.1f}% — manual review"
        else:
            decision, msg = "Rejected", f"Score {score:.1f}% below minimum"

        evaluation = {
            "score": round(score, 2), "skill_match_percentage": round(skill_pct, 2),
            "matched_skills": list(matched), "experience_met": exp_met,
            "education_met": edu_met, "decision": decision, "message": msg,
            "evaluated_date": datetime.datetime.now().isoformat()
        }
        candidate.status = decision
        candidate.evaluation_result = evaluation

        self.log_action("Candidate Evaluation", {
            "candidate_id": candidate.candidate_id,
            "decision": decision, "score": round(score, 2)
        })
        return {"status": "success", "evaluation": evaluation,
                "candidate_id": candidate.candidate_id}

    # ══════════════════════════════════════════════════════════════
    #  6.  PARSE RESUME (LLM + fallback)
    # ══════════════════════════════════════════════════════════════
    def parse_resume_text(self, resume_text: str) -> Dict:
        if self.llm and self.llm.client:
            try:
                prompt = (
                    "Analyze this resume and extract JSON:\n\n"
                    f"{resume_text[:3000]}\n\n"
                    'Return: {"skills":["..."],"experience_years":<int>,'
                    '"education":"Bachelor\'s Degree|Master\'s Degree|PhD|Diploma|High School|Not Specified"}'
                )
                resp = self.llm.generate_response(
                    prompt, "Expert resume parser. Return valid JSON only.",
                    include_employee_data=False
                )
                # Save LLM response for debugging
                self._save_resume_parse_log(resume_text, prompt, resp)
                
                m = re.search(r'\{[\s\S]*\}', resp)
                if m:
                    data = json.loads(m.group(0))
                    return {"skills": data.get("skills", []),
                            "experience_years": int(data.get("experience_years", 0)),
                            "education": data.get("education", "Not Specified")}
            except Exception as e:
                # Also log parse failures
                self._save_resume_parse_log(resume_text, prompt if 'prompt' in locals() else "", 
                                           resp if 'resp' in locals() else "", 
                                           error=str(e))
        return self._fallback_parse(resume_text)

    def _save_resume_parse_log(self, resume_text: str, prompt: str, llm_response: str, error: str = None):
        """Save LLM resume parsing response to JSON file for debugging"""
        try:
            # Create logs directory if it doesn't exist
            log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs', 'resume_parsing')
            os.makedirs(log_dir, exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
            log_file = os.path.join(log_dir, f'resume_parse_{timestamp}.json')
            
            # Prepare log data
            log_data = {
                'timestamp': datetime.datetime.now().isoformat(),
                'resume_text_preview': resume_text[:500] + '...' if len(resume_text) > 500 else resume_text,
                'resume_text_length': len(resume_text),
                'prompt_sent': prompt,
                'llm_response': llm_response,
                'error': error
            }
            
            # Save to file
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
            
            self.log_action("Resume Parse Log Saved", {"file": log_file})
        except Exception as log_error:
            # Don't let logging errors break the parsing flow
            print(f"Warning: Could not save resume parse log: {log_error}")

    def _fallback_parse(self, text: str) -> Dict:
        t = text.lower()
        kw = [
            'python','java','javascript','c++','c#','ruby','php','react','angular',
            'vue','node.js','django','flask','fastapi','fast api','spring','sql',
            'mysql','postgresql','postgres','mongodb','redis','aws','azure','gcp',
            'docker','kubernetes','k8s','machine learning','ml','ai',
            'artificial intelligence','data science','rest api','restful','graphql',
            'git','github','gitlab','agile','scrum','marketing','seo',
            'content strategy','digital marketing','project management','leadership',
            'communication','html','css','typescript','golang','go lang','rust',
            'swift','kotlin','scala','r','matlab','tableau','power bi','excel',
            'jira','confluence','ci/cd','cicd','jenkins','terraform','ansible',
            'linux','unix','networking','cybersecurity','devops','microservices',
            'api development','web development','mobile development','ios','android',
            'figma','ui/ux','ux design','ui design','social media','analytics',
            'team leadership','team management','budget management','strategic planning',
        ]
        # Normalize some multi-word keywords for matching
        skill_map = {
            'fast api': 'FastAPI', 'fastapi': 'FastAPI',
            'postgres': 'PostgreSQL', 'postgresql': 'PostgreSQL',
            'k8s': 'Kubernetes', 'kubernetes': 'Kubernetes',
            'ml': 'Machine Learning', 'machine learning': 'Machine Learning',
            'ai': 'AI', 'artificial intelligence': 'AI',
            'go lang': 'Golang', 'golang': 'Golang',
            'ci/cd': 'CI/CD', 'cicd': 'CI/CD',
            'ui/ux': 'UI/UX', 'ux design': 'UI/UX', 'ui design': 'UI/UX',
            'rest api': 'REST API', 'restful': 'REST API',
            'github': 'Git', 'gitlab': 'Git',
            'power bi': 'Power BI',
            'node.js': 'Node.js',
            'c++': 'C++', 'c#': 'C#',
        }
        found_skills = set()
        for k in kw:
            if k in t:
                display_name = skill_map.get(k, k.title())
                found_skills.add(display_name)
        skills = sorted(found_skills)

        exp = 0
        for pat in [r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
                     r'experience[:\s]+(\d+)\+?\s*years?',
                     r'(\d+)\+?\s*years?\s+in',
                     r'(\d+)\+?\s*years?\s+of',
                     r'(\d+)\+?\s*yrs']:
            m = re.search(pat, t)
            if m: exp = max(exp, int(m.group(1)))
        edu = "Not Specified"
        for level, keys in [
            ("PhD", ["phd","ph.d"]),
            ("Master's Degree", ["master","msc","mba"]),
            ("Bachelor's Degree", ["bachelor","bsc","b.tech","b.e"]),
            ("Diploma", ["diploma"]),
            ("High School", ["high school"])
        ]:
            if any(k in t for k in keys):
                edu = level; break
        return {"skills": skills, "experience_years": exp, "education": edu}

    # ── Delegate email ────────────────────────────────────────────
    def send_test_result_email(self, candidate_email, candidate_name,
                                passed, test_score, position,
                                username=None, password=None) -> Dict:
        return self.email.send_test_result_email(
            candidate_email, candidate_name, passed,
            test_score, position, username, password
        )
