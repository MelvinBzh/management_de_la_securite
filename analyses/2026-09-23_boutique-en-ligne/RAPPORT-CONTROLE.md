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

*En attente.*