  Workflow Git du projet

  ## Principes fondamentaux
  - **Jamais de travail sur `main`** — toujours sur une branche dédiée
  - **Jamais de commit direct sur `main`** — uniquement par merge de PR
  - **Toute PR est liée à une issue** — pas de PR orpheline
  - **Le CI doit passer avant le merge** — pas de merge si CI rouge

  ## Branches
  - `main` — production, protégée, reçoit uniquement des merges de PR
  - `develop` — intégration (optionnel, pour les projets multi-développeurs)
  - `feature/[nom]` — nouvelles fonctionnalités
  - `fix/[nom]` — corrections de bugs
  - `chore/[nom]` — maintenance, docs, CI

  Créer une branche :
  ```bash
  git checkout -b feature/ma-fonctionnalite
  git push -u origin feature/ma-fonctionnalite
  ```

  ## Format des commits
  ```
  type(scope): description courte en français

  Corps optionnel : explication du pourquoi

  Refs #[numéro-issue]
  ```

  Types : `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

  ## Pull Requests
  - Titre : `[type] description courte`
  - Description : lien vers l'issue + résumé des changements
  - **Toujours lier à une issue GitHub** via `Closes #N` ou `Refs #N`
  - Review obligatoire avant merge
  - Tests passants obligatoires
  - Après merge → supprimer la branche

  ## Règles
  - Un commit = une chose précise
  - Messages en français
  - Toujours `git pull --rebase` avant de pusher
  - Ne pas `force push` sur `main`
  - Ne pas modifier l'historique des commits mergés

  ## Synchronisation
  ```bash
  # Avant de travailler sur une branche
  git checkout main
  git pull --rebase
  git checkout -b feature/ma-branche

  # Pendant le travail (synchronisation quotidienne)
  git pull --rebase origin main

  # Après merge de la PR → supprimer la branche locale
  git checkout main
  git pull --rebase
  git branch -d feature/ma-branche
  ```
