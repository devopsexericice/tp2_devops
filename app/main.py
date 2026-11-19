import os

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Order, Product

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Restaurant API")


class OrderIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class StockIn(BaseModel):
    # Stock négatif rejeté ici : FastAPI répond 422 sans toucher au modèle Product.
    stock: int = Field(ge=0)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": os.getenv("APP_VERSION", "dev"),
        "commit": os.getenv("GIT_COMMIT", "unknown"),
    }


@app.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.id).all()
    return [
        {"id": p.id, "name": p.name, "price": p.price, "stock": p.stock}
        for p in products
    ]


@app.put("/products/{product_id}/stock")
def update_product_stock(
    product_id: int, payload: StockIn, db: Session = Depends(get_db)  # noqa: B008
):
    product = db.get(Product, product_id)
    # 404 si le produit n'existe pas ; le corps invalide est déjà un 422.
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Remplace le stock, ne le décrémente pas (réservé à POST /orders).
    product.stock = payload.stock
    db.commit()
    db.refresh(product)
    return {"id": product.id, "name": product.name, "price": product.price, "stock": product.stock}


@app.post("/orders", status_code=201)
def create_order(payload: OrderIn, db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock < payload.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    product.stock -= payload.quantity
    order = Order(product_id=payload.product_id, quantity=payload.quantity)
    db.add(order)
    db.commit()
    db.refresh(order)
    return {"id": order.id, "product_id": order.product_id, "quantity": order.quantity}
