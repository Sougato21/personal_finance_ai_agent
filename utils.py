import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from fpdf import FPDF

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
COLOR_PALETTE = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#6b7280']


def create_category_donut_chart(df):
    """Donut chart of category-wise expense distribution."""
    expenses_df = df[df['Category'] != 'Income']
    if expenses_df.empty:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No Expense Data Available", ha='center', va='center')
        ax.axis('off')
        return fig

    cat_totals = expenses_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)

    fig, ax = plt.subplots(figsize=(6, 5), dpi=100)
    wedges, texts, autotexts = ax.pie(
        cat_totals.values,
        labels=cat_totals.index,
        autopct='%1.1f%%',
        startangle=140,
        colors=COLOR_PALETTE[:len(cat_totals)],
        pctdistance=0.75,
        textprops=dict(color="black", fontsize=9)
    )
    plt.setp(autotexts, size=8, weight="bold", color="white")

    centre_circle = plt.Circle((0, 0), 0.55, fc='white')
    fig.gca().add_artist(centre_circle)

    ax.axis('equal')
    plt.tight_layout()
    return fig


def create_monthly_trend_chart(df):
    """Line chart comparing monthly income vs. expenses."""
    if df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No Data Available", ha='center', va='center')
        ax.axis('off')
        return fig

    df_copy = df.copy()
    df_copy['Month'] = df_copy['Date'].dt.to_period('M').astype(str)
    monthly_data = df_copy.groupby(['Month', 'Category'])['Amount'].sum().unstack(fill_value=0.0)

    months = monthly_data.index.tolist()
    expenses = monthly_data.drop(columns=['Income'], errors='ignore').sum(axis=1).tolist()
    income = monthly_data['Income'].tolist() if 'Income' in monthly_data.columns else [0.0] * len(months)

    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    ax.plot(months, income, marker='o', linewidth=2.5, color='#10b981', label='Income')
    ax.plot(months, expenses, marker='s', linewidth=2.5, color='#ef4444', label='Expenses')
    ax.fill_between(months, income, color='#10b981', alpha=0.1)
    ax.fill_between(months, expenses, color='#ef4444', alpha=0.1)

    ax.set_title("Monthly Income vs. Expenses Trend", fontsize=12, fontweight='bold', pad=15)
    ax.set_xlabel("Month", fontsize=10)
    ax.set_ylabel("Amount ($)", fontsize=10)
    ax.legend(frameon=True, facecolor='white', framealpha=0.9)
    ax.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(rotation=15)
    plt.tight_layout()
    return fig


def create_budget_vs_actual_chart(df, budgets, selected_month=None):
    """Bar chart comparing category budget vs. actual spending."""
    if not budgets or df.empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "Budgets not set or transaction history empty.", ha='center', va='center')
        ax.axis('off')
        return fig

    df_copy = df.copy()
    df_copy['Month'] = df_copy['Date'].dt.to_period('M')
    target_month = df_copy['Month'].max() if selected_month is None else pd.Period(selected_month, freq='M')

    monthly_df = df_copy[(df_copy['Month'] == target_month) & (df_copy['Category'] != 'Income')]
    spending = monthly_df.groupby('Category')['Amount'].sum().to_dict()

    categories, actual_spent, budget_limits, colors = [], [], [], []
    for cat, limit in budgets.items():
        if limit <= 0:
            continue
        categories.append(cat)
        spent = spending.get(cat, 0.0)
        actual_spent.append(spent)
        budget_limits.append(limit)

        pct = (spent / limit) * 100
        if pct >= 100:
            colors.append('#ef4444')
        elif pct >= 80:
            colors.append('#f59e0b')
        else:
            colors.append('#3b82f6')

    if not categories:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No budgets configured for active categories.", ha='center', va='center')
        ax.axis('off')
        return fig

    y_pos = np.arange(len(categories))
    fig, ax = plt.subplots(figsize=(8, 4.5), dpi=100)

    ax.barh(y_pos, budget_limits, align='center', alpha=0.15, color='#9ca3af', edgecolor='#4b5563', height=0.6, label='Budget Limit')
    ax.barh(y_pos, actual_spent, align='center', color=colors, height=0.4, label='Actual Spent')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=9, fontweight='bold')
    ax.invert_yaxis()

    ax.set_xlabel('Amount ($)', fontsize=10)
    ax.set_title(f'Budget vs Actual Spending ({target_month})', fontsize=12, fontweight='bold', pad=15)

    for i, (spent, limit) in enumerate(zip(actual_spent, budget_limits)):
        ax.text(max(spent, limit) * 1.02, i, f"${spent:.1f} / ${limit:.1f}", va='center', ha='left', fontsize=8, weight='bold')

    ax.grid(True, axis='x', linestyle='--', alpha=0.5)
    ax.legend(loc='lower right', frameon=True)
    plt.tight_layout()
    return fig


class PDFReport(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'Personal Finance Analysis Report', 0, 1, 'C')
        self.set_font('Helvetica', 'I', 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 1, 'C')
        self.set_text_color(0, 0, 0)
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


