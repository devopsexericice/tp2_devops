# TP2 — Restaurant API

## Membres:

## Ray Viho AGUE
## Bethsaïda JEAN VALDEMAR
## Réné Oke Codjo HOUENANGNON
## Elvis NDUWIMANA

API minimale Python (FastAPI) + PostgreSQL pour le TP DevOps.

## Lancer en local

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec api python scripts/seed.py
```

- Health : `GET http://localhost:8000/health`
- Produits : `GET http://localhost:8000/products`
- Stock : `PUT http://localhost:8000/products/{id}/stock` avec `{"stock":10}`
- Commande : `POST http://localhost:8000/orders` avec `{"product_id":1,"quantity":1}`

## Tests

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest -q
```

## Secrets

Aucun secret réel dans le dépôt. Valeurs locales factices dans `.env.example` / `docker-compose.yml`. Les secrets CI/CD passent uniquement par GitHub Secrets.
