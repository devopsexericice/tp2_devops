import os

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import Order, Product

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Restaurant API")


class OrderIn(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


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


@app.post("/orders", status_code=201)
def create_order(payload: OrderIn, db: Session = Depends(get_db)):
    with db.begin():
        product = db.scalar(
            select(Product)
            .where(Product.id == payload.product_id)
            .with_for_update()
        )
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        if product.stock < payload.quantity:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "insufficient_stock",
                    "message": (
                        f"Stock insuffisant : {payload.quantity} demandés, "
                        f"{product.stock} disponibles"
                    ),
                    "product_id": product.id,
                    "requested": payload.quantity,
                    "available": product.stock,
                },
            )

        product.stock -= payload.quantity
        order = Order(product_id=payload.product_id, quantity=payload.quantity)
        db.add(order)
    db.refresh(order)
    return {"id": order.id, "product_id": order.product_id, "quantity": order.quantity}
