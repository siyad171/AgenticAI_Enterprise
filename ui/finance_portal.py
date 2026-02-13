"""Finance Portal — Expenses, payroll, budget"""
import streamlit as st
import datetime


def show_finance_portal():
    fin = st.session_state.agents['finance']
    db = st.session_state.db
    st.header("💰 Finance Management")
    tab1, tab2, tab3 = st.tabs(["📑 Expenses", "💵 Payroll", "📊 Budget"])

    with tab1:
        _expense_management(fin, db)
    with tab2:
        _payroll_management(fin, db)
    with tab3:
        _budget_management(fin, db)


def _expense_management(fin, db):
    st.subheader("Submit Expense")
    with st.form("submit_expense"):
        emp_id = st.selectbox("Employee", list(db.employees.keys()))
        category = st.selectbox("Category",
                                ["Travel", "Equipment", "Software", "Training", "Meals", "Other"])
        amount = st.number_input("Amount ($)", min_value=0.0, step=10.0)
        description = st.text_area("Description")
        if st.form_submit_button("Submit", type="primary"):
            result = fin.submit_expense(emp_id, category, amount, description)
            if result['status'] == 'success':
                st.success(f"✅ {result['message']} (ID: {result['expense_id']})")

    st.subheader("Recent Expenses")
    expenses = getattr(db, 'expenses', {})
    for eid, exp in expenses.items():
        status_icon = "✅" if exp.status == "Approved" else "⏳" if exp.status == "Pending" else "❌"
        with st.expander(f"{status_icon} {eid} — ${exp.amount} ({exp.status})"):
            st.write(f"**Employee:** {exp.employee_id} | **Category:** {exp.category}")
            st.write(f"**Description:** {exp.description}")
            if exp.status == "Pending":
                c1, c2 = st.columns(2)
                if c1.button("Approve", key=f"approve_{eid}"):
                    fin.approve_expense(eid, "Admin", "Approved")
                    st.rerun()
                if c2.button("Reject", key=f"reject_{eid}"):
                    fin.approve_expense(eid, "Admin", "Rejected")
                    st.rerun()


def _payroll_management(fin, db):
    st.subheader("Process Payroll")
    with st.form("payroll_form"):
        c1, c2 = st.columns(2)
        month = c1.selectbox("Month", ["January","February","March","April","May",
                                        "June","July","August","September",
                                        "October","November","December"])
        year = c2.number_input("Year", min_value=2024, max_value=2030, value=2025)
        if st.form_submit_button("Process Payroll", type="primary"):
            result = fin.process_payroll(month, year)
            if result['status'] == 'success':
                st.success(f"✅ Payroll processed for {result['total_employees']} employees")
                for r in result['records']:
                    st.write(f"• {r['employee_id']}: ${r['net_salary']:,.0f}")

    st.subheader("Payroll Summary")
    c1, c2 = st.columns(2)
    s_month = c1.selectbox("Month", ["January","February","March","April","May",
                                      "June","July","August","September",
                                      "October","November","December"],
                           key="summary_month")
    s_year = c2.number_input("Year", min_value=2024, max_value=2030, value=2025,
                             key="summary_year")
    if st.button("View Summary"):
        result = fin.get_payroll_summary(s_month, s_year)
        if result['total_employees'] > 0:
            st.metric("Total Payroll", f"${result['total_payroll']:,.0f}")
            st.metric("Employees", result['total_employees'])
        else:
            st.info("No payroll data for this period")


def _budget_management(fin, db):
    st.subheader("Department Budgets")
    departments = set(emp.department for emp in db.employees.values())
    for dept in departments:
        result = fin.manage_budget(dept)
        if result['status'] == 'success':
            remaining_pct = (result['remaining'] / result['allocated'] * 100) if result['allocated'] else 0
            st.write(f"**{dept}:** ${result['allocated']:,.0f} allocated, "
                     f"${result['spent']:,.0f} spent, "
                     f"${result['remaining']:,.0f} remaining ({remaining_pct:.0f}%)")
            st.progress(min(result['spent'] / max(result['allocated'], 1), 1.0))

    st.subheader("Allocate Budget")
    with st.form("allocate_budget"):
        dept = st.text_input("Department")
        amount = st.number_input("Amount ($)", min_value=0.0, step=1000.0)
        if st.form_submit_button("Allocate", type="primary"):
            result = fin.manage_budget(dept, "allocate", amount)
            st.success(f"✅ ${amount:,.0f} allocated to {dept}")
