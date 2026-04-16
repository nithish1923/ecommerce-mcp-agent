import streamlit as st
import pandas as pd
from agent import run_agent

# Page config
st.set_page_config(page_title="MCP Agent", layout="wide")

# Header
st.title("🛒 Agentic E-commerce MCP")
st.caption("LLM-powered pricing agent with dynamic tool orchestration")

st.divider()

# ---------------------------
# SESSION STATE (IMPORTANT FIX)
# ---------------------------
if "user_input" not in st.session_state:
    st.session_state.user_input = ""

# Input box
st.session_state.user_input = st.text_area(
    "💬 Enter your scenario",
    value=st.session_state.user_input,
    height=120,
    placeholder="Describe your purchase in natural language..."
)

# ---------------------------
# EXAMPLE BUTTONS (FIXED)
# ---------------------------
st.subheader("🧪 Try Examples")

examples = [
    "Laptop 50000, 20% discount, SAVE10 coupon, 18% GST, add shipping",
    "Phone 30000, 10% discount, 18% GST",
    "Laptop 50000 convert to USD"
]

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Example 1"):
        st.session_state.user_input = examples[0]

with col2:
    if st.button("Example 2"):
        st.session_state.user_input = examples[1]

with col3:
    if st.button("Example 3"):
        st.session_state.user_input = examples[2]

st.divider()

# ---------------------------
# RUN AGENT
# ---------------------------
if st.button("🚀 Calculate") and st.session_state.user_input:

    result = run_agent(st.session_state.user_input)

    # Final price
    st.metric("💰 Final Price", result["final_price"])

    st.divider()

    # ---------------------------
    # AGENT EXECUTION LOGS
    # ---------------------------
    st.subheader("🧠 Agent Execution")

    for log in result["logs"]:
        if "discount" in log:
            st.info(log)
        elif "coupon" in log:
            st.warning(log)
        elif "tax" in log:
            st.error(log)
        elif "shipping" in log:
            st.success(log)
        elif "USD" in log:
            st.info(log)
        else:
            st.write(log)

    st.divider()

    # ---------------------------
    # EXECUTION FLOW
    # ---------------------------
    flow = " → ".join([
        log.split("|")[0].replace("Step", "").strip()
        for log in result["logs"]
        if "Step" in log
    ])

    st.subheader("🔄 Execution Flow")
    st.code(flow)

    st.divider()

    # ---------------------------
    # BREAKDOWN TABLE
    # ---------------------------
    steps_data = []

    for log in result["logs"]:
        if "→" in log:
            try:
                parts = log.split("→")
                step_name = parts[0].strip()
                value = parts[1].split("|")[0].strip()
                steps_data.append({
                    "Step": step_name,
                    "Value": value
                })
            except:
                pass

    if steps_data:
        df = pd.DataFrame(steps_data)
        st.subheader("📊 Price Breakdown")
        st.dataframe(df, use_container_width=True)

st.divider()

# ---------------------------
# CLEAN FOOTER (FIXED)
# ---------------------------
st.markdown("Built with **Streamlit + Render + OpenAI**")
