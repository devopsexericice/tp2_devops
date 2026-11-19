# Registre des incidents de processus

Ce document trace les écarts entre les règles écrites (`CONTRIBUTING.md`, ADR) et l'historique Git réel. Il ne remplace pas une review : une approbation ne peut pas être ajoutée rétroactivement. Les écarts sont documentés ici et, quand c'est possible, commentés directement dans la Pull Request concernée.

## Incidents d'amorçage

| PR | Auteur | Merge par | Date de merge (UTC) | Reviews | CI au moment du merge | Écart constaté |
| :--- | :--- | :--- | :--- | :---: | :--- | :--- |
| #1 | `elvisnduwimana28-hash` | `elvisnduwimana28-hash` | 2026-11-19 15:36:49 | 0 | Rouge | Auto-merge et CI rouge : la PR d'import initial a été mergée avant que le pipeline ne soit fonctionnel. |
| #3 | `reneOkeCodjo` | `elvisnduwimana28-hash` | 2026-11-19 15:49:22 | 0 | Verte | Merge sans approbation interne alors que le CONTRIBUTING en exige une. La PR corrige l'import `app` pour pytest. |
| #5 | `reneOkeCodjo` | `elvisnduwimana28-hash` | 2026-11-19 16:33:59 | 0 | Verte | Merge sans approbation interne. La PR corrige les placeholders de `CODEOWNERS`, mais omet `@PyData98`. |

### Contexte

- Ces trois PR ont été mergées pendant la phase d'amorçage, **avant l'activation de la protection de `main`**.
- Aucun tag, aucune release et aucun déploiement en production n'existaient à ces dates : l'impact est limité au dépôt, pas à un environnement livré.
- La CI était rouge sur `main` après la PR #1. Elle est redevenue verte après la PR #3.

### Mesures correctives

1. Activer la protection de `main` : PR obligatoire, 1 approbation d'un interne, review des code owners, checks requis, résolution des conversations, pas de force-push.
2. Ajouter `@PyData98` à `CODEOWNERS` dans une PR de suivi (fichier de gouvernance, auteur interne).
3. Utiliser le template `.github/pull_request_template.md` pour toute nouvelle PR, avec la section « Dérogation » renseignée si le processus n'est pas respecté.
4. Commenter les PR #1, #3 et #5 pour rattacher ce registre à l'historique GitHub, sans prétendre à une approbation rétroactive.
5. Supprimer les branches temporaires après merge (`feature/init`, `fix/2-import-pytest`, `docs/4-codeowners`, `feaute/test_pr_auto`) et activer la suppression automatique des branches de PR.
6. Ne plus merger aucune PR sans review interne, même en cas d'urgence : une dérogation doit être écrite dans la PR avec qui, quand et pourquoi.
