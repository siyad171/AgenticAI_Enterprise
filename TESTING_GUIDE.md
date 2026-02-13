# 🧪 Complete Feature Testing Guide
**Agentic AI Enterprise Platform — Manual Testing Checklist**

---

## 📋 Prerequisites

### 1. Start the Application
```powershell
cd "c:\Users\siyad\OneDrive\Desktop\College Project\AgenticAI_Enterprise"
.\.venv\Scripts\Activate.ps1
streamlit run ui/app.py
```

### 2. Verify Setup
- ✅ App opens at `http://localhost:8501`
- ✅ No red error messages in terminal
- ✅ Groq API key is valid in `.env` file
- ✅ You see the login page with 3 tabs

### 3. Test Credentials (Pre-seeded in Database)
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Employee (John) | `john.doe` | `pass123` |
| Employee (Jane) | `jane.smith` | `pass123` |
| New Candidate | Create during test | Create during test |

---

## 🎯 PART 1: CANDIDATE PORTAL (Recruitment & Interviews)

### Test 1.1: Candidate Registration & Resume Upload
**Where:** Login Page → Candidate Login Tab

**Steps:**
1. Click **"Candidate Login"** tab
2. Enter any username (e.g., `test_candidate_001`)
3. Enter any password (e.g., `test123`)
4. Click **"Login / Register"**

**Expected:**
- ✅ You're redirected to "Candidate Application Portal"
- ✅ See "Step 1: Basic Information" form

**Steps (continued):**
5. Fill in:
   - Full Name: `Alice Johnson`
   - Email: `alice@test.com`
   - Phone: `9876543210`
   - Position: Select `Senior Python Developer`
6. Upload a PDF resume (create a simple text file named `resume.pdf` if needed)
7. Click **"Submit Application"**

**Expected:**
- ✅ Success message: "✅ Application submitted successfully!"
- ✅ Shows candidate ID (e.g., `CAND003`)
- ✅ Shows extracted skills (Python, Django, etc.)
- ✅ Shows evaluation score (40-100%)
- ✅ Decision: "Accepted" / "Pending Review" / "Rejected"
- ✅ Button to "Proceed to MCQ Test" appears

**What's Being Tested:**
- Resume PDF parsing
- LLM-based skill extraction
- Automatic candidate evaluation
- Score calculation (skill match + experience + education)
- Database candidate creation

---

### Test 1.2: MCQ Technical Test
**Where:** Candidate Portal → After Application

**Steps:**
1. Click **"Proceed to MCQ Test"**
2. Answer 5 multiple-choice questions
3. Click **"Submit Answers"**

**Expected:**
- ✅ Shows score (e.g., "You scored 4/5 (80%)")
- ✅ Pass/Fail status (≥60% = Pass)
- ✅ If passed: Button to "Proceed to Technical Interview"
- ✅ Test score saved in database

**What's Being Tested:**
- MCQ question rendering
- Answer submission
- Score calculation
- Pass/fail threshold logic

---

### Test 1.3: AI Chat Interview
**Where:** Candidate Portal → Technical Interview Choice

**Steps:**
1. Click **"Proceed to Technical Interview"**
2. Choose **"Chat with AI Interviewer"**
3. Select a problem (e.g., "Two Sum")
4. Click **"Start Chat Interview"**

**Expected:**
- ✅ AI asks: "Can you explain the problem in your own words?"
- ✅ Chat interface with text input

**Steps (continued):**
5. Type your response (e.g., "I need to find two numbers that add up to target")
6. Click **"Send"**
7. Continue conversation through 6 stages:
   - Problem understanding
   - Approach discussion
   - Algorithm design
   - Complexity analysis
   - Edge cases
   - Summary

**Expected at Each Stage:**
- ✅ AI responds with follow-up questions
- ✅ Chat history shows all messages
- ✅ Stage indicator updates (1/6 → 2/6 → ... → 6/6)
- ✅ Can request hints (max 3) by typing "hint"
- ✅ After stage 6: Shows **"Interview Complete"** with summary
- ✅ Final assessment with confidence score

**What's Being Tested:**
- TechnicalInterviewChat class
- 6-stage conversation flow
- LLM dual-model approach (chat + analysis)
- Hint system
- Interview storage (JSON files)
- Stage progression logic

---

### Test 1.4: Quick Code Challenge
**Where:** Candidate Portal → Technical Interview Choice

**Steps:**
1. Go back and choose **"Quick Code Challenge"** instead
2. Select problem "Two Sum"
3. See code editor (streamlit-ace)

**Expected:**
- ✅ Code editor with Python syntax highlighting
- ✅ Problem description shown
- ✅ Default starter code loaded

**Steps (continued):**
4. Write solution:
```python
def solution(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        if target - num in seen:
            return [seen[target - num], i]
        seen[num] = i
    return []
```
5. Click **"Run Code"**

