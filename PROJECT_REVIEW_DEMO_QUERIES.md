# 🎯 Project Review Demo Queries - Multi-Agent System

## Employee Portal Demo Scenarios
Use these queries in the **Employee AI Assistant** chat for your project review. The system will automatically route to the appropriate agent.

---

## 🏥 HR Agent Tools & Demo Queries

### 1. **Emergency Medical Handler** 
*Handles medical/safety emergencies*
```
Demo Query: "Emp 002 got heart attack what to do?"
Demo Query: "Someone collapsed in the office - cardiac arrest!"
Expected Result: 
- First-aid instructions (CPR, AED usage)
- Emergency services notification (simulated)
- HR email alert
- Incident logged
```

### 2. **Process Leave Request**
*Validate & approve employee leave*
```
Demo Query: "I want to take casual leave from May 8 to May 12, 2026 for family trip"
Demo Query: "I need 3 days of sick leave starting May 9 due to flu"
Demo Query: "Can I take annual leave June 1-15 for vacation?"
Expected Result:
- Leave balance checked
- Auto-approval (≤10 days)
- Email confirmation sent
- Calendar updated
```

### 3. **Handle Employee Onboarding**
*Onboard new employees*
```
Demo Query: "Please onboard a new employee: Rajesh Kumar, raj.kumar@company.com, IT Dept, Software Engineer, joining May 15, 2026"
Expected Result:
- Employee profile created
- User credentials generated
- IT/Finance/Compliance setup triggered
- Welcome email sent
```

### 4. **Ask HR Policy Question**
*Answer HR policy questions*
```
Demo Query: "What is the company policy on remote work?"
Demo Query: "How many sick leaves do I have left?"
Demo Query: "What's our code of conduct regarding dress code?"
Demo Query: "What are the working hours?"
Expected Result:
- Policy information retrieved from database
- Employee-specific details shown (leave balance, etc.)
```

### 5. **Generate Audit Report**
*Create HR audit reports*
```
Demo Query: "Generate an HR audit report for the past 30 days"
Demo Query: "Can you create an audit report from April 1 to May 6, 2026?"
Expected Result:
- Leave requests summary
- Onboarding events
- Policy questions
- Compliance issues listed
```

### 6. **Get Employee Info**
*Lookup employee details*
```
Demo Query: "Tell me about employee EMP001"
Demo Query: "What's John Doe's department and email?"
Expected Result:
- Employee ID, name, email
- Department, position
- Join date, leave balance
```

### 7. **Get Leave History**
*View past leave records*
```
Demo Query: "Show me my leave request history"
Demo Query: "What leave has employee EMP002 taken?"
Expected Result:
- All past leave requests
- Status (Approved/Rejected/Pending)
- Dates and leave types

---

## 🔧 IT Agent Tools & Demo Queries

### 1. **Create Ticket**
*Create IT support tickets*
```
Demo Query: "My laptop monitor is not displaying anything - I think it's broken. This is critical!"
Demo Query: "I can't connect to company WiFi, medium priority"
Demo Query: "GitHub access not working, I need it for development"
Expected Result:
- Ticket created (TKT-XXX)
- Priority assigned
- LLM suggests resolution
- Ticket tracked
```

### 2. **Get Ticket Status**
*Check ticket progress*
```
Demo Query: "What's the status of ticket TKT-001?"
Demo Query: "Is my WiFi ticket TKT-002 resolved yet?"
Expected Result:
- Current status displayed
- Resolution details (if resolved)
- Priority level shown
```

### 3. **Resolve Ticket**
*Close completed tickets*
```
Demo Query: "Ticket TKT-001 is resolved - we replaced the monitor"
Demo Query: "Fixed the WiFi issue by resetting network settings"
Expected Result:
- Ticket marked as resolved
- Resolution logged
- Employee notified
```

### 4. **Grant Access**
*Provide system access to employees*
```
Demo Query: "Grant me VPN access for remote work"
Demo Query: "I need GitHub admin access for my project"
Demo Query: "Can I get read-only access to the AWS console?"
Demo Query: "Please provide JIRA access and Slack access"
Expected Result:
- Access provisioned
- User credentials provided
- Email confirmation sent
- Access level recorded
```

### 5. **Revoke Access**
*Remove system access*
```
Demo Query: "Revoke AWS console access - employee left"
Demo Query: "Remove GitHub access due to project completion"
Expected Result:
- Access removed immediately
- Reason logged
- Audit trail maintained
```

### 6. **Manage Software License**
*Assign/release software licenses*
```
Demo Query: "Assign a Microsoft Office license to EMP001"
Demo Query: "Release the Adobe Creative Suite license - no longer needed"
Expected Result:
- License allocated/released
- Tracked for reporting
- Automatic notifications
```

### 7. **Track Asset**
*Monitor IT equipment*
```
Demo Query: "Which laptop is assigned to me?"
Demo Query: "List all assets for employee EMP001"
Demo Query: "Find asset ASSET-123"
Expected Result:
- Asset details shown
- Assignment tracking
- Equipment list per employee
```

### 8. **Get Open Tickets Summary**
*View all pending tickets*
```
Demo Query: "Show me all open IT tickets"
Demo Query: "What tickets are currently pending?"
Expected Result:
- List of all open tickets
- Priority breakdown
- Category distribution
- Status patterns

