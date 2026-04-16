import streamlit as st
from agent import run_agent

st.title("🛒 Agentic E-commerce MCP")

user_input = st.text_input(
    "Enter details",
    "Laptop 50000, 20% discount, SAVE10 coupon, 18% GST, add shipping"
)

if st.button("Calculate"):
    result = run_agent(user_input)

    st.success(f"Final Price: {result['final_price']}")

    st.subheader("🧠 Agent Steps")
    for log in result["logs"]:
        st.write(log)