**Expected:**
- ✅ Test results table appears
- ✅ Shows "Passed" for correct test cases
- ✅ Shows execution time
- ✅ Overall pass rate (e.g., "2/2 tests passed")

**Steps (continued):**
6. Click **"Submit for AI Review"**

**Expected:**
- ✅ AI feedback appears in expandable section
- ✅ Shows code quality assessment
- ✅ Performance/style suggestions
- ✅ Security notes (if any)

7. Click **"Submit Solution"**

**Expected:**
- ✅ Success message
- ✅ Solution saved to storage
- ✅ Button to proceed to psychometric test

**What's Being Tested:**
- Code editor integration (streamlit-ace)
- Code execution (Judge0 API or local fallback)
- Test case validation
- AI code analyzer (AICodeAnalyzer class)
- Interview storage persistence

---

### Test 1.5: Psychometric Assessment
**Where:** Candidate Portal → After Technical Interview

**Steps:**
1. Click **"Proceed to Psychometric Assessment"**
2. Answer all 20 questions (select any option for each)
3. Click **"Submit Assessment"**

**Expected:**
- ✅ Shows 4 dimension scores:
  - 🧠 Emotional Quotient (EQ) - 30%
  - 🔄 Adaptability Quotient (AQ) - 25%
  - 🤝 Behavioral Quotient (BQ) - 25%
  - 💬 Social Quotient (SQ) - 20%
- ✅ Each dimension shows:
  - Raw score (e.g., 18/25)
  - Percentage (e.g., 72%)
  - Color-coded card
- ✅ Overall weighted score (e.g., 68.5%)
- ✅ AI-generated feedback for each dimension
- ✅ Expandable "View Detailed Feedback" section

**What's Being Tested:**
- PsychometricAssessment class
- 20-question form rendering
- Answer submission tracking
- Weighted score calculation (EQ 30%, AQ 25%, BQ 25%, SQ 20%)
- LLM feedback generation
- Results storage

---

### Test 1.6: Video Interview (Optional)
**Where:** Candidate Portal → After Psychometric

**Steps:**
1. Click **"Proceed to Video Interview"**
2. If you see "Video analysis libraries not installed":
   - Click **"Skip Video Interview"**
   - ✅ Proceeds to final results
3. If video upload is available:
   - Upload any video file (MP4)
   - Click **"Submit Video"**

**Expected (if libraries installed):**
- ✅ Processing message appears
- ✅ Shows transcription of speech
- ✅ Shows confidence metrics:
  - Transcript Clarity Score
  - Visual Confidence Score
  - Overall Confidence Score
- ✅ Detailed analysis with timestamps

**What's Being Tested:**
- Video file upload
- HybridVideoAnalyzer class
- Whisper speech-to-text
- Confidence scoring (60% transcript + 40% visual)
- Graceful fallback when heavy deps missing

---

### Test 1.7: Final Results Viewer
**Where:** Candidate Portal → After All Steps

**Expected:**
- ✅ "Application Complete! 🎉" message
- ✅ Summary card showing:
  - Candidate ID
  - Applied Position
  - Application Date
  - Current Status
- ✅ Detailed results:
  - MCQ Score
  - Technical Interview (Chat or Code)
  - Psychometric Overall Score
  - Video Analysis (if completed)
- ✅ Final recommendation
- ✅ Next steps instructions

**What's Being Tested:**
- InterviewStorage.get_final_report()
- Results aggregation
- Multi-format display
- Complete candidate journey tracking

---

## 👨‍💼 PART 2: EMPLOYEE PORTAL (Self-Service)

### Test 2.1: Employee Login & Dashboard
**Where:** Login Page → Employee Login Tab

**Steps:**
1. Click **"Employee Login"** tab
2. Username: `john.doe`
3. Password: `pass123`
4. Click **"Login"**

**Expected:**
- ✅ Welcome message: "Welcome, John Doe!"
- ✅ Dashboard shows:
  - Leave balance (Casual: 12, Sick: 15, Annual: 20)
  - Recent leave requests table
  - Department: Engineering
  - Position: Senior Developer
- ✅ Sidebar has navigation: Dashboard, Leave Request, Policy Q&A, Profile

**What's Being Tested:**
- User authentication
- Database user/employee lookup
- Session state management
- Dashboard data aggregation

---

### Test 2.2: Leave Request Submission
**Where:** Employee Portal → Leave Request

**Steps:**
1. Click **"📝 Leave Request"** in sidebar
2. Fill form:
   - Leave Type: `Casual Leave`
   - Start Date: Tomorrow's date
   - End Date: Day after tomorrow
   - Reason: `Family event`
3. Click **"Submit Request"**

