# Management de la Sécurité

Projet E21 « Des agents IA pour analyser les risques » : système multi-agents opencode (orchestrateur + chaîne d'analyse) qui assiste un analyste de risques, avec suivi via GitHub Projects.

## Structure

- `.opencode/agents` — agents (orchestrateur E21, chaîne `e21-*`, github-manager, research, security)
- `.opencode/skills/*/SKILL.md` — skills (analyse-risques, frameworks STRIDE/LINDDUN/EBIOS-RM…, garde-fous-ia, registre, schémas)
- `knowledge_base/` — sources à ID stable (références des menaces et contre-mesures)
- `analyses/<date>_<cas>/` — dossier généré pour chaque analyse (registre + synthèse)
- `documentation/` — documentation technique et documents du sujet

## Workflow

Toute évolution passe par une issue GitHub sur le board « Sécurité — Management », une branche dédiée et une PR liée à l'issue.

## Documentation

Voir [documentation/README.md](documentation/README.md).

## Outillage livré (semaine d'amélioration 2026-10-04)

- `tools/ingest/` — ingestion documentaire (PDF texte + **OCR FR/EN**, XLSX/CSV, DOCX, PPTX, PNG, ZIP, défense zip-slip) et préparation (brouillon `00-description.md` + `questions-auto.md`).
- `tools/methodes/` — **EBIOS RM** (ateliers A1–A5), **PASTA** (7 étapes), **LINDDUN** (7 fiches + DPF), **STRIDE** (validateur DFD).
- `tools/reseau/` — inventaire **100 % local** (`--out-anon`, aucune IP/MAC réelle dans le dépôt) + détecteur **12 règles MITRE ATT&CK**.
- `web/` — interface locale Streamlit : bibliothèque des analyses, préparation, exports, lancement de la chaîne via la **commande fixe** opencode (seule commande exécutable, aucun contenu utilisateur n'y entre).
- `tools/studio/` — **Studio E21** (page web + CLI `tools/studio/cli.py`) : la base locale `stockage_local/e21.sqlite3` (gitignorée) est la **source de vérité** des agents et skills ; édition/ajout depuis l'interface, déploiement vers `.opencode/**`, versionnage git en branche + PR, export/import JSON (portabilité machine), état **Ollama**. Portabilité : `make studio-init` (nouvelle machine, après `git clone`) + `make studio-deploy`.
- `opencode.jsonc` — fournisseur local **Ollama** déclaré (`ollama/qwen2.5:7b`) : chaîne d'agents 100 % locale optionnelle (`opencode run --model ollama/qwen2.5:7b …`).
- `tools/export/` — rapport exécutif MD/HTML/PDF/JSON (WeasyPrint).
- `.github/workflows/suite.yml` — CI : suite `verification.py` (20 tests) sur chaque push/PR vers `main`.

Suite de référence : `python3 soutenance/tests/verification.py` → **19 PASS + 0 SKIP**.