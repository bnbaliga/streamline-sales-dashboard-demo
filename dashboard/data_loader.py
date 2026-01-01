import pandas as pd
from pathlib import Path
import streamlit as st

@st.cache_data(show_spinner="Reading sales data...", ttl="1d")
def load_data():
    base_dir = Path(__file__).resolve().parent
    sales_data_path = base_dir / "data/sales_data.csv"

    if sales_data_path.exists():
        return pd.read_csv(sales_data_path)
    else:
        raise FileNotFoundError(f"Data file not found at {sales_data_path}")
