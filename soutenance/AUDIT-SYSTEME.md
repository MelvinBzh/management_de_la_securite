# Audit du système E21 — rapport de l'agent `security`

> Produit par l'agent `security` (audit du dépôt, 2026-09-24), mis en forme par l'orchestrateur.
> Usage : section « Audit & améliorations » de la soutenance.

## 1. Périmètre et méthode

Audit de l'infrastructure du projet (dépôt, agents, skills, base de connaissances, trace de l'analyse ShoPix) — contrôle de sécurité applicative (`npm audit`), revue des conventions (`garde-fous-ia`), cohérence des livrables et de la checklist du sujet (p. 28).

## 2. Résultats mesurés

### 2.1 Sécurité de l'environnement
- `npm audit` : **0 vulnérabilité** sur 32 dépendances (`@opencode-ai/plugin` 1.18.32).
- Aucune donnée réelle/sensible dans le dépôt : le cas pilote utilise des données **fictives** ; l'historique git ne contient aucun secret réel (clés, tokens).

### 2.2 Points forts constatés
1. **Humain dans la boucle réellement appliqué** : `valide_par` rempli par l'analyste (R-13 rejeté le 23/09 *pour essayer le circuit*, R-14 modifié — traces dans `06-validation.md`). Cet essai a permis de confirmer que la décision humaine est **opposable** ; il a aussi été reconsidéré le 24/09 (un rejet sans motif de gestion n'est pas une décision — R-13 retenu, cf. `MODIFICATIONS.md`).
2. **Sources à ID stable + rejet si inconnu** : chaque risque cite `STRIDE-*`, `LINDDUN-*`, `ISO27002-*`, `ATT&CK-T1190`, `CVE` placeholder explicitement signalé (pas de note CVSS fabriquée).
3. **Traçabilité** : une branche par analyse, push à chaque étape, issue + board GitHub suivis, `RAPPORT-CONTROLE.md` à chaque étape.
4. **Démo = POC piloté par consignes** : il n'existe **pas de code applicatif** (ni `LlmProvider` ni `config.py` exécutés) — le « prototype » est une chaîne d'agents dont les consignes (`.md` + skills) *sont* le programme, exécutée dans opencode. La démonstration ne dépend donc d'aucun service externe : elle utilise le modèle d'exécution d'opencode (`opencode/big-pickle`, API cloud) ; le **passage en local (ollama) est planifié en roadmap** (« solution plus tard »).
5. **Permissions minimales (renforcées le 24/09)** : agents de chaîne en lecture seule + écriture **limitée à `analyses/**`** (`edit: deny **` puis `allow analyses/**` — dernière règle gagnante) ; `bash` refusé ; `e21-controle` entièrement en lecture seule ; aucun agent ne modifie de système réel.
6. **Contrôles déterministes en plus du LLM** : suite `verification.py` (schéma JSON, matrice proba×impact, sources ⊆ index, index ISO canonique) + checks du drapeau `valide_par`.

### 2.3 Faiblesses — détaillées par criticité

#### 🔴 ÉLEVÉ — Index `knowledge_base/README.md` : identifiants ISO 27002 erronés
| ID de l'index | Libellé actuel (faux) | Réel dans ISO/IEC 27002:2022 |
|---|---|---|
| `ISO27002-A8.4` | « Journalisation et surveillance » | **8.4 — Accès au code source** (journalisation = 8.15/8.16) |
| `ISO27002-A7.2` | « Sensibilisation, formation, compétences » | **7.2 — Conditions d'emploi** (sensibilisation = 6.3) |
| `ISO27002-A5.36` | « Continuité de l'activité » | **5.36 — Conformité aux politiques, règles et normes** (continuité = 5.30) |
| `ISO27002-A6.2` / `A6.2.3` | « Contrôle d'accès / privilèges d'accès » | **n'existent pas** dans la révision 2022 (accès = 5.15/5.18 ; privilèges = 5.18/8.2) |
| `ISO27002-A8.4.2` | « Chiffrement des données au repos/en transit » | **n'existe pas** (chiffrement = 8.24 ; masquage = 8.11) |

**Impact** : ces IDs erronés sont **cités par des risques validés du registre** (R-06 → A8.4 ; R-08/R-09/R-14 → A5.36 ; R-01 → A6.2/A7.2 ; R-08 → A8.4.2 ; R-10 → A6.2.3) → les références normatives du registre de référence sont inexactes.

#### 🟠 MOYEN — Contrôle circulaire de `e21-controle`
`e21-controle` vérifie l'**existence** des sources dans l'index… mais l'index est lui-même la source de vérité → une erreur de l'index n'est jamais détectée en aval. Il manque une vérification de 2ᵉ niveau (mapping canonique ISO).

#### 🟠 MOYEN — Checklist du plan de test non bouclée
- ❌ **Analyse manuelle de référence** (`analyses/…/analyese_manuelle.md` prévu par `06-plan-de-test.md` §1) **absente** → pas de comparatif « agents vs main » documenté.
- ❌ **Test du document piégé** (jalon 4) non documenté (voir `soutenance/tests/` — cette lacune est comblée par la campagne de tests de la soutenance).
- ⚠️ `knowledge_base/` ne contient qu'un **README.md** : les fichiers par thématique annoncés (`stride.md`, `iso27002.md`, `oss_fr.md`, `cve.json`) sont absents.