def export_pdf_report(df, budgets, ai_advice=None):
    """Generates a PDF report: financial summary, category breakdown, budget status, AI advice."""
    try:
        expenses_df = df[df['Category'] != 'Income']
        total_spending = expenses_df['Amount'].sum()
        total_income = df[df['Category'] == 'Income']['Amount'].sum()
        net_savings = total_income - total_spending

        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # 1. Summary
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '1. Financial Summary Overview', 0, 1, 'L')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'Total Income: ${total_income:,.2f}', 0, 0)
        pdf.cell(90, 8, f'Total Expenses: ${total_spending:,.2f}', 0, 1)
        pdf.cell(90, 8, f'Net Savings: ${net_savings:,.2f}', 0, 0)
        pdf.cell(90, 8, f'Total Transactions: {len(df)}', 0, 1)
        pdf.cell(90, 8, f'Report Period: {df["Date"].min().strftime("%Y-%m-%d")} to {df["Date"].max().strftime("%Y-%m-%d")}', 0, 1)
        pdf.ln(10)

        # 2. Category breakdown
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '2. Expense Breakdown by Category', 0, 1, 'L')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(60, 8, 'Category', 1, 0, 'L', True)
        pdf.cell(40, 8, 'Total Spent', 1, 0, 'R', True)
        pdf.cell(40, 8, 'Txn Count', 1, 0, 'C', True)
        pdf.cell(50, 8, '% of Total Expenses', 1, 1, 'R', True)

        pdf.set_font('Helvetica', '', 10)
        cat_totals = expenses_df.groupby('Category')['Amount'].agg(['sum', 'count']).sort_values(by='sum', ascending=False)
        for cat, row in cat_totals.iterrows():
            pct = (row['sum'] / total_spending * 100) if total_spending > 0 else 0
            pdf.cell(60, 8, f' {cat}', 1, 0, 'L')
            pdf.cell(40, 8, f'${row["sum"]:,.2f}', 1, 0, 'R')
            pdf.cell(40, 8, f'{row["count"]}', 1, 0, 'C')
            pdf.cell(50, 8, f'{pct:.1f}%', 1, 1, 'R')
        pdf.ln(10)

        # 3. Budget status
        if budgets:
            df_copy = df.copy()
            df_copy['Month'] = df_copy['Date'].dt.to_period('M')
            latest_month = df_copy['Month'].max()
            monthly_data = df_copy[(df_copy['Month'] == latest_month) & (df_copy['Category'] != 'Income')]
            category_spending = monthly_data.groupby('Category')['Amount'].sum().to_dict()

            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, f'3. Budget Analysis ({latest_month})', 0, 1, 'L')
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            pdf.set_fill_color(240, 240, 240)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(60, 8, 'Category', 1, 0, 'L', True)
            pdf.cell(40, 8, 'Spent', 1, 0, 'R', True)
            pdf.cell(40, 8, 'Limit', 1, 0, 'R', True)
            pdf.cell(50, 8, 'Usage Status', 1, 1, 'C', True)

            pdf.set_font('Helvetica', '', 10)
            for cat, limit in budgets.items():
                if limit <= 0:
                    continue
                spent = category_spending.get(cat, 0.0)
                pct = (spent / limit) * 100
                status = "Exceeded" if pct >= 100 else "Warning" if pct >= 80 else "Normal"
                pdf.cell(60, 8, f' {cat}', 1, 0, 'L')
                pdf.cell(40, 8, f'${spent:,.2f}', 1, 0, 'R')
                pdf.cell(40, 8, f'${limit:,.2f}', 1, 0, 'R')
                pdf.cell(50, 8, f'{status} ({pct:.1f}%)', 1, 1, 'C')
            pdf.ln(10)

        # 4. AI advice (optional)
        if ai_advice and isinstance(ai_advice, str):
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, '4. AI Financial Advice', 0, 1, 'L')
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

            pdf.set_font('Helvetica', '', 9.5)
            pdf.multi_cell(0, 5, ai_advice.encode('latin-1', 'ignore').decode('latin-1'))

        raw_output = pdf.output(dest='S')
        if isinstance(raw_output, str):
            return raw_output.encode('latin-1', 'ignore')
        elif isinstance(raw_output, (bytes, bytearray)):
            return bytes(raw_output)
        return str(raw_output).encode('latin-1', 'ignore')
    except Exception:
        fallback_pdf = FPDF()
        fallback_pdf.add_page()
        fallback_pdf.set_font('Helvetica', 'B', 16)
        fallback_pdf.cell(0, 10, 'Personal Finance Analysis Report', 0, 1, 'C')
        res = fallback_pdf.output(dest='S')
        if isinstance(res, str):
            return res.encode('latin-1', 'ignore')
        return bytes(res)

