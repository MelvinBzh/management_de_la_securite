# Semaine d'amélioration — 2026-10-05 → 2026-10-09
> « Rendre l'outil le plus utile et utilisable possible » — plan de la semaine, enchaînement des chantiers, décisions du jour.
> **Exécution effective : le 2026-10-04** (préparation soutenance) — la planification 05→09 octobre reste la cible visée ; bilan ci-dessous à l'état du 2026-10-04.
> Source d'état : `ROADMAP.md`, `soutenance/MODIFICATIONS.md`, `AUDIT-SYSTEME.md`, `06-plan-de-test.md`, issues #15–#24 (remédiation fusionnée), issues #25–#31 (chantiers).
> Règle du jeu inchangée : **humain décideur final**, données **fictives**, une branche + une issue par chantier, suite de tests toujours verte avant merge.
> Les recommandations techniques de la section 5 ont été **vérifiées par recherches web le 04/10/2026** (version, maintenance, disponibilité) avant lancement des chantiers.

## 1. État des lieux (ce qui est acquis, ce qui manque)

### ✅ Acquis (validé, fusionné sur main)
- Chaîne des 6 étapes opérationnelle sur le cas A (ShoPix, 14 risques validés, `valide_par` nominatif).
- Garde-fous en place : `e21-controle`, permissions bornées à `analyses/**`, sources ⊆ index, index ISO 27002:2022 canonique.
- Suite de tests T-01…T-19 (**18 PASS + 0 SKIP**), POC piloté par consignes, artefacts soutenance.

### ⚠️ Manques identifiés (ce qui limite « l'utilisabilité »)
| Manque | Conséquence concrète |
|---|---|
| **Pas d'ingestion documentaire** | L'analyste doit tout saisir à la main (description, actifs, flux) — aucun PDF/Word/Excel/image exploité |
| **Pas d'interface** | L'outil s'utilise uniquement en CLI/editeur opencode — pas de parcours « upload → rapport » |
| **Rapports non exportables** | Sorties `.md/.json` brutes, pas de PDF/exécutif présentable ni d'accès web |
| **EBIOS RM seulement « documenté »** | Skill/skills théorique ; pas de déroulé opérationnel atelier par atelier ni livrables dédiés |
| **Pas de volet détection/amont** | L'analyse est « design-time » ; aucun inventaire réseau, aucune entrée « détection » (journaux, exports, questions de monitoring) |
| **Automatisation partielle** | Questions posées manuellement à l'ouverture ; pas de génération automatique de questions à partir des intrants |
| **T-11 non exécuté** | Démo d'injection réelle pas encore archivée (SKIP) |
| **#17 / #20 ouverts** | Analyse manuelle de référence à produire ; arbitrage cyber-assurance à trancher |

## 2. Périmètre proposé (priorisé)

### P0 — Chantier « Ingestion & structure d'entrée » (fondation, jours 1–2)
Objectif : **déposer n'importe quel document, en ressortir une description de système structurée et automatisable** (études amont de la chaîne).

