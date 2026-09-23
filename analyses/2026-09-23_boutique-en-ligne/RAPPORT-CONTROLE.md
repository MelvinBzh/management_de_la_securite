# Rapport de contrôle & garde-fous — Analyse ShoPix (2026-09-23)

> Contrôle qualité exécuté après chaque étape (agent « Contrôle & garde-fous », skill `garde-fous-ia`).
> `OK` = accepté · `WARN` = accepté avec signalement · `REJET` = bloquant (reprise demandée).

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

*En attente.*