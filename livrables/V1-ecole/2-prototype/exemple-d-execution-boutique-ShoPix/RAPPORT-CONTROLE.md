# Rapport de contrôle & garde-fous — Analyse ShoPix (2026-09-23)

> Contrôle qualité exécuté après chaque étape (agent « Contrôle & garde-fous », skill `garde-fous-ia`).
> `OK` = accepté · `WARN` = accepté avec signalement · `REJET` = bloquant (reprise demandée).

> **Post-audit (2026-09-24)** : les ID `ISO27002-A*` cités dans ce rapport (mélange années 2013/2022) suivaient l'ancien index. L'index a été ré-indexé en ISO 27002:2022 canonique et les sources des registres corrigées en conséquence (issue #15). Ce document date d'avant la correction : il décrit l'état **d'origine**, pas l'état courant.

---

## Étape 1 — Existant & actifs (`00-description.md`, `01-actifs.md`)

| Contrôle | Statut | Détail |
|---|---|---|
| Conformité de fond | OK | Description cas, DFD Mermaid, 4 frontières de confiance, `donnees_personnelles: true` ; inventaire de 16 actifs tangibles/intangibles avec type, valeur, sensibilité |
| Sources vérifiables | OK | Tous les faits proviennent de `etude-de-cas.md` (seule source d'entrée à ce stade), rappelé dans l'en-tête des fichiers |
| Hallucination | OK | Les valeurs (CA, commandes, pic) sont reprises telles quelles de l'étude de cas ; aucune CVE/norme citée à ce stade |
| Injection de prompt | OK | Le document d'entrée est traité comme donnée non fiable ; aucune instruction parasite dans les sorties |
| Fuite de données | OK | Données fictives de l'étude de cas, aucun nom/e-mail/IP réel ; « Mélanie » provient de l'énoncé |
| Excès d'autonomie | OK | Aucune décision prise (étape descriptive) ; valeurs marquées « estimées » |
| Empoisonnement | OK | Une seule source d'entrée (`etude-de-cas.md`), versionnée |
| Dépendance | OK | Markdown autonome + diagramme Mermaid rendu par GitHub |
| Format | OK | Tables Markdown, conventions `A-0X` / `R-0X` respectées ; pas de risque à cette étape |

**Verdict étape 1 : OK — poussée.**

---

## Étape 2 — Choix de la méthode (`02-methodes.md`)

| Contrôle | Statut | Détail |
|---|---|---|
| Conformité de fond | OK | Tableau comparatif (7 méthodes), choix STRIDE + LINDDUN + DREAD/CVSS justifié PAR le cas (DFD existant, données personnelles, incidents, budget), méthodes écartées expliquées, chaîne ①–⑥ en Mermaid |
| Sources vérifiables | OK | 100 % des ID cités (`STRIDE-*`, `LINDDUN-*`, `EBIOS-RM-2018`, `PASTA-*`, `ATT&CK-T1190`, `DREAD-*`, `CVSS-*`) présents dans `knowledge_base/README.md` |
| Hallucination | WARN | `CVE-2023-XXXX` est un **placeholder de l'étude de cas** (non inventé) ; la référence exacte sera vérifiée à l'étape 3 avant notation CVSS. Absence de note inventée : OK |
| Injection de prompt | OK | Aucune instruction parasite ; le rapport indique lui-même que toute nouvelle technique ATT&CK devra être ajoutée à l'index avant citation |
| Fuite de données | OK | Données fictives ; aucun nom/e-mail réel |
| Excès d'autonomie | OK | En-tête explicite « Statut : proposition — **validation humaine requise** avant de lancer l'étape 3 » |
| Empoisonnement | OK | Sources contrôlées |
| Dépendance | OK | Markdown autonome + Mermaid |
| Format | OK | Tables, conventions, aligné avec `analyse-risques` et `registre-risques` |

**Verdict étape 2 : OK — poussée** (note : vérifier la CVE exacte à l'étape 3).

---

## Étape 3 — Menaces (`03-menaces.md`)

| Contrôle | Statut | Détail |
|---|---|---|
| Conformité de fond | OK | 14 menaces (M-01…M-14), grille STRIDE appliquée par élément/aux frontières F1–F4 + LINDDUN limité aux actifs RGPD (A-05/A-06/A-11) ; tableau de couverture incidents/vulnérabilités documentés |
| Sources vérifiables | OK | Tous les ID (`STRIDE-*`, `LINDDUN-*`, `ATT&CK-T1190`) présents dans l'index ; renvois `etude-de-cas.md`/`00-description.md`/`01-actifs.md` exacts |
| Hallucination | OK | `CVE-2023-XXXX` reconnu comme placeholder de l'énoncé, **aucun numéro inventé** ; 3 techniques ATT&CK proposées (§ 6) explicitement marquées « hors index, non citées » |
| Injection de prompt | OK | Aucune instruction parasite dans les descriptions de menaces |
| Fuite de données | OK | Données fictives (Mélanie, Shopix) ; aucun e-mail/IP/nom réel |
| Excès d'autonomie | OK | En-tête « Statut : proposition — aucun `valide_par` » |
| Empoisonnement | OK | Les techniques ATT&CK hors index sont proposées (à research), pas injectées dans les sources |
| Dépendance | OK | Markdown autonome |
| Format | OK | Tableau une ligne par menace (ID/Actif/Catégorie/Description/CVE/Source) ; conventions M-0X respectées |

**Verdict étape 3 : OK — poussée.** Suivi : proposer à `research` l'ajout de `ATT&CK-T1110`, `ATT&CK-T1078`, `ATT&CK-T1566` à l'index (phase clôture).

---

## Étape 4 — Évaluation (`04-evaluation.md`)

| Contrôle | Statut | Détail |
|---|---|---|
| Conformité de fond | OK | 14 menaces évaluées ; probabilité/impact justifiés chacun par une phrase ancrée dans le cas ; 2 critiques, 10 élevés, 2 moyens |
| Matrice | OK | Les 14 combinaisons proba×impact correspondent exactement à la matrice du skill `analyse-risques` (vérifiées une à une) |
| Sources vérifiables | OK | Section Sources : matrice (`analyse-risques`), `DREAD-*`, `CVSS-*` (index), menaces M-01…M-14, faits `etude-de-cas.md` |
| Hallucination | OK | **Aucune note CVSS fabriquée** — placeholder CVE (M-05) explicitement non noté en CVSS, action `composer audit` proposée ; DREAD recalculée et cohérente |
| Injection de prompt | OK | Aucune instruction parasite |
| Fuite de données | OK | Données fictives |
| Excès d'autonomie | OK | « Statut : proposition — niveaux validés à l'étape 6 par l'analyste » |
| Empoisonnement | OK | Sources contrôlées |
| Dépendance | OK | Markdown autonome |
| Format | OK | Enums bornées {faible, moyen, élevé}+critique ; tableaux clairs |

**Verdict étape 4 : OK — poussée.**

---

## Étape 5 — Traitement (`05-traitement.md`)

| Contrôle | Statut | Détail |
|---|---|---|
| Conformité de fond | OK | 14 risques traités (2 critiques en priorité), 4 réponses possibles appliquées (réduire dominant, + transférer pour R-05/R-09), résiduel estimé jamais nul |
| Hallucination | OK | Aucun ID inventé ; le renvoi « CVE réelle à confirmer » est conservé, pas de numéro fabriqué |
| Injection de prompt | OK | Aucune instruction parasite |
| Fuite de données | OK | Données fictives ; les exports .csv traités sont ceux du cas |
| Excès d'autonomie | OK | En-tête « Statut : projet de registre — aucune décision finale » + avertissement en pied de fichier ; `valide_par: null` sur les 14 entrées JSON |
| Empoisonnement | OK | Sources contrôlées |
| Dépendance | OK | Markdown + JSON autonomes |
| Format | OK | Tableau conforme (ID/Actif/Menace/Proba·Impact·Niveau/Traitement/Contre-mesures/Sources/Résiduel) ; JSON conforme au skill `registre-risques` |

**Verdict étape 5 : OK — poussée.** Prêt pour la validation humaine (étape 6).

---

## Étape 6 — Validation & suivi (`06-validation.md`, `registre-risques.md`)

| Contrôle | Statut | Détail |
|---|---|---|
| Conformité de fond | OK | `06-validation.md` : tableau de décision 14/14 (en attente), plan de suivi, déclencheurs de ré-analyse ; `registre-risques.md` : 14 risques complets colonne `Validé par` = *(analyste)* |
| Sources vérifiables | OK | Sources déjà contrôlées étape 5, reprises à l'identique |
| Hallucination | OK | Aucune valeur modifiée ; niveaux/impacts repris de l'étape 4 |
| Injection de prompt | OK | Rien de parasite |
| Fuite de données | OK | Données fictives |
| Excès d'autonomie | OK | **Validation humaine obligatoire** : `valide_par` vide, décisions en attente (`*(en attente)*`), le registre est marqué « projet » |
| Empoisonnement | OK | Sources contrôlées |
| Dépendance | OK | Markdown autonome |
| Format | OK | Colonnes du skill `registre-risques` respectées ; aucun risque « Done » sans `valide_par` |

**Verdict étape 6 : OK — poussée, en ATTENTE de la validation humaine.**

### Mise à jour après validation humaine (2026-09-23)

| Contrôle | Statut | Détail |
|---|---|---|
| Décision analyste | OK | R-01…R-12 **validés** ; **R-13 rejeté** (consigné § 2 décisions + section « risque rejeté » du registre) ; **R-14 modifié** (impact → Élevé, résiduel → Moyen), tracé et opposable |
| `valide_par` | OK | Rempli sur R-01…R-12, R-14 (Analyste · 2026-09-23) ; **R-13 reste non validé** (`valide_par: null` dans le JSON, section rejetés) |
| Registre | OK | 13 risques validés (2 critiques, 10 élevés, 1 moyen) ; `registre_risques.json` annexé |
| Garde-fous | OK | La modification R-14 est une décision humaine directive « tu modifi » — valeurs changées avec accord écrit ; aucune autre valeur altérée |

**État final étape 6 : OK — registre validé. La synthèse peut démarrer.**

---

## Étape 7 — Synthèse (`SYNTHESE.md`)

| Contrôle | Statut | Détail |
|---|---|---|
| Conformité de fond | OK | Résumé exécutif (13 risques : 2 critiques, 10 élevés, 1 moyen), top 5 priorisés et justifiés, décisions (R-13 rejeté, R-14 modifié, résiduels acceptés), 13 recommandations A1–A13 **toutes liées à un ID du registre**, qualité/limites, schéma Mermaid |
| Fidélité au registre | OK | Reprise exacte des niveaux et décisions de `registre-risques.md`/`06-validation.md` ; en-tête « aucun élément nouveau » respecté ; R-13 exclu des recommandations actives (déclencheur de ré-analyse conservé) |
| Sources vérifiables | OK | ID du registre et `knowledge_base` cohérents ; CVE placeholder reprise sans inventaire de numéro |
| Hallucination | OK | Rang DREAD recoupés avec `04-evaluation.md` (8,8 / 7,6 / 7,6) ; aucune note CVSS fabriquée |
| Injection de prompt | OK | Aucune instruction parasite |
| Fuite de données | OK | Données fictives |
| Excès d'autonomie | OK | Décisions attribuées à l'analyste/« Mélanie » avec dates ; aucun risque refinalisé sans validation |
| Empoisonnement | OK | Sources contrôlées |
| Dépendance | OK | Markdown + Mermaid autonomes |
| Format | OK | Structure 6 sections conforme à `e21-synthese` |

**Verdict étape 7 : OK — poussée. Chaîne complète terminée, clôture PR en cours.**