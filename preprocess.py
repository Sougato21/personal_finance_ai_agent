import pandas as pd
import re
import numpy as np

def normalize_columns(columns):
    """
    Normalizes column names to standard names: Date, Description, Amount, Category.
    Ensure each standard target column is only mapped to a single source column.
    """
    normalized = {}
    mapped_targets = set()
    date_patterns = [r'date', r'timestamp', r'txn.*date', r'transaction.*date']
    desc_patterns = [r'desc', r'description', r'payee', r'merchant', r'details', r'title']
    amount_patterns = [r'amount', r'price', r'cost', r'value', r'charge', r'sum', r'total']
    cat_patterns = [r'cat', r'category', r'type', r'group', r'tag']

    for col in columns:
        col_lower = col.lower().strip()
        
        # Check Date
        if 'Date' not in mapped_targets and any(re.search(pat, col_lower) for pat in date_patterns):
            normalized[col] = 'Date'
            mapped_targets.add('Date')
        # Check Description (make sure it doesn't match date/amount)
        elif 'Description' not in mapped_targets and any(re.search(pat, col_lower) for pat in desc_patterns) and 'date' not in col_lower:
            normalized[col] = 'Description'
            mapped_targets.add('Description')
        # Check Amount
        elif 'Amount' not in mapped_targets and any(re.search(pat, col_lower) for pat in amount_patterns):
            normalized[col] = 'Amount'
            mapped_targets.add('Amount')
        # Check Category
        elif 'Category' not in mapped_targets and any(re.search(pat, col_lower) for pat in cat_patterns):
            normalized[col] = 'Category'
            mapped_targets.add('Category')
            
    return normalized


def load_and_validate_csv(file_path_or_buffer):
    """
    Loads transaction CSV, normalizes columns, validates required fields, and cleans the data.
    """
    try:
        # Load CSV
        df = pd.read_csv(file_path_or_buffer)
    except Exception as e:
        raise ValueError(f"Failed to read CSV file: {str(e)}")

    if df.empty:
        raise ValueError("The uploaded CSV file is empty.")

    # Normalize column names
    col_mapping = normalize_columns(df.columns)
    df = df.rename(columns=col_mapping)

    # Check required columns
    required_cols = ['Date', 'Description', 'Amount']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV is missing required columns (or equivalents): {', '.join(missing_cols)}. "
                         f"Found columns: {list(df.columns)}")

    # Clean Date column
    try:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        # Drop rows where Date is invalid
        invalid_dates = df['Date'].isna().sum()
        if invalid_dates > 0:
            df = df.dropna(subset=['Date'])
    except Exception as e:
        raise ValueError(f"Error parsing 'Date' column: {str(e)}")

    if df.empty:
        raise ValueError("No rows with valid dates found in the CSV.")

    # Sort by date
    df = df.sort_values(by='Date').reset_index(drop=True)

    # Clean Description
    df['Description'] = df['Description'].fillna('Unknown Transaction').astype(str).str.strip()

    # Clean Amount column (handle strings, currency symbols, commas, negative values)
    def clean_amount(val):
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        
        # Convert to string and clean
        val_str = str(val).strip()
        # Remove currency symbols ($ , £, €) and commas
        val_str = re.sub(r'[\$,£,€]', '', val_str)
        val_str = val_str.replace(',', '')
        
        try:
            return float(val_str)
        except ValueError:
            return 0.0

    df['Amount'] = df['Amount'].apply(clean_amount)
    
    # Standardize: make sure expenses are positive numbers, income is optional.
    # Usually in expense files, all expenses are positive, or all are negative.
    # Let's check if the majority of non-zero entries are negative.
    # If so, invert sign. Otherwise keep as is, but ensure we don't have mixed signs.
    # For a personal finance tracker, we'll treat all amounts as expense amounts,
    # unless they are explicitly categorizable as income.
    
    # If Category column doesn't exist, initialize it
    if 'Category' not in df.columns:
        df['Category'] = 'Uncategorized'
    else:
        df['Category'] = df['Category'].fillna('Uncategorized').astype(str).str.strip()
        df['Category'] = df['Category'].replace({'nan': 'Uncategorized', '': 'Uncategorized'})

    return df

