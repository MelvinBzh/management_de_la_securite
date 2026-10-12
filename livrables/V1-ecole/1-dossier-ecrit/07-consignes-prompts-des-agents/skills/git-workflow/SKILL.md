---
name: git-workflow
description: Use for any git operation in this repository (branches, commits, pull requests, push). Enforces the team conventions: no work on main, branch per task, PR linked to an issue.
---

# Workflow Git du projet

## Principes fondamentaux
- **Jamais de travail sur `main`** — toujours sur une branche dédiée
- **Jamais de commit direct sur `main`** — uniquement par merge de PR
- **Toute PR est liée à une issue** — pas de PR orpheline
- **Le CI doit passer avant le merge** — pas de merge si CI rouge

## Branches
- `main` — production, protégée, reçoit uniquement des merges de PR
- `feature/<nom>` — fonctionnalités
- `fix/<nom>` — corrections
- `chore/<nom>` — maintenance, docs, CI
- `analyses/<AAAA-MM-JJ>_<cas>` — dossier d'analyse de risques (poussé régulièrement)

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
- **Toujours lier à une issue** (`Closes #N` ou `Refs #N`)
- Après merge → supprimer la branche

## Règles
- Un commit = une chose précise ; messages en français
- `git pull --rebase` avant de pusher ; pas de force push sur `main`
- Une **analyse de risques** = un dossier `analyses/…` commité et **pushé à chaque étape**