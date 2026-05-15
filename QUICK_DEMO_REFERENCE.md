# 📱 Quick Demo Cheat Sheet (One-Page Reference)

## Copy-Paste Demo Queries

---

## 🏥 HR AGENT (Copy any below)

```
"I want to take casual leave from May 10 to May 14 for family trip"

"Emp 002 got heart attack what to do?"

"What's company policy on remote work?"

"How many sick leaves do I have left?"

"Tell me about employee EMP001"

"Show me my leave request history"

"Generate an HR audit report for the past 30 days"
```

---

## 🔧 IT AGENT (Copy any below)

```
"My laptop monitor is not working - it's critical!"

"I can't connect to WiFi - medium priority"

"What's the status of ticket TKT-001?"

"Grant me VPN access for remote work"

"I need GitHub admin access"

"Which laptop is assigned to me?"

"Show me all open IT tickets"

"Release my Adobe license - no longer needed"
```

---

## 💰 FINANCE AGENT (Copy any below)

```
"I need to submit an expense: $250 travel reimbursement"

"What's the status of expense EXP-001?"

"Approve expense EXP-001 for $250"

"Process reimbursement for EXP-001"

"Show payroll summary for May 2026"

"Process payroll for May 2026"

"What's the IT department budget?"

"Allocate $50,000 to Engineering team"
```

---

## 📋 COMPLIANCE AGENT (Copy any below)

```
"Report violation: Employee working 10+ hours daily - High severity"

"What's the status of violation VIO-001?"

"Resolve violation VIO-001 - Employee completed training"

"Schedule GDPR training for EMP001, due June 30 - mandatory"

"What's EMP001's training status?"

"Run a full compliance audit"

"Upload GDPR compliance document - 2026 Annual Report"

"List all compliance documents"
```

---

## 🎯 DEMO SEQUENCE (Recommended Order - 15 mins)

### Part 1: HR Agent (3 min)
1. "I want to take casual leave from May 10 to May 14"
   → Shows leave balance, auto-approval
2. "What's company policy on remote work?"
   → Shows policy from database

### Part 2: IT Agent (3 min)
1. "My laptop monitor is not working - critical!"
   → Creates ticket, shows priority
2. "Grant me VPN access for remote work"
   → Shows access provisioning

### Part 3: Finance Agent (3 min)
1. "I need to submit expense: $250 travel reimbursement"
   → Creates expense claim
2. "Show payroll summary for May 2026"
   → Shows payroll details

### Part 4: Emergency Handling (2 min)
1. "Someone got heart attack in office!"
   → Shows first-aid, HR alert, emergency protocol

### Part 5: Compliance Agent (2 min)
1. "Report violation: Not following work hours - Critical"
   → Creates violation
2. "Schedule GDPR training for EMP001"
   → Shows training assignment

### Q&A (2 min)
- Answer review questions
- Show email notifications (refresh UI)
- Demo learning module

---

## 🎬 Performance Tips

✅ **Pre-Demo:**
- Keep browser open to Employee Portal
- Be logged in as John Doe (username: john.doe, password: pass123)
- Have this cheat sheet ready

✅ **During Demo:**
- Copy-paste queries from above (no typing errors)
- Highlight each agent's unique capabilities
- Show planning steps (agent routing, tool selection)
- Mention email notifications being sent

✅ **If Something Slow:**
- Use simpler queries (e.g., "check my leave balance")
- Skip complex ones temporarily
- Have fallback: "What's the weather?" (shows conversation fallback)

✅ **Backup Plan:**
- If any agent unavailable: Skip to next agent
- If LLM down: Show system architecture diagram
- Have screenshots of previous successful runs ready

---

## 📊 Expected Results Summary

| Agent | Tool | Time | Expected Output |
|-------|------|------|-----------------|
| HR | Leave Request | 15s | ✅ Approved + Email |
| HR | Policy Q&A | 10s | ✅ Answer + Facts |
| IT | Create Ticket | 12s | ✅ Ticket ID + Priority |
| IT | Grant Access | 10s | ✅ Access + Credentials |
| Finance | Submit Expense | 12s | ✅ Expense ID + Status |
| Finance | Payroll | 8s | ✅ Payroll Summary |
| Emergency | Heart Attack | 20s | ✅ First Aid + Email |
| Compliance | Report Violation | 10s | ✅ Violation ID + Alert |

---

## 🔗 Key URLs

- **App**: http://localhost:8502
- **Employee Login**: john.doe / pass123
- **Admin Login**: admin / admin123

---

## 🎯 Key Talking Points

1. **Multi-Agent Routing** → System knows which agent to use
2. **Tool-Based Architecture** → Each agent has 7-8 specialized tools
3. **Intelligent Planning** → Uses ReAct loop (Perceive → Plan → Act → Learn)
4. **Emergency Detection** → Automatically handles medical emergencies
5. **Real Email Integration** → Actual SMTP notifications
6. **End-to-End Workflows** → Leave request through email confirmation

---

*Last Updated: May 6, 2026*
