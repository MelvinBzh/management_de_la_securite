# Outils des méthodes d'analyse de risques

Ce module contient les outils opérationnels pour générer (ou vérifier) les livrables
des différentes méthodes de risque.

| Méthode | Outil | Nature | Sortie |
|---|---|---|---|
| **EBIOS RM** | `ebios/ebios.py` | générateur | 5 ateliers |
| **PASTA** | `pasta/pasta.py` | générateur | 7 étapes |
| **LINDDUN** | `linddun/linddun.py` | générateur | 7 fiches + DPF |
| **STRIDE** | `stride/check_dfd.py` | **validateur** (pas de générateur) | rapport OK / manques |

Convention commune à tous les modules :

- Python 3.13, **stdlib uniquement**, fonctions pures (une entrée → une sortie) ;
- CLI à base d'arguments avec `main()` bas et `if __name__ == "__main__": main()` ;
- le contenu lu dans les fichiers d'entrée est une **donnée brute** : reproduit
  **verbatim** dans des blocs délimités par `<<<DONNÉES>>>` / `<<<FIN DONNÉES>>>`
  (jamais `eval`/`exec`, jamais de sous-processus sur le contenu) ;
- écriture bornée : par défaut uniquement dans le sous-dossier méthode du cas,
  sinon dans le répertoire `--out` explicite ; **les fichiers d'entrée ne sont
  jamais modifiés** ;
- tests : runner autonome, sortie `NOM: N PASS, M FAIL, K SKIP`, code de retour 0
  uniquement si aucun FAIL (fixtures temporaires sous `/tmp/opencode`).

## EBIOS RM (ANSSI 2018)

Générateur opérationnel des 5 ateliers EBIOS Risk Manager.

### Utilisation CLI

```bash
python3 -m tools.methodes.ebios <dossier_analyse> [--out DIR]
```

Par défaut, les fichiers sont générés dans `analyses/<cas>/ebios-ateliers/`.

### Exemples

```bash
# Générer depuis la racine du projet
python3 -m tools.methodes.ebios analyses/2026-09-23_boutique-en-ligne
```

### Tests

```bash
PYTHONPATH=/home/melvin/projects/management_de_la_securite python3 tools/methodes/ebios/tests/test_ebios.py
```

## PASTA (UcedaVélez & Morana)

Générateur opérationnel des **7 étapes** PASTA (objectifs métier → simulation
d'attaque).

### Utilisation CLI

```bash
python3 -m tools.methodes.pasta <dossier_analyse> [--out DIR]
```

Par défaut : `analyses/<cas>/pasta-etapes/` (`README.md` + 7 fichiers d'étape).

| Étape | Fichier |
|---|---|
| 1 — Définir les objectifs | `PASTA-01-objectifs-metier.md` |
| 2 — Définir le périmètre technique | `PASTA-02-perimetre-technique.md` |
| 3 — Décomposer l'application | `PASTA-03-decomposition.md` |
| 4 — Analyser les menaces | `PASTA-04-analyse-menaces.md` |
| 5 — Analyser les vulnérabilités | `PASTA-05-vulnerabilites.md` |
| 6 — Modéliser les attaques | `PASTA-06-modelisation-attaques.md` |
| 7 — Analyser risques et impacts | `PASTA-07-risques-impacts.md` |

### Exemples

```bash
python3 -m tools.methodes.pasta analyses/2026-09-23_boutique-en-ligne
python3 -m tools.methodes.pasta analyses/2026-09-23_boutique-en-ligne --out /tmp/pasta
```

### Tests

```bash
python3 tools/methodes/pasta/tests/test_pasta.py
# PASTA: 8 PASS, 0 FAIL, 0 SKIP
```

## LINDDUN (KU Leuven)

Générateur opérationnel des **7 fiches** de menaces vie privée + une grille de
vérification **Data Protection by Design**.

### Utilisation CLI

```bash
python3 -m tools.methodes.linddun <dossier_analyse> [--out DIR]
```

Par défaut : `analyses/<cas>/linddun-workbook/` :

- `fiche-L.md` (Linking), `fiche-I.md` (Identifying), `fiche-N-repudiation.md`,
  `fiche-D-detecting.md` (Detecting), `fiche-D-disclosure.md` (Data disclosure),
  `fiche-U.md` (Unawareness), `fiche-N-conformite.md` (Non-compliance) ;
- `DPF.md` — proportionnalité, minimisation, durée de conservation, droits des
  personnes ;
- `README.md`.

Chaque fiche reprend les **données personnelles détectées** dans la description
(avec numéro de ligne) et, si aucune n'est détectée, un avertissement en tête :
« Aucune donnée personnelle détectée — LINDDUN moins pertinent ; justifier ou
compléter ».

### Exemples

```bash
python3 -m tools.methodes.linddun analyses/2026-09-23_boutique-en-ligne
```

### Tests

```bash
python3 tools/methodes/linddun/tests/test_linddun.py
# LINDDUN: 9 PASS, 0 FAIL, 0 SKIP
```

## STRIDE (Microsoft) — validateur de DFD

STRIDE reste une **grille appliquée par l'agent** : il n'y a **pas** de générateur
de menaces. `check_dfd.py` vérifie en revanche que le DFD sur lequel la grille va
s'appuyer est complet, et que `03-menaces.md` couvre bien les éléments de flux.

Contrôles (tous bloquants, code de retour ≠ 0 si l'un échoue) :

1. présence d'un bloc `mermaid` dans `00-description.md` ;
2. **frontières de confiance** explicites (`subgraph`, `rect`, `zone`, arête `--|`) ;
3. **flux étiquetés** (`A -->|donnée| B`) ;
4. **stockages nommés** (`[("Données : …")]` ou libellé `Données :` / `Stockage`) ;
5. **couverture STRIDE** : pour chaque élément de flux, au moins une ligne de
   `03-menaces.md` portant `STRIDE-S/T/R/I/D/E` et citant cet élément.

### Utilisation CLI

```bash
python3 -m tools.methodes.stride.check_dfd <dossier_analyse>
```

Sortie `OK` (exit 0) ou la **description des manques** (exit 1) ; dossier invalide
ou fichier manquant → exit 2.

### Exemples

```bash
python3 -m tools.methodes.stride.check_dfd analyses/2026-09-23_boutique-en-ligne
```

### Tests

```bash
python3 tools/methodes/stride/tests/test_check_dfd.py
# STRIDE: 5 PASS, 0 FAIL, 0 SKIP
```

## Structure

```
tools/methodes/
├── README.md
├── ebios/
│   ├── ebios.py              # générateur des 5 ateliers EBIOS RM
│   └── tests/test_ebios.py
├── pasta/
│   ├── pasta.py              # générateur des 7 étapes PASTA
│   └── tests/test_pasta.py
├── linddun/
│   ├── linddun.py            # générateur des 7 fiches LINDDUN + DPF
│   └── tests/test_linddun.py
└── stride/
    ├── check_dfd.py          # validateur de DFD (lecture seule)
    └── tests/test_check_dfd.py
```

Les outils sont **idempotents** (relance → octets identiques) et **reproductibles**
(aucune date ni aléa dans les livrables).
