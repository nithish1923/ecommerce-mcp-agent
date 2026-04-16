import requests
import json
import re
import time
import streamlit as st
from openai import OpenAI

# OpenAI client
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 🔥 Replace with your Render URL
BASE_URL = "https://ecommerce-tools-api.onrender.com"


# 🔥 Wake backend (fix Render sleep)
def wake_backend():
    try:
        requests.get(BASE_URL, timeout=10)
        time.sleep(2)
    except:
        pass


# 🔥 Safe POST (handles errors + bad responses)
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


# 🔥 Extract numbers from input
def extract_data(text):
    nums = list(map(int, re.findall(r'\d+', text)))
    return {
        "price": nums[0] if len(nums) > 0 else 0,
        "discount": nums[1] if len(nums) > 1 else 0,
        "tax": nums[2] if len(nums) > 2 else 0
    }


# 🔥 Clean LLM output (fix ```json issue)
def clean_llm_json(reply):
    text = reply.strip()

    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) > 1:
            text = parts[1]
        text = text.replace("json", "").strip()

    return text


def run_agent(user_input):
    wake_backend()

    data = extract_data(user_input)
    current_price = data["price"]

    logs = []

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
- Call ONLY one tool at a time
- After each tool, continue reasoning
- Finally return answer

Respond ONLY in RAW JSON (no markdown, no ```):

{
  "action": "apply_discount | apply_tax | final",
  "input": {}
}
"""
        },
        {"role": "user", "content": user_input}
    ]

    for step in range(5):  # prevent infinite loop
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        reply = response.choices[0].message.content

        # 🔥 Clean LLM output
        clean_reply = clean_llm_json(reply)

        # 🔥 Parse JSON safely
        try:
            action = json.loads(clean_reply)
        except:
            return {
                "final_price": "Error",
                "logs": logs + [f"⚠️ LLM format error:\n{reply}"]
            }

        # 🔧 TOOL: apply_discount
        if action["action"] == "apply_discount":
            result = safe_post(
                f"{BASE_URL}/apply_discount",
                {
                    "price": current_price,
                    "discount": data["discount"]
                }
            )

            if "error" in result:
                return {
                    "final_price": "Error",
                    "logs": logs + [f"❌ Discount failed: {result['error']}"]
                }

            current_price = result["price_after_discount"]
            logs.append(f"Step {step+1}: 🔧 apply_discount → {result}")

        # 🔧 TOOL: apply_tax
        elif action["action"] == "apply_tax":
            result = safe_post(
                f"{BASE_URL}/apply_tax",
                {
                    "price": current_price,
                    "tax": data["tax"]
                }
            )

            if "error" in result:
                return {
                    "final_price": "Error",
                    "logs": logs + [f"❌ Tax failed: {result['error']}"]
                }

            current_price = result["final_price"]
            logs.append(f"Step {step+1}: 🔧 apply_tax → {result}")

        # ✅ FINAL ANSWER
        elif action["action"] == "final":
            return {
                "final_price": f"₹{int(current_price):,}",
                "logs": logs + [f"Step {step+1}: ✅ Final Answer"]
            }

        else:
            return {
                "final_price": "Error",
                "logs": logs + [f"❌ Invalid action: {action}"]
            }

        # 🔁 Feed result back to LLM
        messages.append({
            "role": "assistant",
            "content": reply
        })

        messages.append({
            "role": "user",
            "content": f"Tool result: {result}, current_price: {current_price}"
        })

    return {
        "final_price": "Error",
        "logs": logs + ["❌ Max steps reached"]
    }
