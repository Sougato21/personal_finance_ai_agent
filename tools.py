from langchain_core.tools import tool
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime

def make_tools(df: pd.DataFrame, chart_dir: Path):
    
    @tool
    def get_financial_summary() -> str:
        """
        Returns a high-level summary of the user's financial dataset, including date range,
        total transactions, total income, total expenses, and net savings.
        """
        expenses_df = df[df['Category'] != 'Income']
        income_df = df[df['Category'] == 'Income']
        total_expenses = expenses_df['Amount'].sum()
        total_income = income_df['Amount'].sum()
        net_savings = total_income - total_expenses
        
        summary = f"""Financial Dataset Overview:
- Date Range: {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}
- Total Transactions: {len(df)}
- Total Income: ${total_income:.2f}
- Total Expenses: ${total_expenses:.2f}
- Net Savings: ${net_savings:.2f}
"""
        return summary

    @tool
    def get_category_spending() -> str:
        """
        Returns a markdown table of category-wise spending totals, counts, and percentages.
        """
        expenses_df = df[df['Category'] != 'Income']
        if expenses_df.empty:
            return "No expense data."
        total_expenses = expenses_df['Amount'].sum()
        cat_summary = expenses_df.groupby('Category')['Amount'].agg(['sum', 'count']).sort_values(by='sum', ascending=False)
        
        md = "| Category | Total Spent | Transaction Count | % of Total |\n|---|---|---|---|\n"
        for cat, row in cat_summary.iterrows():
            pct = (row['sum'] / total_expenses * 100) if total_expenses > 0 else 0
            md += f"| {cat} | ${row['sum']:.2f} | {row['count']} | {pct:.1f}% |\n"
        return md

    @tool
    def get_transactions_by_category(category: str) -> str:
        """
        Returns a list of transactions belonging to a specific category (case-insensitive).
        For example: category='Food & Dining' or category='Transport'.
        """
        cat_df = df[df['Category'].str.lower() == category.lower()]
        if cat_df.empty:
            return f"No transactions found for category '{category}'."
        
        md = "| Date | Description | Amount |\n|---|---|---|\n"
        for _, row in cat_df.head(50).iterrows():
            md += f"| {row['Date'].strftime('%Y-%m-%d')} | {row['Description']} | ${row['Amount']:.2f} |\n"
        return md

    @tool
    def get_top_expenses(limit: int = 10) -> str:
        """
        Returns the top largest expense transactions (outliers).
        """
        expenses_df = df[df['Category'] != 'Income']
        top = expenses_df.nlargest(limit, 'Amount')
        
        md = "| Date | Description | Category | Amount |\n|---|---|---|---|\n"
        for _, row in top.iterrows():
            md += f"| {row['Date'].strftime('%Y-%m-%d')} | {row['Description']} | {row['Category']} | ${row['Amount']:.2f} |\n"
        return md

    @tool
    def search_transactions(query: str) -> str:
        """
        Search for transactions whose descriptions contain the search query (case-insensitive).
        """
        results = df[df['Description'].str.contains(query, case=False, na=False)]
        if results.empty:
            return f"No transactions matching '{query}' found."
        
        md = "| Date | Description | Category | Amount |\n|---|---|---|---|\n"
        for _, row in results.head(30).iterrows():
            md += f"| {row['Date'].strftime('%Y-%m-%d')} | {row['Description']} | {row['Category']} | ${row['Amount']:.2f} |\n"
        return md

    return [get_financial_summary, get_category_spending, get_transactions_by_category, get_top_expenses, search_transactions]
