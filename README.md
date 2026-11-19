# TP2 — Restaurant API

## Ray Viho AGUE
## Bethsaïda JEAN VALDEMAR
## Réné Oke Codjo HUENAGNON
## Elvis NDUWIMANA

![CI](https://github.com/devopsexericice/tp2_devops/actions/workflows/ci.yml/badge.svg)
![CD](https://github.com/devopsexericice/tp2_devops/actions/workflows/cd.yml/badge.svg)

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
pip install -r requirements-dev.txt
pytest -q
```

En local, les tests utilisent SQLite par défaut. En CI, ils tournent contre PostgreSQL.

## CI/CD

- CI de PR : `secret-scan` (gitleaks), `lint` (Ruff), `test` (PostgreSQL), `build` Docker.
- CD : publication GHCR (`sha-...`, `vX.Y.Z`), staging éphémère avec smoke test `/health`, release sur tag et rollback manuel sans rebuild.
- Production : environnement GitHub `production` avec approbation interne et secrets `PROD_*`. Procédure complète dans `docs/deploy.md`.
- Migrations : Alembic (`alembic upgrade head`), appliquées automatiquement par `scripts/deploy.sh`.

## Secrets

Aucun secret réel dans le dépôt. Valeurs locales factices dans `.env.example` / `docker-compose.yml`, allowlistées dans `.gitleaks.toml`. Les secrets CI/CD passent uniquement par GitHub Secrets.