**Expected:**
- ✅ Success message with request ID (e.g., "LR20260210123045")
- ✅ Decision shown:
  - **"Approved"** (if ≤10 days + balance sufficient)
  - **"Pending"** (if >10 days)
  - **"Rejected"** (if insufficient balance or date conflict)
- ✅ Leave balance updated (if approved)
- ✅ Email notification sent (check terminal for SMTP logs)

**What's Being Tested:**
- HR Agent leave processing logic
- Date conflict checking
- Balance validation
- Auto-approval vs manual review
- Email service integration
- Event bus (leave_processed event)

---

### Test 2.3: HR Policy Chatbot
**Where:** Employee Portal → Policy Q&A

**Steps:**
1. Click **"💬 Policy Q&A"** in sidebar
2. Type question: `What is the leave policy?`
3. Click **"Ask"**

**Expected:**
- ✅ AI response appears with policy details
- ✅ Mentions Casual/Sick/Annual leave types
- ✅ References database context

**Steps (continued):**
4. Ask: `How many days of annual leave does John Doe have?`
5. Click **"Ask"**

**Expected:**
- ✅ Response includes specific data: "20 days of Annual Leave"
- ✅ Shows relevant policies section

**What's Being Tested:**
- HR Agent ask_hr_policy_question()
- LLM integration with policy context
- Database querying from natural language
- Employee data extraction from questions

---

### Test 2.4: Profile View
**Where:** Employee Portal → Profile

**Steps:**
1. Click **"👤 Profile"** in sidebar

**Expected:**
- ✅ Shows employee details:
  - ID: EMP001
  - Name: John Doe
  - Email: john.doe@company.com
  - Department: Engineering
  - Position: Senior Developer
  - Join Date: 2023-01-15
  - Leave Balance breakdown

**What's Being Tested:**
- Database employee retrieval
- Profile data display

---

## 🔧 PART 3: ADMIN PORTAL (System Management)

### Test 3.1: Admin Login & Dashboard
**Where:** Login Page → Admin Login Tab

**Steps:**
1. Click **"Admin Login"** tab
2. Username: `admin`
3. Password: `admin123`
4. Click **"Login"**

**Expected:**
- ✅ "Admin Dashboard — System Overview"
- ✅ Four metric cards:
  - 👥 Total Employees (≥2)
  - 📋 Total Candidates (≥1 if you completed Part 1)
  - 🎫 Total Tickets (starts at 0)
  - 💰 Total Expenses (starts at 0)
- ✅ Recent Activity section
- ✅ Links to specialized portals

**What's Being Tested:**
- Admin authentication
- System-wide statistics aggregation
- Database counts across all modules

---

### Test 3.2: Employee Management
**Where:** Admin Portal → Employee Management

**Steps:**
1. Click **"👥 Employee Management"** in sidebar
2. See employee list table

**Expected:**
- ✅ Shows EMP001 (John Doe) and EMP002 (Jane Smith)
- ✅ Columns: ID, Name, Email, Department, Position, Join Date

**Steps (continued):**
3. Click **"➕ Add New Employee"** expander
4. Fill form:
   - Name: `Bob Wilson`
   - Email: `bob@company.com`
   - Department: `Finance`
   - Position: `Accountant`
   - Join Date: Today's date
5. Click **"Add Employee"**

**Expected:**
- ✅ Success message with new ID (e.g., EMP003)
- ✅ Employee appears in table
- ✅ Event published: "employee_onboarded"
- ✅ IT/Compliance agents notified (check orchestrator)

**What's Being Tested:**
- HR Agent handle_employee_onboarding()
- Database employee creation
- Event bus publishing
- Cross-agent coordination

---

### Test 3.3: Candidate Review
**Where:** Admin Portal → Candidate Review

**Steps:**
1. Click **"📋 Candidate Review"** in sidebar

**Expected:**
- ✅ Shows candidates table
- ✅ Your test candidate from Part 1 appears
- ✅ Columns: ID, Name, Position, Status, Evaluation Score

**Steps (continued):**
2. Select a candidate from dropdown
3. Click **"View Details"**

**Expected:**
- ✅ Shows full candidate profile:
  - Personal info
  - Resume text
  - Extracted skills
  - Evaluation results
  - Test scores
  - Interview results (if completed)
- ✅ "Update Status" section
- ✅ Can change status to Hired/Rejected

**What's Being Tested:**
- Database candidate retrieval
- Evaluation result display
- Status update functionality

---

### Test 3.4: Audit Report Generation
**Where:** Admin Portal → Audit Report

**Steps:**
1. Click **"📊 Audit Report"** in sidebar
2. Leave default dates (last 30 days)
3. Click **"Generate Report"**

**Expected:**
- ✅ Report ID generated (e.g., AUDIT20260210...)
- ✅ Summary statistics:
  - Total activities count
  - Leave requests (Approved/Rejected/Pending breakdown)
  - Onboarding count
  - Policy questions count
