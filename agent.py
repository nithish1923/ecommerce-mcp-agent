import requests
import re
import streamlit as st
from openai import OpenAI

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# 🔥 Replace after Render deploy
BASE_URL = "https://ecommerce-tools-api.onrender.com"


def extract_data(text):
    numbers = list(map(int, re.findall(r'\d+', text)))

    return {
        "price": numbers[0],
        "discount": numbers[1],
        "tax": numbers[2]
    }


def run_agent(user_input):
    data = extract_data(user_input)

    # Step 1: Apply discount
    discount_res = requests.post(
        f"{BASE_URL}/apply_discount",
        json={
            "price": data["price"],
            "discount": data["discount"]
        }
    ).json()

    # Step 2: Apply tax
    tax_res = requests.post(
        f"{BASE_URL}/apply_tax",
        json={
            "price": discount_res["price_after_discount"],
            "tax": data["tax"]
        }
    ).json()

    # Step 3: LLM explanation
    prompt = f"""
Original price: {data['price']}
After discount: {discount_res['price_after_discount']}
Final price: {tax_res['final_price']}

Explain clearly.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content
