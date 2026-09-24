# Roadmap — E21 « Des agents IA pour analyser les risques »

> **Échéance : DEMAIN.** Objectif : un rendu propre et fonctionnel (dossier + prototype + soutenance).
> Méthode : follow-up quotidien via GitHub issues/board, jalons du sujet.

## Stack retenue (décisions — cf. `documentation/technique/`)

| Décision | Choix | Pourquoi |
|---|---|---|
| Plateforme du prototype | **Environnement opencode** (agents + skills `.opencode/`) — pas de site web | Le système ISE le prototype ; démontrable en direct, documents `.md` tracés |
| Orchestrateur | `orchestrator.md` : **collecte tout en une passe**, puis lance la chaîne | Conforme au design demandé (bonnes questions d'abord, lance ensuite) |
| Agents chaîne | 1 agent par étape des 6 étapes + analyse-existant + **expert méthodes** + **synthèse finale** + contrôle garde-fous | Chaque étape vérifiable, sources et niveaux justifiés |
| Méthodes | Skill par framework : **STRIDE (défaut)**, EBIOS RM, LINDDUN, PASTA, ATT&CK, DREAD, CVSS | L'agent `e21-choix-methode` compare et justifie par le cas |
| Cas d'étude | **A — Boutique en ligne** + **STRIDE** | Frontière de confiance « prestataire de paiement » idéale pour le DFD |
| Sorties | Dossier `analyses/<AAAA-MM-JJ>_<cas>/` : `.md` + `.json` (registre), `valide_par` obligatoire | Traçabilité + suivi board |
| Modèle LLM | **Interchangeable à la config opencode** : nominal `opencode/big-pickle` (API cloud, données fictives uniquement) ; **roadmap : ollama en local** (aucune donnée ne sort du poste) | Machine : pas de gros modèle local, pas de clé API détectée → POC piloté par consignes, la démo reste rejouable |
| Garde-fous | Skill `garde-fous-ia` : hallucination, injection, fuite, excès d'autonomie, empoisonnement, dépendance + agent `e21-controle` | Critère « Sécurité du système d'agents » |
| Suivi | Push régulier + issues + board #6 (Todo / In Progress / Review / Done) | Critère « gestion de projet » |

## Jalons du sujet → livrables

1. **Cadrer** — description du cas, actifs attendus
2. **Concevoir** — architecture + consigne de chaque agent/skill
3. **Prototyper** — chaîne fonctionnelle sur le cas A (dans opencode)
4. **Tester** — comparaison analyse manuelle + scénario d'injection de prompt
5. **Restituer** — dossier + soutenance (45 min)

## Plan d'exécution (jour J-1)

### Matin
- [x] Skills par framework (`SKILL.md`) : analyse-risques, registre-risques, garde-fous-ia, schemas-diagrammes, STRIDE, LINDDUN, EBIOS RM, PASTA, ATT&CK, DREAD, CVSS
- [x] Ordonnancement : `analyses/<date>_<cas>/` + fichier par étape
- [x] `knowledge_base/` (STRIDE, baseline de contre-mesures ISO 27002) — sources à ID stable
- [ ] Orchestrateur collecte le cas A (description, flux, prestataire de paiement) en une passe
- [ ] Lancer la chaîne sur le cas A : analyse-existant → choix-méthode

### Mi-journée
- [ ] menaces → évaluation (matrice probabilité×impact) → traitement (contre-mesures sourcées ISO 27002)
- [ ] Contrôle `e21-controle` à chaque étape (sources vérifiables, pas d'injection/fuite)
- [ ] Validation humaine (remplit `valide_par`) → `registre-risques.json` + registre final
- [ ] Push régulier de la branche `analyses/…` + commentaires d'issue + board

### Après-midi
- [ ] Garde-fous démontrés : scénario « document piégé » / injection de prompt (jalon 4)
- [ ] Analyse manuelle de référence des risques (comparatif attendu par le correcteur)
- [ ] `e21-synthese` : SYNTHESE.md avec recommandations expliquées (chaque action liée à un ID du registre)
- [ ] Exécution complète sur cas A → registre final validé

### Soir
- [ ] Dossier écrit (`documentation/`) : architecture, consignes, analyse critique, outils cités
- [ ] Préparation soutenance : ce qui marche / ne marche pas, risques de notre système (skill `garde-fous-ia`)
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