import requests
import json
import re
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

BASE_URL = "https://your-api.onrender.com"


# Extract numbers (fallback)
def extract_data(text):
    nums = list(map(int, re.findall(r'\d+', text)))
    return {
        "price": nums[0] if len(nums) > 0 else 0,
        "discount": nums[1] if len(nums) > 1 else 0,
        "tax": nums[2] if len(nums) > 2 else 0
    }


def run_agent(user_input):
    data = extract_data(user_input)

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
- After getting result, continue reasoning
- Finally return final answer

Respond ONLY in JSON format:

{
  "action": "apply_discount | apply_tax | final",
  "input": {}
}
"""
        },
        {"role": "user", "content": user_input}
    ]

    current_price = data["price"]

    while True:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        reply = response.choices[0].message.content

        try:
            action = json.loads(reply)
        except:
            return reply  # fallback if LLM breaks

        # 🔧 TOOL: Discount
        if action["action"] == "apply_discount":
            result = requests.post(
                f"{BASE_URL}/apply_discount",
                json={
                    "price": current_price,
                    "discount": data["discount"]
                }
            ).json()

            current_price = result["price_after_discount"]

        # 🔧 TOOL: Tax
        elif action["action"] == "apply_tax":
            result = requests.post(
                f"{BASE_URL}/apply_tax",
                json={
                    "price": current_price,
                    "tax": data["tax"]
                }
            ).json()

            current_price = result["final_price"]

        # ✅ FINAL ANSWER
        elif action["action"] == "final":
            return f"Final Price: ₹{current_price}"

        else:
            return "Invalid action"

        # Feed result back to LLM
        messages.append({
            "role": "assistant",
            "content": reply
        })

        messages.append({
            "role": "user",
            "content": f"Tool result: {result}, current_price: {current_price}"
        })
