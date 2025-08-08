import streamlit as st
import pandas as pd
from datetime import date

# Page settings
st.set_page_config(page_title="💰 Budget Planner", layout="wide")

st.title("💰 Budget Planner")

# Initialize data storage in session
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Category", "Amount", "Note"])

# Input section
st.subheader("➕ Add Expense")
col1, col2 = st.columns(2)

with col1:
    expense_date = st.date_input("Date", value=date.today())
    category = st.selectbox("Category", ["Food", "Transport", "Entertainment", "Bills", "Other"])

with col2:
    amount = st.number_input("Amount (₹)", min_value=0.0, step=0.01)
    note = st.text_input("Note")

if st.button("Add Expense"):
    if amount > 0:
        new_row = pd.DataFrame([[expense_date, category, amount, note]], 
                               columns=["Date", "Category", "Amount", "Note"])
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.success("✅ Expense added successfully!")
    else:
        st.error("❌ Please enter a valid amount.")

# Display expense table
st.subheader("📜 Expense Records")
if not st.session_state.data.empty:
    st.dataframe(st.session_state.data)
else:
    st.info("No expenses recorded yet.")

# Summary charts
st.subheader("📊 Summary")
if not st.session_state.data.empty:
    summary = st.session_state.data.groupby("Category")["Amount"].sum()
    st.bar_chart(summary)

    monthly_summary = st.session_state.data.copy()
    monthly_summary["Month"] = pd.to_datetime(monthly_summary["Date"]).dt.to_period("M")
    monthly_total = monthly_summary.groupby("Month")["Amount"].sum()
    st.line_chart(monthly_total)
