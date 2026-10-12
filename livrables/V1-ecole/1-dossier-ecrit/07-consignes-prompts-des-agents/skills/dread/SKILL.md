---
name: dread
description: Use to prioritize already-identified threats. DREAD scores each threat on 5 criteria (1-10), the average gives the risk level. Quick triage; subjective scores. Complements STRIDE (which identifies but does not prioritize).
---

# DREAD — priorisation rapide des menaces

Système de notation (Microsoft) : chaque menace reçoit une note (de 1 à 10) sur **5 critères** ; la moyenne donne le niveau de risque.

## Les 5 critères

| Critère | Question posée |
|---|---|
| **D** Damage | Quelle est la gravité des dégâts si l'attaque réussit ? |
| **R** Reproducibility | L'attaque est-elle facile à reproduire ? |
| **E** Exploitability | Faut-il beaucoup de compétences ou de moyens ? |
| **A** Affected users | Combien de personnes/utilisateurs sont concernés ? |
| **D** Discoverability | La faille est-elle facile à trouver ? |

Niveau = moyenne des notes (`faible < 5`, `moyen 5–6`, `élevé 7–8`, `critique 9–10`).

## Limites et usage

- Notes **subjectives** (avis d'experts) → justifier chaque note.
- Idéal pour **trier rapidement** des menaces déjà listées (choix de l'ordre de traitement).
- À citer `DREAD` dans `sources`.

Microsoft a cessé de l'utiliser en interne, mais DREAD reste pratique pour un tri documenté et relisible en soutenance.