# Simple rule-based categorization dictionary
CATEGORIES_RULES = {
    'Food & Dining': [
        'grocery', 'groceries', 'supermarket', 'walmart', 'target', 'whole foods', 'kroger', 'safeway', 'aldi', 'lidl',
        'restaurant', 'mcdonald', 'starbucks', 'subway', 'uber eats', 'doordash', 'pizza', 'burger', 'cafe', 'coffee',
        'baker', 'dine', 'eat', 'grill', 'diner', 'kfc', 'taco bell', 'burger king', 'starbuck', 'bistro', 'food'
    ],
    'Transport': [
        'uber', 'lyft', 'taxi', 'transit', 'subway', 'metro', 'bus', 'train', 'flight', 'airline', 'delta', 'united',
        'gas', 'fuel', 'shell', 'chevron', 'exxon', 'mobil', 'bp', 'parking', 'toll', 'trainline', 'cab', 'petrol'
    ],
    'Shopping': [
        'amazon', 'ebay', 'zara', 'h&m', 'nike', 'adidas', 'mall', 'department', 'clothing', 'apparel', 'shoes',
        'online store', 'walmart shopping', 'target store', 'best buy', 'sephora', 'ikea', 'macys', 'nordstrom', 'asos'
    ],
    'Bills & Utilities': [
        'electric', 'power', 'water', 'gas bill', 'utility', 'comcast', 'verizon', 'at&t', 't-mobile', 'internet',
        'phone', 'insurance', 'rent', 'mortgage', 'hoa', 'geico', 'progressive', 'landlord', 'electricity', 'sewer'
    ],
    'Entertainment': [
        'netflix', 'spotify', 'hulu', 'disney', 'hbo', 'youtube', 'cinema', 'theater', 'concert', 'ticket', 'game',
        'steam', 'playstation', 'xbox', 'nintendo', 'bar', 'pub', 'club', 'brewery', 'netflix.com', 'sport'
    ],
    'Healthcare': [
        'pharmacy', 'cvs', 'walgreens', 'doctor', 'dentist', 'hospital', 'medical', 'clinic', 'therapy', 'health',
        'dental', 'vision', 'prescription', 'optician', 'physio'
    ],
    'Education': [
        'tuition', 'school', 'college', 'course', 'udemy', 'coursera', 'book', 'stationery', 'university', 'class'
    ],
    'Income': [
        'salary', 'paycheck', 'deposit', 'direct deposit', 'dividend', 'interest earned', 'refund', 'venmo cashout'
    ]
}

def auto_categorize(df, force_reclassify=False):
    """
    Categorizes transactions based on keyword matches in description.
    Only updates 'Uncategorized' or 'Other' unless force_reclassify is True.
    """
    df_copy = df.copy()
    
    def get_category(desc, current_cat):
        if not force_reclassify and current_cat not in ['Uncategorized', 'Other', '', 'nan', None]:
            return current_cat
            
        desc_lower = str(desc).lower()
        for cat, keywords in CATEGORIES_RULES.items():
            for kw in keywords:
                # Use word boundary or simple contains depending on keyword
                if re.search(r'\b' + re.escape(kw) + r'\b', desc_lower) or kw in desc_lower:
                    return cat
        return 'Other'

    df_copy['Category'] = df_copy.apply(lambda row: get_category(row['Description'], row['Category']), axis=1)
    return df_copy

def get_dataset_info(df):
    """
    Returns high-level statistics of the dataset.
    """
    info = {
        'total_rows': len(df),
        'columns': list(df.columns),
        'missing_values': df.isnull().sum().to_dict(),
        'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
        'start_date': df['Date'].min().strftime('%Y-%m-%d') if not df.empty else None,
        'end_date': df['Date'].max().strftime('%Y-%m-%d') if not df.empty else None,
        'total_spending': float(df[df['Category'] != 'Income']['Amount'].sum()),
        'total_income': float(df[df['Category'] == 'Income']['Amount'].sum()),
    }
    return info

def check_budget_alerts(df, budgets, selected_month=None):
    """
    Checks if spending in the latest month or selected month exceeds budget limits.
    budgets: dict of category -> budget limit
    selected_month: pd.Timestamp or 'YYYY-MM' string, if None uses the latest month in data
    """
    if df.empty:
        return {}

    # Standardize date format to Year-Month
    df_copy = df.copy()
    df_copy['Month'] = df_copy['Date'].dt.to_period('M')

    if selected_month is None:
        latest_month = df_copy['Month'].max()
    else:
        latest_month = pd.Period(selected_month, freq='M')

    # Filter for the selected month and exclude Income from expense budgets
    monthly_data = df_copy[(df_copy['Month'] == latest_month) & (df_copy['Category'] != 'Income')]
    
    category_spending = monthly_data.groupby('Category')['Amount'].sum().to_dict()
    
    alerts = {}
    for cat, limit in budgets.items():
        if limit <= 0:
            continue
        spent = category_spending.get(cat, 0.0)
        percentage = (spent / limit) * 100
        
        status = 'Normal'
        if percentage >= 100:
            status = 'Critical'
        elif percentage >= 80:
            status = 'Warning'
            
        alerts[cat] = {
            'spent': float(spent),
            'budget': float(limit),
            'percentage': float(percentage),
            'status': status
        }
        
    return {
        'month': str(latest_month),
        'alerts': alerts
    }
