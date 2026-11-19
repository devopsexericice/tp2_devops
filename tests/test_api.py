import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ["APP_VERSION"] = "test"
os.environ["GIT_COMMIT"] = "abcdef1"

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Order, Product

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


def _extract_error_payload(response):
    body = response.json()
    detail = body.get("detail")
    return detail if isinstance(detail, dict) else body


def test_create_order_insufficient_stock():
    product_id = _add_product(stock=5)
    db = SessionLocal()
    try:
        order_count_before = db.query(Order).count()
    finally:
        db.close()

    response = client.post(
        "/orders",
        json={"product_id": product_id, "quantity": 8},
    )

    assert response.status_code == 409
    payload = _extract_error_payload(response)
    assert payload["error"] == "insufficient_stock"
    assert payload["product_id"] == product_id
    assert payload["requested"] == 8
    assert payload["available"] == 5

    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.stock == 5
        assert db.query(Order).count() == order_count_before
    finally:
        db.close()


def test_create_order_exact_stock():
    product_id = _add_product(stock=5)
    response = client.post(
        "/orders",
        json={"product_id": product_id, "quantity": 5},
    )

    assert response.status_code in (200, 201)

    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.stock == 0
        order = (
            db.query(Order)
            .filter(Order.product_id == product_id)
            .order_by(Order.id.desc())
            .first()
        )
        assert order is not None
        assert order.quantity == 5
    finally:
        db.close()


def test_create_order_zero_stock():
    product_id = _add_product(stock=0)
    db = SessionLocal()
    try:
        order_count_before = db.query(Order).count()
    finally:
        db.close()

    response = client.post(
        "/orders",
        json={"product_id": product_id, "quantity": 1},
    )

    assert response.status_code == 409
    payload = _extract_error_payload(response)
    assert payload["error"] == "insufficient_stock"
    assert payload["available"] == 0

    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.stock == 0
        assert db.query(Order).count() == order_count_before
    finally:
        db.close()


def test_update_product_stock():
    product_id = _add_product(stock=10)
    response = client.put(
        f"/products/{product_id}/stock",
        json={"stock": 25},
    )

    assert response.status_code == 200

    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.stock == 25
    finally:
        db.close()

    response = client.get("/products")
    assert response.status_code == 200
    listed_product = next(
        item for item in response.json() if item["id"] == product_id
    )
    assert listed_product["stock"] == 25


def test_product_not_found_stock_and_order():
    response = client.put(
        "/products/999999/stock",
        json={"stock": 10},
    )
    assert response.status_code == 404

    db = SessionLocal()
    try:
        order_count_before = db.query(Order).count()
    finally:
        db.close()

    response = client.post(
        "/orders",
        json={"product_id": 999999, "quantity": 1},
    )
    assert response.status_code == 404

    db = SessionLocal()
    try:
        assert db.query(Order).count() == order_count_before
    finally:
        db.close()


def test_invalid_quantities_and_negative_stock():
    product_id = _add_product(stock=10)
    db = SessionLocal()
    try:
        order_count_before = db.query(Order).count()
    finally:
        db.close()

    for quantity in (0, -2):
        response = client.post(
            "/orders",
            json={"product_id": product_id, "quantity": quantity},
        )
        assert response.status_code == 422

    db = SessionLocal()
    try:
        assert db.query(Order).count() == order_count_before
    finally:
        db.close()

    response = client.put(
        f"/products/{product_id}/stock",
        json={"stock": -5},
    )
    assert response.status_code == 422

    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        assert product is not None
        assert product.stock == 10
    finally:
        db.close()
