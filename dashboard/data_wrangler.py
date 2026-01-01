import data_loader as dl
import streamlit as st

filter_dims = ["Age group", "Gender", "Category", "Segment",
               "Product name", "State"]

def clean_column_names(df):
  df.columns = df.columns.str.replace('_', ' ').str.capitalize()
  return df


def prep_data():
  return clean_column_names(dl.load_data())

def get_unique_values(df, column):
  return list(df[column].unique())

def filter_panel(df):
  with st.expander("Filters"):
    filter_cols = st.columns(len(filter_dims))
    for idx, dim in enumerate(filter_dims):
      with filter_cols[idx]:
        unique_vals = get_unique_values(df, dim)
        st.multiselect(dim, unique_vals)