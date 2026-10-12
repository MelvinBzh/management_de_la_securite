# MODIFICATIONS.md — changements appliqués le 2026-09-24 (remédiation de l'audit)

> **Destinataire** : l'IA qui régénère le support de soutenance (`soutenance/presentation.pptx`, plan : `PLAN-45MIN.md`).
> Les slides actuelles racontent une version **obsolète** du projet. Ce fichier liste **tout ce qui a changé** : régénérer le deck depuis ces faits, pas depuis les slides existantes.
> Contexte : un auditeur indépendant a évalué le dépôt le 24/09 (constats en grande partie confirmés) ; la remédiation est sur la branche `corrections/audit-2026-09-24` (issues #15→#20) et doit rejoindre `main` par PR.

## 1. Chiffres et faits à jour (à reprendre tels quels)

| Sujet | AVANT (faux) | APRÈS (à présenter) |
|---|---|---|
| Registre validé | 13 risques (R-13 « rejeté ») | **14 risques** : 2 critiques, **11 élevés**, 1 moyen. R-13 est **retenu** (programme de mise en conformité RGPD, échéance déc. 2026, résiduel Faible) |
| Validation humaine | R-13 rejeté le 23/09 | Rejet du 23/09 = **essai du circuit** de validation ; **reconsidéré le 24/09** (un rejet sans motif de gestion n'est pas une décision). Décisions : traces dans `06-validation.md`, `valide_par` « Melvin RAIMBAULT · 2026-09-24 » |
| Niveau de référence | DREAD semblait concurrent | La **matrice probabilité × impact** fait foi ; DREAD = ordre de traitement (rappelé en tête du registre et dans le JSON) |
| ISO 27002 | Index « codes A » mélangeant 2013/2022 (ex. `A8.5.2`, `A6.2.3`, `A5.36`) | **Index ISO/IEC 27002:2022 canonique** : codes 5.3, 5.15, 5.19, 5.30, 6.3, 8.2, 8.5, 8.8, 8.11, 8.13, 8.14, 8.15, 8.16, 8.22, 8.24, 8.25, 8.26, 8.28, 8.29, 8.34 (+ tables de correspondance documentaire). **T-10 = invariant** : tout retour de `ISO27002-A*` fait échouer la suite |
| Budget sécurité | ~2 300 €/an (sous l'enveloppe) | **~4 300 €/an** (dont **~2 000 € de cyber-assurance** pour R-09) → **dépasse l'enveloppe de 2 500 € : arbitrage de l'analyste en cours** (issue #20). C'est un point de discussion, pas une erreur |
| Le système | « prototype », « `LlmProvider` / mock déterministe / `config.py` » | **POC piloté par consignes** : les consignes `.md` + skills **sont le programme** ; aucun code applicatif. Modèle d'exécution : **`opencode/big-pickle`** (API). **ollama (local) = roadmap** (« solution plus tard ») |
| Permissions des agents | « lecture seule + écriture markdown » | `edit: deny "**"` + `allow "analyses/**"` (dernière règle gagnante) sur les 7 agents de chaîne ; **`e21-controle` en lecture seule** ; `bash` refusé |
| Suite de tests | 10 tests, « SKIP compté PASS », « 13 » en dur, WARN = PASS | **T-01→T-11**, trois statuts (**PASS / SKIP / FAIL**), comptages **dynamiques**, manifeste `.opencode/package.json` versionné, `gh` optionnel. Résultat 24/09 : **10 PASS + 1 SKIP** (T-11) = OK (1 saut documenté) |
| T-11 injection | test de document piégé statique (T-07) seulement | **T-07** = régression statique conservée ; **T-11** = protocole d'exposition réelle (`soutenance/tests/injection/PROTOCOLE.md`) — **SKIP tant que la démo n'a pas tourné** (ne pas afficher « 11/11 » avant exécution) |
| Faits de la chaîne | 13 menaces → 13 risques | 14 menaces (M-01…M-14) → **14 risques** (R-01…R-14) |

## 2. Changements avant/après par fichier

### `analyses/2026-09-23_boutique-en-ligne/`
- **`knowledge_base/README.md`** (compté dans l'analyse) : index ré-écrit canonique + correspondance 2013→2022.
- **`03-menaces.md`** : M-02 décomposé en 2 mécanismes (credential stuffing / cassage SHA-1) ; M-12 = risque de *conséquence* (non cumulé, notification 72 h) ; M-13 amende **« 4 % du CA mondial ou 20 M€ »** (art. 83(5) RGPD — ancien « 2 % »).
- **`04-evaluation.md`** : justifications M-02/M-10/M-12 précisées ; §5 : agrégation explicite pour R-10 (Élevée = 3 précurseurs), non-cumul pour R-12, règles de référence (matrice vs DREAD).
- **`05-traitement.md`** : R-05 = transfert de la responsabilité **financière** (DPA = obligation RGPD, pas un transfert) ; R-09 cyber-assurance `ISO27002-5.30` ; budget ~4 300 € avec arbitrage ouvert ; JSON projet aligné (dédoublonnage sources, chiffrement R-14).
- **`06-validation.md`** : état décidé (plus « en attente ») ; décision R-13 **« retenu (rejet initial reconsidéré) »** ; plan de suivi : référent RGPD à désigner, échéance déc. 2026 ; dates de validation **2026-09-24**.
- **`registre-risques.md` + `registre_risques.json`** : 14 risques, R-13 réintégré, section « rejeté » supprimée, `niveau_reference` ajouté, sources tous codes 2022.
- **`SYNTHESE.md`** : résumé exécutif (14 risques), décisions et action **A14** (programme de conformité RGPD), budget/ré-interprétations, limites (référent RGPD à désigner).
- **`02-methodes.md`** : justification STRIDE **non circulaire** (l'énoncé §11 = alignement vérifié, pas la cause) ; labels LINDDUN officiels.
- **`RAPPORT-CONTROLE.md`** : bandeau « post-audit » (document historique, IDs d'origine).

### `soutenance/`
- **`TESTS.md`** : réécrit (T-01→T-11, statuts honnêtes, résultats réels 10 PASS + 1 SKIP).
- **`tests/verification.py`** : refondu (3 statuts, invariants dynamiques, T-10 ISO canonique, T-11 protocole).
- **`tests/injection/`** : nouvel artefact — `PROTOCOLE.md` + `rapport.md` (T-11).
- **`AUDIT-SYSTEME.md`** : faits corrigés (POC, permissions, R-13) + §6 « Remédiation appliquée » (table constat→verdict→remède).
- **`PLAN-45MIN.md`** : bandeau + slides corrigées (14 risques, permissions, T-11, POC).
- **`MODIFICATIONS.md`** : ce fichier.

### Infra (`.opencode/`, `documentation/`)
- **7 agents de chaîne** (`e21-*` sauf `e21-controle`) : `edit: deny "**" / allow "analyses/**"`.
- **`e21-controle`** : entièrement **lecture seule**.
- **`.opencode/.gitignore`** : `package.json` + `package-lock.json` **désormais suivis** (sinon T-01 redevenait un SKIP-PASS).
- **`documentation/technique/01-architecture.md`** et **`04-garde-fous.md`** : état réel (POC piloté par consignes, modèle `opencode/big-pickle`, ollama en roadmap, permissions, correspondance garde-fous → tests réels).

## 3. Ce qui est encore OUVERT (ne pas présenter comme fait)

1. **Arbitrage budgétaire cyber-assurance** (2 000 € vs enveloppe 2 500 €) — issue #20, reste à trancher.
2. **Analyse manuelle de référence** (exigence 4 de la checklist, comparatif « agents vs main ») — issue #17, reste à produire (l'analyste a autorisé l'assistant à la rédiger).
3. **T-11 protocole d'exposition réelle** — exécution à archiver avant une démonstration.
4. **Tests pytest pérennes** (P2) et **connaissances nouvelles** à proposer au `research` (ATT&CK-T1110/-T1078/-T1566, innocuité du commerce/2 % → 4 %) — en cours.
5. **`valide_par` nominatif** : réglé — les fichiers portent « **Melvin RAIMBAULT · 2026-09-24** ».

## 4. Instructions pour l'IA qui régénère le support

- Reprendre `PLAN-45MIN.md` (mise à jour) comme squelette de slides et **uniquement les faits du tableau §1 ci-dessus**.
- Ne plus dire : « mode mock », « LlmProvider », « aucun LLM », « 13 risques », « R-13 rejeté », « T-10 = WARN », « 29 sources », « 2 300 € ».
- Dire : POC piloté par consignes, exécuté sur `opencode/big-pickle`, ollama en roadmap ; 14 risques ; R-13 retenu après essai du circuit ; tests T-01→T-11 (10 PASS + 1 SKIP) ; index ISO 2022 canonique avec invariant T-10 ; permissions bornées à `analyses/**`.
- La slide « Audit » doit présenter la **remédiation** (table du §6 de `AUDIT-SYSTEME.md`), pas seulement les findings.
- Vérifier chaque chiffre cité contre `registre_risques.json` (source unique) avant de l'écrire sur une slide.