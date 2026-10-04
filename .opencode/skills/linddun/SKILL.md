---
name: linddun
description: Use when the system processes personal / sensitive data and you must analyze privacy threats (RGPD). "The STRIDE of privacy" (KU Leuven); 7 threat categories. Combine with the analyse-risques matrix for evaluation.
---

# LINDDUN — menaces vie privée (KU Leuven)

« Le STRIDE de la vie privée » : grille de **7 catégories de menaces** quand on traite beaucoup de **données personnelles / données sensibles** (santé, opinions, biométrie…).

## La grille

| Lettre | Menace | Définition |
|---|---|---|
| **L** | Linking (liaison) | Relier plusieurs données ou actions à une même personne |
| **I** | Identifying (identification) | Identifier une personne à partir de ses données |
| **N** | Non-repudiation | Ne plus pouvoir nier une action (négatif pour la vie privée) |
| **D** | Detecting (détection) | Déduire la présence ou l'activité d'une personne |
| **D** | Data disclosure (divulgation) | Exposer des données personnelles |
| **U** | Unawareness (méconnaissance) | La personne ne sait pas / ne contrôle pas le traitement |
| **N** | Non-compliance (non-conformité) | Ne pas respecter le RGPD ou les règles applicables |

## Usage

- Prioritaire si le cas traite des données de santé, identités, données financières, profilage.
- Chaque menace → contre-mesures RGPD-oriented : minimisation, chiffrement, anonymisation, pseudonymisation, consentement, accès limité.
- Citer l'ID `LINDDUN-X` dans `sources`.

Références : LINDDUN (KU Leuven) ; RGPD (UE 2016/679).

## Mise en œuvre opérationnelle

L'agent e21-* peut générer automatiquement un workbook LINDDUN (7 fiches + grille
DPF) à partir des fichiers d'entrée d'une analyse. À n'utiliser que si le système
traite des données personnelles : sinon la grille n'a pas d'objet.

### CLI

```bash
python3 -m tools.methodes.linddun <dossier_analyse> [--out DIR]
```

- Par défaut : `analyses/<cas>/linddun-workbook/`
- `--out` : rediriger la sortie vers un autre répertoire (explicite uniquement)

### Livrables

| Menace | Fichier | Identifiant `sources` |
|---|---|---|
| **L** — Linking | `fiche-L.md` | `LINDDUN-L` |
| **I** — Identifying | `fiche-I.md` | `LINDDUN-I` |
| **N** — Non-repudiation | `fiche-N-repudiation.md` | `LINDDUN-NR` |
| **D** — Detecting | `fiche-D-detecting.md` | `LINDDUN-D` |
| **D** — Data disclosure | `fiche-D-disclosure.md` | `LINDDUN-DD` |
| **U** — Unawareness | `fiche-U.md` | `LINDDUN-U` |
| **N** — Non-compliance | `fiche-N-conformite.md` | `LINDDUN-NC` |
| **DPF** — Data Protection by Design (art. 25) | `DPF.md` | RGPD art. 25 |

### Patron d'une fiche (sections obligatoires)

1. Bandeau `<!-- LINDDUN — fiche générée — à valider par l'analyste -->` ;
2. **Définition** (reprise de la grille ci-dessus) + propriété affectée + intuition ;
3. **Menace concrète** : questions à poser sur ce système, réponse à remplir ;
4. **Donnée / flux concerné** : colonnes **Donnée | Terme détecté | Provenance |
   Flux concerné | Accès / détenteur**, **pré-remplies** quand la description cite
   des données personnelles (nom, e-mail, adresse, téléphone, santé, paiement,
   authentification, préférences, journaux) — chaque mention est reprise avec son
   **numéro de ligne** pour rester traçable ;
5. **Contre-mesures RGPD** : minimisation, pseudonymisation, anonymisation,
   chiffrement, consentement, accès limité, durées de conservation, information
   des personnes, droits des personnes — colonnes « applicable ici ? » et
   « mise en œuvre / preuve » à remplir ;
6. Éléments de contexte RGPD (données sensibles, registre / DPO, conservation) ;
7. Reprises **verbatim** de 00-description.md et 01-actifs.md dans des blocs
   `<<<DONNÉES>>>` / `<<<FIN DONNÉES>>>` + section des lignes suspectes.

**Cas particulier :** si aucune donnée personnelle n'est détectée, chaque fiche et
`DPF.md` commencent par l'avertissement « Aucune donnée personnelle détectée —
LINDDUN moins pertinent ; justifier ou compléter ».

### Grille DPF (`DPF.md`)

Vérification « privacy by design » (RGPD art. 25) en quatre catégories, avec cases
à cocher et colonnes de preuve : **proportionnalité**, **minimisation des données**,
**durée de conservation**, **droits des personnes** (plus confidentialité et
sécurité dès la conception), et une **synthèse** (conforme ? / preuve / action /
responsable / échéance).

### Utilisation par les agents e21-*

- **Étape 3 (menaces)** : produire les fiches que sur les actifs de données
  personnelles, **sans dupliquer** les menaces STRIDE déjà traitées ; citer
  l'identifiant `LINDDUN-X` dans `sources`.
- **Étape 4 (évaluation)** : combiner avec la matrice du skill `analyse-risques`
  (vraisemblance × impact) ; les impacts réglementaires (art. 83) se chiffrent en
  sanction pécuniaire, pas en note.
- **Étape 5 (traitement)** : `DPF.md` fournit l'état de conception ; les
  contre-mesures cochées dans les fiches deviennent les actions du plan de traitement.

Le workbook est **idempotent** : il peut être régénéré à l'identique si les
fichiers d'entrée ont évolué, sans jamais modifier ces fichiers.