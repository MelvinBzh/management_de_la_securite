# 10 — Export du dossier d'analyse complet et réparation des schémas

Deux modules, tous deux **déterministes** (aucun modèle) : `tools/export/dossier.py` (export) et `tools/export/schemas.py`
(réparation des schémas Mermaid).

## 1. Export du dossier complet (page ③ « Résultats »)

Un seul point d'entrée : `tools/export/export.exporter(dossier, "dossier-html" | "dossier-pdf" | "dossier-zip")`.

| Format | Contenu |
|---|---|
| **HTML** | un fichier autonome : sommaire, tous les livrables, une **fiche par risque** (actif, menace, évaluation, traitement, décision, preuves), annexe des preuves (document d'origine + extrait exact), historique des décisions |
| **PDF** | le même dossier, mis en page par WeasyPrint |
| **ZIP** | HTML, PDF, livrables d'origine (`.md`), registre en tableur (`.xlsx`, `.csv`), graphe de traçabilité (`.json`), décisions, mode d'emploi |

La chaîne de liaison est `document → preuve [E12] → actif → menace → évaluation → traitement → décision de l'analyste`.
Chaque identifiant d'un tableau (A01, M001, [E12]) est un lien vers la ligne ou la fiche concernée. Les documents d'origine
(`intrants/`) ne sont **jamais** inclus : seuls les extraits cités le sont. Le contenu est échappé (aucune balise exécutable).

## 2. Schémas Mermaid

Les petits modèles écrivent des schémas qui ne passent pas l'analyseur de Mermaid : flèche Unicode (`-.→`), parenthèses dans un
libellé, nom d'étape avec espaces, zone sans identifiant, citation `[E12]` collée à un nœud, lien mal formé.
`schemas.reparer_mermaid(code)` corrige ces défauts **sans rien inventer** :

- libellés mis entre guillemets seulement si nécessaire, structure du schéma conservée ;
- ce qui ne peut pas être réparé est **mis en commentaire** (`%% …`), jamais deviné : le reste du schéma s'affiche ;
- un schéma déjà correct est rendu à l'identique ;
- `reparer_fichier(chemin)` n'écrit que s'il y a eu correction et garde l'ancienne version à côté
  (`<nom>.avant-correction-schema.md`).

Où c'est appliqué :

| Lieu | Moment |
|---|---|
| `web/chaine.py` (`derouler`, `regenerer_description`) | dès l'écriture du livrable par l'étape |
| page ③ du site (`afficher_markdown`) | à l'affichage : schéma dessiné par mermaid.js, code réparé consultable dans un volet |
| export HTML/PDF | à la génération : bloc `mermaid` dessiné dans le navigateur ; sans réseau ou en PDF, le code reste lisible |

Validation : 30 schémas (13 réels de projets, dont 3 en erreur, et 17 cas piégés) valides avec l'analyseur officiel
(`mermaid.parse`, v11). Tests : `tools/export/tests/test_schemas.py`, `test_dossier.py`, `web/tests/test_page_export.py`,
`web/tests/test_derouler.py`.