#### 🟡 FAIBLE — Dérives rédactionnelles
- `01-actifs.md` : « ~500 €/semaine » de perte (defacing) **non dérivable** du chiffre d'affaires de l'énoncé (≈ 15 k€/trimestre) → estimation, à marquer comme telle.
- `05-traitement.md` §1 : R-06 listé « Moyen » alors qu'il est « Élevé » (R-02 était dans les « Élevés ») → **corrigé avant le merge** (commit `ac2a64b`).

## 3. Plan d'amélioration proposé (P1 → P3)

| Priorité | Action | Effort | Livrable |
|---|---|---|---|
| **P1** | **Ré-indexer `knowledge_base/`** : mappings exacts ISO/IEC 27002:2022 (5.15/5.18, 6.2, 6.3, 8.4, 8.15/8.16, 8.24…), séparer les fichiers par thématique (`stride.md`, `iso27002.md`, …) | ½ j | `knowledge_base/` restructuré + re-validation des citations du registre |
| **P2** | **Tests pytest sur les conventions** (`test_registre.py`, `test_sources.py`, `test_matrice.py`, `test_format_md.py` — cf. `06-plan-de-test.md` §2) | 1 j | `tests/` + passage CI local |
| **P3** | **Campagne garde-fous** : document piégé, source inexistante, fuite de données, excès d'autonomie — scénarisée et journalisée | 1 j | `soutenance/tests/TESTS.md` (section 2) |

## 4. Conclusion de l'audit

Le cœur du système (garde-fous par skills, humain obligatoire, traçabilité git/GitHub) est **solide et démontrable**. Les faiblesses sont **corrigeables sans refonte** : la priorité absolue est la **fiabilisation de l'index ISO 27002** (erreurs citées par des risques validés), puis la mise en œuvre des tests de conventions prévus au plan de test.

## 6. Remédiation appliquée (audit externe du 24/09/2026)

> Un auditeur indépendant a évalué tout le dépôt le 24/09 (note indicative 11–12/20). Constats confirmés en grande partie ; la remédiation a été menée dans la branche `corrections/audit-2026-09-24` (issues #15–#20). Détail complet : `soutenance/MODIFICATIONS.md`.

| Constat | Verdict | Remédiation |
|---|---|---|
| IDs ISO 27002 non canoniques (10/13 risques mal sourcés) | ✅ confirmé | Index ré-écrit en **ISO/IEC 27002:2022 canonique** + table de correspondance 2013→2022 ; registres ré-indexés (R-06→8.15/8.16, R-01→8.5/5.15, R-08→8.24/8.13/8.11, R-09→5.30, R-14→8.13/8.16/8.24…) ; **T-10** interdit tout retour de `ISO27002-A*` (issue #15) |
| R-13 « rejeté sans justification » | ⚠️ confirmé/atténué | Le rejet était un **essai du circuit** ; reconsidéré le 24/09 : R-13 **retenu** (état de fait RGPD), programme de mise en conformité, échéance déc. 2026, résiduel Faible (issue #16) |
| « Niveaux concurrents R-02 » | ❌ **réfuté** | `04-evaluation.md` §5 dit déjà « le niveau de référence est la **matrice** ; DREAD = ordre de traitement » — rappelé en tête du registre + JSON (`niveau_reference`) |
| Analyse manuelle de référence (exigence 4 checklist) | ✅ confirmé | À produire : issue #17 (comparatif agents vs main) |
| Suite de tests surévaluée (SKIP compté PASS, 13 en dur, pas de test d'injection réel) | ✅ confirmé | `verification.py` refondu : **3 statuts** (PASS/SKIP/FAIL), comptage dynamique, manifeste `.opencode/package.json` versionné, `gh` optionnel, **T-10** ISO canonique, **T-11** protocole d'injection réel (SKIP tant que non exécuté) (issue #18) |
| Permissions « edit: allow » trop larges | ✅ confirmé | `edit: deny **` + `allow analyses/**` sur les 7 agents de chaîne ; `e21-controle` en lecture seule (issue #19) |
| Discours « prototype LlmProvider/mock » non conforme au dépôt | ✅ confirmé | Documents corrigés : POC piloté par consignes, modèle réel `opencode/big-pickle`, ollama en roadmap (issue #20) |

## 5. Sources / références
- `documentation/technique/06-plan-de-test.md`, `04-garde-fous.md`, `01-architecture.md`
- `knowledge_base/README.md` (index audité)
- ISO/IEC 27002:2022 (contrôles 5.x, 6.x, 7.x, 8.x) — mappings de contrôle de la révision 2022.
- `analyses/2026-09-23_boutique-en-ligne/` (registre, RAPPORT-CONTROLE, 05-traitement corrigé au commit `ac2a64b`).