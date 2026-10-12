# Plan de soutenance V2 — 45 minutes

> Support : `Soutenance_E21_V2.pptx` (31 slides, notes de présentation dans chaque slide).
> Base : la soutenance V1 (29 slides, `V1-ecole/3-soutenance/`). La V2 garde ce qui est resté vrai, corrige ce qui ne l'est plus,
> et ajoute 16 slides pour la V2.

## 1. Ce qui change par rapport à la V1

| | V1 | V2 |
|---|---|---|
| Slides | 29 | 31 |
| Gardées telles quelles | — | 8 (contexte, cas ShoPix, méthode, architecture V1, agents, résultat, décision, point clé « format ≠ contenu ») |
| Retouchées | — | 7 (couverture, plan, limites, injection, feuille de route, conclusion, merci) |
| Nouvelles | — | 16 (cadre, déplacement, architecture, chaîne, connaissance, preuve, modèles, contrôles, validation, mise à jour, essai réel, export, résultats, limites, sécurité, démonstration) |
| Retirées | — | 14 slides V1 devenues fausses ou redondantes (modèle unique cloud, traçabilité GitHub seule, suite T-01…T-11 détaillée, benchmark, audit…) |
| Étiquettes | `01 ·` à `08 ·` | `V1 ·` (école) ou `V2 ·` (hors cours) sur chaque slide |

## 2. Déroulé

### Partie 0 — Cadre (0 → 2 min)

| # | Slide | Message | Min |
|---|---|---|---|
| 1 | Couverture | La V1 rendue en cours, la V2 hors cours ; le modèle propose, le code vérifie, l'humain décide | 0,5 |
| 2 | Plan | Six parties | 0,5 |
| 3 | **Cadre** (nouvelle) | Frontière : le 24 septembre, tag `ecole-2026-09-24` ; 640 → 22 500 lignes | 1 |

### Partie 1 — Rappel de la V1 (2 → 10 min)

| # | Slide | Message | Min |
|---|---|---|---|
| 4 | Contexte | Pourquoi des agents : méthode exigeante, peu reproductible, coûteuse | 1 |
| 5 | Cas ShoPix | Terrain de test fictif | 1 |
| 6 | Méthode E21 | Six étapes, quatre traitements | 1 |
| 7 | Architecture V1 | Orchestrateur, chaîne, contrôleur | 1 |
| 8 | 12 agents | Un rôle, une sortie chacun | 1 |
| 9 | Résultat ShoPix | 14 risques validés | 1 |
| 10 | Décider et revenir sur une décision | R-13 retenu, R-14 modifié, `valide_par` humain | 1 |
| 11 | **Limites V1 → V2** (retouchée) | Chaque limite annoncée a un statut | 1 |

### Partie 2 — V2 : architecture et preuves (10 → 22 min)

| # | Slide | Message | Min |
|---|---|---|---|
| 12 | **Le déplacement** | De la consigne au code : le modèle propose, le programme vérifie | 2 |
| 13 | **Architecture V2** | Quatre blocs, tout en local | 2 |
| 14 | **La chaîne** | Qui fait quoi à chaque étape | 2 |
| 15 | **Dossier de connaissance** | 97 % de faits exacts ; contradictions bruyantes (60–70 %) | 2 |
| 16 | **La preuve** | Chaque phrase renvoie à un extrait ; une citation inexistante est signalée | 2 |
| 17 | **Modèles** | Un modèle par rôle, mesuré ; écartés après mesure | 1 |
| 18 | Un format valide n'est pas un contenu juste (V1, gardée) | La leçon de l'audit, qui justifie le contrôle par le code | 1 |

### Partie 3 — V2 : validation et mise à jour (22 → 32 min)

| # | Slide | Message | Min |
|---|---|---|---|
| 19 | **Contrôles par le code** | 15 · 13 · 1 références retirées ; niveau calculé ; registre en 2 min | 2 |
| 20 | **Validation humaine** | Page 4, validée ; décisions conservées | 2 |
| 21 | **Mise à jour** | 13 minutes, le reste identique à l'octet près | 3 |
| 22 | **Essai réel** | Trois défauts trouvés que les tests ne voyaient pas, corrigés | 2 |
| 23 | **Traçabilité livrée** | Dossier unique avec tous les liens | 1 |

### Partie 4 — Résultats, limites, sécurité (32 → 40 min)

| # | Slide | Message | Min |
|---|---|---|---|
| 24 | **Résultats** | Nordval 151 risques, SanteTech 135 ; niveaux à relire | 2 |
| 25 | Injection de prompt (retouchée) | T-11 exécuté, limite : pas de modèle en direct | 2 |
| 26 | **Ce qui ne marche pas** | Six limites avec leur chiffre | 2 |
| 27 | **Sécurité du système** | Ce qui est traité, ce qui ne l'est pas | 2 |

### Partie 5 — Démonstration et conclusion (40 → 45 min)

| # | Slide | Message | Min |
|---|---|---|---|
| 28 | Feuille de route (retouchée) | Réalisé / à faire | 1 |
| 29 | Conclusion (retouchée) | Fiable par construction, traçable à la phrase, humain décideur | 1 |
| 30 | **Démonstration** | Huit minutes, rien de long en direct, plan B | (parcours) |
| 31 | Merci | Questions | — |

> La démonstration (slide 30) se joue **avant** la conclusion si le temps le permet : 8 minutes sur le site, avec un projet déjà
> analysé et un dossier complet déjà exporté. Voir `EXPLICATIONS-DU-PROJET.md`, partie 7.

## 3. Messages clés

1. **Le modèle propose, le code vérifie, l'humain décide.**
2. **Une preuve pour chaque phrase**, vérifiée mot pour mot.
3. **Ajouter un document ne casse rien** : 13 minutes, lignes inchangées identiques à l'octet près.
4. **On dit ce qui ne marche pas, avec le chiffre** : « Critique » 48–56 %, doublons, citations inexistantes, validation lourde.
5. **La sécurité du site n'est pas faite** : aucune donnée réelle, pas d'usage réel avant durcissement.

## 4. Ce qu'il faut préparer avant le jour J

| À faire | Pourquoi |
|---|---|
| Un projet déjà analysé, ouvert sur la page ③ | Aucune attente de calcul pendant la démo |
| Le dossier complet exporté en HTML, sur le poste | Plan B sans serveur |
| Un document « à ajouter » prêt, et le résultat de sa mise à jour déjà calculé | Montrer `MISE-A-JOUR.md` sans attendre 13 minutes |
| La carte graphique libre | Évite une lenteur imprévue |
| Le document piégé et la commande de test d'injection (si on tente la démo en direct) | Combler la limite de la slide 25 |
| Les chiffres de la partie 9 de `EXPLICATIONS-DU-PROJET.md` relus | Citer sans hésiter |

## 5. Pièges à éviter à l'oral

- Ne pas dire « l'IA analyse les risques » : dire « le système **prépare, vérifie et trace**, l'analyste **décide** ».
- Ne pas affirmer que le test d'injection a été fait avec le modèle en direct : il a été fait sur l'ingestion et la commande, **sans appel du modèle**.
- Ne pas présenter les niveaux de risque comme fiables : ils sont **à relire**.
- Ne pas laisser croire que le site est sécurisé.
- Ne pas attribuer à la V2 ce qui est de la V1, ni l'inverse : la frontière est le 24 septembre.