---

## 💰 Finance Agent Tools & Demo Queries

### 1. **Submit Expense**
*Create expense claims*
```
Demo Query: "I need to submit an expense: $250 travel reimbursement for client visit in Mumbai"
Demo Query: "Expense claim - $75 for office supplies for team"
Demo Query: "Submit meal expenses: $45 for client meeting lunch"
Expected Result:
- Expense ID created (EXP-XXX)
- Amount validated
- Category assigned
- Awaiting approval status
```

### 2. **Get Expense Status**
*Check expense progress*
```
Demo Query: "What's the status of my expense claim EXP-001?"
Demo Query: "Is expense EXP-002 approved?"
Expected Result:
- Current status (Submitted/Approved/Rejected/Paid)
- Approver name
- Next steps
```

### 3. **Approve Expense**
*Approve/reject expenses*
```
Demo Query: "Approve expense EXP-001 for $250 travel reimbursement"
Demo Query: "Reject expense EXP-002 - duplicate submission"
Expected Result:
- Decision recorded
- Employee notified
- Status updated
```

### 4. **Process Reimbursement**
*Pay approved expenses*
```
Demo Query: "Process reimbursement for approved expense EXP-001"
Expected Result:
- Payment initiated
- Bank transfer scheduled
- Employee notified with transaction details
- Receipt filed
```

### 5. **Process Payroll**
*Run monthly payroll*
```
Demo Query: "Process payroll for May 2026"
Demo Query: "Run payroll for March 2026"
Expected Result:
- Salary calculations
- Tax deductions applied
- Deductions processed
- Payment scheduled
```

### 6. **Get Payroll Summary**
*View payroll details*
```
Demo Query: "Show me the payroll summary for May 2026"
Demo Query: "What was the payroll for April 2026?"
Expected Result:
- Total employees paid
- Total payroll amount
- Deductions summary
- Payment date
```

### 7. **Manage Budget**
*Handle department budgets*
```
Demo Query: "What's the budget for IT department?"
Demo Query: "Allocate $50,000 budget to Engineering for tools"
Expected Result:
- Budget information displayed
- Allocation recorded
- Tracking updated
```

