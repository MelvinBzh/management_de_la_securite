---
name: new-project
description: Use when creating a new GitHub project from the MelvinBzh/template and preparing it for opencode. NOTE — skills now use the .opencode/skills/<name>/SKILL.md folder structure, not flat files.
---

# Créer un nouveau projet GitHub

Procédure depuis le template `MelvinBzh/template`, préparé pour opencode.

## Quand utiliser
Création d'un nouveau projet / app / repo GitHub.

## Procédure
1. Créer le repo : `gh repo create <nom-projet> --private` (+ git init si vide).
   Conventions : `project-*` (dév), `tool-*` (outils), `homelab-*` (infra).
2. Importer `.opencode/` depuis le template :
   ```bash
   git clone https://github.com/MelvinBzh/template.git /tmp/oc-template
   cp -r /tmp/oc-template/.opencode .
   rm -rf /tmp/oc-template
   ```
3. **Restructurer les skills** : chaque skill doit être dans `.opencode/skills/<nom>/SKILL.md` (loader opencode = `**/SKILL.md`). Migrer les fichiers plats.
4. Remplir `.opencode/skills/project-context/SKILL.md` (nom, description, repo, board, stack, architecture, contraintes).
5. Créer `.gitignore` si absent, commit initial (`feat: init <projet> avec contexte OpenCode`), push.
6. Créer le board GitHub Projects et lier au repo ; `project-context` doit référencer l'URL du board.
7. Lancer opencode.

## Règles
- Remplir `project-context` AVANT de lancer opencode
- Jamais de secrets en clair ; un projet = un repo = un dossier `~/projects/`