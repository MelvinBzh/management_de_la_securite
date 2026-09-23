# Skill — Créer un nouveau projet GitHub

Ce skill décrit la procédure complète pour créer un nouveau projet depuis le template `MelvinBzh/template` et le préparer pour OpenCode.

## Quand utiliser ce skill

Quand l'utilisateur demande de créer un nouveau projet, une nouvelle app, ou un nouveau repo GitHub.

## Procédure

### 1. Créer le repo depuis le template

```bash
gh repo create <nom-projet> --template MelvinBzh/template --private --clone
cd <nom-projet>

Convention de nommage :
- project-* — projets de développement
- tool-* — outils/scripts publiables
- homelab-* — infrastructure home lab

2. Vérifier .opencode/

Si .opencode/ est absent du clone :

git clone https://github.com/MelvinBzh/template.git /tmp/oc-template
cp -r /tmp/oc-template/.opencode .
rm -rf /tmp/oc-template

3. Remplir project-context.md

Éditer .opencode/skills/project-context.md avec :
- Nom et description du projet
- URL GitHub + GitHub Projects Board
- Stack technique
- Commandes (lancer, tester, builder)
- Architecture des composants
- Contraintes spécifiques

4. Créer .gitignore si absent

printf "node_modules/\n.next/\ndist/\n.env\n.env.local\n*.log\n" > .gitignore

5. Commit initial

git add -A
git commit -m "feat: init <nom-projet> avec contexte OpenCode"
git push

6. Lancer OpenCode

opencode

Règles importantes

- Toujours remplir project-context.md AVANT de lancer OpenCode
- Ne jamais committer de secrets en clair
- Un projet = un repo GitHub = un dossier dans ~/projects/

Format de réponse attendu

Confirmer après création :
- URL du repo créé
- Chemin local du projet
- Contenu de project-context.md initialisé
