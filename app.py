import streamlit as st
import pandas as pd
import io
import os
from datetime import datetime
from dotenv import load_dotenv

# Import custom modules
import preprocess
import agent
import utils

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Personal Finance AI Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

def sanitize_for_markdown(text) -> str:
    """
    Prepares AI / text output for safe st.markdown() rendering.

    Streamlit's markdown renderer treats a pair of '$' characters as
    LaTeX/MathJax delimiters. Since financial responses are full of dollar
    amounts (e.g. "$300...$8.37 million"), any two dollar signs get parsed
    as a math block, which silently eats whitespace and drops the literal
    '$' characters -- producing mangled, run-together text.

    This escapes '$' as '\\$' ONLY for display purposes. Do not apply this
    to text going into the PDF export (utils.export_pdf_report) -- that
    path wants the raw '$'.
    """
    if not isinstance(text, str):
        text = agent.extract_text_content(text)
    if not isinstance(text, str):
        text = str(text)
    return text.replace("$", "\\$")


# Initialize Session State
if 'raw_df' not in st.session_state:
    st.session_state['raw_df'] = None
if 'df' not in st.session_state:
    st.session_state['df'] = None
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'ai_savings_advice' not in st.session_state:
    st.session_state['ai_savings_advice'] = ""
if 'ai_predictions_advice' not in st.session_state:
    st.session_state['ai_predictions_advice'] = ""

# Sidebar Configuration
st.sidebar.title("Personal Finance AI")
st.sidebar.caption("AI-Powered Financial Insights & Budgeting")

# 2. Budget Settings
st.sidebar.header("Monthly Budget Planner")
total_monthly_budget = st.sidebar.number_input("Total Monthly Budget ($)", min_value=0, value=2500, step=100)

with st.sidebar.expander("Category Budget Limits"):
    budgets = {
        'Food & Dining': st.slider('Food & Dining ($)', 0, 1000, 500, 50),
        'Transport': st.slider('Transport ($)', 0, 800, 200, 50),
        'Shopping': st.slider('Shopping ($)', 0, 1000, 300, 50),
        'Bills & Utilities': st.slider('Bills & Utilities ($)', 0, 2000, 1200, 50),
        'Entertainment': st.slider('Entertainment ($)', 0, 800, 150, 50),
        'Healthcare': st.slider('Healthcare ($)', 0, 1000, 100, 50),
        'Education': st.slider('Education ($)', 0, 1000, 100, 50),
    }

# 3. CSV File Upload / Sample data load
st.sidebar.header("Data Ingestion")
uploaded_file = st.sidebar.file_uploader("Upload Transaction CSV", type=["csv"])

if uploaded_file is not None:
    try:
        df_loaded = preprocess.load_and_validate_csv(uploaded_file)
        df_categorized = preprocess.auto_categorize(df_loaded)
        st.session_state['raw_df'] = df_categorized.copy()
        st.session_state['df'] = df_categorized.copy()
    except Exception as e:
        st.sidebar.error(f"Error: {str(e)}")

# Main Dashboard Content
if st.session_state['df'] is None:
    st.title("Welcome to Personal Finance AI Agent")
    st.subheader("Your Intelligent Personal Financial Assistant")

    st.markdown("""
    Analyze, categorize, and visualize your personal expenses.

    ### Get Started in 2 Easy Steps:
    1. **Load your Data**: Upload a transaction CSV.
    2. **Explore the Dashboard**: View spending charts, category analysis, monthly summaries, budget alerts, and export your report.
    """)

