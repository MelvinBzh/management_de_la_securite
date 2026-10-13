# Fiche de contrôle des livrables V2

> Pour vérifier soi-même ce que disent le dossier écrit V2 et la soutenance. Chaque chiffre a une source et, quand c'est possible,
> une commande. Les commandes se lancent dans une copie du dépôt (`git clone https://github.com/MelvinBzh/management_de_la_securite`).
> Les chiffres de dépôt sont figés au commit **`cc1b2c0`** (12/10/2026, 18h44) pour rester vérifiables.

## 1. Frontière école / V2 (vérifiable dans Git)

| Affirmation | Valeur | Commande |
|---|---|---|
| Le tag école pointe sur le dernier commit du 24/09 | `b7f3155`, 24/09/2026 13h34 | `git show -s --format='%h %ad %s' ecole-2026-09-24^{commit}` |
| Commits jusqu'au tag | 40 | `git rev-list --count ecole-2026-09-24` |
| Commits depuis le tag | 144, dont 118 hors fusions | `git rev-list --count ecole-2026-09-24..cc1b2c0` ; avec `--no-merges` |
| Fichiers et lignes ajoutés depuis le tag | 184 fichiers, + 35 125 / − 115 | `git diff --shortstat ecole-2026-09-24 cc1b2c0` |
| Python hors tests : 640 → 22 455 lignes | idem | `git ls-tree -r --name-only <rév> \| grep '\.py$' \| grep -v -i test`, puis compter les lignes |
| Fichiers de tests | 35 (`test_*.py`), ≈ 10 320 lignes | `git ls-tree -r --name-only cc1b2c0 \| grep -c 'test_.*\.py'` |
| 12 agents et 15 skills au tag, 16 skills ensuite | 12 / 15 / 16 | `git ls-tree -r --name-only <rév> .opencode/agents` et `.opencode/skills` |
| Auteurs | 2 (MelvinBzh, lucash : 1 commit ANSSI) | `git shortlog -sn origin/main` |

## 2. Résultats des projets (vérifiables dans les pièces fournies)

| Affirmation | Valeur | Où vérifier |
|---|---|---|
| SanteTech : 3 documents, 39 actifs, 135 risques, Critique 75 (56 %) | idem | `preuves-execution-SanteTech/livrables/SYNTHESE.md` (« Chiffres clés ») |
| SanteTech : traitement 123 réduire / 7 éviter / 4 accepter / 1 transférer | idem | même fichier |
| SanteTech : 18 décisions de l'analyste, 0 risque décidé | idem | `validations.json` ; `registre-risques.md` (colonne `valide_par` vide) |
| 13 contrôles numérotés, 2 conformes (étapes 6 et 7) | idem | `RAPPORT-CONTROLE.md` (titres « Contrôle n° ») |
| 12 doublons d'actifs fusionnés par le code | idem | `traces/…log`, ligne « 01-actifs.md assemblé par le programme » |
| Nordval : 22 documents, 38 actifs, 151 risques, Critique 72 (48 %) | idem | `documentation/technique/09-dossier-de-connaissance.md` § 4 sexies ; projet `2026-10-10_test-nordval` du serveur : `SYNTHESE.md` |
| Nordval : 10 risques décidés (9 tels quels, 1 modifié) | idem | `validations.json` du même projet |
| ShoPix (V1) : 14 risques, 2 critiques / 11 élevés / 1 moyen | idem | `V1-ecole/1-dossier-ecrit/04-registre-des-risques/registre-risques.md` |
| Analyse manuelle : 9 menaces retrouvées sur 12 | idem | `analyses/2026-09-23_boutique-en-ligne/reference-manuelle.md`, § 8 |

## 3. Mesures de qualité (consignées à la date du run, non rejouables d'un clic)

| Affirmation | Valeur | Source |
|---|---|---|
| Faits à extrait exact | 435 / 447 (97 %) | Mesure v3 du 10/10 sur Nordval (22 documents) : `documentation/technique/09-dossier-de-connaissance.md` § 3 bis (le § 3 donne la mesure v1, plus ancienne : 93 %, 75 %, 86 %) |
| Relations vérifiées | 372 / 430 (86 %) | idem |
| Bon passage parmi les 8 premiers | 96 % (30 questions) | idem |
| Contradictions : précision | 60–70 % | idem (estimation sur échantillon relu) |
| Indexation ≈ 70 min ; chaîne ≈ 2 h ; étapes 6–7 : 2 min au lieu de 30 | idem | `documentation/technique/09-dossier-de-connaissance.md` § 4 sexies (runs des 10 et 11/10) |
| Références inventées retirées : 15 / 13 / 1 (étapes 3, 5, 7) | idem | idem, run du 11/10 |
| Mise à jour : 32 min puis 13 min ; 134 puis 3 éléments ; 39 actifs et 135 risques identiques | idem | Essai du 12/10 : `documentation/technique/09-dossier-de-connaissance.md` § 4 quinquies |

> Les mesures de la partie 3 ont été faites sur le serveur d'essai ; les journaux bruts ne sont pas tous conservés. Si un jury
> demande une preuve rejouable, il faut relancer l'indexation (≈ 70 min) ou la mise à jour (≈ 13 min) devant lui.

## 4. Ce qui n'est PAS affirmé (à ne pas laisser croire)

| Point | Réalité |
|---|---|
| « Tous les risques sont validés par un humain » | Faux pour SanteTech (0 / 135) et Nordval (10 / 151). Vrai pour ShoPix (14 / 14, V1). |
| « Le test d'injection a été joué avec le modèle » | Faux. Exécuté sur l'ingestion et la commande (11 contrôles), pas avec le modèle en direct. |
| « La mise à jour gère modification et retrait » | Testé avec de faux modèles ; non rejoué avec le modèle réel. |
| « Le système est sécurisé » | Faux : pas d'authentification, SSH root par mot de passe, Ollama exposé, conteneur en root. |
| « La répartition des tâches du groupe est retraçable dans Git » | Non : le groupe (Melvin Raimbault, Lucas Huard, Jérémy Lessa, David Amaro Monteiro) est identifié, mais Git ne montre que deux identités (`MelvinBzh`, `lucash`) ; le détail des tâches est à donner par l'équipe. |

## 5. Où regarder sur GitHub

| Quoi | Adresse |
|---|---|
| Tag école (figé) | `https://github.com/MelvinBzh/management_de_la_securite/tree/ecole-2026-09-24` |
| Branche de la V2 | `https://github.com/MelvinBzh/management_de_la_securite/tree/corrections/chaine-ollama-pilote` |
| Livrables (V1 + V2) | `…/tree/corrections/chaine-ollama-pilote/livrables` |
| Comparaison école → V2 | `…/compare/ecole-2026-09-24...corrections/chaine-ollama-pilote` |

> Le dépôt est **public**. La branche de la V2 n'est pas fusionnée dans `main` : `main` ne contient pas la V2.
