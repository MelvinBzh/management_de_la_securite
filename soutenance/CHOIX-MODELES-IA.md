# Choix des modèles IA pour la chaîne E21 — état de l'art 2026

> Produit par l'agent `research` (benchmark modèles, septembre 2026), mis en forme par l'orchestrateur.
> Usage : section « Choix des modèles IA » de la soutenance (slide ~8 min).
> ⚠️ Les prix, noms et classements sont un **instantané de septembre 2026** — à revérifier avant la soutenance (les leaders changent tous les 2–3 mois).

## 0. Contexte mesuré sur le dépôt

- Une analyse E21 complète ≈ **98 Ko ≈ 25–30 k tokens** (cas ShoPix : 11 fichiers) → **128 k de contexte suffit** ; 1M est superflu mais confortable.
- La machine de démo a **~1 Go de RAM libre** → aucun LLM local > 4B réellement exécutable ; démo garantie par le modèle opencode + `mock/déterministe`.
- `knowledge_base/` n'a **aucune entrée « modèles IA »** → cette note est la première source interne dédiée.

## 1. Tableau récapitulatif « par tâche »

| Tâche E21 | Meilleur choix (recommandé) | Alternative local / sensitive | Alternative gratuite / démo | Sources |
|---|---|---|---|---|
| **Lecture / parsing docs (PDF, scan, xlsx, captures)** | **PyMuPDF + Docling** (born-digital, MIT, CPU) + **Mistral OCR 4** (scans, $4/1 000 p.) ; LLM : **Gemini 3.1 Pro** (multimodal, 1M ctx, $2/$12) ou **Claude Opus 4.7** (PDF multi-pages) | **PaddleOCR-VL 1.6** (0,9B, 96,34 OmniDocBench, local) / **MinerU 3.4** ; analyse **Qwen3-8B** (ollama) | **Tesseract 5.5.3 + OCRmyPDF** (0 €, CPU, excellent sur PDF digital, faible manuscrit) ; **Docling** (MIT) ; démo web **crawl4ai** | OmniDocBench ; newtuple OCR-2026 ; parser-eval |
| **Génération structurée (registre markdown + JSON)** | **GPT-5.x `response_format` strict** ou **Claude JSON outputs** — structure 100 % garantie ; mais *valeurs* : **Qwen3.5-35B (0,828)** / **Phi-4 14B (0,798)** — SO-Bench | **Qwen3-8B + Outlines/SGLang** (décodage contraint) | **Outlines + Qwen3-8B** (gratuit, local) ; Gemini API free tier | arXiv 2604.25359 (SOB) ; SynthorAI |
| **Raisonnement / chaîne agentique 7 étapes** | **Claude Sonnet 4.6** ($3/$15, 1M ctx) — discipline d'outils (~30 % d'actions destructives de moins que GPT-5, ZTABS) ; **o4-mini** ($1,10/$4,40) pour les reprises | **DeepSeek-R1-Distill-Qwen-14B** (~9 Go, 69,7 % AIME) ; R1 671B complet = datacenter (~375 Go VRAM) → **hors machine E21** | **o4-mini / GPT-5-mini** ; Gemini free tier ; local **Qwen3-8B** | OpenRouter/OpenAI pricing ; ZTABS |
| **Contrôle / anti-hallucination** | **Hybride : contrôles 100 % déterministes** (`sources ⊆ index`, schéma JSON) **+ petit modèle** : **GPT-5-mini** ($0,25/$2), **Claude Haiku 4.5** ($1/$5) ou **Gemini 3.1 Flash-Lite** | **Phi-4-mini** (3,8B, ~2,5 Go Q4, CPU, MIT) ; **HalluGuard-4B** (77,1 % BAcc > GPT-4o 75,9 %) | **MiniCheck-7B / Bespoke-MiniCheck** (77,4 %) ; démo juge Gemini api tier gratuit | arXiv 2606.19544 ; HalluGuard (ACL 2026) |
| **Synthèse long contexte (11 fichiers ≈ 25–30 k tokens)** | **128 k suffit** → **Claude Sonnet 4.6** ou **GPT-5** ; vraie fusion >200 k : **Gemini 3.1 Pro** (1M, $4/$18 au-delà de 200 k) | **Qwen3-14B/32B** (128 k, ollama) — multi-fusion dégradée au-delà 32–64 k | Gemini **free tier** ; coût réel d'une synthèse ≈ **3–15 cts** | llmtest.io ; arXiv 2605.02173 |

