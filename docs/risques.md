# Analyse des Risques — Nouveau Socle & Chaîne CI/CD

## 1. Registre des 5 risques majeurs

| ID | Risque | Scénario concret de défaillance | Gravité | Mesure de traitement dans le socle |
| :--- | :--- | :--- | :---: | :--- |
| **R1** | **Mise en ligne bloqué et base de données désynchronisée** | Un dev pousse directement sur `main` sans tests un vendredi soir, écrasant la version en ligne (`:latest`) et oubliant de mettre à jour la base de données. Les commandes bloquent 14 h et personne ne sait quelle version tourne. | **Critique** | Bloquer le push direct sur `main`, lancer les tests automatiquement avant validation, numéroter chaque version (`v1.0.0`) et automatiser la sauvegarde et la mise à jour de la base. |
| **R2** | **Fuite des mots de passe et accès trop larges du freelance** | Le fichier `.env` contenant les mots de passe est envoyé par erreur sur le dépôt public GitHub, ou le freelance garde des accès au serveur de production après la fin de sa mission. | **Critique** | Ignorer le fichier `.env` (`.gitignore`), stocker les vrais mots de passe uniquement dans les secrets de GitHub, et limiter le freelance à l'écriture de code (seuls les 3 internes accèdent à la production). |
| **R3** | **Blocage des livraisons et perte de temps facturée par le freelance** | Avec seulement 3 devs internes, demander plusieurs relecteurs bloque chaque modification. Les demandes du PO prennent du retard et le freelance (payé à l'heure) facture des heures d'attente inutilement. | **Moyenne** | Demander **1 seul relecteur interne** par modification, automatiser les vérifications simples (tests, syntaxe) et s'engager à relire rapidement (en moins de 4 h). |
| **R4** | **Code mal fini ou incompréhensible avant l'arrêt du projet** | Pressé par le temps, le freelance livre du code sans tests ni explications juste avant la livraison finale. Comme le projet est ensuite figé, l'équipe interne ne saura pas corriger un bug des mois plus tard. | **Élevée** | Fixer une checklist claire (*Definition of Done*) : aucune tâche n'est validée sans tests qui passent, documentation à jour et relecture par un interne. |
| **R5** | **Impossibilité d'intervenir en urgence (« force majeure ») après la livraison** | Des mois après la livraison finale (`v1.0.0`), une panne grave survient. L'équipe est passée à autre chose et ne sait plus comment relancer le projet ni revenir en arrière rapidement. | **Élevée** | Tout automatiser avec GitHub Actions (tests, création de l'image, déploiement), documenter la procédure d'urgence (`hotfix`) et garder l'ancienne version prête à être relancée en moins de 5 minutes. |

---

## 2. Matrice Gravité / Effort

| | **Effort Faible** | **Effort Moyen** | **Effort Élevé** |
| :--- | :--- | :--- | :--- |
| **Gravité Critique** | **R2** (Protéger les secrets et limiter les droits du freelance) | **R1** (Bloquer `main`, tests auto, numéros de version, BDD) | — |
| **Gravité Élevée** | **R4** (Checklist de validation et relecture interne) | **R5** (Automatisation complète, procédure d'urgence et retour arrière < 5 min) | — |
| **Gravité Moyenne** | **R3** (1 seul relecteur interne et délai de relecture court) | — | — |

### Justification de nos priorités
1. **Priorité 1 — Éviter les catastrophes immédiates (R2 puis R1) :** Cacher les mots de passe et limiter les accès du freelance (**R2**) prend 5 minutes sur GitHub et évite une faille critique. Sécuriser les mises en ligne et la base de données (**R1**) demande un peu plus de travail (écrire les tests et configurer le pipeline), mais empêche directement de revivre la panne de 14 h du mois d'août.
2. **Priorité 2 — Préparer l'après-livraison (R4 puis R5) :** Comme le produit ne sera plus modifié après la livraison, il faut exiger du code propre et testé dès maintenant (**R4**, simple règle d'équipe) et avoir un bouton de retour arrière rapide en cas de force majeure (**R5**, effort technique moyen).
3. **Priorité 3 — Garder un rythme fluide (R3) :** Limiter la relecture à 1 seul développeur interne est facile à mettre en place et permet d'aller vite (pour le PO et le freelance) tout en gardant un contrôle qualité (pour la CEO et la Lead Dev).