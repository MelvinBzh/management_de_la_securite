---
name: stride
description: Use to identify threats on an application/system described by a DFD (data-flow diagram). Default Microsoft grid of 6 threat categories. Best when analyzing a web application at design time. Combine with DREAD/CVSS for prioritization.
---

# STRIDE (Microsoft)

Grille de **6 catégories de menaces**, en partie le « miroir » des propriétés de sécurité (CIA + authentificité + non-répudiation + autorisation). On applique les 6 questions à **chaque élément du DFD** (acteurs, processus, stockages, flux).

## La grille

| Lettre | Menace | Question à poser | Contre-mesure type | Propriété violée |
|---|---|---|---|---|
| **S** | Usurpation (Spoofing) | Quelqu'un peut-il se faire passer pour un autre ? | Authentification forte (MFA), certificats | Authenticité |
| **T** | Falsification (Tampering) | Peut-on modifier les données ? | Signature numérique, contrôle d'intégrité | Intégrité |
| **R** | Répudiation (Repudiation) | Peut-on nier avoir fait une action ? | Journaux horodatés, signature | Non-répudiation |
| **I** | Divulgation (Information disclosure) | Des informations peuvent-elles fuiter ? | Chiffrement, contrôle d'accès | Confidentialité |
| **D** | Déni de service (DoS) | Peut-on rendre le service indisponible ? | Redondance, limitation de débit | Disponibilité |
| **E** | Élévation de privilèges (Elevation of privilege) | Peut-on obtenir plus de droits ? | Moindre privilège | Autorisation |

## Méthode d'application

1. Dessiner le **DFD** du système + frontières de confiance (passage des données entre zones : Internet → DMZ → réseau interne).
2. Les attaques se concentrent au **passage des frontières** : y chercher en priorité.
3. Appliquer STRIDE élément par élément ; noter `categorie = STRIDE-X`.
4. STRIDE dit **quoi chercher**, pas comment prioriser → compléter par DREAD ou CVSS.

## Variantes

Les trois variantes de Shostack répondent à des questions différentes. Choisir
explicitement **une** variante par itération et le noter dans `02-methodes.md`
(aucune ne se substituent l'une l'autre) :

| Variante | Grille appliquée | Question à laquelle elle répond | Quand l'utiliser |
|---|---|---|---|
| **STRIDE par élément** | Les 6 catégories sur **chaque** élément du DFD (acteurs, processus, stockages, flux) | « Que peut-on attaquer ici ? » | Cartographie exhaustive, DFD stable, avant conception détaillée |
| **STRIDE par interaction** | Les 6 catégories sur **chaque flux** (et non sur les nœuds) | « Que se passe-t-il sur ce passage de données ? » | Ciblage sur le **passage des frontières**, là où les attaques se concentrent |
| **STRIDE par interface** | Les 6 catégories sur **chaque interface d'entrée/sortie** (API, formulaire, fichier, web service) | « Que peut-on envoyer / demander par cette interface ? » | Audit d'exposabilité, revue de code, Pentest, API / apps web |

Règle de choix : **par interaction** dès que le DFD contient des frontières de
confiance explicites (le DFD décrit des *passages*), **par élément** pour un
inventaire large, **par interface** pour un audit technique ciblé.

## Double-contrôle du DFD (à faire avant d'appliquer la grille)

Un DFD incomplet produit une analyse STRIDE fausse : les menaces sont alors
attachées à des éléments qui n'existent pas, ou à aucun élément du tout. Avant
d'appliquer la grille, vérifier point par point :

- [ ] **Frontières de confiance explicites** — `subgraph` / `rect` / `zone` nommés (« Internet », « DMZ », « Prestataires »), pas seulement des flèches ; sans frontière nommée, les notions de passage F1, F2… n'existent pas.
- [ ] **Flux étiquetés** — `A -->|donnée transportée| B` : sans étiquette, on ne sait pas *ce qui* circule, donc ni sa sensibilité ni les menaces de divulgation.
- [ ] **Stockages nommés** — formes `[("…")]` (cylindre) ou libellé `Données : …` ; les stockages concentrent les fuites massives et doivent figurer au même titre que les processus.
- [ ] **Propriétés CIA+ par élément** — pour chaque élément, préciser la propriété menacée *et* la propriété non menacée : « telle donnée : confidentialité », « tel flux : intégrité + authentification ». Une propriété par élément donne une ligne de menace possible ; zéro propriété = un angle mort.

**Vérification outillée** (lecture seule, n'écrit rien) :

```bash
python3 -m tools.methodes.stride.check_dfd analyses/<cas>
```

Le validateur contrôle les 4 premiers points **et** la couverture STRIDE : pour
chaque élément de flux, il exige au moins une ligne `STRIDE-S/T/R/I/D/E` dans
`03-menaces.md` qui le cite. Sortie `OK` (exit 0) ou **description des manques**
(exit 1). Un échec du validateur n'est pas un échec de l'analyse : c'est un DFD ou
un `03-menaces.md` à compléter avant d'aller plus loin.

Référence : Microsoft STRIDE ; A. Shostack, *Threat Modeling: Designing for Security* (2014) [source autorisée].