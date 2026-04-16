from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"status": "running"}

@app.post("/apply_discount")
def apply_discount(data: dict):
    price = data["price"]
    discount = data["discount"]
    final = price - (price * discount / 100)
    return {"price_after_discount": final}

@app.post("/apply_tax")
def apply_tax(data: dict):
    price = data["price"]
    tax = data["tax"]
    final = price + (price * tax / 100)
    return {"final_price": final}
