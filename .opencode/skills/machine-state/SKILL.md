---
name: machine-state
description: Use to consult or update the inventory of the local machine state (OS, dependencies, services, runners, deployed apps, env variables).
---

# État de la machine

Dernière mise à jour : 2026-09-23.

## Système
- OS : Debian / Linux
- Python : 3.13.5 (pip, venv) — node v20 LTS, docker 29.5.3, git, gh CLI disponibles
- RAM : ~3,8 Gi — espace disque : ~18 G libres (pas de GPU, pas d'Ollama, pas de clé API détectée)
- Disque projets : /home/melvin/projects

## Dépendances installées
| Outil | Version | Installé le |
|---|---|---|
| python3 | 3.13.5 | - |
| node | v20.19.2 | - |
| docker | 29.5.3 | - |
| opencode | 1.18.32 | - |
| pydantic / fastapi / pytest | installés | - |

## Services actifs
| Service | Port | Statut |
|---|---|---|
| - | - | - |

## Snapshot de référence (prototype IA)
- Pas de modèle LLM local → exécution opencode via API cloud (modèle nominal `opencode/big-pickle`) ; **roadmap : ollama en local** (swap de modèle en une ligne d'ouverture opencode, pas de code applicatif à modifier)
- Reste : sqlite3, make, curl/wget, PyYAML, python-docx/pptx, openpyxl, pillow, pymupdf, bcrypt, cryptography, PyJWT