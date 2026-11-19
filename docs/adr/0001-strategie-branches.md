# ADR-0001 : Stratégie de gestion des branches (`docs/adr/0001-strategie-branches.md`)

* **Statut :** Accepté
* **Date :** 19 novembre 2026
* **Décideurs :** 3 développeurs internes, 1 développeur freelance

---

## 1. Contexte et choix de la stratégie

Notre équipe est petite (3 internes + 1 freelance) et le produit sera **figé après la livraison finale** (aucune modification sauf cas de force majeure). 

* **Pourquoi pas GitFlow ?** Trop lourd avec plusieurs branches permanentes (`develop`, `release`, `main`). Cela créerait des fusions complexes inutiles pour une petite équipe **[R3]** et serait difficile à reprendre des mois plus tard en cas d'urgence **[R5]**.
* **Pourquoi pas le Trunk-Based Development pur (pousser directement sur `main`) ?** Trop risqué au vu de l'historique du projet (panne de 14 h après un push direct) **[R1]** et impossible pour encadrer le travail du freelance avant le gel **[R4]**.

**Décision :** Nous adoptons **GitHub Flow avec des tags de version (`vX.Y.Z`)**. C'est un modèle simple avec une seule branche principale, facile à suivre au quotidien et facile à comprendre à froid des mois après la livraison **[R5]**.

---

## 2. Fonctionnement des branches (Quelles branches ? Qui ? Comment ?)

| Branche / Tag | Rôle | Qui peut l'utiliser ? | Règles et justification |
| :--- | :--- | :--- | :--- |
| **`main`** | Contient uniquement du code testé, stable et prêt à être livré. | Lecture pour tous. Fusion réservée aux **3 développeurs internes**. | **Push direct interdit** (même pour les admins) **[R1]**. Toute modification passe par une Pull Request (PR) avec tests automatiques au vert **[R1, R4]** et **1 seule approbation** d'un interne **[R3, R4]**. |
| **`feat/*`**<br>**`fix/*`**<br>**`docs/*`** | Branches temporaires pour développer une tâche ou corriger un bug. | Les **3 internes** et le **freelance**. | Créées depuis `main`. Durée de vie courte (1 à 2 jours max) pour faciliter une relecture en moins de 4 h **[R3]**. Supprimées automatiquement après fusion. Le freelance peut ouvrir une PR, mais **ne peut pas la fusionner lui-même** **[R2, R4]**. |
| **`hotfix/*`** | Branche d'urgence créée uniquement en cas de panne grave ou faille critique. | Les **3 développeurs internes** uniquement. | Créée depuis le tag de production actuel pour corriger un problème bloquant, même après le gel du produit **[R2, R5, Carte Contexte]**. |
| **Tags `vX.Y.Z`** | Marque une version officielle livrée (ex : `v1.0.0`). | Les **3 développeurs internes** uniquement. | Posé sur `main` après validation. Déclenche la création d'une image Docker numérotée (fini le `:latest`) et la mise en production **[R1, R2]**. |

---

## 3. Gestion d'un correctif urgent (« force majeure ») et retour dans le travail en cours

Si un bug bloquant ou une faille critique survient en production (pendant le projet ou des mois après l'arrêt des développements) **[R5, Carte Contexte]** :

1. **Création de la branche :** Un développeur interne crée une branche `hotfix/v1.0.1-nom-du-bug` directement depuis le tag actuellement en production (ex : `v1.0.0`) **[R2, R5]**.
2. **Correction et test :** Il corrige le bug et ajoute un test automatique qui vérifie que le problème ne peut plus se reproduire **[R1, R4]**.
3. **Validation accélérée :** Il ouvre une PR vers `main`. Dès que les tests automatiques passent, un autre interne relit immédiatement (prioritaire sur le délai habituel de 4 h) et fusionne dans `main` **[R1, R3]**.
4. **Mise en production :** Un interne crée le tag `v1.0.1` sur `main`, ce qui lance automatiquement le déploiement de la nouvelle version en production **[R1, R2]**.
5. **Retour dans le travail en cours :** Comme `main` est notre unique branche permanente, le correctif est automatiquement intégré à la référence du projet (pas besoin de le recopier sur une branche `develop`). Si un développeur a une branche `feat/*` en cours, il lui suffit de faire un `git pull origin main` sur sa branche pour récupérer le correctif et continuer son travail sans conflit.

---

## 4. Signaux d'alerte (Quand remettre en cause ce choix ?)

Nous saurons que cette stratégie n'est plus adaptée et qu'il faudra la changer si l'un de ces 3 signaux apparaît :

1. **Changement de stratégie produit :** La direction décide finalement de faire évoluer l'application en continu avec plusieurs versions différentes maintenues en parallèle pour plusieurs clients (il faudra alors créer des branches de version `release/*`).
2. **Embouteillage sur les Pull Requests :** Plus de **3 PR** restent bloquées en attente ou le temps moyen avant relecture dépasse **24 heures**, prouvant que notre rythme de validation ralentit trop l'équipe **[R3]**.
3. **Instabilité après fusion :** Plus de **10 % des fusions** dans `main` cassent l'environnement de test, ce qui montrerait qu'une étape d'intégration intermédiaire manque avant d'arriver sur `main` **[R1]**.