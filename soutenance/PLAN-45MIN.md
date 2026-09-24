# Plan de soutenance — 45 min

> Projet E21 « Des agents IA pour analyser les risques » — M2 Cybersécurité.
> Déroulé : 45 min + questions. Support : `soutenance/presentation.pptx` (~34 slides).
> Données d'appui : `CHOIX-MODELES-IA.md`, `AUDIT-SYSTEME.md`, `BENCHMARK.md`, `TESTS.md`, `analyses/2026-09-23_boutique-en-ligne/`.

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
9. Modes et permissions : agents en lecture seule + markdown, `bash` refusé (1 min)
10. Le LLM interchangeable : `ollama` / `api` / **mock déterministe** (démo garantie) (1 min)

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
18. Chaîne exécutée : 14 menaces → 13 risques validés, 2 critiques, 10 élevés, 1 moyen (1 min)
19. Exemple de risque complet (R-01 : brute force `/admin`) — actif, menace, niveau, source, résiduel (2 min)
20. La validation humaine : R-13 rejeté, R-14 modifié → `valide_par` (1 min)
21. `RAPPORT-CONTROLE.md` : trace du contrôle à chaque étape (1 min)

### Partie 7 — Tests effectués (28 → 32 min)
22. Stratégie de test (`06-plan-de-test.md`) : analyse manuelle de réf., conventions, garde-fous, bout en bout (1 min)
23. Suite de tests automatisée T-01 → T-10 (script rejouable `soutenance/tests/verification.py`) — **artefacts sur `main`** (2 min)
24. Résultats : 14/14 DREAD recalculés, 14/14 matrice, sources 29/29, JSON valide, npm audit 0 vuln (1 min)
25. Test du document piégé (injection de prompt) : consigne ignorée → sorties non modifiées (1 min)

### Partie 8 — Choix des modèles IA (32 → 37 min)
25'. Routeur de modèles : **un modèle par étape**, pas un modèle unique (1 min)
26. Tâche → meilleur modèle : parsing PDF (PyMuPDF/Docling + Mistral OCR 4 / PaddleOCR-VL), registre JSON (décodage contraint), raisonnement (Claude Sonnet 4.6), contrôle (déterministe + petit juge), synthèse (128 k suffit) (3 min)
27. Point clé : « JSON à 100 % = la forme, jamais les valeurs » → contrôle déterministe + humain (1 min)

### Partie 9 — Ce que l'outil ne fait PAS (37 → 40 min)
28. Limites : pas de scan réseau, pas de parsing auto des documents entrants, pas d'analyse de code réel, CVE non fabriquées, probabilité/impact qualitatifs, pas de plateforme web, dépendance opencode, pas de supervision continue (3 min)

### Partie 10 — Avantages / inconvénients + audit (40 → 43 min)
29. Benchmark : E21 vs TMT/Threat Dragon/IriusRisk/pytm/LLM générique/multi-agents (2 min)
30. Audit : findings (index ISO 27002 à ré-indexer, contrôle circulaire, checklist) + forces (1 min)

### Partie 11 — Perspectives & conclusion (43 → 45 min)
31. **Feuille de route** : analyse réseau automatique (scan, vulns, CVE → registre), **ingestion documentaire automatisée** (`.xlsx`, `.doc`, `.pdf`, `.img` → OCR/parsing), ré-indexation ISO, tests pytest, supervision continue (2 min)
32. Conclusion : reproductibilité + traçabilité + humain décideur (1 min)
33. Questions (45 min →)

## Messages clés à faire passer
1. « L'analyse est reproductible grâce aux skills ; chaque risque cite une source ; l'humain valide tout. »
2. « Les garde-fous IA sont déterministes (rejet sans source), pas une promesse du LLM. »
3. « Le contrôle des sources est gratuit et déterministe ; les LLM n'apportent qu'une couche d'anomalie sémantique. »
4. « Ce que l'outil ne fait pas est documenté » → feuille de route : réseau + documents.

## Sections de contenu détaillées (à lire pour préparer les slides)

### A. Ce que l'outil ne fait PAS
1. ❌ **Pas d'analyse technique automatique du système réel** : aucun scan réseau, aucun scan de vulnérabilités, aucun test d'intrusion (le cas d'emploi est l'analyse *amont* au sens EBIOS/architecture).
2. ❌ **Pas de parsing automatique des documents entrants** : les PDF / `.doc` / `.xlsx` / images ne sont pas lus automatiquement ; l'analyste (ou l'orchestrateur, par questions) fournit le contenu résumé.
3. ❌ **Pas d'analyse de code** : aucune lecture de code applicatif réel, pas d'AST, pas de SCA automatique (la CVE du SDK PayFlow reste un placeholder tant que `composer audit` n'a pas tourné).
4. ❌ **Pas de CVE fabriquées** : aucune note CVSS inventée — un placeholder est signalé comme tel (anti-hallucination).
5. ❌ **Pas de quantification financière** : probabilité/impact qualitatifs (matrice), les évaluations chiffrées supposent un référentiel métier.
6. ❌ **Pas de plateforme web / multi-utilisateurs** : le système vit dans l'environnement opencode d'un poste ; pas de dashboard, pas d'API publique.
7. ❌ **Pas de supervision continue** : une analyse = un instantané ; pas de collecte de logs, pas de SOC, pas d'alerte.
8. ❌ **Pas de validation automatique** : `valide_par` est **toujours humain** ; le système ne « valide » jamais seul.
9. ❌ **En local limité** : la machine de démo (~1 Go RAM libre) ne peut pas exécuter de gros LLM local (7–8B+) ; démo = mock/opencode.
10. ⚠️ **Risque résiduel d'erreurs de libellés** : index `knowledge_base/` imparfait (audit P1) → les références normatives seront ré-indexées.

### B. Perspectives (feuille de route)
1. **Analyse réseau automatique** : brancher des collecteurs (nmap, OpenVAS/Greenbone, OWASP ZAP) → preuves automatisées pour la matrice (probabilité = mesure réelle de l'exposition) → rattachement des CVE réelles (feed NVD + `composer audit` / `npm audit`).
2. **Ingestion documentaire automatisée** : `.pdf` (PyMuPDF/Docling, scans → PaddleOCR-VL / Mistral OCR 4), `.doc/.docx`, `.xlsx` (tableaux → DFD), `.img`/captures (VLMs) → structuration en entrées de la chaîne (actifs, flux, hypothèses) — sondage direct via `CHOIX-MODELES-IA.md` §1.
3. **Ré-indexation ISO 27002:2022** de `knowledge_base/` (audit P1) + fichiers par thématique (`stride.md`, `iso27002.md`, `oss_fr.md`, `cve.json`).
4. **Campagne de tests pytest** des conventions (registre, sources, matrice, formats) — `06-plan-de-test.md` §2.
5. **Analyse manuelle de référence** (comparatif « agents vs main » exigé par le sujet, jalon 1) + test document piégé documenté (jadis manquant — désormais `soutenance/tests/`).
6. **Supervision continue** : ré-analyse périodique des actifs critiques, delta-registre (nouveaux risques vs N-1), lien avec un outil de tickets.
7. **Extensions de méthode** : mode EBIOS RM « 5 ateliers » pour OIV/administration, PASTA pour comités métier, arbres d'attaque.