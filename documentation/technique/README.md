# Documentation technique — E21 « Des agents IA pour analyser les risques »

Documentation de conception et d'implémentation du prototype. Base : sujet E21 et support CISSP Partie 1 (`documentation/*.pdf`).

## Documents

| Doc | Contenu |
|---|---|
| `01-architecture.md` | Architecture globale, entrée → traitement → sortie, orchestration |
| `02-agents.md` | Fiche et consigne (prompt) de chaque agent |
| `03-format-echanges.md` | Schémas JSON (Pydantic) des échanges inter-agents |
| `04-garde-fous.md` | Sécurité du système : injection, fuite, hallucination, excès d'autonomie |
| `05-cas-et-modele.md` | Choix du cas d'étude et du modèle de menaces (justifié) |
| `06-plan-de-test.md` | Comparatif analyse manuelle, test d'injection, checklist de rendu |

## Conventions

- JSON des échanges **strictement** conforme au format du sujet (`id, actif, menace, categorie, probabilite, impact, niveau, traitement, mesures, sources, valide_par`).
- Tout risque doit **citer une source** de la base de connaissances.
- `valide_par` reste `null` tant qu'un humain n'a pas validé.