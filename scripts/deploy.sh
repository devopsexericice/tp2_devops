#!/usr/bin/env bash
set -euo pipefail
umask 077

: "${API_IMAGE:?API_IMAGE est requis}"
: "${APP_VERSION:?APP_VERSION est requis}"
: "${PROD_DIR:=/opt/restaurant}"
: "${API_PORT:=}"

cd "$PROD_DIR"

if [ ! -f .env ]; then
  echo "Erreur: $PROD_DIR/.env est absent. Copier deploy/.env.example et renseigner POSTGRES_PASSWORD." >&2
  exit 1
fi

if [ -z "$API_PORT" ]; then
  API_PORT="$(sed -n 's/^API_PORT=//p' .env | tail -n1)"
fi
API_PORT="${API_PORT:-8000}"

mkdir -p backups

if [ -n "$(docker compose -f docker-compose.prod.yml ps -q db 2>/dev/null || true)" ]; then
  backup="backups/db-$(date -u +%Y%m%dT%H%M%SZ).sql"
  echo "Backup PostgreSQL -> $backup"
  if ! docker compose -f docker-compose.prod.yml exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB"' > "$backup"; then
    echo "Erreur: backup PostgreSQL échoué, déploiement annulé." >&2
    rm -f "$backup"
    exit 1
  fi
fi

export API_IMAGE APP_VERSION API_PORT

echo "Pull de $API_IMAGE"
docker compose -f docker-compose.prod.yml pull api

if [ -z "${GIT_COMMIT:-}" ]; then
  GIT_COMMIT="$(docker image inspect "$API_IMAGE" --format '{{ index .Config.Labels "org.opencontainers.image.revision" }}' 2>/dev/null || true)"
fi
GIT_COMMIT="${GIT_COMMIT:-unknown}"
export GIT_COMMIT

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