- ✅ Detailed logs table with:
  - Timestamp
  - Agent
  - Action
  - User
  - Details
- ✅ Compliance status: "COMPLIANT" or "ISSUES_FOUND"
- ✅ Compliance issues list (e.g., pending requests >7 days)

**What's Being Tested:**
- HR Agent generate_audit_report()
- Audit log filtering by date
- Activity categorization
- Compliance checking logic

---

### Test 3.5: System Settings
**Where:** Admin Portal → Settings

**Steps:**
1. Click **"⚙️ Settings"** in sidebar

**Expected:**
- ✅ Shows current configuration:
  - LLM models
  - HR thresholds (Accept: 50%, Review: 40%, Test Pass: 60%)
  - IT settings
  - Finance limits (Auto-approve: ₹5000, Budget alert: 90%)
  - Compliance defaults
  - Learning module status
- ✅ Can view/modify settings (if implemented)

**What's Being Tested:**
- Config file values display
- System parameter visibility

---

## 💻 PART 4: IT PORTAL (IT Support)

### Test 4.1: Create IT Ticket
**Where:** Admin Portal → 🖥️ IT Portal → Create Ticket

**Steps:**
1. Click **"🖥️ IT Portal"** link
2. Click **"🎫 Create Ticket"** in sidebar
3. Fill form:
   - Employee: Select `John Doe (EMP001)`
   - Issue Type: `Hardware`
   - Priority: `High`
   - Description: `Laptop screen flickering`
4. Click **"Create Ticket"**

**Expected:**
- ✅ Success message with ticket ID (e.g., TKT20260210...)
- ✅ Ticket appears in "View Tickets" table
- ✅ Status: "Open"
- ✅ AI troubleshooting suggestions appear

**What's Being Tested:**
- IT Agent create_ticket()
- Ticket ID generation
- LLM-based troubleshooting suggestions
- Database ticket storage

---

### Test 4.2: Resolve IT Ticket
**Where:** IT Portal → View Tickets

**Steps:**
1. Click **"📋 View Tickets"** in sidebar
2. Select the ticket you just created
3. Click **"View Details"**
4. In "Resolve Ticket" section:
   - Status: `Resolved`
   - Resolution Notes: `Replaced display cable`
5. Click **"Update Ticket"**

**Expected:**
- ✅ Success message
- ✅ Ticket status changed to "Resolved"
- ✅ Resolved date recorded
- ✅ Resolution notes saved

**What's Being Tested:**
- IT Agent resolve_ticket()
- Ticket status updates
- Resolution tracking

---

### Test 4.3: Access Management
**Where:** IT Portal → Access Management

**Steps:**
1. Click **"🔑 Access Management"** in sidebar
2. Click **"Grant Access"** tab
3. Fill form:
   - Employee: `Bob Wilson (EMP003)`
   - Access Type: `VPN`
   - Reason: `Remote work access`
4. Click **"Grant Access"**

**Expected:**
- ✅ Success message with access ID
- ✅ Access record created
- ✅ Status: "Active"

**Steps (continued):**
5. Click **"Revoke Access"** tab
6. Select Bob Wilson's VPN access
7. Enter reason: `Employee offboarded`
8. Click **"Revoke Access"**

**Expected:**
- ✅ Success message
- ✅ Access status changed to "Revoked"
- ✅ Revoked date recorded

**What's Being Tested:**
- IT Agent grant_access() and revoke_access()
- Access record lifecycle
- Multi-access type support

---

### Test 4.4: Asset Tracking
**Where:** IT Portal → Asset Tracking

**Steps:**
1. Click **"💼 Asset Tracking"** in sidebar
2. In "Add Asset" section:
   - Asset Type: `Laptop`
   - Serial Number: `LAP-12345`
   - Assign to: `John Doe (EMP001)`
   - Purchase Date: Last month
   - Warranty Expiry: Next year
   - Condition: `Excellent`
3. Click **"Add Asset"**

**Expected:**
- ✅ Success message with asset ID
- ✅ Asset appears in "Current Assets" table
- ✅ Shows assignment to John Doe

**What's Being Tested:**
- IT Agent add_asset()
- Asset assignment
- Warranty tracking

---

## 💰 PART 5: FINANCE PORTAL

### Test 5.1: Submit Expense Claim
**Where:** Admin Portal → 💰 Finance Portal → Submit Expense

**Steps:**
1. Click **"💰 Finance Portal"** link
2. Click **"💳 Submit Expense"** in sidebar
3. Fill form:
   - Employee: `John Doe (EMP001)`
   - Category: `Travel`
   - Amount: `3500`
   - Description: `Client meeting in Mumbai`
   - Date: Today
