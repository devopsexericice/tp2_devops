import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ["APP_VERSION"] = "test"
os.environ["GIT_COMMIT"] = "abcdef1"

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Product

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)


def _add_product(name: str = "Pizza", price: float = 12.5, stock: int = 10) -> int:
    db = SessionLocal()
    product = Product(name=name, price=price, stock=stock)
    db.add(product)
    db.commit()
    db.refresh(product)
    product_id = product.id
    db.close()
    return product_id


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "test"
    assert body["commit"] == "abcdef1"


def test_list_products():
    _add_product()
    response = client.get("/products")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_create_order():
    product_id = _add_product(stock=5)
    response = client.post("/orders", json={"product_id": product_id, "quantity": 2})
    assert response.status_code == 201
    body = response.json()
    assert body["product_id"] == product_id
    assert body["quantity"] == 2
