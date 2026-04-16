import requests
import json
import re
import time
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

BASE_URL = "https://ecommerce-tools-api.onrender.com"


def wake_backend():
    try:
        requests.get(BASE_URL, timeout=10)
        time.sleep(2)
    except:
        pass


def safe_post(url, payload):
    try:
        res = requests.post(url, json=payload, timeout=20)

        if res.status_code != 200:
            return {"error": f"HTTP {res.status_code}"}

        return res.json()
    except Exception as e:
        return {"error": str(e)}


def extract_data(text):
    nums = list(map(int, re.findall(r'\d+', text)))

    coupon = None
    if "save10" in text.lower():
        coupon = "SAVE10"
    elif "save20" in text.lower():
        coupon = "SAVE20"

    return {
        "price": nums[0] if len(nums) > 0 else 0,
        "discount": nums[1] if len(nums) > 1 else 0,
        "tax": nums[2] if len(nums) > 2 else 0,
        "coupon": coupon
    }


def clean_json(reply):
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
You are an intelligent e-commerce pricing agent.

Available tools:
apply_discount, apply_tax, apply_coupon, shipping_cost, convert_currency

Rules:
- Use only needed tools
- Order: discount → coupon → tax → shipping → currency
- One tool at a time
- Return final answer at end

Respond ONLY in JSON:
{"action": "...", "input": {}}
"""
        },
        {"role": "user", "content": user_input}
    ]

    for step in range(6):
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        reply = res.choices[0].message.content
        clean = clean_json(reply)

        try:
            action = json.loads(clean)
        except:
            return {"final_price": "Error", "logs": logs + [reply]}

        # DISCOUNT
        if action["action"] == "apply_discount":
            result = safe_post(
                f"{BASE_URL}/apply_discount",
                {"price": current_price, "discount": data["discount"]}
            )

            current_price = result["price_after_discount"]
            logs.append(f"Step {step+1}: 🔧 discount → {int(current_price)}")

        # COUPON
        elif action["action"] == "apply_coupon":
            result = safe_post(
                f"{BASE_URL}/apply_coupon",
                {"price": current_price, "coupon": data["coupon"]}
            )

            current_price = result["price_after_coupon"]
            logs.append(f"Step {step+1}: 💸 coupon → {int(current_price)}")

        # TAX
        elif action["action"] == "apply_tax":
            result = safe_post(
                f"{BASE_URL}/apply_tax",
                {"price": current_price, "tax": data["tax"]}
            )

            current_price = result["final_price"]
            logs.append(f"Step {step+1}: 🧾 tax → {int(current_price)}")

        # SHIPPING
        elif action["action"] == "shipping_cost":
            result = safe_post(
                f"{BASE_URL}/shipping_cost",
                {"price": current_price}
            )

            current_price = result["price_with_shipping"]
            logs.append(f"Step {step+1}: 🚚 shipping → {int(current_price)}")

        # CURRENCY
        elif action["action"] == "convert_currency":
            result = safe_post(
                f"{BASE_URL}/convert_currency",
                {"price": current_price}
            )

            usd = round(result["price_usd"], 2)

            return {
                "final_price": f"${usd}",
                "logs": logs + [f"Step {step+1}: 🪙 USD → {usd}"]
            }

        # FINAL
        elif action["action"] == "final":
            return {
                "final_price": f"₹{int(current_price):,}",
                "logs": logs + [f"Step {step+1}: ✅ Final"]
            }

        else:
            return {"final_price": "Error", "logs": logs}

        messages.append({"role": "assistant", "content": reply})
        messages.append({
            "role": "user",
            "content": f"Result: {result}, price: {current_price}"
        })

    return {"final_price": "Error", "logs": logs}
