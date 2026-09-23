# 03 — Format des échanges (JSON / Pydantic)

Tous les échanges entre agents sont **structurés** et **validés** (Pydantic). Un risque respecte exactement le format du sujet :

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

## Schémas par agent

- `EntreeSysteme` : description du système (texte libre + champ `donnees_personnelles` booléen).
- `ListeActifs` : `actifs: [Actif]` — `Actif { id, nom, type, valeur, classe }`.
- `ModeleMenaces` : `{ modele, justification, grille_posée?: [str] }`.
- `ListeMenaces` : `menaces: [Menace]` — `Menace { id, actif_id, categorie, description, cve?: str }`.
- `MenaceNotee` : `Menace + probabilite + impact + niveau + justification` (enums `faible|moyen|élevé`).
- `Risque` : schéma ci-dessus (ajoute `mesures`, `sources`, `traitement`, `valide_par`).
- `Registre` : `risques: [Risque]` + `modele` + `date` + `analyse_par`.

## Enums (bornées par Pydantic)

- `probabilite`, `impact`, `niveau` : `faible | moyen | élevé`
- `traitement` : `réduire | transférer | éviter | accepter`
- `categorie` de menace : `STRIDE-S | STRIDE-T | STRIDE-R | STRIDE-I | STRIDE-D | STRIDE-E` (+ préfixes des autres grilles si utilisées)

## Règles

1. **`sources` obligatoire** et non vide pour chaque risque ; vérifiée par `valider_sources()` contre l'index de `knowledge_base/` — toute source inconnue → rejet + retour à l'agent.
2. **`valide_par`** : `null` en sortie des agents ; rempli uniquement par la validation humaine.
3. Une sortie d'agent est **re-validée Pydantic** avant d'être injectée dans l'agent suivant (sanitisation inter-agents).

## Journalisation

Chaque étape écrit dans `logs/run_<ts>.jsonl` : `{ts, etape, agent, modele, sortie_json(anonymisée), erreur?, relance?}` — ce sont les **traces des échanges** exigées par le rendu.