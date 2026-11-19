#!/usr/bin/env bash
set -euo pipefail
umask 077

: "${API_IMAGE:?API_IMAGE est requis}"
: "${APP_VERSION:?APP_VERSION est requis}"
: "${PROD_DIR:=/opt/restaurant}"
: "${API_PORT:=}"
: "${RUN_MIGRATIONS:=true}"

cd "$PROD_DIR"

if [ ! -f .env ]; then
  echo "Erreur: $PROD_DIR/.env est absent. Copier deploy/.env.example et renseigner POSTGRES_PASSWORD." >&2
  exit 1
fi

if [ -z "$API_PORT" ]; then
  API_PORT="$(sed -n 's/^API_PORT=//p' .env | tail -n1)"
fi
API_PORT="${API_PORT:-8000}"

export API_IMAGE APP_VERSION API_PORT

echo "Démarrage de PostgreSQL"
docker compose -f docker-compose.prod.yml up -d db

echo "Attente de PostgreSQL"
for _ in $(seq 1 60); do
  if docker compose -f docker-compose.prod.yml exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker compose -f docker-compose.prod.yml exec -T db sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"'

mkdir -p backups
backup="backups/db-$(date -u +%Y%m%dT%H%M%SZ).sql"
echo "Backup PostgreSQL -> $backup"
if ! docker compose -f docker-compose.prod.yml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$backup"; then
  echo "Erreur: backup PostgreSQL échoué, déploiement annulé." >&2
  rm -f "$backup"
  exit 1
fi

echo "Pull de $API_IMAGE"
docker compose -f docker-compose.prod.yml pull api

if [ -z "${GIT_COMMIT:-}" ]; then
  GIT_COMMIT="$(docker image inspect "$API_IMAGE" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' 2>/dev/null || true)"
fi
GIT_COMMIT="${GIT_COMMIT:-unknown}"
export GIT_COMMIT

if [ "$RUN_MIGRATIONS" = "true" ]; then
  if docker compose -f docker-compose.prod.yml run --rm --no-deps api python -c 'import alembic' >/dev/null 2>&1; then
    has_version="$(docker compose -f docker-compose.prod.yml exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -tAc \"SELECT to_regclass('public.alembic_version')\"")"
    has_products="$(docker compose -f docker-compose.prod.yml exec -T db sh -c "psql -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -tAc \"SELECT to_regclass('public.products')\"")"
    if [ -z "$has_version" ] && [ -n "$has_products" ]; then
      echo "Schéma existant sans Alembic : adoption avec stamp 0001"
      docker compose -f docker-compose.prod.yml run --rm --no-deps api alembic stamp 0001
    fi
    echo "Application des migrations Alembic"
    docker compose -f docker-compose.prod.yml run --rm --no-deps api alembic upgrade head
  else
    echo "Image sans Alembic : migrations ignorées."
  fi
else
  echo "Migrations ignorées (RUN_MIGRATIONS=$RUN_MIGRATIONS)."
fi

echo "Déploiement de $API_IMAGE (version $APP_VERSION, commit $GIT_COMMIT)"
docker compose -f docker-compose.prod.yml up -d --remove-orphans

for i in $(seq 1 60); do
  if curl -fsS "http://localhost:${API_PORT}/health" -o /tmp/restaurant-health.json; then
    if grep -Eq "\"version\"[[:space:]]*:[[:space:]]*\"${APP_VERSION}\"" /tmp/restaurant-health.json; then
      echo "Health OK: $(cat /tmp/restaurant-health.json)"
      exit 0
    fi
    echo "Health répond mais la version ne correspond pas encore (tentative $i)"
  fi
  sleep 2
done

echo "Erreur: /health ne répond pas avec la version ${APP_VERSION}." >&2
cat /tmp/restaurant-health.json 2>/dev/null || true
docker compose -f docker-compose.prod.yml logs --tail=50 api || true
exit 1
