import streamlit as st
from agent import run_agent

st.title("🛒 Agentic E-commerce MCP")

user_input = st.text_input(
    "Enter details",
    "Laptop 50000, 20% discount, 18% GST"
)

if st.button("Calculate"):
    result = run_agent(user_input)

    if isinstance(result, dict):
        st.success(f"Final Price: {result['final_price']}")

        st.subheader("🧠 Agent Steps")
        for log in result["logs"]:
            st.write(log)
    else:
        st.write(result)
