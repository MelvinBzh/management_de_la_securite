---
name: registre-risques
description: Use when producing or validating the risk register output. Enforces the exact expected format (columns, JSON fields, per-analysis folder, sources required, valide_par filled by humans), and the GitHub push + board tracking conventions for every analysis.
---

# Registre des risques — format des sorties

Toute analyse produit une **dossier dédié** `analyses/<AAAA-MM-JJ>_<cas>/` contenant les `.md` de chaque étape. Les fichiers sont **poussés sur GitHub régulièrement** et suivis sur le board.

## Colonnes du registre

| Field | Exemple |
|---|---|
| Identifiant et description | `R-07` — vol des identifiants admin par hameçonnage |
| Actif concerné | Console d'administration du site |
| Catégorie de menace | STRIDE-S (usurpation d'identité) |
| Probabilité · Impact · Niveau | Moyenne · Élevé · Élevé |
| Traitement et contre-mesures | Réduire : MFA FIDO2, sensibilisation |
| Justification et sources | Règle STRIDE, cas similaires, référence de la mesure |
| Risque résiduel et validation | Faible · validé par [analyste] |

## JSON structuré (échanges inter-agents)

```json
{
  "id": "R-07",
  "actif": "Console d'administration",
  "menace": "Vol d'identifiants par hameçonnage",
  "categorie": "STRIDE-S",
  "probabilite": "moyenne",
  "impact": "élevé",
  "niveau": "élevé",
  "traitement": "réduire",
  "mesures": ["MFA FIDO2", "sensibilisation"],
  "sources": ["STRIDE", "OWASP ASVS V2"],
  "valide_par": null
}
```

Enums : `probabilite/impact/niveau` ∈ {faible, moyen, élevé} ; `traitement` ∈ {réduire, transférer, éviter, accepter}.

## Règles absolues

1. **`sources` obligatoire** pour chaque risque ; chaque source doit exister dans la base de connaissances (`knowledge_base/`).
2. **`valide_par` = null** en sortie des agents ; rempli uniquement par la **validation humaine**.
3. Fichiers par étape dans le dossier d'analyse : `00-description.md`, `01-actifs.md`, `02-methodes.md`, `03-menaces.md`, `04-evaluation.md`, `05-traitement.md`, `06-validation.md`, `registre-risques.md`, `SYNTHESE.md`, `RAPPORT-CONTROLE.md`.
4. Après chaque étape : commit + push + mise à jour issue/board par `github-manager`.