# Guide de Contribution et Règles de Gestion (`CONTRIBUTING.md`)

Toutes les règles ci-dessous répondent directement aux risques identifiés dans `docs/risques.md` (`[R1]` à `[R5]`) et aux contraintes de notre équipe (`[Carte Contexte]`).

---

## 1. Relecture des Pull Requests et gestion des absences `[R1, R3, R4]`
* **Nombre de relecteurs :** **1 seule approbation** par un développeur interne est obligatoire pour fusionner une Pull Request (PR). Demander plus de relecteurs bloquerait notre petite équipe de 3 internes `[R3]`.
* **Pas d'auto-validation :** L'auteur d'une PR ne peut jamais approuver son propre code `[R1, R4]`.
* **En cas d'absence du relecteur compétent :** Les **3 développeurs internes** ont les droits d'approbation sur l'ensemble du projet. Si le référent d'un fichier est absent plus de **4 heures ouvrées**, n'importe lequel des deux autres internes prend le relais en s'appuyant sur la *Definition of Done* `[R3]`.

---

## 2. Gestion du développeur freelance
* **Permissions limitées :** Le freelance a uniquement le rôle **Write** sur GitHub. Il peut créer des branches (`feat/*`, `fix/*`) et ouvrir des PR, mais **ne peut pas fusionner dans `main`, n'a aucun accès aux secrets ni au serveur de production** `[R2]`.
* **Respect de sa facturation horaire :** Comme il est payé à l'heure, les internes s'engagent à relire ses PR en **moins de 4 heures ouvrées** `[R3]`. Pendant l'attente, il travaille sur une autre tâche indépendante pour éviter toute heure facturée à vide `[R3]`.
* **Exigence de finition avant le gel :** Une tâche du freelance n'est validée que si elle respecte la *Definition of Done* (tests + documentation), afin que les 3 internes puissent maintenir le code seuls après l'arrêt du projet `[R4, Carte Contexte]`.

---

## 3. Conventions de nommage `[R1, R4, R5]`
* **Nom des branches :** `<type>/<numero-issue>-<description-courte>`
  * Types autorisés : `feat/`, `fix/`, `hotfix/`, `docs/`, `ci/`.
  * *Exemple :* `feat/12-gestion-stock` ou `hotfix/v1.0.1-fix-commande`.
* **Messages de commit :** `<type>: <description courte à l'impératif>`
  * *Exemple :* `feat: ajout verification du stock avant commande` ou `test: ajout test stock insuffisant`.
  * Permet de comprendre l'historique facilement des mois plus tard en cas d'urgence `[R4, R5]`.

---

## 4. Definition of Done (Quand une tâche est-elle terminée ?) `[R1, R2, R4, R5]`
Une tâche / PR est considérée comme **terminée** uniquement si tous ces critères sont remplis :
1. Le code répond au besoin de l'issue associée.
2. Les tests automatiques (unitaires et API) sont écrits et passent au vert `[R1, R4]`.
3. Aucun secret, mot de passe ou fichier `.env` n'est présent dans le code `[R2]`.
4. Si la base de données est modifiée, le script de mise à jour est inclus et rétrocompatible `[R1]`.
5. La documentation (`README.md` ou docs) est mise à jour `[R4, R5]`.
6. La PR a été relue, approuvée par **1 développeur interne** et fusionnée dans `main` `[R1, R3, R4]`.

### Checks CI requis
Avant tout merge, les checks `secret-scan`, `lint`, `test` et `build` doivent être verts. La PR doit utiliser le template `.github/pull_request_template.md`. Toute dérogation (review absente, merge hors protection, urgence) est documentée dans la PR avec qui, quand et pourquoi, puis reportée dans `docs/incidents.md`.

---

## 5. Versionnage : savoir en 10 secondes ce qui tourne en production `[R1, R5]`
* **Numéros de version (SemVer) :** Chaque livraison est marquée par un tag Git `vX.Y.Z` (ex : `v1.0.0` pour la livraison finale, `v1.0.1` pour un correctif de force majeure).
* **Images Docker numérotées :** Chaque image construite porte le tag exact de sa version (`v1.0.0`) et l'identifiant du commit. **Le tag `:latest` est strictement interdit** `[R1]`.
* **Vérification en 10 secondes :** L'API dispose d'une route publique `GET /health` qui renvoie directement la version active en production :
  ```json
  { "status": "ok", "version": "v1.0.0", "commit": "a1b2c3d" }
  ```
* **Publication automatique :** `cd.yml` publie `sha-<sha>` à chaque merge sur `main` et `vX.Y.Z` sur tag. Le staging est vérifié avant la production.
* **Production :** le job `production` exige l'environnement GitHub `production` (approbation interne) et les secrets `PROD_*` ; voir `docs/deploy.md`.
* **Rollback :** le workflow manuel `Rollback` redéploie une version `vX.Y.Z` depuis GHCR, sans rebuild.

---

## 6. Gestion des secrets et procédure en cas de fuite `[R2]`

### Où vivent les secrets ?
* **En local** : dans un fichier `.env` ignoré par Git (`.gitignore`), créé à partir du modèle `.env.example`.
* **En CI/CD et Production** : uniquement dans **GitHub Secrets** et **GitHub Environments** (`staging`, `production`).
* **Secrets de déploiement :** `PROD_HOST`, `PROD_USER`, `PROD_SSH_KEY`, `PROD_DIR`, `PROD_KNOWN_HOSTS` (optionnel). `GITHUB_TOKEN` est fourni par Actions pour GHCR.

### Qui y a accès ?
* Uniquement les **3 développeurs internes** (rôle `Admin` / `Maintain`).
* Le freelance utilise des identifiants locaux factices `[R2]`.

### Procédure si un secret fuite
1. **Révoquer et changer** immédiatement (`< 15 min`) le mot de passe ou la clé sur le serveur / PostgreSQL et mettre à jour **GitHub Secrets** `[R2]`.
2. **Vérifier les logs d'accès** pour détecter une éventuelle intrusion.
3. **Nettoyer l'historique Git** si le secret a été commité et **noter l'incident** dans `docs/incidents.md`.