else:
    df = st.session_state['df']

    monthly_income = st.sidebar.number_input(
        "Monthly Income ($)",
        min_value=0.0,
        value=5000.0,
        step=100.0
    )

    expenses_df = df[df["Category"] != "Income"]

    total_spent = expenses_df["Amount"].sum()
    total_income = monthly_income
    net_savings = total_income - total_spent

    if total_income > 0:
        savings_rate = (net_savings / total_income) * 100
    else:
        savings_rate = 0.0

    net_savings_display = (
        f"-${abs(net_savings):,.2f}"
        if net_savings < 0
        else f"${net_savings:,.2f}"
    )

    st.title("Personal Finance AI Agent Dashboard")
    st.caption(
        f"Analyzing {len(df)} transactions from "
        f"{df['Date'].min().strftime('%Y-%m-%d')} to "
        f"{df['Date'].max().strftime('%Y-%m-%d')}"
    )
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Monthly Income",
            value=f"${total_income:,.2f}"
        )

    with col2:
        st.metric(
            label="Total Expenses",
            value=f"${total_spent:,.2f}"
        )

    with col3:
        st.metric(
            label="Net Savings",
            value=net_savings_display,
            delta="Surplus" if net_savings >= 0 else "Deficit"
        )
    # Budget Breach Summary
    latest_month = df['Date'].dt.to_period('M').max()
    alerts_data = preprocess.check_budget_alerts(df, budgets, selected_month=latest_month)

    breached_cats = []
    warning_cats = []

    for cat, status_dict in alerts_data.get('alerts', {}).items():
        if status_dict["status"] == "Critical":
            breached_cats.append(
                f"<b>{cat}</b> (Spent: ${status_dict['spent']:,.2f} / Limit: ${status_dict['budget']:,.2f})"
            )
        elif status_dict["status"] == "Warning":
            warning_cats.append(
            f"<b>{cat}</b> (Spent: ${status_dict['spent']:,.2f} / Limit: ${status_dict['budget']:,.2f})"
        )

    if breached_cats or warning_cats:
        with st.expander("Active Budget Alerts", expanded=True):
            for alert in breached_cats:
                st.markdown(
                    f'<div class="alert-box"><strong>Budget Breached:</strong> {alert}</div>',
                    unsafe_allow_html=True
            )

        for alert in warning_cats:
            st.markdown(
                f'<div class="warning-box"><strong>Nearing Budget Limit:</strong> {alert}</div>',
                unsafe_allow_html=True
            )

    # App Tabs
    tab1, tab2 = st.tabs([
        "Spending Overview & Charts",
        "AI Financial Advisor Chat"
    ])

    # --- Tab 1: Overview & Charts ---
    with tab1:
        st.subheader("Visual Spending Analysis")

        col_charts1, col_charts2 = st.columns(2)
        with col_charts1:
            st.write("**Expense Allocation (By Category)**")
            donut_fig = utils.create_category_donut_chart(df)
            st.pyplot(donut_fig)

        with col_charts2:
            st.write("**Budget vs. Actual Spending (Latest Month)**")
            budget_fig = utils.create_budget_vs_actual_chart(df, budgets, selected_month=latest_month)
            st.pyplot(budget_fig)

        st.markdown("---")
        st.write("**Cash Flow Trend (Income vs. Expenses over time)**")
        trend_fig = utils.create_monthly_trend_chart(df)
        st.pyplot(trend_fig)

        st.markdown("---")
        st.subheader("Spending Category Details")
        cat_totals = expenses_df.groupby('Category')['Amount'].agg(['sum', 'count']).sort_values(by='sum', ascending=False)
        cat_totals = cat_totals.reset_index()
        cat_totals.columns = ['Category', 'Total Spent', 'Transaction Count']
        cat_totals['% of Total Expenses'] = (cat_totals['Total Spent'] / total_spent * 100).round(1)

        st.dataframe(
            cat_totals.style.format({
                'Total Spent': '${:,.2f}',
                '% of Total Expenses': '{:.1f}%'
            }),
            use_container_width=True,
            hide_index=True
        )

    # --- Tab 2: AI Financial Advisor Chat ---
    with tab2:
        st.subheader("Ask Your Financial Agent")
        st.caption(
            "Enter a question about your expenses, income, category summaries, or request custom recommendations."
        )

        for role, msg_text in st.session_state['chat_history']:
            with st.chat_message(role):
                st.markdown(sanitize_for_markdown(msg_text))

        user_query = st.chat_input(
            "Ask a question (e.g. 'What is my top spending category?', 'How can I save $300 next month?')"
        )

        if user_query:
            st.session_state['chat_history'].append(("user", user_query))

            with st.chat_message("user"):
                st.markdown(sanitize_for_markdown(user_query))

            with st.spinner("Analyzing transaction data..."):
                gemini_api_key = os.getenv("GOOGLE_API_KEY")
                raw_response = agent.query_financial_agent(
                    df,
                    user_query,
                    api_key=gemini_api_key,
                    budgets=budgets,
                    chat_history=st.session_state['chat_history'][:-1]
                )

            # Store the raw (unescaped) response in history -- keep the
            # source of truth clean. Escaping happens only at render time,
            # both here and in the history loop above.
            st.session_state['chat_history'].append(("assistant", raw_response))

            with st.chat_message("assistant"):
                st.markdown(sanitize_for_markdown(raw_response))

        if len(st.session_state['chat_history']) > 0:
            if st.button("Clear Chat History"):
                st.session_state['chat_history'] = []
                st.rerun()

    # --- Footer Export actions ---
    st.markdown("---")
    st.subheader("Export Analysis Reports")
    col_exp1, col_exp2 = st.columns([1, 4])

    with col_exp1:
        # NOTE: PDF export intentionally uses the RAW (unescaped) advice text,
        # not sanitize_for_markdown() output -- the PDF renderer has no
        # markdown/LaTeX parsing, so escaped backslashes would show up
        # literally in the document.
        pdf_advice = st.session_state['ai_savings_advice'] if st.session_state['ai_savings_advice'] else None
        pdf_preds = st.session_state['ai_predictions_advice'] if st.session_state['ai_predictions_advice'] else None

        pdf_data = utils.export_pdf_report(df, budgets, pdf_advice, pdf_preds)

        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name="Personal_Finance_Analysis_Report.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_exp2:
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()

        st.download_button(
            label="Download Cleaned CSV Data",
            data=csv_data,
            file_name="Cleaned_Expense_Data.csv",
            mime="text/csv"
        )

    st.sidebar.markdown("---")
    if st.sidebar.button("Reset Application Data", type="secondary"):
        st.session_state['raw_df'] = None
        st.session_state['df'] = None
        st.session_state['chat_history'] = []
        st.session_state['ai_savings_advice'] = ""
        st.session_state['ai_predictions_advice'] = ""
        st.sidebar.success("Session state cleared.")
        st.rerun()