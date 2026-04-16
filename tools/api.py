from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}


@app.post("/apply_discount")
def apply_discount(data: dict):
    price = data["price"]
    discount = data["discount"]
    return {"price_after_discount": price * (1 - discount / 100)}


@app.post("/apply_tax")
def apply_tax(data: dict):
    price = data["price"]
    tax = data["tax"]
    return {"final_price": price * (1 + tax / 100)}


@app.post("/apply_coupon")
def apply_coupon(data: dict):
    price = data["price"]
    coupon = data.get("coupon", "")

    if coupon == "SAVE10":
        price *= 0.9
    elif coupon == "SAVE20":
        price *= 0.8

    return {"price_after_coupon": price}


@app.post("/shipping_cost")
def shipping_cost(data: dict):
    price = data["price"]
    shipping = 0 if price > 50000 else 500

    return {
        "shipping": shipping,
        "price_with_shipping": price + shipping
    }


@app.post("/convert_currency")
def convert_currency(data: dict):
    price = data["price"]
    return {"price_usd": price * 0.012}