4. Click **"Submit Claim"**

**Expected:**
- ✅ Success message with expense ID
- ✅ Status: **"Approved"** (because ₹3,500 < ₹5,000 auto-approve threshold)
- ✅ Shows in "View Expenses" table

**Steps (continued):**
5. Submit another expense:
   - Category: `Training`
   - Amount: `15000`
   - Description: `AWS certification course`
6. Click **"Submit Claim"**

**Expected:**
- ✅ Status: **"Pending"** (because ₹15,000 > ₹5,000 threshold)
- ✅ Requires manual approval

**What's Being Tested:**
- Finance Agent submit_expense()
- Auto-approval logic (< ₹5,000)
- Manual review threshold
- Expense categorization

---

### Test 5.2: Approve Expense
**Where:** Finance Portal → Approve Expenses

**Steps:**
1. Click **"✅ Approve Expenses"** in sidebar
2. See pending expenses table
3. Select the ₹15,000 training expense
4. Click **"View Details"**
5. Status: `Approved`
6. Notes: `Training approved by manager`
7. Click **"Update Expense"**

**Expected:**
- ✅ Success message
- ✅ Expense status changed to "Approved"
- ✅ Approval date recorded

**What's Being Tested:**
- Finance Agent approve_expense()
- Manual approval workflow
- Approval notes tracking

---

### Test 5.3: Process Payroll
**Where:** Finance Portal → Process Payroll

**Steps:**
1. Click **"💼 Process Payroll"** in sidebar
2. Click **"Process Monthly Payroll"** button

**Expected:**
- ✅ Processing message
- ✅ Success: "Payroll processed for X employees"
- ✅ Summary table shows:
  - Employee names
  - Base salary
  - Deductions
  - Net pay
  - Status: "Paid"
- ✅ Total payroll amount displayed

**What's Being Tested:**
- Finance Agent process_payroll()
- Payroll calculation with deductions
- Bulk processing
- Payroll record creation

---

### Test 5.4: Budget Management
**Where:** Finance Portal → Budget Management

**Steps:**
1. Click **"📊 Budget Management"** in sidebar
2. See current budgets table
3. In "Allocate Budget" section:
   - Department: `Marketing`
   - Quarter: `Q1`
   - Year: `2026`
   - Amount: `500000`
4. Click **"Allocate Budget"**

**Expected:**
- ✅ Success message with budget ID
- ✅ Budget appears in table
- ✅ Shows: Allocated: ₹5,00,000 | Spent: ₹0 | Remaining: ₹5,00,000
- ✅ Utilization: 0%

**What's Being Tested:**
- Finance Agent allocate_budget()
- Budget tracking
- Utilization calculation
- Budget alert system (triggers at 90%)

---

## 📋 PART 6: COMPLIANCE PORTAL

### Test 6.1: Report Violation
**Where:** Admin Portal → 📋 Compliance Portal → Report Violation

**Steps:**
1. Click **"📋 Compliance Portal"** link
2. Click **"⚠️ Report Violation"** in sidebar
3. Fill form:
   - Type: `Data Privacy`
   - Severity: `Moderate`
   - Employee: `John Doe (EMP001)`
   - Description: `Shared customer data via personal email`
4. Click **"Report Violation"**

**Expected:**
- ✅ Success message with violation ID
- ✅ Status: "Reported"
- ✅ Appears in violations table
- ✅ Reported date recorded

**What's Being Tested:**
- Compliance Agent report_violation()
- Violation categorization (6 types)
- Severity tracking (Minor/Moderate/Major/Critical)

---

### Test 6.2: Resolve Violation
**Where:** Compliance Portal → View Violations

**Steps:**
1. Click **"📋 View Violations"** in sidebar
2. Select the violation you just created
3. In "Resolve Violation" section:
   - Status: `Resolved`
   - Actions Taken: `Employee counseled, data security training scheduled`
4. Click **"Update Violation"**

**Expected:**
- ✅ Success message
- ✅ Status changed to "Resolved"
- ✅ Resolution date recorded
- ✅ Actions taken saved

**What's Being Tested:**
- Compliance Agent resolve_violation()
- Investigation workflow
- Action tracking

---

### Test 6.3: Schedule Training
**Where:** Compliance Portal → Training Management

**Steps:**
1. Click **"📚 Training Management"** in sidebar
2. In "Schedule Training" section:
   - Employee: `Bob Wilson (EMP003)`
   - Training Type: `Data Privacy`
   - Scheduled Date: Next week
3. Click **"Schedule Training"**

**Expected:**
- ✅ Success message with training ID
- ✅ Status: "Scheduled"
- ✅ Appears in training records table

**Steps (continued):**
4. Select Bob's training record
5. Mark as complete:
   - Status: `Completed`
   - Completion Date: Today
   - Certificate ID: `CERT-2026-001`
