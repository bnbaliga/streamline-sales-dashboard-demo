import streamlit as st
import data_loader as dl
import data_wrangler as dw
import yfinance as yf

df = dw.prep_data()

st.title("Sales Data Overview")
st.write("This application provides an overview of the sales data.")
st.set_page_config(layout='wide')

dw.filter_panel(df)


