import streamlit as st
from agent import run_agent

st.title("🛒 Agentic E-commerce MCP")

user_input = st.text_input(
    "Enter details",
    "Laptop 50000, 20% discount, 18% GST"
)

if st.button("Calculate"):
    result = run_agent(user_input)
    st.success(result)
