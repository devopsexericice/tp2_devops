# Déploiement, release et rollback

## 1. Vue d'ensemble

- **`CD`** (`.github/workflows/cd.yml`) : un push sur `main` publie l'image `sha-<sha>` sur GHCR, démarre un staging éphémère et exécute le smoke test `/health`. Un tag `vX.Y.Z` publie aussi l'image `vX.Y.Z`, refait le staging, puis déploie la production après approbation de l'environnement `production`.
- **`Rollback`** (`.github/workflows/rollback.yml`) : workflow manuel avec une version cible `vX.Y.Z`. Il réutilise l'image GHCR déjà publiée, sauvegarde la base, redémarre le service et vérifie `/health`. Aucun rebuild.
- **Image** : `ghcr.io/devopsexericice/tp2_devops:<tag>`. Les tags `vX.Y.Z` et `sha-...` sont autorisés ; `latest` est interdit.
- **Staging** : conteneurs éphémères sur le runner GitHub avec PostgreSQL 16. Ce n'est pas un serveur de staging permanent.
- **Production** : serveur Docker accessible en SSH, décrit par `deploy/docker-compose.prod.yml` et `scripts/deploy.sh`.

## 2. Prérequis serveur

- Docker Engine et le plugin Compose v2, `curl`, `sed`.
- Un utilisateur SSH membre du groupe `docker`.
- Un répertoire de déploiement, par défaut `/opt/restaurant`, accessible en écriture.
- Un fichier `.env` créé depuis `deploy/.env.example`, avec un vrai `POSTGRES_PASSWORD` (URL-safe) et, si besoin, `API_PORT`.
- Ne jamais committer `.env`.

## 3. Secrets et environnements GitHub

Secrets à configurer au niveau du dépôt ou de l'environnement `production` :

| Nom | Rôle |
| :--- | :--- |
| `PROD_HOST` | Adresse IP ou nom du serveur de production. |
| `PROD_USER` | Utilisateur SSH de déploiement. |
| `PROD_SSH_KEY` | Clé privée SSH sans passphrase. |
| `PROD_DIR` | Répertoire de déploiement, par exemple `/opt/restaurant`. |
| `PROD_KNOWN_HOSTS` | Optionnel : empreinte SSH connue, pour éviter `ssh-keyscan`. |

`GITHUB_TOKEN` est fourni automatiquement par GitHub Actions pour publier et tirer l'image GHCR. Il ne faut pas le créer.

Environnements GitHub :

- `staging` : aucune protection obligatoire.
- `production` : **required reviewers = 1 développeur interne** et, si possible, restriction aux tags protégés. Seul un admin peut configurer ces règles. Le freelance n'a accès ni aux secrets ni à la production.

## 4. Premier déploiement et baseline `v1.0.0`

1. Un admin prépare le serveur, le répertoire et le fichier `.env`.
2. Un admin crée les secrets `PROD_*` et protège l'environnement `production`.
3. Merger la PR CD dans `main`.
4. Depuis `main`, créer le tag annoté de baseline :

   ```bash
   git switch main
   git pull --ff-only
   git tag -a v1.0.0 -m "Baseline v1.0.0"
   git push origin v1.0.0
   ```

5. Approuver le job `production` dans l'onglet Actions.
6. Vérifier la version active :

   ```bash
   curl -fsS https://<domaine>/health
   ```

   La réponse doit contenir `"version":"v1.0.0"` et le commit attendu.
7. Vérifier que GHCR contient les tags `v1.0.0` et `sha-...`, et aucun tag `latest`.

## 5. Release suivante

1. La PR est mergée dans `main` : le staging et le smoke test se lancent automatiquement.
2. Créer le tag de version sur `main` :

   ```bash
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```

3. Approuver le job `production`.
4. Vérifier `/health` : la version doit être `v1.1.0`.

## 6. Rollback en moins de 5 minutes

1. Onglet **Actions** → **Rollback** → **Run workflow**.
2. Saisir la version cible, par exemple `v1.0.0`.
3. Approuver l'environnement `production`.
4. Le workflow se connecte au serveur, sauvegarde la base, tire l'image `v1.0.0` depuis GHCR, redémarre le service et vérifie `/health`.
5. Vérifier la réponse : `"version":"v1.0.0"`.

Le rollback ne recompile pas l'image. Le backup est écrit dans `backups/db-<timestamp>.sql` sur le serveur.

## 7. Backup et restauration

Un backup PostgreSQL est pris avant chaque déploiement ou rollback si la base tourne. Pour restaurer un backup en urgence (admin uniquement) :

```bash
cd /opt/restaurant
docker compose -f docker-compose.prod.yml exec -T db \
  psql -U "$POSTGRES_USER" "$POSTGRES_DB" < backups/db-<timestamp>.sql
```

La restauration écrase les données actuelles : elle doit être validée par un interne.

## 8. Migrations de base

- `app/main.py` ne crée plus les tables : le schéma est géré par Alembic (`alembic.ini` + `migrations/`).
- `scripts/deploy.sh` démarre PostgreSQL, prend un backup, applique `alembic upgrade head`, puis redémarre l'API.
- Si la base existe déjà sans table `alembic_version`, le script fait d'abord `alembic stamp 0001` pour adopter le schéma initial, puis `upgrade head`.
- Le rollback passe `RUN_MIGRATIONS=false` : il ne rejoue pas les migrations et suppose que le schéma reste rétrocompatible. Toute migration doit donc rester compatible avec la version précédente.

## 9. Dépannage

- **`Le secret PROD_HOST n'est pas configuré`** : configurer les secrets `PROD_*` et, si utilisé, l'environnement `production`.
- **`docker login` échoue sur le serveur** : vérifier les droits `packages: read` et la visibilité du package GHCR.
- **`/health` ne répond pas** : consulter `docker compose -f docker-compose.prod.yml logs --tail=100 api`.
- **Version incorrecte** : vérifier que le tag poussé correspond à l'image et que le job de publication a réussi.
- **Le job production attend** : approuver le déploiement dans l'environnement `production`.

## 10. Limites

- Le staging est éphémère (runner GitHub) et ne remplace pas un serveur de staging permanent.
- La production dépend d'un serveur et de secrets configurés par un admin.
- Le freelance ne peut ni créer de tag, ni approuver la production, ni merger une PR.
