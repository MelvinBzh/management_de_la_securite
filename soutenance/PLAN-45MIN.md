# Plan de soutenance — 45 min

> Projet E21 « Des agents IA pour analyser les risques » — M2 Cybersécurité.
> Déroulé : 45 min + questions. Support : `soutenance/presentation.pptx` (~34 slides).
> Data d'appui : `CHOIX-MODELES-IA.md`, `AUDIT-SYSTEME.md`, `BENCHMARK.md`, `TESTS.md`, `analyses/2026-09-23_boutique-en-ligne/`.
>
> ⚠️ **Mise à jour 2026-09-24 (audit externe remédié)** : ce plan et le support reflètent l'état **corrigé** du dépôt. Si le `.pptx` est régénéré, se baser sur **`soutenance/MODIFICATIONS.md`** (liste exhaustive des changements) — notamment : index ISO 27002:2022 canonique, R-13 retenu (14 risques), permissions `analyses/**`, POC piloté par consignes (pas de « mock LLM » exécuté), suite de tests T-01→T-11, oLLama en roadmap.

## Déroulé détaillé (timing cumulé)

### Partie 1 — Introduction (0 → 3 min)
1. Titre & plan (1 min)
2. Le sujet E21 : « des agents IA pour analyser les risques » — l'analyste reste décideur (2 min)

### Partie 2 — Contexte & objectif (3 → 8 min)
3. Problématique : analyse de risques = méthode exigeante, peu reproductible, coûteuse (1 min)
4. Objectif : un **système multi-agents** dans opencode qui applique la méthode 6 étapes, sourcée et traçable (1 min)
5. Le cas pilote : boutique en ligne « ShoPix » (données fictives, RGPD) (1 min)
6. La méthode E21 en 6 étapes + 4 traitements (2 min)

### Partie 3 — Infrastructure (8 → 13 min)
7. Architecture globale (Mermaid) : opencode, orchestrateur, chaîne 7 agents, contrôle, GitHub, board (2 min)
8. Dépôt / workflow : branches par analyse, issues, board (Todo → In Progress → Review → Done) (1 min)
9. Modes et permissions : lectures + écriture **limitée à `analyses/**`**, `bash` refusé, `e21-controle` en lecture seule (1 min)
10. Le système : un **POC piloté par consignes** dans opencode — les consignes `.md` + skills *sont* le programme (pas de code applicatif exécuté) ; le **local (ollama) est en roadmap** (1 min)

### Partie 4 — Les agents (13 → 19 min)
11. Vue d'ensemble : 12 agents dans `.opencode/agents/` (tableau rôles → sorties) (1 min)
12. La chaîne E21 pas à pas : `e21-analyse-existant` → `e21-synthese`, fichiers produits 00→06 + registre + SYNTHESE (2 min)
13. `e21-controle` : les garde-fous à chaque étape, reprise si REJET (2 min)
14. Agents de support : `github-manager`, `research`, `security` (1 min)
15. Exemple réel : le passage de l'étape 5 à 6 sur ShoPix (projet de registre → validation) (1 min)

### Partie 5 — Les skills (19 → 23 min)
16. Skills métier : `analyse-risques`, `registre-risques`, `garde-fous-ia`, `schemas-diagrammes` (2 min)
17. Skills framework : STRIDE, LINDDUN, EBIOS RM, PASTA, ATT&CK, DREAD, CVSS — **bascule de méthode** (2 min)

### Partie 6 — Démo : cas ShoPix (23 → 28 min)
18. Chaîne exécutée : 14 menaces → **14 risques validés** (2 critiques, 11 élevés, 1 moyen) (1 min)
19. Exemple de risque complet (R-01 : brute force `/admin`) — actif, menace, niveau, source, résiduel (2 min)
20. La validation humaine : R-13 rejeté (essai du circuit) **puis retenu** le 24/09, R-14 modifié → `valide_par` (1 min)
21. `RAPPORT-CONTROLE.md` : trace du contrôle à chaque étape (1 min)

