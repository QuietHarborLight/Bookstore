"""Bookstore Management MVP — home page."""

import streamlit as st

import db

st.set_page_config(page_title="Bookstore MVP", page_icon="📚", layout="wide")

db.init_db()

st.title("Bookstore Management")
st.markdown(
    """
    Manage inventory, record sales, place manufacturer orders, and track customer
    special orders from the sidebar.

    **Daily workflow**
    1. Check inventory and stock levels
    2. Record sales (stock updates automatically)
    3. Create purchase orders and mark them received
    4. Log and update customer special-order requests

    Data is stored locally in `bookstore.db`. Back it up by copying that file.
    """
)

st.info("Use the sidebar to open Inventory, Sales, Purchase Orders, or Customer Orders.")
