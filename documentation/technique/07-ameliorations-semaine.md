# Semaine d'amélioration — 2026-09-28 → 2026-10-02
> « Rendre l'outil le plus utile et utilisable possible » — plan de la semaine, enchaînement des chantiers, décisions du jour.
> Source d'état : `ROADMAP.md`, `soutenance/MODIFICATIONS.md`, `AUDIT-SYSTEME.md`, `06-plan-de-test.md`, issues #15–#24 (remédiation fusionnée).
> Règle du jeu inchangée : **humain décideur final**, données **fictives**, une branche + une issue par chantier, suite de tests toujours verte avant merge.

## 1. État des lieux (ce qui est acquis, ce qui manque)

### ✅ Acquis (validé, fusionné sur main)
- Chaîne des 6 étapes opérationnelle sur le cas A (ShoPix, 14 risques validés, `valide_par` nominatif).
- Garde-fous en place : `e21-controle`, permissions bornées à `analyses/**`, sources ⊆ index, index ISO 27002:2022 canonique.
- Suite de tests T-01…T-11 (10 PASS + 1 SKIP), POC piloté par consignes, artefacts soutenance.

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
- **CI (#4)** : lancer `verification.py` automatiquement sur chaque PR (workflow GitHub Actions minimal) — la suite est déjà le référé.
- Dossier & soutenance : intégrer les démos web/ingestion/rapports au `PLAN-45MIN.md` + régénérer le PPT via `MODIFICATIONS.md`.

## 3. Déroulé de la semaine (7 jours)

| Jour | Chantier | Sortie attendue | Test sortant |
|---|---|---|---|
| Lun. 28/09 | P0 Ingestion (parseurs PDF/OCR/Word/Excel/Image + ZIP) | `tools/ingest/` + fixtures | T-12 |
| Mar. 29/09 | P0 Description auto + questions automatiques | `00-description.md` pré-générée + skill | T-13 |
| Mer. 30/09 | P1 Interface web + bibliothèque des analyses | site local, liste + lecture des rapports | T-14 |
| Jeu. 01/10 | P1 Rapports (PDF/exécutif) + méthodes (EBIOS RM opérationnel, PASTA) | exports + skill EBIOS ateliers | T-15, T-16 |
| Ven. 02/10 | P2 Détection/inventaire réseau + mapping détections | `07-detection.md` sur un cas + prompts | T-17 |
| Sam./Dim. | P3 : T-11 réel, #17, #20, CI, dossier, démos soutenance | traces archivées, décisions consignées | suite complète 16 tests |

## 4. Garde-fous spécifiques aux nouveaux chantiers

- **Tout intrant = donnée non fiable** : l'ingestion et le web appliquent la règle `<<<DONNÉES>>>` ; le protocole T-11 (injection) s'applique aussi aux uploads web (jamais d'instruction exécutable depuis un document).
- **Zéro donnée réelle/sensible vers un service externe** : l'app web tourne en local, les scans réseau sont limités au périmètre déclaré par l'utilisateur et opt-in.
- **Espace de travail borné** : le web n'écrit que dans `analyses/**` ; pas d'outil d'exécution générale exposé.
- **Chaque sortie reste sourcée** : toute nouvelle fichier (`07-detection.md`, EBIOS A1–A5) cite des IDs de `knowledge_base/`.
- **Merge uniquement suite verte** (T-01…T-17) + revue humaine des décisions (`valide_par` reste nominatif).

## 5. Décisions à trancher (par l'analyste)

1. **Stack de l'interface web** : recommandation **Streamlit** (rapide, upload+tableaux+PDF out-of-the-box) vs **FastAPI + Jinja** (plus contrôlé). → à valider.
2. **Exports PDF** : weasyprint (contrôle CSS) vs pandoc→LaTeX (plus lourd). → à valider.
3. **Scans réseau actifs** : autorisés **uniquement en local/bac à sable sur périmètre déclaré** (jamais d'externe) ? → à confirmer.
4. **Cas pilote d'application** : continuer sur le cas A ShoPix pour la démo web/rapports, ou créer un **cas B (téléconsultation médicale)** pour prouver la généricité + un mini-cas EBIOS ? → à choisir.
5. **CI GitHub Actions** : autorisée sur ce dépôt (public) ? → à confirmer.
6. A rappeler : **#20 arbitrage cyber-assurance** (2 000 €/2 500 €) à trancher cette semaine.

## 6. Suivi (issues)

| Issue | Titre | Chantier |
|---|---|---|
| #25 | P0 ingestion documentaire (PDF/OCR/Word/Excel/Image/ZIP → description structurée) | P0 |
| #26 | P0 questions automatiques + collecte structurée à partir des intrants | P0 |
| #27 | P1 interface web locale + bibliothèque des analyses | P1 |
| #28 | P1 rapports exportables (PDF/exécutif) accessibles sur le site | P1 |
| #29 | P1 méthodes approfondies opérationnelles (EBIOS RM 5 ateliers, PASTA, LINDDUN, STRIDE) | P1 |
| #30 | P2 inventaire réseau + détection amont (mapping menace→signaux, `07-detection.md`) | P2 |
| #31 | P3 consolidation : T-11 réel, analyse manuelle #17, arbitrage #20, CI #4, dossier/soutenance | P3 |

## Liens
- Dépôt : https://github.com/MelvinBzh/management_de_la_securite · Board : https://github.com/users/MelvinBzh/projects/6
- Documentation technique : `documentation/technique/` · Log de la remédiation précédente : `soutenance/MODIFICATIONS.md`