6. Click **"Update Training"**

**Expected:**
- ✅ Status changed to "Completed"
- ✅ Completion date recorded
- ✅ Certificate ID saved

**What's Being Tested:**
- Compliance Agent schedule_training()
- Training lifecycle (Scheduled → Completed)
- Certificate tracking
- 5 training types support

---

### Test 6.4: Compliance Audit
**Where:** Compliance Portal → Compliance Audit

**Steps:**
1. Click **"🔍 Compliance Audit"** in sidebar
2. In "Conduct Audit" section:
   - Audit Type: `Internal`
   - Auditor: `External Firm XYZ`
   - Findings: `2 minor policy violations found`
   - Score: `85`
   - Recommendations: `Update data retention policy`
3. Click **"Record Audit"**

**Expected:**
- ✅ Success message with audit ID
- ✅ Audit appears in table
- ✅ Shows score: 85%
- ✅ Next audit date calculated

**What's Being Tested:**
- Compliance Agent conduct_audit()
- Audit types (Internal/External/Regulatory/ISO/GDPR)
- Score tracking
- Recommendations recording

---

### Test 6.5: Compliance Policy Q&A
**Where:** Compliance Portal → Policy Q&A

**Steps:**
1. Click **"💬 Policy Q&A"** in sidebar
2. Ask: `What is our data privacy policy?`
3. Click **"Ask"**

**Expected:**
- ✅ AI response with policy details
- ✅ Mentions GDPR compliance, data handling, etc.

**What's Being Tested:**
- Compliance Agent ask_compliance_policy_question()
- LLM integration with compliance policies
- Policy database access

---

## 🎛️ PART 7: ORCHESTRATOR DASHBOARD

### Test 7.1: Agent Status Monitoring
**Where:** Admin Portal → 🎛️ Orchestrator Dashboard

**Steps:**
1. Click **"🎛️ Orchestrator Dashboard"** link
2. View "Agent Status" section

**Expected:**
- ✅ Four agent cards:
  - 🤝 HR Agent (7 capabilities)
  - 💻 IT Agent (7 capabilities)
  - 💰 Finance Agent (8 capabilities)
  - 📋 Compliance Agent (8 capabilities)
- ✅ Each card shows:
  - Capabilities count
  - Recent actions (if any)
  - Status indicator

**What's Being Tested:**
- Orchestrator get_dashboard()
- Agent metadata aggregation
- Capability counting

---

### Test 7.2: Task Routing
**Where:** Orchestrator Dashboard → Route Task

**Steps:**
1. Click **"🎯 Route Task"** in sidebar
2. Enter task: `I need to apply for leave`
3. Click **"Route Task"**

**Expected:**
- ✅ Routed to: **HR Agent**
- ✅ Shows reasoning (LLM explanation)
- ✅ Confidence score displayed

**Steps (continued):**
4. Try: `My laptop is broken`
5. Click **"Route Task"**

**Expected:**
- ✅ Routed to: **IT Agent**

**Steps (continued):**
6. Try: `I need to submit an expense claim`
7. Click **"Route Task"**

**Expected:**
- ✅ Routed to: **Finance Agent**

**Steps (continued):**
8. Try: `Report a security violation`
9. Click **"Route Task"**

**Expected:**
- ✅ Routed to: **Compliance Agent**

**What's Being Tested:**
- Orchestrator route_task()
- LLM-based task classification
- Natural language understanding
- Agent routing logic
- Fallback handling (defaults to HR for ambiguous)

---

### Test 7.3: Workflow Execution
**Where:** Orchestrator Dashboard → Execute Workflow

**Steps:**
1. Click **"⚙️ Execute Workflow"** in sidebar
2. Select workflow: `new_hire`
3. Fill parameters:
   - Name: `Carol Davis`
   - Email: `carol@company.com`
   - Department: `Sales`
   - Position: `Sales Manager`
   - Join Date: Today
4. Click **"Execute Workflow"**

**Expected:**
- ✅ Workflow execution starts
- ✅ Shows step-by-step progress:
  1. ✅ HR onboards employee (creates EMP00X)
  2. ✅ IT creates access request
  3. ✅ Compliance schedules training
- ✅ Final status: "completed"
- ✅ Employee appears in Employee Management

**Steps (continued):**
5. Try workflow: `expense_claim`
6. Parameters:
   - Employee: `EMP001`
   - Amount: `8000`
   - Category: `Client Meeting`
7. Click **"Execute Workflow"**

**Expected:**
- ✅ Finance processes expense
- ✅ Creates reimbursement record
- ✅ Shows approval status

**What's Being Tested:**
- Orchestrator execute_workflow()
- Multi-agent coordination
- 4 workflows:
  - `new_hire` (HR → IT → Compliance)
  - `employee_exit` (HR → IT → Finance → Compliance)
  - `expense_claim` (Finance)
  - `security_incident` (IT → Compliance)
