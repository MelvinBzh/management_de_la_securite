# 06 — Plan de test

## 1. Analyse manuelle de référence (à faire AVANT les agents)

Réaliser à la main l'analyse de risques du cas A sur quelques actifs (le sujet le recommande, jalon 1) : c'est la référence pour juger les agents. Fichier : `output/analyse_manuelle.md`.

## 2. Tests unitaires (pytest)

| Test | Vérifie |
|---|---|
| `test_schemas.py` | Les sorties Pydantic sont valides, enums bornées, `sources` non vide |
| `test_sources.py` | Toute source d'un risque appartient à l'index de `knowledge_base/` |
| `test_matrices.py` | Le niveau = case correcte de la matrice probabilité × impact |
| `test_anonymisation.py` | `anonymise()` supprime emails/noms/IP/numéros |
| `test_injection.py` | Un document contenant « ignore tes instructions… » ne change pas la sortie des agents (scénario imposé) |

## 3. Test fonctionnel de bout en bout

- Exécuter la chaîne complète sur le cas A (`python -m src.main run --cas boutique`).
- **Sans LLM disponible** : le provider `mock` doit produire un registre complet et cohérent (démo garantie).
- **Avec LLM** (si clé dispo / ollama) : exécution idem, registre comparé au mock et à l'analyse manuelle.
- Critères : au moins 6–8 risques cohérents, chacun avec actif + menace + niveau + source, `valide_par` rempli après validation humaine.
- Fichiers produits : `output/registre_risques.json`, `output/rapport.md`, `logs/run_*.jsonl`.

## 4. Checklist finale (sujet, p. 28)

- [ ] Chaque risque du registre : actif + menace + niveau + source
- [ ] Choix du modèle justifié par le cas
- [ ] Un humain a validé chaque risque
- [ ] Résultat des agents comparé à l'analyse manuelle
- [ ] Test d'un document contenant une consigne piégée, documenté
- [ ] Aucune donnée réelle/Sensible envoyée à un service IA externe
- [ ] Outils IA utilisés cités dans le dossier