# 💰 Personal Finance AI Agent

An interactive, production-ready, and modular **Personal Finance AI Agent** built using **Python, Pandas, Matplotlib, Streamlit, LangChain, and Google Gemini API**.

This application allows users to upload their transaction history (CSV), auto-categorize transactions using robust keywords and AI, manage monthly budgets, analyze spending trends, predict future expenses, and chat with a specialized **LangChain AI Financial Advisor** powered by **Google Gemini API**.

---

## ✨ Key Features

* **Data Ingestion & Cleaning**: Automatically recognizes, validates, and cleans columns (Date, Description, Amount) from any generic bank CSV.
* **Auto-Categorization**: Instantly labels transactions (Food & Dining, Transport, Shopping, Bills & Utilities, Entertainment, Healthcare, Education, Income) using rule-based parsing, with the option to manually edit categories dynamically.
* **Budget Tracking & Alerts**: Track spending progress and display clear visual alerts (Normal, Warning, Critical) when categories exceed configured thresholds.
* **Financial Dashboards**: Clean Matplotlib visualizations including a category expense donut chart, monthly income vs. expense trend lines, and budget limit bars.
* **LangChain AI Chatbot**: Chat directly with a Gemini AI financial agent about your transactions. The agent has context memory, allowing you to ask follow-up questions like *"Why was my bills category so high?"* or *"How can I save $200 next month?"*
* **Budget Planner & AI Forecasting**: Computes statistical next-month spending predictions using weighted historical trends, with AI-generated breakdown explanations and personalized savings plans.
* **Transaction Explorer**: Search, filter by date ranges, filter by multiple categories, and edit transaction categories in real-time.
* **Report Exporter**: Download a formal PDF financial analysis report (containing tables, budget breach details, and AI advice) or download the cleaned CSV.

---

## 🛠️ Project Structure

```text
Personal-Finance-AI-Agent/
│
├── 📄 app.py
│   └── Streamlit Web App UI, dashboard layout & state management
│
├── ⚙️ preprocess.py
│   └── Data ingestion, validation, cleaning & auto-categorization
│
├── 🤖 agent.py
│   └── LangChain Gemini LLM client, financial prompts & AI predictions
│
├── 📊 utils.py
│   └── Data visualization, PDF report generation & mock CSV generator
│
├── 📦 requirements.txt
│   └── Required Python package dependencies
│
├── 🔐 .env.example
│   └── Environment variable configuration template
│
└── 📖 README.md
    └── Project documentation & setup instructions
```

---

## 💻 Technology Stack

| Technology              | Purpose                                                        |
| ----------------------- | -------------------------------------------------------------- |
| 🐍 **Python**           | Core programming language and application logic                |
| 🐼 **Pandas**           | Data loading, cleaning, processing and financial analysis      |
| 🔢 **NumPy**            | Numerical operations and statistical calculations              |
| 📈 **Seaborn**          | Data visualization and analytical charts                       |
| 📊 **Matplotlib**       | Financial dashboards and visual reports                        |
| 🎨 **Streamlit**        | Interactive web application and dashboard                      |
| 🔗 **LangChain**        | AI agent framework, prompt handling and conversational context |
| ✨ **Google Gemini API** | AI-powered financial advice, analysis and insights             |

---

## 🚀 Setup Guide

### 1. Prerequisites

Ensure you have **Python 3.9 to 3.12** installed on your system.

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

**Windows PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Duplicate `.env.example` to `.env`:

```bash
cp .env.example .env
```

Provide your `GOOGLE_API_KEY` in `.env` or input it in the Streamlit sidebar text field.

---

## ▶️ Running the Application

Launch the Streamlit dashboard:

```bash
streamlit run app.py
```

This will start the local server and open the application in your browser (typically at `http://localhost:8501`).

---

## 🔄 How It Works

The Personal Finance AI Agent follows a simple workflow to turn raw transaction data into meaningful financial insights:

### 1. 📂 Upload a Finance Dataset
Upload your personal finance or bank transaction history in **CSV format** through the Streamlit interface.

### 2. 🔍 Automatic Detection & Categorization
The system automatically detects and validates the important columns in your dataset and categorizes transactions into relevant financial categories.

### 3. 📊 Get Financial Reports & Analysis
Once your data is processed, the dashboard provides financial reports and visual analysis.

### 4. 💬 Ask Questions to the AI Agent
Use the integrated **LangChain + Google Gemini AI Financial Advisor** to ask questions about your finances.

### 5. 🧠 Get AI-Powered Financial Insights
The AI agent analyzes your processed financial data and provides personalized insights


---
Made with using **Python, Streamlit, LangChain & Google Gemini**   