- Règle : tous les documents d'entrée = **`<<<DONNÉES>>>`** (jamais des instructions) ; aucun contenu utilisé comme consigne.
- Parseurs (briques Python, testées, locales) :
  - **PDF** (PyMuPDF) : texte + tableaux ; **PDF scannés → OCR** (Tesseract/paddleocr, FR/EN).
  - **Images** (PNG/JPG/WebP) : OCR + description (schémas d'architecture → proposition de DFD, via skill `schemas-diagrammes`).
  - **Excel/CSV** (openpyxl/pandas) : actifs, ports, sous-traitants, budgets…
  - **Word/PPT** (python-docx/python-pptx) : cahier des charges, comptes rendus, slides d'archi.
  - Archives (ZIP) : extraction récursive, limites de taille/type.
- Sortie normalisée : `analyses/<cas>/intrants/` (copies anonymisées si besoin) + **`00-description.md`** pré-généré (résumé automatique par le parseur + DFD suggéré + zone « à confirmer par l'analyste »).
- **Questions automatiques** : à partir des intrants, l'outil propose une liste de questions ciblées (actifs manquants, flux non décrits, mots-clés « admin »/« mot de passe »/« API »…) → l'analyste ne répond qu'aux vraies trous.
- Tests : **T-12 ingestion** (fixtures : PDF texte, PDF scanné, XLSX, DOCX, PNG, ZIP) + **T-13 questions** (les questions proposées couvrent les trous injectés dans les fixtures).
- Livrable outil : `tools/ingest/` + skill `ingestion-documents`.

### P1 — Chantier « Interface web + rapports accessibles » (jours 3–4)
Objectif : **utiliser l'outil sans éditeur, voir les rapports sur un site local**.

- Application web **locale** (démarrage `make web`) :
  - Upload de documents (piloté par le parseur P0), affichage de la description générée.
  - Lancement de la chaîne opencode sur un cas (appel CLI) et **suivi des étapes** en direct.
  - **Bibliothèque des analyses** : liste des dossiers `analyses/`, lecture des rapports (registre, synthèse, décision), tableaux du registre rendus.
  - **Exports de rapports** : Markdown / JSON / **PDF** (weasyprint/pandoc) — rapport exécutif généré depuis `SYNTHESE.md` + registre.
- Architecture : déclarée dans `01-architecture.md` comme **wrapper de présentation** (le cœur reste le POC piloté par consignes — l'interface ne remplace pas la chaîne).
- Sécurité : app locale (localhost), aucune donnée réelle, uploads traités comme données, garde-fou injection rejoué en web (→ booléen à brancher sur **T-11**), pas d'auth externe (scope démo).
- Tests : **T-14** (« le site se lance, sert un rapport depuis un dossier d'analyse, exporte un PDF »), **T-15** (injection via upload rejetée).

### P1 — Chantier « Méthodes approfondies » (jours 3–4, en parallèle)
Objectif : **des méthodes réellement exécutables**, pas seulement documentées.

- **EBIOS RM opérationnalisé** : déroulé des 5 ateliers dans `e21-*` (livrables par atelier : **A1 cadrage → A2 sources de risque → A3 scénarios → A4 appréciation → A5 traitement**) + skill `ebios-rm` enrichi (artefacts, votes, tableaux) + cas pilote EBIOS optionnel.
- **PASTA** : étapes 1–7 effectives (objectifs métier → DFD → menace mapping ATT&CK → simulation).
- **LINDDUN** : déjà opérationnel (RGPD) — ajouter le workbook par catégorie (7 fiches) + lien DPF.
- **STRIDE approfondi** : variantes (STRIDE-per-interaction), double-check du DFD.
- L'agent `e21-choix-methode` propose désormais des **méthodes combinables** (ex. STRIDE + LINDDUN + EBIOS-A3) et le justifie.
- Tests : T-16 (chaque méthode skill produit ses livrables attendus sur une fixture ; EBIOS = 5 fichiers A1–A5).

### P2 — Chantier « Analyse réseau & détection amont » (jour 5)
Objectif : **amener la donnée « terrain » avant l'analyse** (inventaire + signaux de détection), en sécurité.

- **Inventaire** :
  - Mode passif/opt-in : imports d'exports (routeur/switch, `ipconfig`/`ip a`, LDAP/AD export), `arp`/`nmap -sn` **uniquement sur le réseau local déclaré et en bac à sable** (prompt d'inventaire `homelab` existant réutilisé) — jamais de scan externe ni automatique au-delà du périmètre donné.
  - Sortie : actifs/ports/logiciels vers `01-actifs.md` + `knowledge_base` (CVE locales via `composer audit`/`npm audit` si dépendances).
- **Détection amont** :
  - Mapping automatique menace ↔ **détection** : pour chaque risque, proposition de règles/signaux (attendu : `ATT&CK-T1190` → logs WAF/IDS ; brute force → compteur d'échecs ; exfiltration → volumétrie sortante).
  - Livrable : **`07-detection.md`** par analyse (signaux, sources à surveiller, fréquence) + « questions de détection » posées à l'analyste (ex. « avez-vous un WAF ? des logs centralisés ? »).
- Parseurs P0 réutilisés pour les exports.
- Tests : T-17 (sur une fixture d'exports, l'inventaire retrouve les actifs/ports et produit ≥ N propositions de détection sourcées).

### P3 — Consolidation & fondations (en continu)
- Exécuter et archiver **T-11** (démo d'injection réelle).
- Produire **#17 analyse manuelle de référence** (comparatif agents/humain) — autorisé, validation humaine finale.
- Trancher **#20** (arbitrage cyber-assurance) et mettre la décision dans les documents.
- **CI (#4)** : lancer `verification.py` automatiquement sur chaque PR (workflow GitHub Actions minimal) — la suite est déjà le référé. **Vision CI/CD analyste (04/10)** : à terme, un plan de test + un agent déploient automatiquement la nouvelle app web sur un serveur (à formaliser dans un chantier dédié, après les P0/P1).
- Dossier & soutenance : intégrer les démos web/ingestion/rapports au `PLAN-45MIN.md` + régénérer le PPT via `MODIFICATIONS.md`.

## 3. Déroulé de la semaine (7 jours)

| Jour | Chantier | Sortie attendue | Test sortant |
|---|---|---|---|
| Lun. 05/10 | P0 Ingestion (parseurs PDF/OCR/Word/Excel/Image + ZIP) | `tools/ingest/` + fixtures | T-12 |
| Mar. 06/10 | P0 Description auto + questions automatiques | `00-description.md` pré-générée + skill | T-13 |
| Mer. 07/10 | P1 Interface web + bibliothèque des analyses | site local, liste + lecture des rapports | T-14 |
| Jeu. 08/10 | P1 Rapports (PDF/exécutif) + méthodes (EBIOS RM opérationnel, PASTA) | exports + skill EBIOS ateliers | T-15, T-16 |
| Ven. 09/10 | P2 Détection/inventaire réseau + mapping détections | `07-detection.md` sur un cas + prompts | T-17 |
| Sam./Dim. 10–11/10 | P3 : T-11 réel, #17, #20, CI, dossier, démos soutenance | traces archivées, décisions consignées | suite complète 16 tests |

## 4. Garde-fous spécifiques aux nouveaux chantiers

- **Tout intrant = donnée non fiable** : l'ingestion et le web appliquent la règle `<<<DONNÉES>>>` ; le protocole T-11 (injection) s'applique aussi aux uploads web (jamais d'instruction exécutable depuis un document).
- **Zéro donnée réelle/sensible vers un service externe** : l'app web tourne en local, les scans réseau sont limités au périmètre déclaré par l'utilisateur et opt-in.
- **Espace de travail borné** : le web n'écrit que dans `analyses/**` ; pas d'outil d'exécution générale exposé.
- **Chaque sortie reste sourcée** : toute nouvelle fichier (`07-detection.md`, EBIOS A1–A5) cite des IDs de `knowledge_base/`.
- **Merge uniquement suite verte** (T-01…T-19, 18 PASS + 0 SKIP) + revue humaine des décisions (`valide_par` reste nominatif).

## 5. Décisions techniques — vérifiées par recherches (04/10/2026)

Chaque choix ci-dessous a été contrôlé (version, maintenance, licence, limites) avant validation. Statut : ✅ vérifié / 🟡 à valider par l'analyste / 🔒 décidé par l'analyste.

| # | Décision | Recommandation (sourcée) | Statut |
|---|---|---|---|
| 1 | **Stack interface web** | **Streamlit** (v1.55+, avril 2026, développé activement sous Snowflake, releases bimensuelles) — parfait pour app locale/proto : upload, tableaux, PDF out-of-the-box ; limites connues : re-run complet à chaque interaction (câbler `@st.cache_data`), pas d'auth native (OK scope local), pas de push serveur natif. **FastAPI** seulement si API REST/async nécessaire — pas notre besoin. L'interface reste un **wrapper de présentation** (le cœur = POC piloté par consignes). | 🔒 décidé 04/10 — **Streamlit** |
| 2 | **Export PDF** | **WeasyPrint v69** (juin 2026, actif, BSD, Python 3.10+, Pango 1.44+) — rendu print-grade CSS Paged Media (numérotation, PDF/A, accessibilité). Pandoc ≥ 3.4 a fait de weasyprint son moteur HTML→PDF par défaut. **wkhtmltopdf = archivé, à éviter.** LaTeX = multi-GB, surdimensionné. Limites : n'exécute pas le JS (OK, HTML généré par nos gabarits) ; concurrency ~dizaines (OK, local). Attention : CVE juin 2026 (injection CSS via HTML non fiable) → n'appliquer que sur l'HTML produit par nos propres gabarits. | 🔒 décidé 04/10 — **WeasyPrint** |
| 3 | **Parsing PDF** | **PyMuPDF v1.28.0** (juin 2026, maintenu par Artifex, très actif — ~50 M téléchargements/mois ; wheels Python 3.10–3.14). `import pymupdf` (alias `fitz` legacy) ; `find_tables()` → tableaux en markdown ; hook OCR Tesseract intégré (`get_textpage_ocr()`) ; PyMuPDF4LLM → markdown prêt IA. | ✅ |
| 4 | **OCR FR/EN** | **Tesseract 5.5.3** (juil. 2026, CPU seul, léger, Apache 2.0) en défaut : scans propres FR ~7–10 % WER, modèle `best` + prétraitement (deskew, contraste) ; **PaddleOCR 3.7.0 / PP-OCRv6** (juin 2026) en option (photos, tableaux, multilingue : CER −39 % vs Tesseract sur reçus ; modèle **tiny ~6 Mo, CPU OK**, mais dépendance PaddlePaddle lourde). Sur notre machine (~1 Go RAM libre) : Tesseract par défaut, PaddleOCR-tiny optionnel. | ✅ |
| 5 | **Office (Word/Excel/PPT)** | **python-docx 1.2.0** (juin 2025, MIT, maintenu, py3.13), **openpyxl** (XLSX, actif), **python-pptx 0.6.22** (stable), CSV → stdlib/pandas. Lecture XLSX volumineux : `python-calamine` (Rust, rapide) en option. Tous maintenus. | ✅ |
| 6 | **Scans réseau actifs (P2)** | Uniquement **local / bac à sable / périmètre déclaré par l'utilisateur** (imports d'exports, `nmap -sn` sur le LAN déclaré), jamais automatique ni externe. **Homelab = vraies données** → inventaire en local, mapping menace→signaux **générique** (ATT&CK en connaissance, pas de données réelles vers un service externe). | 🔒 (décidé : local homelab) |
| 7 | **Cas pilote** | **ShoPix (cas A)** pour la démo web/rapports/ingestion (registre le plus riche, 14 risques) ; **détection testée depuis le homelab** de l'analyste ; mini-cas EBIOS optionnel pour #29 (méthodes approfondies). | 🔒 (décidé par l'analyste) |
| 8 | **CI GitHub Actions** | **D'abord minimal** : `verification.py` (suite T-01…T-19, 18 PASS + 0 SKIP) exécutée sur chaque PR — le fichier est déjà le référé. **Ensuite CI/CD complet** (vision analyste 04/10) : plan de test + **déploiement automatique sur un serveur avec un agent** (cible : la future app web P1) — à chiffrer en P3. | 🔒 décidé 04/10 — **minimal maintenant, auto-déploiement serveur+agent ensuite** |

Rappels en attente : **#20 arbitrage cyber-assurance** (2 000 € vs enveloppe 2 500 €) à trancher ; **#17 analyse manuelle de référence** (brouillon autorisé, validation humaine finale).

## 6. Suivi (issues)

| Issue | Titre | Chantier |
|---|---|---|
| #25 | P0 ingestion documentaire (PDF/OCR/Word/Excel/Image/ZIP → description structurée) | P0 |
| #31 | P0 questions automatiques + collecte structurée à partir des intrants | P0 |
| #26 | P1 interface web locale + bibliothèque des analyses | P1 |
| #27 | P1 rapports exportables (PDF/exécutif) accessibles sur le site | P1 |
| #28 | P1 méthodes approfondies opérationnelles (EBIOS RM 5 ateliers, PASTA, LINDDUN, STRIDE) | P1 |
| #29 | P2 inventaire réseau + détection amont (mapping menace→signaux, `07-detection.md`) | P2 |
| #30 | P3 consolidation : T-11 réel, analyse manuelle #17, arbitrage #20, CI #4, dossier/soutenance | P3 |

## Liens
- Dépôt : https://github.com/MelvinBzh/management_de_la_securite · Board : https://github.com/users/MelvinBzh/projects/6
- Documentation technique : `documentation/technique/` · Log de la remédiation précédente : `soutenance/MODIFICATIONS.md`