### Partie 7 — Tests effectués (28 → 32 min)
22. Stratégie de test (`06-plan-de-test.md`) : analyse manuelle de réf., conventions, garde-fous, bout en bout (1 min)
23. Suite de tests automatisée **T-01 → T-20 — 19 PASS + 0 SKIP** (script rejouable `soutenance/tests/verification.py`, 3 statuts incl. SKIP) — **artefacts sur `main`** (2 min)
24. Résultats : **14/14 DREAD recalculés, 42 cas matrice, 65 sources ⊆ index, JSON valide, npm audit 0 vuln, T-10 index ISO 2022 canonique, T-19 index git sans donnée privée** ; périmètre : ingestion+préparation (T-12, T-13), web (T-14, T-15), méthodes opérationnelles (T-16), détection+inventaire (T-17), CI (T-18), données privées (T-19), Studio/Ollama (T-20) (2 min)
25. Test du document piégé (injection de prompt) : consigne ignorée → sorties non modifiées (régression T-07) + **T-11 exécuté le 04/10 et archivé** (`soutenance/tests/injection/resultats/`, `VERDICT: PAS DE CONSIGNE EXECUTEE`) — démo interactive e21-* en séance (1 min)

### Partie 8 — Choix des modèles IA (32 → 37 min)
25'. Routeur de modèles : **un modèle par étape**, pas un modèle unique (1 min)
26. Tâche → meilleur modèle : parsing PDF (PyMuPDF/Docling + Mistral OCR 4 / PaddleOCR-VL), registre JSON (décodage contraint), raisonnement (Claude Sonnet 4.6), contrôle (déterministe + petit juge), synthèse (128 k suffit) (3 min)
27. Point clé : « JSON à 100 % = la forme, jamais les valeurs » → contrôle déterministe + humain (1 min)

### Partie 9 — Ce que l'outil ne fait PAS (37 → 40 min)
28. Limites assumées : pas de plateforme web publique (app locale), pas de supervision continue en production, pas d'analyse automatisée de code réel à la chaîne, CVE non fabriquées (scores CVSS re-cités), probabilité/impact qualitatifs, dépendance opencode/big-pickle, modèles non auto-hébergés (roadmap ollama), coûts d'exploitation POC non chiffrés (3 min)

### Partie 10 — Avantages / inconvénients + audit (40 → 43 min)
29. Benchmark : E21 vs TMT/Threat Dragon/IriusRisk/pytm/LLM générique/multi-agents (2 min)
30. Audit : findings (index ISO 27002 corrigé, contrôle circulaire → T-10, checklist) + forces ; **remédiation appliquée** (`MODIFICATIONS.md`) (1 min)

### Partie 11 — Perspectives & conclusion (43 → 45 min)
31. **Feuille de route** : déploiement serveur automatisé (CI/CD complet : plan de test + agent de déploiement), détection étendue au homelab réel (inventaire opt-in), PaddleOCR optionnel (reçus/photos), tests pytest, supervision continue, intégration des ateliers EBIOS générés en cas réel (2 min)
32. Conclusion : reproductibilité + traçabilité + humain décideur (1 min)
33. Questions (45 min →)

## Messages clés à faire passer
1. « L'analyse est reproductible grâce aux skills ; chaque risque cite une source ; l'humain valide tout. »
2. « Les garde-fous IA sont déterministes (rejet sans source), pas une promesse du LLM. »
3. « Le contrôle des sources est gratuit et déterministe ; les LLM n'apportent qu'une couche d'anomalie sémantique. »
4. « Ce que l'outil ne fait pas est documenté » → feuille de route : réseau + documents.

## Sections de contenu détaillées (à lire pour préparer les slides)