def export_pdf_report(df, budgets, ai_advice=None, ai_predictions=None):
    """
    Generates a PDF analysis report containing dataset metrics and AI advice.
    """
    try:
        expenses_df = df[df['Category'] != 'Income']
        total_spending = expenses_df['Amount'].sum()
        total_income = df[df['Category'] == 'Income']['Amount'].sum()
        net_savings = total_income - total_spending
        
        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        
        # Financial Overview Summary
        pdf.set_text_color(50, 50, 50)
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '1. Financial Summary Overview', 0, 1, 'L')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(90, 8, f'Total Income: ${total_income:,.2f}', 0, 0)
        pdf.cell(90, 8, f'Total Expenses: ${total_spending:,.2f}', 0, 1)
        pdf.cell(90, 8, f'Net Savings: ${net_savings:,.2f}', 0, 0)
        pdf.cell(90, 8, f'Total Transactions: {len(df)}', 0, 1)
        pdf.cell(90, 8, f'Report Period: {df["Date"].min().strftime("%Y-%m-%d")} to {df["Date"].max().strftime("%Y-%m-%d")}', 0, 1)
        pdf.ln(10)
        
        # Category Spending Table
        pdf.set_font('Helvetica', 'B', 14)
        pdf.cell(0, 10, '2. Expense Breakdown by Category', 0, 1, 'L')
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        
        # Table Header
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(60, 8, 'Category', 1, 0, 'L', True)
        pdf.cell(40, 8, 'Total Spent', 1, 0, 'R', True)
        pdf.cell(40, 8, 'Txn Count', 1, 0, 'C', True)
        pdf.cell(50, 8, '% of Total Expenses', 1, 1, 'R', True)
        
        pdf.set_font('Helvetica', '', 10)
        cat_totals = expenses_df.groupby('Category')['Amount'].agg(['sum', 'count']).sort_values(by='sum', ascending=False)
        for cat, row in cat_totals.iterrows():
            pct = (row['sum'] / total_spending * 100) if total_spending > 0 else 0
            pdf.cell(60, 8, f' {cat}', 1, 0, 'L')
            pdf.cell(40, 8, f'${row["sum"]:,.2f}', 1, 0, 'R')
            pdf.cell(40, 8, f'{row["count"]}', 1, 0, 'C')
            pdf.cell(50, 8, f'{pct:.1f}%', 1, 1, 'R')
        pdf.ln(10)
        
        # Budget alerts if any
        if budgets:
            df_copy = df.copy()
            df_copy['Month'] = df_copy['Date'].dt.to_period('M')
            latest_month = df_copy['Month'].max()
            monthly_data = df_copy[(df_copy['Month'] == latest_month) & (df_copy['Category'] != 'Income')]
            category_spending = monthly_data.groupby('Category')['Amount'].sum().to_dict()
            
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, f'3. Budget Analysis ({latest_month})', 0, 1, 'L')
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_fill_color(240, 240, 240)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(60, 8, 'Category', 1, 0, 'L', True)
            pdf.cell(40, 8, 'Spent', 1, 0, 'R', True)
            pdf.cell(40, 8, 'Limit', 1, 0, 'R', True)
            pdf.cell(50, 8, 'Usage Status', 1, 1, 'C', True)
            
            pdf.set_font('Helvetica', '', 10)
            for cat, limit in budgets.items():
                if limit <= 0:
                    continue
                spent = category_spending.get(cat, 0.0)
                pct = (spent / limit) * 100
                status = "Normal"
                if pct >= 100:
                    status = "Exceeded"
                elif pct >= 80:
                    status = "Warning"
                pdf.cell(60, 8, f' {cat}', 1, 0, 'L')
                pdf.cell(40, 8, f'${spent:,.2f}', 1, 0, 'R')
                pdf.cell(40, 8, f'${limit:,.2f}', 1, 0, 'R')
                pdf.cell(50, 8, f'{status} ({pct:.1f}%)', 1, 1, 'C')
            pdf.ln(10)

        # AI Savings Advice Page
        if ai_advice and isinstance(ai_advice, str):
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, '4. AI Savings Recommendations', 0, 1, 'L')
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_font('Helvetica', '', 9.5)
            pdf.multi_cell(0, 5, ai_advice.encode('latin-1', 'ignore').decode('latin-1'))
            pdf.ln(10)
            
        # AI Predictions Page
        if ai_predictions and isinstance(ai_predictions, str):
            if not ai_advice:
                pdf.add_page()
            else:
                pdf.ln(5)
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, '5. AI Expense Forecasting & Budgets', 0, 1, 'L')
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            
            pdf.set_font('Helvetica', '', 9.5)
            pdf.multi_cell(0, 5, ai_predictions.encode('latin-1', 'ignore').decode('latin-1'))
            
        raw_output = pdf.output(dest='S')
        if isinstance(raw_output, str):
            return raw_output.encode('latin-1', 'ignore')
        elif isinstance(raw_output, (bytes, bytearray)):
            return bytes(raw_output)
        else:
            return str(raw_output).encode('latin-1', 'ignore')
    except Exception as e:
        # Fallback simple PDF
        fallback_pdf = FPDF()
        fallback_pdf.add_page()
        fallback_pdf.set_font('Helvetica', 'B', 16)
        fallback_pdf.cell(0, 10, 'Personal Finance Analysis Report', 0, 1, 'C')
        res = fallback_pdf.output(dest='S')
        if isinstance(res, str):
            return res.encode('latin-1', 'ignore')
        return bytes(res)