- Event-driven architecture

---

### Test 7.4: Event Log Viewer
**Where:** Orchestrator Dashboard → View Events

**Steps:**
1. Click **"📜 View Events"** in sidebar

**Expected:**
- ✅ Shows recent events table (last 20)
- ✅ Columns: Timestamp, Event Type, Source, Data
- ✅ Events include:
  - `leave_processed`
  - `employee_onboarded`
  - `ticket_created`
  - `expense_submitted`
  - `violation_reported`
- ✅ Shows JSON data for each event

**What's Being Tested:**
- Event bus get_event_log()
- Event persistence
- Cross-agent event tracking

---

### Test 7.5: System Metrics
**Where:** Orchestrator Dashboard → Metrics

**Steps:**
1. View "System Metrics" section

**Expected:**
- ✅ Shows counts:
  - Total Employees (≥3 after tests)
  - Total Candidates (≥1)
  - Total Tickets (≥1)
  - Total Expenses (≥2)
- ✅ Real-time data from database

**What's Being Tested:**
- Cross-module statistics
- Database aggregation
- Dashboard data integration

---

## 🧪 PART 8: AUTOMATED TEST SUITE

### Test 8.1: Run pytest Tests
**Where:** Terminal

**Steps:**
```powershell
cd "c:\Users\siyad\OneDrive\Desktop\College Project\AgenticAI_Enterprise"
.\.venv\Scripts\Activate.ps1
python -m pytest tests/ -v
```

**Expected:**
```
===================== test session starts =====================
22 passed in ~10s
```

**Expected Tests:**
- ✅ test_seed_data_creates_employees
- ✅ test_seed_data_creates_job_positions
- ✅ test_add_employee
- ✅ test_add_candidate
- ✅ test_leave_balance_update
- ✅ test_audit_log
- ✅ test_subscribe_and_publish
- ✅ test_multiple_subscribers
- ✅ test_event_log
- ✅ test_process_leave_approved
- ✅ test_process_leave_insufficient
- ✅ test_evaluate_candidate
- ✅ test_parse_resume
- ✅ test_hr_policy_question
- ✅ test_audit_report
- ✅ test_full_onboarding_flow
- ✅ test_orchestrator_routes_hr_task
- ✅ test_orchestrator_routes_it_task
- ✅ test_local_executor
- ✅ test_local_executor_timeout
- ✅ test_psychometric_scoring
- ✅ test_interview_storage

**What's Being Tested:**
- All core modules
- Database operations
- Agent functions
- Tool classes
- Integration workflows

---

### Test 8.2: Run Verification Script
**Where:** Terminal

**Steps:**
```powershell
python verify_setup.py
```

**Expected:**
```
  ✅ core.config
  ✅ core.database
  ✅ core.llm_service
  ✅ core.event_bus
  ✅ core.base_agent
  ✅ core.orchestrator
  ✅ core.goal_tracker
  ✅ core.learning_module
  ✅ agents.hr_agent
  ✅ agents.it_agent
  ✅ agents.finance_agent
  ✅ agents.compliance_agent
  ✅ tools.email_service
  ✅ tools.code_executor
  ✅ tools.local_executor
  ✅ tools.ai_code_analyzer
  ✅ tools.interview_storage
  ✅ tools.psychometric_assessment
  ✅ tools.technical_interview_chat

========================================
Results: 19 passed, 0 failed out of 19
All imports OK! Ready to run.
```

**What's Being Tested:**
- All module imports
- No missing dependencies
- Configuration loaded correctly

---

## ✅ SUCCESS CRITERIA CHECKLIST

### Core Functionality (20 items)
- [ ] Candidate can register and upload resume
- [ ] Resume parsing extracts skills automatically
- [ ] Candidate evaluation scores calculated correctly
- [ ] MCQ test works and saves scores
- [ ] AI chat interview progresses through 6 stages
- [ ] Code editor runs code with test cases
- [ ] AI code review provides feedback
- [ ] Psychometric test calculates 4 dimensions
- [ ] Video upload works (or skips gracefully)
- [ ] Final results display all interview data
- [ ] Employee can submit leave requests
- [ ] Leave auto-approval/rejection works correctly
- [ ] HR chatbot answers policy questions
- [ ] Admin can add new employees
- [ ] Admin can view candidate evaluations
- [ ] Audit reports generate with statistics
- [ ] IT tickets can be created and resolved
- [ ] Access management grant/revoke works
- [ ] Expense claims auto-approve under ₹5,000
- [ ] Payroll processing calculates correctly

