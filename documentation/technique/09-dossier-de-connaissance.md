# 09 — Dossier de connaissance : plan de mise en place

> Statut : **plan validé en entier** par Melvin le 2026-10-10 ; **étapes 0 et A à G réalisées et testées de façon hermétique**
> (aucun modèle contacté par les tests). Reste à **mesurer sur le serveur** (compaction, temps, qualité des citations) et à faire
> tester par l'analyste. Ce document dit pourquoi, quoi, dans quel ordre, et comment on saura que ça marche.

## 1. Le problème

Sur un cas réel (Nordval : 22 documents, 40 Ko), les agents d'analyse :
- relisent tous les documents à chaque étape → le contexte déborde, opencode **résume** la conversation et l'agent
  perd des détails (cause mesurée des hallucinations) ;
- **inventent** des faits (nginx, CTO, DPO…) que les contrôles ne rattrapent qu'en partie ;
- ne savent pas dire « je ne sais pas » : une information absente est comblée plutôt que signalée.

## 2. Principe

> **On ne lit chaque document qu'une fois. On en garde des preuves exactes, reliées et interrogeables. Tout ce qui
> est écrit cite ses preuves ; ce qui n'a pas de preuve est dit « non documenté », jamais inventé.**

Quatre garanties, par ordre de solidité :

1. **Le code** vérifie que chaque extrait cité existe mot pour mot dans le document (aucun modèle ne peut le tromper).
2. **Deux vérificateurs indépendants** (Gemma 4 + MiniCheck) jugent qu'une affirmation est soutenue par ses preuves ;
   désaccord = **« nécessite une validation humaine »**, avec le pourquoi et quoi vérifier.
