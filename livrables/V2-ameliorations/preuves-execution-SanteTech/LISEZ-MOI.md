# Preuves d'exécution — projet d'étude SanteTech (V2)

> Pièces **réelles**, produites par le système le 12 octobre 2026 sur le projet d'étude « SanteTech » (3 documents fictifs,
> ≈ 33 Ko), avec les modèles locaux. Rien n'a été retouché à la main. Les documents d'origine ne sont pas inclus.

## Ce qu'il y a dans ce dossier

| Dossier | Contenu | Répond à |
|---|---|---|
| `livrables/` | Les livrables des étapes 1 à 7 : `00-description.md` à `06-validation.md`, `registre-risques.md` (135 risques) et son JSON, `SYNTHESE.md`, `recherches-contradictions-questions.md` | **Exemple d'exécution sur le cas** |
| `livrables/RAPPORT-CONTROLE.md`, `controles.json` | 13 contrôles numérotés par version : ce qui n'allait pas, ce qui a changé, verdict, contrôleur | **Traces des échanges entre agents** |
| `traces/chaine-2026-10-12-13-27-50.log` | Journal brut de la chaîne : routage des modèles, lots, reprises, bascule sur le modèle de secours, corrections faites par le code | **Traces des échanges entre agents** |
| `livrables/validations.json`, `decisions-analyste.json` | Les décisions de l'analyste : qui, quand, quoi, pourquoi | **Humain dans la boucle** |
| `exports/dossier-complet.html` | Le dossier d'analyse complet, avec tous les liens document → preuve → actif → risque → décision | **Traçabilité** |
| `exports/dossier-complet.pdf`, `.zip` | Le même dossier en PDF ; l'archive (HTML, PDF, livrables, tableur du registre, graphe) | **Traçabilité** |

## Comment contrôler en cinq minutes

1. Ouvrir `exports/dossier-complet.html` dans un navigateur (aucun serveur nécessaire).
2. Sommaire → **Registre** → cliquer sur un risque (`M001`) : la fiche montre l'actif, la menace, l'évaluation, le traitement
   et les preuves.
3. Cliquer sur une preuve `[E203]` : l'annexe donne le **document d'origine et l'extrait exact**.
4. Ouvrir `livrables/RAPPORT-CONTROLE.md` : les 13 contrôles, avec les points signalés.
5. Ouvrir `traces/…log` et chercher « doublon(s) fusionné(s) », « essai 2/3 », « NÉCESSITE UNE VALIDATION HUMAINE ».

## Ce que ces pièces montrent

| Constat | Où le voir |
|---|---|
| 39 actifs et 135 risques produits : 75 Critique (56 %), 35 Élevé, 13 Moyen, 12 Faible | `SYNTHESE.md`, `registre-risques.md` |
| 12 doublons d'actifs fusionnés **par le code** (39 lignes issues de 3 lots) | journal, ligne « 01-actifs.md assemblé par le programme » |
| Une étape ratée puis reprise : l'étape 2 n'écrit pas son fichier aux essais 1 et 2, réussit à l'essai 3 sur le modèle de secours | journal, « essai 1/3 », « essai 2/3 », « essai 3/3 » |
| Des citations `[E…]` qui n'existent pas dans le dossier sont **détectées et signalées** | `RAPPORT-CONTROLE.md`, « identifiants de preuve INEXISTANTS » |
| Des lignes dont deux vérificateurs divergent sont confiées à l'analyste | `RAPPORT-CONTROLE.md`, « Lignes à relire » |
| 13 contrôles : 2 conformes (étapes 6 et 7, établies par le code), 11 non conformes ou à valider par un humain | `RAPPORT-CONTROLE.md` |
| 18 décisions de l'analyste enregistrées le 12/10 (14h44 → 15h05) : 10 questions « à demander à l'entreprise », 2 réponses fournies, 2 contradictions « les deux conviennent », 4 étapes « à corriger » | `validations.json` |

## Ce qui n'est pas prouvé, et qu'il faut dire

- **Aucun des 135 risques n'est encore décidé** par l'analyste sur ce projet : les 18 décisions portent sur des questions, des
  contradictions et des étapes. Valider chaque risque (point 3 de la liste de contrôle du sujet) est un acte humain à faire.
- Les niveaux (56 % de « Critique ») sont à relire ; des citations inexistantes subsistent (elles sont signalées, pas toutes corrigées).
- La chaîne a été lancée depuis le site, avec les modèles de l'analyste ; elle n'a pas été rejouée pour comparer d'une exécution à l'autre.