## 2. Justifications par tâche (faits 2026 vérifiés)

### Tâche 1 — Lecture / analyse de documents
- **OmniDocBench v1.6** : les VLMs spécialisés écrasent les pipelines classiques — **PaddleOCR-VL-1.6** (0,9B) 96,34 global, **MinerU2.5-Pro** 95,75, **GLM-OCR** 95,22 vs **Gemini 3 Pro** 92,91, **GPT-5.2** 86,59, **Marker** 78,44.
- **parser-eval** (6 vraies pages, 425 valeurs) : sur un PDF **born-digital**, la couche texte native bat les outils locaux (78,1 % sans rien faire) ; sur **manuscrit/scans dégradés**, seuls les VLMs hébergés tiennent (Claude Opus 5 : 97,9 %, GPT-5.6 : 98,4 % vs **Tesseract : 9,1 %**).
- **Mistral OCR 4** (juin 2026, API-only, $4/1 000 p.) : « meilleur taux publié pour l'extraction structurée » ; rend markdown + bounding boxes + scores de confiance.
- newtuple (1 600 évaluations, 2026) : **aucun moteur ne gagne partout** — Docling 0,98–0,99 sur factures/tableaux, PaddleOCR le plus stable (chute 0,16).
- **Recommandation couple** : PyMuPDF (texte intégré, gratuit) → Docling (tableaux/born-digital) → **Mistral OCR 4 ou PaddleOCR-VL** (scans) ; puis **Gemini 3.1 Pro** (MMMU 85,1 %, 1M ctx) ou **Claude Opus 4.7** (meilleur multi-pages) pour la structuration sémantique.

### Tâche 2 — Génération structurée
- **Structured outputs** garants de la *forme* : 100 % de JSON valide mesuré sur 8 APIs quand l'interrupteur est activé (SynthorAI, 25/08/2026). **Mais « valide ≠ correct »** : *Value Accuracy* plafonne à **83,0 %** (GLM-4.7), 82,8 % (Qwen3.5-35B), 82,5 % (GPT-5.4) — SOB, arXiv 2604.25359.
- **La taille ne prédit rien** : **Phi-4 (14B) : 79,8 % > GPT-5 : 79,5 %**. Schémas profonds → dégradation en premier (SCD : à profondeur 4, Qwen2.5-7B déplace 74 % des valeurs).
- Pièges 2026 : **DeepSeek V4 / Qwen3.8-Max corrompent les valeurs quand le « thinking » est activé** ; Claude ignore `response_format` sur la surface OpenAI-compatible (utiliser le tool-call natif) ; OpenAI/Gemini/Claude **facturent le schéma** (jusqu'à ~5 k tokens) vs DeepSeek (~30 tokens).
- **Recommandation E21** : schéma plat + contrôlé → le JSON est « un problème résolu par le décodage contraint » ; la vraie exigence est sur les **valeurs** (IDs `knowledge_base`, enums) → validation déterministe, pas confiance au modèle.

### Tâche 3 — Raisonnement / agentique
- Prix API 2026 (par M tokens, entrée/sortie) : o4-mini $1,10/$4,40 ; GPT-5 $1,25/$10 ; GPT-5-mini $0,25/$2 ; Claude Opus 4.7 $5/$25 ; Sonnet 4.6 $3/$15 ; Haiku 4.5 $1/$5 ; Gemini 3.1 Pro $2/$12 (≤200 k) ; Gemini 3 Flash $0,50/$3.
- Classements : Claude Opus 4.7 SWE-bench 92,1 %, MMLU-Pro 86,4 %, GPQA 73,8 % vs Gemini 3.1 Pro 88,3/84,1/70,1 (Contra Collective).
- **En boucle agentique réelle : Claude « demande avant d'agir » (~30 % d'actions destructives de moins que GPT-5.x, 200 tâches, ZTABS)** → exactement le besoin E21 (agents read-only, humain dans la boucle).
- Local : **R1 671B impossible** (~375 Go VRAM) ; distills utiles : 14B (69,7 % AIME), 32B (72,6 %).