3. **Les contradictions** entre documents sont cherchées activement (un « c'est bon » ne clôt pas le sujet).
4. **Connu / partiel / inconnu** : chaque besoin d'information est classé ; l'inconnu devient une question à poser.

## 3. Ce qui existe déjà (mesuré sur Nordval)

| Brique | Module | Résultat mesuré |
|---|---|---|
| Faits à extrait exact | `fiches.py`, `texte.py` | 93 % des faits ont un extrait retrouvé mot pour mot |
| Relations typées | `relations.py` | 75 % vérifiées ; les 22 documents couverts |
| Passages d'origine (filet) | `passages.py` | texte du document, rien de perdu |
| Index hybride | `index.py` | rappel@5 = 86 % (mots-clés + sens) |
| Fusion d'alias | `alias.py` | 26/26 contrôles étiquetés ; refaite après sur-fusion constatée |
| Contradictions | `contradictions.py` | recherche croisée : 71 signalements (≈ 60 % de précision) |
| Vérification | `verification.py` | Gemma 4 : 100 % / 100 % (test facile) ; MiniCheck 96 % / 94 % |
| Connu / partiel / inconnu | `couverture.py` | voir §6 |

## 4. Plan de branchement (par étapes, chacune mesurée et validée avant la suivante)

| Étape | Livrable | Critère de réussite |
|---|---|---|
| **A. Ingestion → connaissance** | À l'ajout d'un document : fiches, relations, passages, vecteurs ; seuls les NOUVEAUX documents sont traités ; état visible dans le site | 22 documents < 10 min ; un document inchangé n'est pas retraité |
| **B. Page « Connaissances »** (lecture seule) | Dans le site : faits et preuves par document, entités fusionnées, contradictions, besoins connus / partiels / inconnus, questions ouvertes | l'analyste voit ce que le dossier sait, et ce qu'il ignore |
| **C. Les étapes lisent les preuves** | Les agents d'étape reçoivent les preuves pertinentes (recherche, k = 8) au lieu des documents entiers ; plus de débordement de contexte | zéro résumé automatique (`## Objective`) dans les journaux sur Nordval |
| **D. Citations vérifiées** | Chaque ligne d'un livrable cite ses preuves ; le code rejette les citations inexistantes, puis les deux vérificateurs | zéro identifiant ou fait inventé non signalé ; lecture confortable (citations en notes) |
| **E. Rapports numérotés + validation guidée** | Rapport de contrôle par version (ce qui n'allait pas / ce qui a changé) ; « nécessite une validation humaine » avec pourquoi et quoi vérifier, dans l'étape ④ | l'analyste sait quoi relire et pourquoi |
| **F. Propagation après validation** | Une modification demandée retrouve par l'index les lignes liées (risque ↔ actif ↔ menace ↔ mesure) et ne réécrit que celles-là, avec trace | une décision « valide » ne change rien ; une modification ne touche que ce qui en dépend |
| **G. Recherche hors documents** | Source « externe » (web) avec provenance distincte (`origine = externe`, `url`) ; même règle : sans preuve → inconnu | une information externe n'est jamais confondue avec une information fournie |

### 4 bis. Revue du plan (2026-10-10) : ce qui manquait

La revue a comparé, point par point, ce que Melvin a demandé à ce qui est écrit **et à ce qui est réellement déployé**.

**Étape 0 — Stabiliser la chaîne actuelle (avant l'étape A).** Décidé mais pas encore dans le code déployé :

| Point | Décision | État réel constaté |
|---|---|---|
| Retirer Granite du routage | Granite a décrit un seul document ; Qwen3.5 reprend à chaque fois | **toujours premier choix** des étapes 1 et 6 dans `web/chaine.py` |
| Ne plus relire les fichiers joints | La consigne dit déjà de ne pas relire ; à rendre effectif | non mesuré sur Nordval |
| Régler `compaction.reserved` d'opencode | Éviter le résumé automatique (cause des hallucinations) | **jamais testé** |
| Rapports de contrôle numérotés par version | « Contrôle n°3, version 2 : ce qui n'allait pas, ce qui a changé » | **absent** (l'ancien format ajoute des sections sans numéro) |
| « Indéterminé / non vérifié » → « nécessite une validation humaine » + pourquoi + quoi vérifier | Jamais un verdict muet | **absent** : le pilote classe encore « indéterminé » |
| Le contrôle continue jusqu'à un verdict « conforme » lisible | 3 tentatives de verdict, sinon validation humaine | **absent** |
| Figer la version d'opencode | La mise à jour silencieuse peut casser les permissions (1.18.34 → 1.18.35 constaté) | **non figée** |

**Transversal (oubliés dans la première version du plan).**

| Sujet | Pourquoi | Proposition |
|---|---|---|
| Charge de validation humaine | 24 besoins sur 31 sont « à valider » sur Nordval | trier par priorité (déjà dans `couverture.priorite`), valider par lots et par thème ; mesurer ce qu'un analyste accepte de relire |
| Tâches longues dans le site | extraction 14 min, contradictions 37 min | job en arrière-plan avec avancement, reprise sur erreur, un seul job par projet |
| Cycle de vie des documents | un document ajouté, modifié ou retiré | empreinte (hash) par document ; seuls les changés sont retraités ; retrait = suppression de ses preuves et signalement des livrables qui les citaient |
| Isolation par projet | plusieurs projets, plusieurs analystes | un fichier d'index par projet, jamais partagé |
| Jeu de contrôle de l'analyste | mesurer le vrai rappel des contradictions | l'analyste compare lui-même le rapport à son corrigé ; le chiffre revient en mesure officielle |
| Sécurité du site | pas d'authentification, port exposé, SSH root par mot de passe (constatés) | traiter avant toute ouverture à d'autres analystes (reporté à la demande de Melvin) |
| Injection de prompt dans les documents | le nouveau paquet lit des documents non fiables | consignes d'extraction et de jugement = données uniquement ; test avec le document piégé existant |
| CI du nouveau paquet | 88 tests non lancés par la CI | cible `make test-connaissance` + étape dans `.github/workflows/suite.yml` |
| Fusion et publication | la branche contient chaîne + site + paquet | ouvrir la PR (décision de l'analyste), relire par morceaux |

### 4 ter. État de réalisation (2026-10-10)

| Étape | Réalisé | Où |
|---|---|---|
| 0 | Granite retiré ; rapports de contrôle **numérotés par version** (ce qui n'allait pas / ce qui a changé) ; « nécessite une validation humaine » avec pourquoi et quoi vérifier ; 3 contrôleurs en alternance jusqu'à un verdict lisible ; `compaction` réglée ; opencode figé (1.18.35) ; `make test-chaine test-connaissance` + CI | `web/controles.py`, `web/chaine.py`, `opencode.jsonc`, `Dockerfile`, `Makefile` |
| A | Ingestion incrémentale par empreinte, tâche de fond avec état, lancement automatique au dépôt | `ingestion.py`, `travail.py`, `web/connaissance.py` |
| B | Page « Connaissances » (documents, faits et preuves, entités, contradictions, connu / ignoré) en lecture seule | `web/app.py` |
| C | Dossier de preuves par étape à la place des documents (repli : lecture directe) | `preuves.py`, `web/chaine.py` |
| D | Citations `[E…]` vérifiées (code puis 2 vérificateurs), notes discrètes à l'affichage | `citations.py` |
| E | Rapports numérotés + validation guidée dans ④ (pourquoi, quoi vérifier, lignes à relire) | `web/controles.py`, `web/app.py` |
| F | Propagation ciblée après validation, contrôlée et tracée | `web/propagation.py` |
| G | Recherche hors documents (`origine = externe`), jamais mêlée aux documents | `externe.py` |

**Limites connues.** Le croisement incrémental ne reconfronte pas un fait inchangé à un document ajouté (bouton « Tout refaire »). La recherche externe demande un moteur SearXNG configuré. La compaction d'opencode (`reserved`) reste à mesurer sur le serveur. La sécurité du site (authentification, SSH, Ollama exposé) est toujours reportée.

## 5. Règles de conception à ne pas casser

- **Absence d'information ≠ absence de mesure.** Le dossier dit « non documenté », jamais « n'existe pas ».
- **Politique ≠ pratique.** « Comptes désactivés sous 24 h » (PSSI) est une règle ; l'audit peut dire l'inverse. Toute réponse
  tirée d'un document est confrontée aux autres : si contestée, elle est **à valider**, avec la source adverse.
- **Vérifier contre des passages courts**, pas tout le corpus (mesuré : 89 % de vrais faits acceptés contre 67 %).
- **Le code décide de ce qui est une preuve ; les modèles proposent.** Un modèle ne valide jamais seul.
- **Une fusion manquée coûte un doublon ; une fusion abusive corrompt les relations** : on fusionne peu.
- **Tests hermétiques** : aucun test ne contacte un modèle (garanti par un test sans réseau).

## 6. Questions encore ouvertes

- Précision des contradictions (≈ 60 %) : second avis, seuils, vérification sur un jeu étiqueté par l'analyste.
- Faux « inconnu » de la couverture quand l'extraction rate un fait : atténué par les passages d'origine, à re-mesurer.
- Fiches pour de gros volumes (centaines de documents) : traitement en arrière-plan et reprise sur erreur.
- Coût de relecture humaine : combien de signalements un analyste accepte de valider ?

## 7. Modèles (mesurés sur RTX 5070 12 Go)

`qwen3.5:9b` extrait et rédige · `gemma4:12b` juge et vérifie · `bespoke-minicheck` second avis ·
`nomic-embed-text` vecteurs. Écartés après mesure : `granite4:7b-a1b-h` (a décrit un seul document),
`qwen3:14b` (trop lent, déborde du GPU), `llama3.1`, `mistral`, `qwen3-vl` (4 appels d'outils sur 6).
