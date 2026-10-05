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
- `opencode.jsonc` — fournisseur local **Ollama** déclaré (`ollama/qwen2.5:7b`) : chaîne d'agents 100 % locale **optionnelle**. Par défaut les agents utilisent `opencode/big-pickle` (gratuit) ; Ollama n'est activé que si le profil `ollama` est choisi dans la page « Réglages modèles ».
- `web/modeles_ollama.py` — modèle Ollama recommandé **par agent**, calibré pour une **RTX 5070 (12 Go)** (un seul modèle chargé à la fois, 11 Go utiles, aucun 12b+). La page « Réglages modèles » affiche la table et indique ce qui est déjà installé sur le serveur de l'analyste.
- `tools/studio/modeles_agents.py` — applique cette table à **tous** les agents d'une commande : `make agents-modele PROFIL=ollama` (ou `PROFIL=opencode` pour revenir à `big-pickle`, `DRY=1` pour simuler). Écrit dans les deux magasins (base Studio **et** `.opencode/agents/`), donc `make studio-deploy` n'annule rien. Aucun agent à éditer à la main. Comme l'outil ne peut pas interroger le PC GPU depuis le serveur Docker, on lui donne la liste des modèles réellement installés, sinon il retient le premier recommandé — absent du serveur, Ollama le téléchargerait au premier appel : `make agents-modele PROFIL=ollama MODELES=llama3.1:8b,mistral:7b,qwen3-vl:8b`.
- `tools/export/` — rapport exécutif MD/HTML/PDF/JSON (WeasyPrint).
- `.github/workflows/suite.yml` — CI : suite `verification.py` (20 tests) sur chaque push/PR vers `main`.

Suite de référence : `python3 soutenance/tests/verification.py` → **19 PASS + 0 SKIP**.

## Déploiement sur une nouvelle machine / serveur (Ubuntu/Debian)

```bash
# 1) Outillage + dépendances système
apt update && apt install -y make python3 python3-pip git \
  tesseract-ocr tesseract-ocr-fra tesseract-ocr-osd \
  libpango-1.0-0 libpangocairo-1.0-0 fonts-dejavu

# 2) Dépôt + dépendances Python
git clone https://github.com/MelvinBzh/management_de_la_securite.git
cd management_de_la_securite
pip install --break-system-packages -r requirements.txt

# 3) Studio : (re)créer la base source de vérité depuis .opencode/
make studio-init

# 4) Lancer l'interface (écoute sur 0.0.0.0 → accessible depuis le réseau)
make web ADDRESS=0.0.0.0        # http://<ip-du-serveur>:8501
```

Facultatif — agents 100 % locaux : installer **opencode** (`curl -fsSL https://opencode.ai/install | bash`) et **Ollama** (`curl -fsSL https://ollama.com/install.sh | sh` puis `ollama pull qwen2.5:7b`) ; la chaîne se lance alors depuis l'interface web avec `ollama/qwen2.5:7b`.

### Déploiement Docker (alternatif, pour un hôte Docker)

```bash
docker compose up -d --build     # déploie l'application → http://<ip>:8501
```

L'image embarque **tout**, y compris le CLI **opencode** : rien à installer sur la
machine hôte. Vérification :

```bash
docker exec e21-studio opencode --version     # doit afficher une version
```

- **Réseau** : `network_mode: host` → l'application joint Ollama installé sur
  l'hôte (`http://localhost:11434`, déclaré dans `opencode.jsonc`). Si le build
  échoue sur le téléchargement d'opencode (réseau restreint), construire avec
  `docker compose build --build-arg INSTALL_OPENCODE=0` : l'application fonctionne,
  seul le bouton « Lancer la chaîne » est indisponible.
- **Modèles cloud** : copiez `.env.exemple` en `.env` (ignoré par git) et
  renseignez `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`.
- **Identifiants opencode** : conservés dans le volume `e21-opencode` (pas de
  `opencode auth login` à refaire après chaque reconstruction).

**Mise à jour d'une version future** (le code est embarqué dans l'image, un
simple `git pull` ne suffit pas) :

```bash
./scripts/update-docker.sh        # git pull + rebuild + relance + prune
# équivaut à : git pull && docker compose up -d --build
```

Les volumes `analyses/` et `stockage_local/` (bases de données, cas d'étude)
persistent sur l'hôte : la mise à jour ne les touche jamais. Au redémarrage,
l'image réimporte les nouveaux agents/skills du dépôt dans la base (idempotent).