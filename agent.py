import os
import numpy as np
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent

from prompt import SYSTEM_PROMPT
from tools import make_tools

dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

CHART_DIR = Path(__file__).parent / "charts"
CHART_DIR.mkdir(exist_ok=True)


def build_agent(df, api_key: str = None):
    """
    Creates and returns an AI agent configured to analyze
    the provided dataset.

    Args:
        df (pandas.DataFrame): The dataset to be analyzed.
        api_key (str, optional): Google Gemini API Key.

    Returns:
        A LangChain agent with access to the dataset analysis tools.
    """
    key = api_key or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise ValueError("GOOGLE_API_KEY not found. Please provide an API key in the sidebar or .env file.")

    os.environ["GOOGLE_API_KEY"] = key

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        google_api_key=key,
        temperature=0,
    )

    tools = make_tools(df, CHART_DIR)
    agent = create_agent(
        llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
    )
    return agent


import json
import ast
import re

def extract_text_content(content):
    """
    Extracts a clean Markdown string from content which may be a string,
    a list of text blocks (e.g. Gemini [{'type': 'text', 'text': '...'}]), or a dict.
    Also handles stringified JSON/Python lists/dicts and fixes line breaks.
    """
    if content is None:
        return ""

    if isinstance(content, str):
        content_str = content.strip()
        # If stringified list or dict
        if (content_str.startswith('[') and content_str.endswith(']')) or (content_str.startswith('{') and content_str.endswith('}')):
            try:
                parsed = json.loads(content_str)
                return extract_text_content(parsed)
            except Exception:
                try:
                    parsed = ast.literal_eval(content_str)
                    return extract_text_content(parsed)
                except Exception:
                    pass

        # Fix vertical linebreaks between individual characters
        content_str = re.sub(r'([A-Za-z0-9,.\*\:\-\$\%])\n(?=[A-Za-z0-9,.\*\:\-\$\%]\n)', r'\1', content_str)
        return content_str

    if isinstance(content, list):
        text_parts = []
        for item in content:
            extracted = extract_text_content(item)
            if extracted:
                text_parts.append(extracted)
        return "\n\n".join(text_parts)

    if isinstance(content, dict):
        if content.get("type") == "text" and "text" in content:
            return extract_text_content(content["text"])
        if "text" in content:
            return extract_text_content(content["text"])
        if "content" in content:
            return extract_text_content(content["content"])
        return str(content)

    return str(content)


def query_financial_agent(df, user_query: str, api_key: str = None, budgets: dict = None, chat_history: list = None):
    """
    Queries the Gemini agent with a financial question and user chat context.
    """
    try:
        agent_executor = build_agent(df, api_key=api_key)
        
        formatted_messages = []
        if chat_history:
            for role, msg in chat_history:
                formatted_messages.append({"role": role, "content": msg})
        formatted_messages.append({"role": "user", "content": user_query})

        response = agent_executor.invoke({"messages": formatted_messages})
        
        if isinstance(response, dict):
            if "messages" in response and len(response["messages"]) > 0:
                last_msg = response["messages"][-1]
                raw_content = getattr(last_msg, "content", last_msg)
                return extract_text_content(raw_content)
            output = response.get("output", response.get("result", response))
            return extract_text_content(output)
        return extract_text_content(response)
    except Exception as e:
        return f"Error querying Gemini Agent: {str(e)}"


def explain_predictions_agent(df, api_key: str = None):
    """
    Uses Gemini LLM to analyze statistical predictions and provide an explanation.
    """
    try:
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            return "Please provide a Google Gemini API Key."

        predictions = calculate_statistical_predictions(df)
        if not predictions:
            return "No prediction data available."

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=key,
            temperature=0.2,
        )

        prompt = f"""You are a personal finance expert. Analyze the following expense predictions for next month and explain key trends, high-risk growth areas, and expected variations:

Prediction Data:
{predictions}

Provide a clear, professional breakdown in Markdown format without using emojis."""

        res = llm.invoke(prompt)
        raw_content = getattr(res, "content", str(res))
        return extract_text_content(raw_content)
    except Exception as e:
        return f"Error generating forecast explanation: {str(e)}"


def generate_savings_recommendations(df, api_key: str = None, budgets: dict = None):
    """
    Uses Gemini LLM to generate personalized savings advice based on transaction history and budgets.
    """
    try:
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            return "Please provide a Google Gemini API Key."

        expenses_df = df[df['Category'] != 'Income']
        category_totals = expenses_df.groupby('Category')['Amount'].sum().to_dict()

        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash-lite",
            google_api_key=key,
            temperature=0.3,
        )

        prompt = f"""You are a personal finance advisor. Analyze the user's spending habits and current category budget limits, then provide 3 to 5 concrete, actionable strategies to reduce expenses and increase monthly savings.

Category Totals Spent:
{category_totals}

Category Budget Limits:
{budgets}

Provide recommendations in clean Markdown format with bold text, bullet points, and specific dollar figures. Do not use any emojis."""

        res = llm.invoke(prompt)
        raw_content = getattr(res, "content", str(res))
        return extract_text_content(raw_content)
    except Exception as e:
        return f"Error generating savings advice: {str(e)}"


def calculate_statistical_predictions(df):
    """
    Performs a baseline statistical prediction for next month's expenses per category.
    Uses weighted exponential smoothing over recent months:
      - 3+ months of data: 50% last month, 30% prev month, 20% two months ago.
      - 2 months of data: 70% last month, 30% prev month.
      - 1 month of data: repeat last month.

    Returns:
        dict: {category: {historical_mean, last_month, predicted, std_dev, confidence}}
    """
    import pandas as pd

    if df is None or df.empty:
        return {}

    expenses_df = df[df["Category"] != "Income"].copy()
    if expenses_df.empty:
        return {}

    expenses_df["Month"] = expenses_df["Date"].dt.to_period("M")
    monthly_cat = (
        expenses_df.groupby(["Month", "Category"])["Amount"]
        .sum()
        .unstack(fill_value=0.0)
    )

    num_months = len(monthly_cat)
    if num_months == 0:
        return {}

    predictions = {}
    for cat in monthly_cat.columns:
        series = monthly_cat[cat].values

        if num_months == 1:
            pred_amount = series[-1]
            confidence = "Low (only 1 month of data)"
        elif num_months == 2:
            pred_amount = series[-1] * 0.7 + series[-2] * 0.3
            confidence = "Medium-Low (2 months of data)"
        else:
            pred_amount = series[-1] * 0.5 + series[-2] * 0.3 + series[-3] * 0.2
            confidence = "Medium (last 3 months weighted trend)"

        std_dev = float(np.std(series)) if len(series) > 1 else 0.0

        predictions[cat] = {
            "historical_mean": float(np.mean(series)),
            "last_month":      float(series[-1]),
            "predicted":       float(max(0.0, pred_amount)),
            "std_dev":         std_dev,
            "confidence":      confidence,
        }

    return predictions
