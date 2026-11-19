"""Seed the database with 1200 products."""

import os
import sys
import time

from sqlalchemy.exc import OperationalError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, SessionLocal, engine
from app.models import Product

PRODUCT_COUNT = 1200


def wait_for_db(retries: int = 30, delay: float = 1.0) -> None:
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                conn.exec_driver_sql("SELECT 1")
            return
        except OperationalError:
            print(f"DB not ready ({attempt}/{retries}), retrying...")
            time.sleep(delay)
    raise RuntimeError("Database is not available")


def seed() -> None:
    wait_for_db()
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        existing = db.query(Product).count()
        if existing >= PRODUCT_COUNT:
            print(f"Already seeded ({existing} products).")
            return

        products = [
            Product(
                name=f"Product {i:04d}",
                price=round(1.0 + (i % 50) * 0.5, 2),
                stock=100 + (i % 20),
            )
            for i in range(1, PRODUCT_COUNT + 1)
        ]
        db.add_all(products)
        db.commit()
        print(f"Inserted {PRODUCT_COUNT} products.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
