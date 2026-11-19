# Réglages GitHub pour la gouvernance

Ce runbook est destiné aux **admins** du dépôt. Le freelance n'a que le rôle Write et ne peut pas appliquer ces réglages. Les exemples sont en bash/Git Bash ; sous PowerShell, remplacer le heredoc par `@' ... '@ | gh api ... --input -`.

> État constaté au 19/11/2026 : la protection de `main` est absente (HTTP 404), les environnements et les secrets de déploiement ne sont pas configurés, et `@PyData98` manquait dans `CODEOWNERS` (corrigé par cette PR).

## 1. Protection de `main`

```bash
gh api --method PUT repos/devopsexericice/tp2_devops/branches/main/protection --input - <<'JSON'
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["secret-scan", "lint", "test", "build"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_conversation_resolution": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
JSON
```

Vérification :

```bash
gh api repos/devopsexericice/tp2_devops/branches/main/protection
```

Effet attendu : push direct interdit (même pour les admins), PR obligatoire, 1 approbation interne, review des code owners, checks `secret-scan`, `lint`, `test`, `build` obligatoires, conversations résolues, pas de force-push ni de suppression.

## 2. CODEOWNERS

Le fichier `.github/CODEOWNERS` doit couvrir les 3 internes :

```text
* @elvisnduwimana28-hash @reneOkeCodjo @PyData98
```

Après merge de cette PR, vérifier que GitHub demande bien la review des 3 code owners sur les nouvelles PR.

## 3. Environnements

Créer `staging` sans protection :

```bash
gh api --method PUT repos/devopsexericice/tp2_devops/environments/staging --input - <<'JSON'
{}
JSON
```

Créer `production`, restreint aux tags `v*.*.*` et avec les 3 internes comme relecteurs possibles :

```bash
# Récupérer les IDs (à remplacer dans le JSON ci-dessous)
gh api users/elvisnduwimana28-hash --jq .id
gh api users/reneOkeCodjo --jq .id
gh api users/PyData98 --jq .id

gh api --method PUT repos/devopsexericice/tp2_devops/environments/production --input - <<'JSON'
{
  "reviewers": [
    {"type": "User", "id": 111111},
    {"type": "User", "id": 222222},
    {"type": "User", "id": 333333}
  ],
  "deployment_branch_policy": {
    "protected_branches": false,
    "custom_branch_policies": true
  }
}
JSON

gh api --method POST repos/devopsexericice/tp2_devops/environments/production/deployment-branch-policies \
  -f name='v*.*.*' -f type='tag'
```

Remplacer `111111`, `222222`, `333333` par les IDs retournés par les commandes `gh api users/...`. Le job `production` et le workflow `Rollback` attendent alors l'approbation d'un interne.

## 4. Secrets de déploiement

À stocker dans l'environnement `production` (pas dans le code) :

```bash
gh secret set PROD_HOST --repo devopsexericice/tp2_devops --env production
gh secret set PROD_USER --repo devopsexericice/tp2_devops --env production
gh secret set PROD_SSH_KEY --repo devopsexericice/tp2_devops --env production < ~/.ssh/id_ed25519
gh secret set PROD_DIR --repo devopsexericice/tp2_devops --env production
gh secret set PROD_KNOWN_HOSTS --repo devopsexericice/tp2_devops --env production < known_hosts
```

- `PROD_KNOWN_HOSTS` est optionnel ; sans lui, le workflow utilise `ssh-keyscan`.
- `POSTGRES_PASSWORD` ne va **pas** dans GitHub : il reste dans `/opt/restaurant/.env` sur le serveur, créé depuis `deploy/.env.example`.
- `GITHUB_TOKEN` est fourni par Actions pour GHCR ; ne pas le créer.

## 5. Protection des tags `v*.*.*`

Créer un ruleset de tags avec bypass uniquement pour les 3 internes :

```bash
gh api --method POST repos/devopsexericice/tp2_devops/rulesets --input - <<'JSON'
{
  "name": "Protect release tags",
  "target": "tag",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["refs/tags/v*.*.*"],
      "exclude": []
    }
  },
  "rules": [
    {"type": "creation"},
    {"type": "update"},
    {"type": "deletion"}
  ],
  "bypass_actors": [
    {"actor_id": 111111, "actor_type": "User", "bypass_mode": "always"},
    {"actor_id": 222222, "actor_type": "User", "bypass_mode": "always"},
    {"actor_id": 333333, "actor_type": "User", "bypass_mode": "always"}
  ]
}
JSON
```

Remplacer les IDs par ceux des 3 internes. Le freelance n'est pas dans la liste : il ne peut pas créer, modifier ou supprimer un tag de release.

## 6. Checklist de mise en service (Elvis)

1. Merger la PR CD #11, puis cette PR de gouvernance.
2. Appliquer la protection de `main` (section 1).
3. Créer les environnements `staging` et `production` (section 3).
4. Configurer les secrets `PROD_*` (section 4).
5. Configurer le ruleset des tags (section 5).
6. **Avant de merger la PR #8 (stock)** : créer le tag baseline sur `main`.
7. Merger #8 après ajout des tests et approbation interne.
8. Créer `v1.1.0` après la livraison du stock, puis démontrer le rollback `v1.1.0 → v1.0.0` via le workflow `Rollback`.

Création du tag baseline :

```bash
git switch main
git pull --ff-only
git tag -a v1.0.0 -m "Baseline v1.0.0"
git push origin v1.0.0
```

Le tag doit être créé **après** le merge de la PR CD et **avant** le merge de la PR stock, afin que la démo de rollback dispose d'une version de référence.
