"""Minimal frontend (Streamlit / Gradio) talking to the FastAPI backend."""
import os

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Production AI App")
query = st.text_input("Ask a question")

if st.button("Send") and query:
    response = requests.post(f"{BACKEND_URL}/query", json={"query": query}, timeout=60)
    st.write(response.json())