### Tâche 4 — Contrôle / vérification (garde-fous)
- Un **petit modèle seul est insuffisant** comme juge : llm-judge-reliability (DOI 10.5281/zenodo.2139912) — Qwen2.5-7B 0,594 / Llama-3.1-8B 0,551 vs Claude Sonnet 4.6 0,874 (LLMBar) ; **biais de position massif** (Qwen3-8B pb=0,192, le pire du panel de 21).
- Mais les petits **spécialisés** rivalisent sur l'anti-hallucination : **HalluGuard-4B 77,1 % > GPT-4o 75,9 %** ; MiniCheck-7B 77,4 %.
- Consensus 2026 : **vérification fiable = sous-étapes ancrées dans les preuves (Verdi) + décodage contraint + contrôles déterministes**, pas un juge seul.
- **Recommandation E21** : (1) déterministe et gratuit — `sources ⊆ index` + schéma JSON (déjà dans le prototype) ; (2) sémantique — petit modèle pour l'**anomalie, jamais la décision**.

### Tâche 5 — Synthèse long contexte
- Le « 1M marketing » est nuancé : mono-aiguille résolu (Gemini 3.1 Pro, Claude Opus 4.7, GPT-5.5 : 18/18 @1M, arXiv 2605.02173) mais **multi-saut/multi-aiguille chute** (GPT-5.5 s'effondre entre 512K et 1M) ; chiffres divergents selon protocole (MRCR v2 @1M : GPT-5.5 74 % vs Gemini 3.1 Pro 26,3 %).
- Coût d'une synthèse E21 (~30 k in / 5 k out) : ≈ **$0,015 Gemini 3 Flash** ; ≈ $0,10 Claude Sonnet 4.6 ; **context caching** Anthropic (90 %) ou Gemini (TTL 1 h) pour les 7 étapes.

## 3. Routeur de modèles recommandé pour la chaîne E21 (cas A « boutique en ligne », RGPD)

Principe : **router par étape** (objectif de conception du POC — le swap de modèle = une ligne de config opencode ; **ollama en roadmap**). Cas A = données **fictives** → API acceptables en démo ; en production données réelles → **ANSSI : local ou hébergement FR** (Azure France, GCP europe-west9, Mistral EU).

| Étape | Modèle API (recommandé) | Alternative sensitive (locale) | Justification |
|---|---|---|---|
| `e21-analyse-existant` (PDF + captures) | **PyMuPDF/Docling** + **Gemini 3.1 Pro** | Docling + PaddleOCR-VL 1.6 + Qwen2.5-VL-7B | Multi-modal, 1M ctx, 92,9 OmniDocBench |
| `e21-choix-methode` + `e21-menaces` | **Claude Sonnet 4.6** | DeepSeek-R1-Distill-14B (ollama) | Discipline d'outils, 1M ctx |
| `e21-evaluation` (calculs, cohérence) | **GPT-5** (o4-mini en reprise) | Qwen3-8B + Outlines | Fiabilité de calcul / JSON |
| `e21-traitement` (registre JSON) | **Claude JSON outputs** ou **GPT-5 strict** | Qwen3-8B + SGLang/Outlines | Décodage contraint = JSON 100 % valide |
| `e21-validation-suivi` | **Claude Sonnet 4.6** | Qwen3-8B | Registre + `valide_par` humain |
| `e21-synthese` (11 fichiers) | **Claude Sonnet 4.6** (128 k suffit) | Qwen3-14B | Qualité de fusion ; ~10 cts |
| `e21-controle` (garde-fous) | **GPT-5-mini** + contrôles déterministes | Phi-4-mini (3,8B, CPU) | Petit modèle = anomalie sémantique seulement |

> **Message clé de soutenance** : *« le contrôle des sources est à 100 % déterministe et gratuit ; les LLM n'y apportent qu'une couche d'anomalie sémantique »* — c'est la réponse directe au risque « hallucination » du sujet.

## 4. Limites de l'exercice

1. **Volatilité des classements** : chiffres contradictoires publiés (ex. MRCR v2 @1M vs arXiv 2605.02173) ; chaque prix/nom cité est un instantané de septembre 2026.
2. **Biais des benchmarks** : contamination des données d'entraînement, ground truths bruités (Cleanlab), effet « prompting strategy > taille du modèle ».
3. **Coût cumulé** : 7 étapes × reprises × double contrôle + taxe « thinking » → compter ~2–3× le prix nominal d'une analyse.
4. **Confidentialité / ANSSI** : API US et LLM chinois exclus pour données réelles ; la machine E21 (~1 Go RAM libre) **ne peut pas** exécuter de modèle 7–8B local — les alternatives ollama supposent une machine ≥ 16 Go.
5. **« JSON à 100 % » n'existe pas** : le décodage contraint garantit la forme, pas les valeurs (plafond ≈ 83 %) → garder la validation métier (already in architecture : `valider_sources()`, schéma).

## 5. Sources (sélection)

- Prix & docs : developers.openai.com/api/docs/pricing · platform.claude.com/docs (pricing, structured outputs) · ai.google.dev/gemini-api/docs/pricing · mistral.ai/news/ocr-4/ · aws.amazon.com/blogs/machine-learning/structured-outputs-on-amazon-bedrock…
- Parsing/OCR : github.com/opendatalab/OmniDocBench · newtuple.com/post/ocr-benchmark-… · github.laiyagushi.com/jkelly-dev1/parser-eval · builderai.tools/blog/pdf-parsing-for-rag-…
- Structured outputs : arxiv.org/html/2604.25359v1 (SOB) · arxiv.org/pdf/2608.25358v1.pdf (SCD) · synthorai.io/blog/llm-structured-outputs/
- Raisonnement/juges : contracollective.com/blog/gemini-3-1-pro-vs-claude-opus-4-7 (SWE-bench, GPQA) · ztabs.co/blog/claude-vs-gpt-vs-gemini-2026 · arxiv.org/pdf/2606.19544v1 (biais de position) · github.com/rahiqraees/llm-judge-reliability · aclanthology.org/2026.findings-acl.835.pdf (HalluGuard) · arxiv.org/html/2605.11334v1 (Verdi)
- Long contexte : arxiv.org/html/2605.02173v1 (1M retrieval) · llmtest.io/blog/best-llms-1m-context-2026 (MRCR v2)
- Projet : `documentation/technique/02-agents.md`, `04-garde-fous.md`, `knowledge_base/README.md`, `analyses/2026-09-23_boutique-en-ligne/`

## 6. Proposition pour la `knowledge_base/`

Ajouter une section « Modèles IA 2026 » avec des ID stables type `LLM-2026-PARSING`, `LLM-2026-JSON`, `LLM-2026-REASONING`, `LLM-2026-JUDGE`, `LLM-2026-LONGCTX` pointant vers les URLs ci-dessus → permet à `e21-controle` de valider les références « modèles » des futures analyses.