### Agent Coordination (10 items)
- [ ] Orchestrator routes tasks to correct agents
- [ ] New hire workflow triggers HR → IT → Compliance
- [ ] Event bus publishes events correctly
- [ ] Agents receive events from other agents
- [ ] Compliance training auto-scheduled for new hires
- [ ] IT access auto-granted on onboarding
- [ ] Finance approvals trigger reimbursements
- [ ] Violation reports create audit records
- [ ] Multi-agent workflows complete successfully
- [ ] Event logs track all system activities

### UI/UX (10 items)
- [ ] All three login types work (Candidate/Employee/Admin)
- [ ] Session state persists during navigation
- [ ] Forms validate input correctly
- [ ] Success/error messages display appropriately
- [ ] Tables show data properly
- [ ] Cards display metrics correctly
- [ ] Code editor syntax highlighting works
- [ ] Chat interface shows conversation history
- [ ] Progress indicators update correctly
- [ ] Logout clears session

### Data Persistence (5 items)
- [ ] Employees saved to database
- [ ] Candidates saved with evaluation results
- [ ] Interview data stored in JSON files
- [ ] Audit logs accumulate over time
- [ ] Event log tracks all events

### LLM Integration (5 items)
- [ ] Resume parsing uses LLM (or falls back)
- [ ] Policy Q&A generates relevant answers
- [ ] Task routing classifies correctly
- [ ] Code review provides meaningful feedback
- [ ] Psychometric feedback is personalized

---

## 🐛 Common Issues & Solutions

### Issue 1: "Invalid API Key" Error
**Symptom:** LLM calls fail with 401 error  
**Solution:**
- Verify `.env` has valid Groq API key
- Restart app to reload environment
- Check terminal for "Key loaded: Yes"

### Issue 2: Resume Not Parsing
**Symptom:** Skills not extracted  
**Solution:**
- Check PDF is text-based (not scanned image)
- Fallback parser will still extract common keywords
- Upload different resume or use sample text

### Issue 3: Code Won't Run
**Symptom:** Test execution fails  
**Solution:**
- Judge0 API may be rate-limited (free tier)
- Local fallback executes automatically
- Check code has no infinite loops

### Issue 4: Video Upload Fails
**Symptom:** "Libraries not installed" message  
**Solution:**
- This is expected if heavy deps not installed
- Click "Skip Video Interview" to continue
- Optional: Install DeepFace, OpenCV, librosa, moviepy

### Issue 5: Email Not Sending
**Symptom:** No email notifications  
**Solution:**
- SMTP credentials in `.env` are optional
- Check terminal for email logs (won't actually send without valid SMTP)
- Email service fails gracefully if unconfigured

### Issue 6: Tests Failing
**Symptom:** pytest shows failures  
**Solution:**
- Ensure `.env` has Groq API key (some tests need LLM)
- Re-run with `-v` flag for detailed output
- Check specific test error messages

---

## 📊 Final Verification Report

After completing all tests above, you should have:

### Created Records
- ✅ 1+ new candidates
- ✅ 1+ new employees (Bob Wilson, Carol Davis)
- ✅ 2+ leave requests
- ✅ 1+ IT ticket
- ✅ 1+ access record
- ✅ 1+ IT asset
- ✅ 2+ expense claims
- ✅ 1+ payroll record
- ✅ 1+ budget allocation
- ✅ 1+ violation report
- ✅ 1+ training record
- ✅ 1+ compliance audit
- ✅ Multiple audit logs
- ✅ Multiple event log entries

### Verified Features (Total: 50+)
- ✅ All 7 HR Agent capabilities
- ✅ All 7 IT Agent capabilities
- ✅ All 8 Finance Agent capabilities
- ✅ All 8 Compliance Agent capabilities
- ✅ All 6 Orchestrator features
- ✅ All 12 UI portals
- ✅ All 22 automated tests passing
- ✅ All 19 module imports successful

### System Health
- ✅ No critical errors in terminal
- ✅ All agents operational
- ✅ Database populated with diverse data
- ✅ Event bus tracking activities
- ✅ LLM integration functioning
- ✅ File storage working (interview_results/)

---

## 🎉 Congratulations!

If you've completed all tests above, your **Agentic AI Enterprise Platform** is **fully functional** with:
- ✅ 4 autonomous AI agents
- ✅ Multi-stage candidate recruitment system
- ✅ Employee self-service portal
- ✅ Complete HR/IT/Finance/Compliance workflows
- ✅ Intelligent task routing
- ✅ Event-driven coordination
- ✅ Comprehensive testing suite
- ✅ Production-ready architecture

**Next Steps:**
1. Deploy to Streamlit Community Cloud
2. Add real user data
3. Customize workflows for your organization
4. Extend with additional agents/features
5. Monitor with audit logs and analytics

---

**Questions or Issues?** Check the error logs in terminal and review the troubleshooting section above.