### A. Ce que l'outil ne fait PAS
1. ❌ **Pas d'analyse technique automatique du système réel au-delà du périmètre déclaré** : pas de scan de vulnérabilités, pas de test d'intrusion, pas d'inventaire automatique hors homelab local opt-in ; l'analyse reste *amont* (EBIOS/architecture). En local : inventaire + détection opt-in (`tools/reseau/`, T-17).
2. ✅ **Parsing automatique des documents entrants livré** : PDF (texte + **OCR FR/EN**), XLSX/CSV, DOCX, PPTX, PNG — `tools/ingest/` (T-12, T-13) ; la ligne piégée d'un document est reproduite verbatim comme donnée, jamais exécutée (T-15).
3. ❌ **Pas d'analyse de code** : aucune lecture de code applicatif réel, pas d'AST, pas de SCA automatique (la CVE du SDK PayFlow reste un placeholder tant que `composer audit` n'a pas tourné).
4. ❌ **Pas de CVE fabriquées** : aucune note CVSS inventée — un placeholder est signalé comme tel (anti-hallucination).
5. ❌ **Pas de quantification financière** : probabilité/impact qualitatifs (matrice), les évaluations chiffrées supposent un référentiel métier.
6. ❌ **Pas de plateforme web publique / multi-utilisateurs** : l'app Streamlit est **locale** (`make web`, T-14) — bibliothèque, exports PDF/MD/HTML/JSON, rien n'est exécuté depuis le web ; pas d'API publique, pas d'auth.
7. ❌ **Pas de supervision continue** : une analyse = un instantané ; pas de collecte de logs, pas de SOC, pas d'alerte.
8. ❌ **Pas de validation automatique** : `valide_par` est **toujours humain** ; le système ne « valide » jamais seul.
9. ❌ **En local limité** : la machine de démo (~1 Go RAM libre) ne peut pas exécuter de gros LLM local (7–8B+) ; la chaîne tourne sur opencode/big-pickle, le passage à ollama est une ligne de config (roadmap).
10. ✅ **Corrigé (24/09)** : l'index `knowledge_base/` est désormais **ISO/IEC 27002:2022 canonique** (les rares résidus « codes A » cités dans les documents historiques sont datés et annotés comme tels).

### B. Perspectives (feuille de route)
1. ✅ **Inventaire + détection locale livrés** (T-17) : inventaire 100 % local, rapport **anonymisé** (aucune IP/MAC réelle dans le dépôt), détecteur déterministe 12 règles (ATT&CK) ; restent en perspective : collecteurs réseau étendus (nmap/OpenVAS/OWASP ZAP) pour preuves automatisées, puis rattachement des CVE réelles (feed NVD + `composer audit` / `npm audit`).
2. ✅ **Ingestion documentaire automatisée livrée** (T-12, T-13) : `.pdf` (PyMuPDF, scans → OCR Tesseract FR/EN), `.doc/.docx`, `.xlsx`/CSV, `.pptx`, `.png`, ZIP — entrées structurées de la chaîne (actifs, flux, hypothèses) ; PaddleOCR optionnel en perspective (reçus/photos).
3. ✅ **Ré-indexation ISO 27002:2022 effectuée** (24/09) : index canonique + correspondance 2013→2022 + invariant T-10 ; restent optionnels les fichiers par thématique (`stride.md`, `iso27002.md`, `cve.json`).
4. **Campagne de tests pytest** des conventions (registre, sources, matrice, formats) — `06-plan-de-test.md` §2.
5. ✅ **Analyse manuelle de référence livrée** (issue #17) : `analyses/2026-09-23_boutique-en-ligne/reference-manuelle.md` — 12 menaces humaines, comparaison IA vs manuel (écarts : vol de session admin non couvert, sur/sous-notations), conclusion d'usage ; ✅ **test d'injection réel T-11 exécuté le 04/10 et archivé** (`soutenance/tests/injection/resultats/`, `VERDICT: PAS DE CONSIGNE EXECUTEE`).
6. **Supervision continue** : ré-analyse périodique des actifs critiques, delta-registre (nouveaux risques vs N-1), lien avec un outil de tickets.
7. ✅ **Méthodes approfondies livrées** (T-16) : mode EBIOS RM « 5 ateliers » opérationnel (`tools/methodes/ebios`), PASTA 7 étapes, LINDDUN 7 fiches + DPF, validateur DFD STRIDE — choix combinables documentés (e21-choix-methode).
8. **CI/CD complet** (vision analyste) : plan de test + **déploiement automatique sur serveur avec un agent** — CI minimale déjà vert sur chaque PR (`.github/workflows/suite.yml`, T-18).