# `tools/connaissance` — le dossier de connaissance E21

> **Statut : prototype validé en principe, NON branché** sur le site ni sur les agents. Il sert à mesurer
> la qualité de la solution avant de la relier (voir « Branchement prévu »).

## À quoi ça sert

Les agents d'analyse lisaient **tous les documents à chaque étape** : le contexte déborde, le modèle oublie ou
invente. Ce paquet fait le travail **une seule fois par document** et le garde :

1. **séparer** l'information de chaque document en faits atomiques, chacun avec **l'extrait exact** qui le prouve ;
2. **relier** ces faits (entités, relations typées, fusion des alias, contradictions entre documents) ;
3. **retrouver** vite ce dont une étape a besoin (recherche par sens + par mots-clés), sans tout relire.

Règle directrice : **un fait n'entre dans l'index que si son extrait existe mot pour mot dans le document** —
vérification faite par le code (`texte.contient`), jamais par un modèle.

## Schéma

```mermaid
flowchart LR
    D[Documents ingérés<br/>.md] --> F[fiches.py<br/>faits + extrait exact]
    D --> R[relations.py<br/>entités + relations typées]
    F --> V{texte.contient<br/>extrait dans le document ?}
    R --> V
    V -- oui --> I[(index.py<br/>SQLite : éléments + vecteurs + FTS5)]
    V -- non --> X[marqué non vérifié<br/>jamais utilisé]
    R --> A[alias.py<br/>fusion K. Benali = Karim Benali]
    I --> C[contradictions.py<br/>recherche croisée → juge LLM]
    I --> C
    I --> Q[rechercher<br/>sens + mots-clés, fusion RRF]
    Q --> E[étapes d'analyse<br/>lisent seulement les preuves utiles]
```

## Les modules (un rôle chacun, remplaçables séparément)

| Module | Rôle | Dépend d'un modèle ? |
|---|---|---|
| `texte.py` | normaliser, vérifier un extrait, présence d'un nom | **non** (déterministe) |
| `ollama.py` | client Ollama : discuter (JSON contraint), vecteurs, cosinus | — |
| `fiches.py` | faits atomiques d'un document (`Fait.verifie`) | oui (extraction) |
| `relations.py` | entités et relations typées (`Relation.verifiee`) | oui (extraction) |
| `alias.py` | fusion des noms qui désignent la même chose | non (règles) + vecteurs |
| `contradictions.py` | `croiser` : chaque fait face aux passages des AUTRES documents → signalements | oui (juge) sur un fait + 4 passages |
| `index.py` | SQLite : stockage + recherche hybride | non |
| `experience.py` | mesure la qualité de bout en bout sur un dossier | — |

## Ce qui a été mesuré (Nordval : 22 documents, 38 Ko, RTX 5070)

| Mesure | Résultat |
|---|---|
| Extraction (faits + relations, 22 documents) | 7 min 40 s |
| Faits dont l'extrait est retrouvé mot pour mot | **240 / 258 (93 %)** |
| Relations vérifiées (extrait + 2 entités présentes) | **212 / 282 (75 %)**, les 22 documents couverts |
| Recherche, rappel@5 (30 questions) | **86 %** hybride ou mots-clés seuls, 83 % vecteurs seuls ; @1 : 63 / 66 / 53 % |
| Contradictions, méthode « paires proches » | **0** trouvée → méthode écartée (gardée pour comparaison) |
| Contradictions, **recherche croisée** (`croiser`) | **71 signalements**, la plupart des incohérences majeures (PSSI vs audit, COMEX vs README, PRA vs budget…) ; ~60 % de précision → toujours validées par un humain |
| Fusion des alias | **à refaire** : 465 noms → 140 entités, mais des fusions abusives (ex. « LogiSoft » avec « M. Dubreuil » et « M365 ») |

Limites : un seul jeu de documents, un seul passage, étiquettes relues à la main sur un échantillon.

## Points faibles connus (par ordre de priorité)

1. **`alias.fusionner` sur-fusionne** : le type « autre » sert de pont, les vecteurs de noms courts sont trop proches
   et la fusion est transitive. À durcir (pas de pont, seuil vecteur plus haut ET recouvrement de mots, vérification
   par paires) et à mesurer sur un jeu relu à la main.
2. **Faux positifs des contradictions** (≈ 40 %) : à réduire par un second avis (MiniCheck) et par des marqueurs de
   conflit ; la liste finale reste à valider par un humain (« nécessite une validation humaine »).
3. **Rappel de la recherche à k=1** (63 %) : prévoir k=8 pour les agents, puis un reclassement des résultats.

## Changer une pièce

- **Autre modèle d'extraction** : constante `MODELE_EXTRACTION` de `fiches.py` / `relations.py`.
- **Autres types de relations** : tuples `TYPES_RELATION` / `TYPES_ENTITE` de `relations.py` (le schéma JSON en dérive).
- **Autre vérificateur de contradictions** : `contradictions.juger`, seule fonction qui parle à un modèle.
- **Autre stockage** (PostgreSQL, graphe…) : réimplémenter `Index` ; l'interface (`ajouter_*`, `rechercher`) suffit.
- **Autre outil de graphe** (ex. Graphify) : peut s'ajouter en lecture comme carte des documents ; il ne remplace pas
  les extraits vérifiés (sa provenance s'arrête au fichier).

## Lancer

```bash
python3 tools/connaissance/tests/test_connaissance.py            # tests, sans réseau ni modèle
OLLAMA_ENDPOINT=http://<pc-gpu>:11434 \
  python3 -m tools.connaissance.experience <dossier_intrants> --base connaissance.sqlite
sqlite3 connaissance.sqlite "SELECT genre, doc, libelle FROM elements LIMIT 10;"   # tout est inspectable
```

## Modèles utilisés (mesurés sur RTX 5070 12 Go)

`qwen3.5:9b` extrait (rapide, JSON contraint) · `gemma4:12b` juge les contradictions et vérifie ·
`bespoke-minicheck` second avis de vérification · `nomic-embed-text` vecteurs.

## Branchement prévu (à valider avec l'analyste avant de coder)

1. à l'ajout d'un document : fiche + relations + index (seuls les nouveaux documents sont traités) ;
2. les agents d'étape reçoivent les **preuves pertinentes** (recherche) au lieu des documents entiers ;
3. chaque ligne produite cite ses preuves ; le code vérifie qu'elles existent, puis Gemma + MiniCheck ;
4. après validation humaine, une modification retrouve par l'index les lignes liées et ne réécrit que celles-là ;
5. livrable « recherches, relations, contradictions, questions » affiché dans le site.
