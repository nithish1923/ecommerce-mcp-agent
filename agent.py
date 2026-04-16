import requests
import json
import re
import time
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 🔥 Replace with your Render URL
BASE_URL = "https://ecommerce-tools-api.onrender.com"


# 🔥 Wake backend (Render sleep fix)
def wake_backend():
    try:
        requests.get(BASE_URL, timeout=10)
        time.sleep(2)
    except:
        pass


# 🔥 Safe POST (handles JSON errors)
def safe_post(url, payload):
    try:
        res = requests.post(url, json=payload, timeout=20)

        if res.status_code != 200:
            return {"error": f"HTTP {res.status_code}"}

        try:
            return res.json()
        except:
            return {"error": "Invalid JSON response"}

    except Exception as e:
        return {"error": str(e)}


# Extract numbers from input
def extract_data(text):
    nums = list(map(int, re.findall(r'\d+', text)))
    return {
        "price": nums[0] if len(nums) > 0 else 0,
        "discount": nums[1] if len(nums) > 1 else 0,
        "tax": nums[2] if len(nums) > 2 else 0
    }


def run_agent(user_input):
    wake_backend()

    data = extract_data(user_input)
    current_price = data["price"]

    messages = [
        {
            "role": "system",
            "content": """
You are an e-commerce pricing agent.

Available tools:
1. apply_discount(price, discount)
2. apply_tax(price, tax)

Rules:
- Decide which tool to call
- Call one tool at a time
- After each tool, continue reasoning
- Finally return answer

Respond ONLY in JSON:

{
  "action": "apply_discount | apply_tax | final",
  "input": {}
}
"""
        },
        {"role": "user", "content": user_input}
    ]

    for _ in range(5):  # prevent infinite loop
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        reply = response.choices[0].message.content

        try:
            action = json.loads(reply)
        except:
            return f"⚠️ LLM format error:\n{reply}"

        # 🔧 APPLY DISCOUNT
        if action["action"] == "apply_discount":
            result = safe_post(
                f"{BASE_URL}/apply_discount",
                {
                    "price": current_price,
                    "discount": data["discount"]
                }
            )

            if "error" in result:
                return f"❌ Discount tool failed: {result['error']}"

            current_price = result["price_after_discount"]

        # 🔧 APPLY TAX
        elif action["action"] == "apply_tax":
            result = safe_post(
                f"{BASE_URL}/apply_tax",
                {
                    "price": current_price,
                    "tax": data["tax"]
                }
            )

            if "error" in result:
                return f"❌ Tax tool failed: {result['error']}"

            current_price = result["final_price"]

        # ✅ FINAL OUTPUT
        elif action["action"] == "final":
            return f"Final Price: ₹{current_price}"

        else:
            return "❌ Invalid action from LLM"

        # Feed back to LLM
        messages.append({
            "role": "assistant",
            "content": reply
        })

        messages.append({
            "role": "user",
            "content": f"Tool result: {result}, current_price: {current_price}"
        })

    return "❌ Agent stopped (too many steps)"