### 8. **Ask Finance Policy**
*Finance policy questions*
```
Demo Query: "What's our expense claim limit per trip?"
Demo Query: "What categories of expenses can we claim?"
Demo Query: "When are bonuses paid?"
Expected Result:
- Policy details provided
- Employee-specific info shown
- Guidelines clarified

---

## 📋 Compliance Agent Tools & Demo Queries

### 1. **Report Violation**
*Document compliance violations*
```
Demo Query: "Report a violation: Employee working beyond 10 PM daily, multiple days - High severity"
Demo Query: "Report GDPR violation: Sensitive employee data not encrypted"
Demo Query: "Report code of conduct violation - unprofessional behavior - Medium severity"
Expected Result:
- Violation ID created (VIO-XXX)
- Severity tracked
- History maintained
- Alerts sent
```

### 2. **Get Violation Status**
*Check violation progress*
```
Demo Query: "What's the status of violation VIO-001?"
Demo Query: "Has violation VIO-002 been resolved?"
Expected Result:
- Current status
- Resolution details (if resolved)
- Timeline shown
```

### 3. **Resolve Violation**
*Close compliance issues*
```
Demo Query: "Resolve violation VIO-001 - Employee received training on work hours policy"
Demo Query: "Mark VIO-002 as resolved - All data encrypted"
Expected Result:
- Violation closed
- Resolution documented
- Audit trail updated
```

### 4. **Schedule Training**
*Assign compliance training*
```
Demo Query: "Schedule GDPR training for EMP001, due June 30, 2026 - mandatory"
Demo Query: "Assign Data Protection training to all Engineering team - due July 15"
Demo Query: "Schedule code of conduct training for new hires"
Expected Result:
- Training scheduled
- Due date set
- Mandatory flag recorded
- Reminders sent
```

### 5. **Get Training Status**
*Check training progress*
```
Demo Query: "What's EMP001's training status?"
Demo Query: "Who hasn't completed GDPR training?"
Expected Result:
- Training list displayed
- Completion status
- Overdue items highlighted
```

### 6. **Run Compliance Audit**
*Comprehensive compliance check*
```
Demo Query: "Run a full compliance audit"
Demo Query: "Execute compliance audit for Data Protection"
Expected Result:
- Audit findings
- Violations identified
- Recommendations provided
- Report generated
```

### 7. **Manage Document**
*Handle compliance documents*
```
Demo Query: "Upload GDPR compliance document - 2026 Annual Report"
Demo Query: "List all compliance training documents"
Expected Result:
- Documents stored
- Audit trail maintained
- Version control
- Easy retrieval

---

## 🎬 Demo Script for Review

### Scenario 1: Complete HR Flow (5 minutes)
1. Employee asks: **"I want to take casual leave from May 10 to May 14"**
   - Shows leave balance check
   - Auto-approval
   - Email notification

2. Then ask: **"What's company policy on remote work?"**
   - Shows policy retrieval
   - Employee-specific context

### Scenario 2: IT Support Flow (5 minutes)
1. Employee reports: **"My laptop is not charging"**
   - Creates High priority ticket
   - Suggests troubleshooting

2. Then ask: **"I need GitHub access for development"**
   - Shows access provisioning
   - Shows permission levels

### Scenario 3: Finance Flow (5 minutes)
1. Employee submits: **"I need to claim $200 travel expenses for client visit"**
   - Creates expense claim
   - Awaits approval

2. Then query: **"Show payroll summary for May 2026"**
   - Shows complete payroll info

### Scenario 4: Emergency Handling (3 minutes)
1. Query: **"Colleague got heart attack in office!"**
   - Shows immediate first-aid instructions
   - Emergency notifications
   - HR alerts

### Scenario 5: Compliance Flow (3 minutes)
1. Report: **"Employee not following work hour policy - critical"**
   - Creates violation record
   - Shows escalation

2. Then: **"Schedule GDPR training for EMP001"**
   - Shows training assignment

---

## 💡 Pro Tips for Demo

✅ **Chat Examples to Start With:**
- Start with simple queries (e.g., "check my leave balance")
- Progress to complex ones (e.g., "submit expense with approval workflow")
- End with emergency scenario to show intelligent routing

✅ **Show Off Features:**
- **Multi-Agent Routing**: Ask different question types in sequence
- **Context Awareness**: Show how agent remembers employee context
- **Email Notifications**: Refresh browser and show confirmation emails
- **Security**: Highlight access controls and audit trails
- **Learning**: Show how system improves over time

✅ **Backup Queries if Needed:**
- If LLM response is slow: Use simpler queries
- If tool fails: Have a conversation-based backup query
- If you need quick demo: Use the 3-5 minute scenarios above

✅ **Timeline Suggestions:**
- 15-20 minute total demo
- 3-4 minutes per agent (HR → IT → Finance → Compliance)
- 2-3 minutes for emergency scenario
- 2-3 minutes for Q&A

---

## 🚀 System Capabilities to Highlight

### During Demo Mention:
1. **Multi-Agent Orchestration**: System intelligently routes HR vs IT vs Finance questions
2. **Tool-Use Framework**: Each agent has 7-8 specialized tools for their domain
3. **Autonomous Decision Making**: Agents use ReAct loop (Perceive → Reason → Act → Evaluate → Learn)
4. **Emergency Handling**: Detects medical emergencies and bypasses normal workflows
5. **Email Integration**: Real SMTP configured for HR alerts, approvals, notifications
6. **Database Persistence**: All data stored and tracked for audit
7. **Learning System**: Agents learn from interactions and improve over time

---

Last Updated: May 6, 2026
