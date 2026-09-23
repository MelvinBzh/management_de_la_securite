---
name: project-context
description: Use at the start of any work on this repository to load the current project context (goal, repo, board, structure, conventions). Required first skill for every agent of the E21 risk-analysis system.
---

# Contexte du projet — E21 Management de la sécurité

## Informations générales
- **Nom :** management_de_la_securite (projet E21 — Des agents IA pour analyser les risques, M2 Cybersécurité)
- **Objectif :** système multi-agents IA (environnement opencode) qui assiste un analyste dans l'analyse de risques d'un SI
- **Échéance :** rendu + soutenance (45 min)
- **GitHub repo :** https://github.com/MelvinBzh/management_de_la_securite
- **GitHub Project board :** https://github.com/users/MelvinBzh/projects/6

## Env / stack
- **Environnement :** opencode (pas de site web) — les agents et skills `.opencode/` SONT le système
- **Prototype = environnement opencode :** orchestrateur + chaîne d'agents + skills par framework
- **LLM :** abstraction `LlmProvider` (ollama local / API / mock démo) — machine sans gros LLM local (~1 Go RAM libre), pas de clé API détectée

## Structure
- `.opencode/agents/` — agents (orchestrateur + chaîne d'analyse e21-*)
- `.opencode/skills/*/SKILL.md` — skills (métier + frameworks + schémas)
- `analyses/<AAAA-MM-JJ>_<cas>/` — dossier créé à chaque analyse (sorties `.md` poussées sur GitHub)
- `knowledge_base/` — sources à ID stable (STRIDE, LINDDUN, ISO 27002, EBIOS RM, ANSSI)
- `documentation/` — sujets PDF + documentation technique

## Cas d'étude retenu
- **A — Boutique en ligne** + modèle **STRIDE** (prévoir DFD + frontières de confiance)

## Points d'attention
- Evaluer les risques IA du système lui-même : hallucination, injection, fuite, excès d'autonomie, empoisonnement, dépendance (skill `garde-fous-ia`)
- Humain dans la boucle : `valide_par` rempli par l'analyste
- Push régulier des analyses + suivi board (github-manager)