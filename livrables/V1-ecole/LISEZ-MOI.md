# Livrables V1 — production école (figée au 24 septembre 2026)

> **Travail de groupe** : Melvin Raimbault, Lucas Huard, Jérémy Lessa, David Amaro Monteiro.
>
> Ces fichiers sont extraits **tels quels** du tag Git `ecole-2026-09-24` (commit `b7f3155`, le 24/09/2026 à 13h34,
> juste après le dépôt du PPT de soutenance), à une exception près : les noms du groupe ont été ajoutés sur la slide de titre du
> PPT. Pour la suite (améliorations hors cours), voir `../V2-ameliorations/`.

## Ce que le sujet attendait, et où le trouver

| Livrable attendu | Élément | Fichier(s) dans ce dossier |
|---|---|---|
| **Dossier écrit** | Description du cas étudié | `1-dossier-ecrit/01-description-du-cas/` |
| | Architecture et fiche de chaque agent | `1-dossier-ecrit/02-architecture-et-fiches-agents/` (01 à 04) |
| | Choix du modèle de menaces, plan de test | `1-dossier-ecrit/03-choix-du-modele-et-plan-de-test/` |
| | Registre des risques obtenu | `1-dossier-ecrit/04-registre-des-risques/` |
| | Analyse critique des résultats | `1-dossier-ecrit/05-analyse-critique-etat-au-24-09/` (audit, benchmark, remédiation) — voir la note ci-dessous |
| | Présentation générale, feuille de route | `1-dossier-ecrit/06-presentation-generale/` |
| | **Consignes (prompts) utilisées** | `1-dossier-ecrit/07-consignes-prompts-des-agents/` (12 agents, 15 skills, prompt d'inventaire) |
| **Prototype** | Code ou flux sans code | agents et skills ci-dessus (le système est piloté par consignes) |
| | Exemple d'exécution sur le cas | `2-prototype/exemple-d-execution-boutique-ShoPix/` (étapes 00 à 06, rapport de contrôle, registre, synthèse) |
| | Traces des échanges entre agents | `RAPPORT-CONTROLE.md` dans l'exemple d'exécution ; tests dans `2-prototype/tests/` |
| **Soutenance** | Présentation (29 slides) | `3-soutenance/Soutenance_E21_Agents_IA.pptx` |
| | Plan minuté | `3-soutenance/PLAN-45MIN.md` |
| | Script de génération | `3-soutenance/build_presentation.py` (génère une version de 34 slides ; le PPT déposé en compte 29) |

Le dépôt complet au tag (sujet PDF compris) est dans `depot-complet-ecole-2026-09-24.zip`.

## Notes pour la relecture

1. **Pas de document unique « dossier écrit »** dans le dépôt : le contenu est réparti entre `documentation/technique` (01 à 06)
   et `soutenance/`. La V2 (`../V2-ameliorations/DOSSIER-ECRIT-V2.md`) en propose un document unique.
2. **L'analyse critique est la partie la plus faible de la V1.** À la date du 24/09, l'analyse manuelle de référence et le test
   d'injection réel figuraient encore dans la feuille de route (`PLAN-45MIN.md`, § B) : ils ont été réalisés le 4 octobre et
   relèvent donc de la V2.
3. **Le modèle utilisé en V1** est un service cloud gratuit (`opencode/big-pickle`) avec des données fictives ; le passage en
   local était une perspective. La V2 l'a réalisé.
4. **Équipe.** Travail de groupe de 4 : Melvin Raimbault, Lucas Huard, Jérémy Lessa, David Amaro Monteiro.
5. **Modification du PPT.** Dans `3-soutenance/Soutenance_E21_Agents_IA.pptx`, seule la slide de titre diffère du fichier du tag :
   les noms des quatre membres y ont été ajoutés (13/10/2026).
