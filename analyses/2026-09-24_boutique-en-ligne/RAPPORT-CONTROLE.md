# Rapport de contrôle (re-contrôle) — Étape 1 (existant & actifs) · cas « ShoPix »

> Agent `e21-controle` (garde-fous) — **re-contrôle** du **2026-09-24** après reprise.
> Objet : `00-description.md` et `01-actifs.md` avant publication (v2, corrections suite au REJET du 1er contrôle).
> Motif initial : « ~500 €/semaine » non dérivable du cas + contradiction interne A-07.
> Cadre IA : skill `garde-fous-ia` (hallucination, injection, fuite, excès d'autonomie, empoisonnement, dépendance) + **`ANSSI-IA-GEN`** (*Recommandations de sécurité pour un système d'IA générative*, ANSSI 2024) — familles de menace : **manipulation** (injection), **infection des données** (empoisonnement), **exfiltration** (fuite) ; contrôle humain et journalisation exigés.
> Cadre méthode : `ANSSI-CARTO-SI` (ancrage de l'étape 1), grille de contrôle du skill `registre-risques`.

## Verdict global : **OK**

Les deux motifs de REJET du 1er contrôle ont été corrigés : les valeurs économiques sont désormais intégralement dérivées du chiffre sourcé (~15 000 €/trimestre) et la contradiction A-07 est levée. Les 5 WARN du 1er contrôle sont résolus (F5/F6 dessinées, placement FTP clarifié, rôles harmonisés, typo corrigée). Re-contrôle des sources/injection/anonymisation/format : conforme.

---

## Grille de contrôle (re-contrôle ciblé)

| # | Contrôle | Statut | Détail |
|---|---|---|---|
| 1 | **Valeurs CA dérivables** (motif de REJET n°1) | **OK** | Plus aucune « ~500 €/semaine » / « ~1 500 €/semaine » présentée comme donnée du cas dans les deux fichiers. Restent 2 mentions **contextuelles** (`01-actifs.md` l. 6 et l. 70) explicitement étiquetées « hypothèse initiale écartée — non dérivable », ce qui est la trace correcte du contrôle. Dérivations homogènes partout : **≈ 1 150 €/semaine** (15 000 ÷ 13) et **≈ 3 450 €/semaine en pic** (×3) — `00-description.md` l. 23 ; `01-actifs.md` A-01 (l. 27), A-13 (l. 49), §4 (l. 60), §5 (l. 70). |
| 2 | **Cohérence A-07** (motif de REJET n°2) | **OK** | Recalculé à partir des valeurs dérivées : 2 jours de CA perdus = (1 154 ÷ 7) × 2 ≈ **330 € hors pic** ; (3 462 ÷ 7) × 2 ≈ **990 € en pic**. `A-07` (l. 33) indique les deux valeurs et précise la base (« CA hebdomadaire dérivé ÷ 7 ; période de l'incident 2025 non précisée par le cas ») : contradiction levée, approximation honnête. |
| 3 | **F5 et F6 dans le Mermaid ET le tableau** (WARN n°1) | **OK** | Sous-graphe `F6` (« Espace FTP de sauvegarde — même hébergeur HostPlanet · hors VM applicative », l. 87-89) et sous-graphe `F5` (« poste local admin », l. 92-94) présents dans le schéma ; flèche `BACK --> FTP` tracée ; les deux frontières figurent au tableau (l. 123-124). **Placement FTP conforme** : F6 est un sous-graphe propre, **hors du sous-graphe F4 (prestataires externes)** et le tableau précise « Non un prestataire : même zone de confiance hébergeur » (l. 124). Cohérent avec `etude-de-cas.md` §5 (flux 4). |
| 4 | **Cohérence rôles A-09/A-10** (WARN n°3) | **OK** | `01-actifs.md` : A-09/A-10 classés **une seule fois** en §3 « Actifs intangibles et services » (rôles, l. 45-46), rattachés à la **vue métier** dans le mapping §1 (l. 16). Aucun doublon dans le tableau des tangibles (§2). Harmonisé `00-description.md` §1 (rôles, l. 25-34). |
| 5 | **Typo « Eléments » → « Éléments »** (WARN n°4) | **OK** | Accentué partout : `00-description.md` l. 117 (« Éléments »), `01-actifs.md` l. 71 (« Éléments »). Aucune occurrence « Eléments » dans les deux fichiers contrôlés (seule reste dans ce rapport, comme historique). |
| 6 | **Sources vérifiables** | OK | `ANSSI-CARTO-SI` référencé dans `knowledge_base/README.md` ; `etude-de-cas.md` citée pour chaque fait (CA, incidents, dépendances, périmètre) ; RGPD art. 33/83 en mention textuelle signalée « hors index » ; skills `schemas-diagrammes`/`analyse-risques` existants. Placeholder `CVE-2023-XXXX` conservé **tel quel** (celui du cas, §9) — aucune CVE inventée (anti-hallucination). |
| 7 | **Injection / manipulation** (famille `ANSSI-IA-GEN`) | OK | Recherche de marqueurs (« ignore tes instructions », instructions cachées, contenu hostile) dans les deux fichiers : **aucune occurrence**. Aucune entrée traitée comme instruction. Les occurrences trouvées par la recherche automatisée se situent uniquement dans les rapports de contrôle eux-mêmes (citation des marqueurs contrôlés). |
| 8 | **Anonymisation / exfiltration** (famille `ANSSI-IA-GEN`) | OK | Aucun e-mail, IP, téléphone, nom réel. Seuls les noms fictifs du cas (ShoPix, Mélanie, HostPlanet, PayFlow, MailJet, `shopix.example` — TLD réservé). Encart « Données fictives » en tête des deux fichiers. |
| 9 | **Format `registre-risques`** | OK | `donnees_personnelles: true` présent (`00-description.md` l. 13) ; 19 actifs A-01…A-19 avec ID/type/description/valeur/sensibilité/DICT ; tableaux à colonnes homogènes ; `valide_par` non requis à l'étape 1 (registre final uniquement, vide avant validation humaine). |
| 10 | **Mermaid** (WARN n°5) | OK | Sous-graphes `F1`-`F6` équilibrés, nœuds et arcs cohérents, syntaxe valide (revue manuelle complète) ; étiquettes avec `<br/>` et caractères spéciaux entre guillemets OK. Rendu effectif (`mermaid-cli`) toujours recommandé avant publication définitive du dossier, non exécutable dans l'environnement de contrôle. |

### Calculs de référence (dérivation depuis l'étude de cas — inchangés)

- CA trimestriel du cas : **~15 000 €/trimestre** → 15 000 ÷ 13 ≈ **1 154 €/semaine** en période normale.
- Pic ×3 (nov–déc) : ≈ **3 462 €/semaine**.
- 2 jours de commandes perdus : ≈ **330 €** hors pic, ≈ **989-990 €** en pic.
- L'ancienne hypothèse « 500 €/semaine » (= 26 000 €/an) est incompatible avec le chiffre du cas — à juste titre écartée.

---

## Corrections constatées (reprise de l'agent de l'étape 1)

1. `00-description.md` §1 (l. 23) : « ~500 €/semaine normal, ~1 500 €/semaine en pic » → **« ≈ 1 150 €/semaine (15 000 ÷ 13) … ≈ 3 450 €/semaine en pic (×3) »** — fait.
2. `01-actifs.md` l. 6, A-01 (l. 27), A-13 (l. 49), l. 60, l. 70 : mêmes valeurs, et l. 70 rectifiée (ne prétend plus que « 500 €/semaine » est une donnée du cas ; la trace « hypothèse écartée » est conservée) — fait.
3. A-07 (l. 33) : harmonisé sur le calcul dérivé (≈ 330 € / ≈ 990 €, base explicitée) — fait.
4. F5 et F6 ajoutées au Mermaid ; placement FTP sorti du sous-graphe prestataires et justifié « même hébergeur » — fait.
5. Rôles A-09/A-10 harmonisés (mapping vue métier ↔ §3) — fait.
6. « Eléments » → « Éléments » — fait.

## Points WARN résiduels (acceptés, non bloquants — signalés à l'orchestrateur)

- **Arrondi du langage budgétaire** (`00-description.md` l. 23) : « plusieurs dizaines de milliers d'euros si arrêt prolongé » est plus proche d'un scénario maximal (perte de la majeure partie de la saison de fêtes en pic, ≈ 27-31 k€) que d'un arrêt court. Défendable mais à surveiller dans les étapes suivantes (3-5) pour éviter une dérive d'amplification lors de la quantification d'impact.
- **Mermaid** : revue syntaxique OK, mais un rendu effectif est fortement recommandé avant publication définitive (non disponible dans l'environnement de contrôle).
- **Poste local admin (F5)** : reste non décrit par le cas → signalé « à confirmer avec le dirigeant » (l. 69 de `01-actifs.md`) ; à ré-évaluer en étape 6 (validation humaine).

## Éléments complémentaires

- **`CONTRE-MESURES.json`** : non applicable à cette étape — la chaîne n'a pas encore produit de contre-mesures (étapes 4-5). Sera contrôlé sur `05-traitement.md`.
- **`risques_ia.md`** : récapitulatif des contrôles IA mis à jour avec le statut final (fichier joint).
- **Validation humaine** : le présent verdict OK ne remplace pas la validation par le dirigeant/analyste (humain dans la boucle — `ANSSI-IA-GEN`, contrôle humain des sorties) ; l'étape 6 reste la porte de validation formelle.

## Journalisation (garde-fous / `ANSSI-IA-GEN`)

- 1er contrôle : 2026-09-24 → verdict **REJET** (2 motifs bloquants), enregistré dans ce rapport (historique ci-dessous).
- **Re-contrôle : 2026-09-24 → verdict OK** (10/10 contrôles, 0 REJET, 0 WARN bloquant, 3 WARN d'information).
- Aucune écriture de contenu dans les fichiers de sortie (règle : contrôler, ne pas réécrire) — seul ce rapport et `risques_ia.md` ont été mis à jour.

---

## Historique — 1er contrôle (2026-09-24, verdict REJET)

- **Sources vérifiables** : « ~500 €/semaine » / « ~1 500 €/semaine » présentés comme donnée du cas → contredit le chiffre sourcé « ~15 000 €/trimestre ».
- **Cohérence interne** : contradiction entre l'hypothèse 500/1 500 €/semaine et l'estimation « 2 jours ≈ 1 000 € » de A-07 (recalcul correct ≈ 330/990 €).
- **Typo** : « Eléments » (sans accent).
- **WARN** : F5 non dessinée ; placement FTP dans F4 ; classification A-09/A-10 ; rendu Mermaid à confirmer.