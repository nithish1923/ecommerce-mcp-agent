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


# 🔥 Wake backend (Render sleep fix)
def wake_backend():
    try:
        requests.get(BASE_URL, timeout=10)
        time.sleep(2)
    except:
        pass


# 🔥 Safe HTTP call
def safe_post(url, payload):
    try:
        res = requests.post(url, json=payload, timeout=20)

        if res.status_code != 200:
            return {"error": f"HTTP {res.status_code}"}

        try:
            return res.json()
        except:
            return {"error": "Invalid JSON"}
    except Exception as e:
        return {"error": str(e)}


# 🔥 Extract structured data
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


# 🔥 Clean LLM JSON (fix ```json issue)
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
- Use only required tools
- Order: discount → coupon → tax → shipping → currency
- Skip unnecessary steps
- One tool at a time
- Always return final answer

Respond ONLY in JSON:
{"action": "...", "input": {}}
"""
        },
        {"role": "user", "content": user_input}
    ]

    for step in range(6):  # loop safety
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        reply = response.choices[0].message.content
        clean = clean_json(reply)

        # Parse LLM response
        try:
            action = json.loads(clean)
        except:
            return {
                "final_price": "Error",
                "logs": logs + [f"⚠️ LLM format error → {reply}"]
            }

        # 🔧 DISCOUNT
        if action["action"] == "apply_discount":
            result = safe_post(
                f"{BASE_URL}/apply_discount",
                {"price": current_price, "discount": data["discount"]}
            )

            if "error" in result or "price_after_discount" not in result:
                logs.append(f"❌ Discount failed → {result}")
                continue

            current_price = result["price_after_discount"]
            logs.append(f"Step {step+1}: 🔧 discount → {int(current_price)}")

        # 💸 COUPON
        elif action["action"] == "apply_coupon":

            if not data["coupon"]:
                logs.append(f"Step {step+1}: ⚠️ No coupon → skipped")
                continue

            result = safe_post(
                f"{BASE_URL}/apply_coupon",
                {"price": current_price, "coupon": data["coupon"]}
            )

            if "error" in result or "price_after_coupon" not in result:
                logs.append(f"❌ Coupon failed → {result}")
                continue

            current_price = result["price_after_coupon"]
            logs.append(f"Step {step+1}: 💸 coupon → {int(current_price)}")

        # 🧾 TAX
        elif action["action"] == "apply_tax":
            result = safe_post(
                f"{BASE_URL}/apply_tax",
                {"price": current_price, "tax": data["tax"]}
            )

            if "error" in result or "final_price" not in result:
                logs.append(f"❌ Tax failed → {result}")
                continue

            current_price = result["final_price"]
            logs.append(f"Step {step+1}: 🧾 tax → {int(current_price)}")

        # 🚚 SHIPPING
        elif action["action"] == "shipping_cost":
            result = safe_post(
                f"{BASE_URL}/shipping_cost",
                {"price": current_price}
            )

            if "error" in result or "price_with_shipping" not in result:
                logs.append(f"❌ Shipping failed → {result}")
                continue

            current_price = result["price_with_shipping"]
            logs.append(f"Step {step+1}: 🚚 shipping → {int(current_price)}")

        # 🪙 CURRENCY
        elif action["action"] == "convert_currency":
            result = safe_post(
                f"{BASE_URL}/convert_currency",
                {"price": current_price}
            )

            if "error" in result or "price_usd" not in result:
                logs.append(f"❌ Currency failed → {result}")
                continue

            usd = round(result["price_usd"], 2)

            return {
                "final_price": f"${usd}",
                "logs": logs + [f"Step {step+1}: 🪙 USD → {usd}"]
            }

        # ✅ FINAL (robust handling)
        elif action["action"] in ["final", "final_price", "finish", "done"]:

            if "final_price" in action.get("input", {}):
                final_val = action["input"]["final_price"]
            else:
                final_val = current_price

            return {
                "final_price": f"₹{int(final_val):,}",
                "logs": logs + [f"Step {step+1}: ✅ Final"]
            }

        # ⚠️ Unknown action → treat as final
        else:
            return {
                "final_price": f"₹{int(current_price):,}",
                "logs": logs + [f"⚠️ Unknown action treated as final → {action}"]
            }

        # Feed tool result back to LLM
        messages.append({"role": "assistant", "content": reply})
        messages.append({
            "role": "user",
            "content": f"Tool result: {result}, current_price: {current_price}"
        })

    return {
        "final_price": f"₹{int(current_price):,}",
        "logs": logs + ["⚠️ Max steps reached → forced final"]
    }
