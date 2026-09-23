# Roadmap — E21 « Des agents IA pour analyser les risques »

> **Échéance : DEMAIN.** Objectif : un rendu propre et fonctionnel (dossier + prototype + soutenance).
> Méthode : follow-up quotidien via GitHub issues/board, jalons du sujet.

## Stack retenue (décisions — cf. `documentation/technique/`)

| Décision | Choix | Pourquoi |
|---|---|---|
| Framework | **CrewAI** (Process séquentiel) | 5 rôles + orchestrateur, JSON validé à chaque étape, traces des échanges |
| Modèle LLM | **Abstraction : Ollama local** en nominal, **API en secours** + **mode démo déterministe** | Machine : pas de modèle local (~1 Go RAM), pas de clé API → le prototype doit TOUJOURS tourner |
| Sorties | **Pydantic strict**, JSON identique au sujet | Vérification « rien ne manque », champ `sources` + `valide_par` |
| Cas d'étude | **A — Boutique en ligne** + **STRIDE** | Frontière de confiance « prestataire de paiement » idéale pour le DFD |
| Garde-fous | Filtrage injection, sources vérifiées, anonymisation, lecture seule, logs JSONL | Critère « Sécurité du système d'agents » |

## Jalons du sujet → livrables

1. **Cadrer** — description du cas, actifs attendus
2. **Concevoir** — architecture + fiche/consigne de chaque agent
3. **Prototyper** — chaîne fonctionnelle sur le cas A
4. **Tester** — comparaison analyse manuelle + test injection de prompt
5. **Restituer** — dossier + soutenance

## Plan d'exécution (jour J-1)

### Matin
- [ ] Init structure du repo `src/` + environnement (`venv`, `requirements.txt`)
- [ ] `schemas.py` (Pydantic : Actif, Menace, Risque, Registre) — JSON du sujet champ pour champ
- [ ] `knowledge_base/` (STRIDE, baseline de contre-mesures ISO 27002) — sources à ID stable
- [ ] Engine LLM : interface `LlmProvider` — Ollama / API / **mock déterministe**
- [ ] Agent 1 `Inventaire` + Agent 2 `Modèle`

### Mi-journée
- [ ] Agent 3 `Menaces` + Agent 4 `Évaluation` (matrice probabilité×impact)
- [ ] Agent 5 `Traitement` + orchestrateur séquentiel (CrewAI)
- [ ] Validation humaine (rempli `valide_par`) + génération `registre_risques.json` + `rapport.md`
- [ ] Logs JSONL des échanges inter-agents

### Après-midi
- [ ] Garde-fous : filtrage entrées (séparation consignes/données), `anonymise()`, validation des sources
- [ ] `test_injection.py` — scénario « document piégé » démontrable (jalon 4)
- [ ] Analyse manuelle de référence des risques (comparatif attendu par le correcteur)
- [ ] Exécution complète sur cas A → registre final

### Soir
- [ ] Dossier écrit (`documentation/`) : architecture, consignes, analyse critique, outils cités
- [ ] Préparation soutenance : ce qui marche / ne marche pas, risques de notre système
- [ ] Traces des échanges exportées + commit final

## Critères d'évaluation (points de vigilance)

- [ ] Chaque risque : actif + menace + niveau + **source**
- [ ] Choix du modèle justifié par le cas
- [ ] Validation humaine de chaque risque
- [ ] Comparaison agents vs analyse manuelle
- [ ] Test injection de prompt documenté
- [ ] Aucune donnée réelle/sensible vers un service externe
- [ ] Outils IA cités dans le dossier

## Liens

- GitHub issues : https://github.com/MelvinBzh/management_de_la_securite/issues
- Documentation technique : `documentation/technique/`