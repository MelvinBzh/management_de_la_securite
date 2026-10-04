#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur opérationnel des 5 ateliers EBIOS Risk Manager (ANSSI 2018)."""

import argparse
import sys
from pathlib import Path


BANNER = "<!-- EBIOS RM — atelier généré — à valider par l'analyste -->"
A_COMPLETER = "> _À compléter par l'analyste_"


def get_case_name(case_dir: Path, description_path: Path) -> str:
    """Récupère le nom du cas depuis 00-description.md ou depuis le nom du dossier."""
    try:
        if description_path.exists():
            content = description_path.read_text(encoding='utf-8', errors='replace')
            lines = content.splitlines()
            for line in lines:
                stripped = line.strip()
                if stripped.startswith('#'):
                    # Supprime # et espaces
                    title = stripped.lstrip('#').strip()
                    if title:
                        return title
    except Exception:
        pass
    return case_dir.name


def read_file_verbatim(path: Path) -> str:
    """Lit un fichier verbatim."""
    if not path.exists():
        return ""
    return path.read_text(encoding='utf-8', errors='replace')


def extract_section(content: str, start_marker: str = None, end_marker: str = None) -> str:
    """Extrait une section - simple approche verbatim."""
    return content


def generate_a1(cas_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère A1-cadrage-socle.md."""
    description = read_file_verbatim(cas_dir / "00-description.md")
    actifs = read_file_verbatim(cas_dir / "01-actifs.md")

    content = f"""{BANNER}

# A1 — Cadrage et socle de sécurité

> Atelier 1 : périmètre, valeurs métier, événements redoutés, socle de sécurité, parties prenantes.

## 1. Informations générales du cas

**Nom du cas :** {case_name}

{A_COMPLETER}

## 2. Périmètre (reprise de 00-description.md)

```markdown
{description}
```

## 3. Biens essentiels et valeurs métier (à compléter à partir de 01-actifs.md)

```markdown
{actifs}
```

{A_COMPLETER}

## 4. Événements redoutés

| Événement redouté | Biens concernés | Gravité visée | Justification |
|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

## 5. Socle de sécurité et mesures existantes

{A_COMPLETER}

| Mesure existante | Objectif | Efficacité | À améliorer ? |
|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

## 6. Parties prenantes

| Partie prenante | Rôle | Besoins en sécurité |
|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

{A_COMPLETER}
"""
    out_path = out_dir / "A1-cadrage-socle.md"
    out_path.write_text(content, encoding='utf-8')
    return out_path


def detect_system_type(cas_dir: Path, description: str) -> str:
    """Détecte le type de système pour suggérer sources de risque."""
    desc_lower = description.lower()
    if "web" in desc_lower or "site" in desc_lower or "boutique" in desc_lower or "public" in desc_lower:
        return "web_public"
    if "interne" in desc_lower or "intranet" in desc_lower:
        return "interne"
    if "santé" in desc_lower or "health" in desc_lower or "medical" in desc_lower or "données sensibles" in desc_lower:
        return "sante"
    return "general"


def generate_a2(cas_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère A2-sources-risque.md."""
    description = read_file_verbatim(cas_dir / "00-description.md")
    actifs = read_file_verbatim(cas_dir / "01-actifs.md")

    sys_type = detect_system_type(cas_dir, description + actifs)

    suggestions = []
    if sys_type == "web_public":
        suggestions = [
            ("Accès Internet (anonyme)", "Site web / API", "Opportuniste (scan, exploitation automatisée)", "Faible à moyen"),
            ("Accès Internet (anonyme)", "Site web / API", "Cybercriminel (monétisation)", "Moyen à élevé"),
            ("Accès Internet (anonyme)", "Site web / API", "Hacktiviste (visibilité)", "Variable"),
        ]
    elif sys_type == "interne":
        suggestions = [
            ("Accès interne (employé)", "Système interne", "Employé mécontent (rétribution/vengeance)", "Moyen"),
            ("Accès interne (employé)", "Système interne", "Erreur humaine (non intentionnelle)", "Élevé (fréquent)"),
            ("Accès externe via VPN", "Système interne", "Attaquant ayant obtenu accès", "Variable"),
        ]
    elif sys_type == "sante":
        suggestions = [
            ("Accès distant", "Données de santé", "Acteur motivé (récupération valeur)", "Élevé"),
            ("Accès interne", "Données de santé", "APT / acteur étatique (si OIV)", "Très élevé"),
            ("Accès externe", "Système", "Cybercriminel (rançongiciel)", "Élevé"),
        ]
    else:
        suggestions = [
            ("Accès externe", "Cible identifiée", "Opportuniste", "Variable"),
            ("Accès interne", "Ressources critiques", "Insider", "Moyen à élevé"),
            ("Accès via tiers/fournisseur", "Écosystème", "Fournisseur compromis", "Variable"),
        ]

    table_rows = []
    for acc, cible, motiv, niveau in suggestions:
        table_rows.append(f"| {acc} | {cible} | {motiv} | {niveau} | {A_COMPLETER} |")

    content = f"""{BANNER}

# A2 — Sources de risque

> Atelier 2 : identification des sources de risque (qui attaque, avec quels moyens/motivations).

## 1. Informations générales

**Nom du cas :** {case_name}

**Type de système détecté :** {sys_type}

{A_COMPLETER}

## 2. Tableau des sources de risque

| Accès de l'attaquant | Cible visée | Motivations | Capacité/Niveau estimé | Remarques |
|---|---|---|---|---|
""" + "\n".join(table_rows) + f"""

{A_COMPLETER}

## 3. Détails complémentaires

{A_COMPLETER}

## 4. Données d'entrée exploitées (verbatim)

### 00-description.md
```markdown
{description}
```

### 01-actifs.md
```markdown
{actifs}
```
"""
    out_path = out_dir / "A2-sources-risque.md"
    out_path.write_text(content, encoding='utf-8')
    return out_path


def generate_a3(cas_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère A3-scenarios-strategiques.md."""
    description = read_file_verbatim(cas_dir / "00-description.md")
    actifs = read_file_verbatim(cas_dir / "01-actifs.md")
    menaces = read_file_verbatim(cas_dir / "03-menaces.md") if (cas_dir / "03-menaces.md").exists() else ""

    content = f"""{BANNER}

# A3 — Scénarios stratégiques

> Atelier 3 : scénarios d'attaque via l'écosystème (fournisseurs, hébergeurs, prestataires, partenaires).

## 1. Informations générales

**Nom du cas :** {case_name}

{A_COMPLETER}

## 2. Écosystème et dépendances

{A_COMPLETER}

| Acteur de l'écosystème | Type (fournisseur/hebergeur/prestataire) | Degré de dépendance | Points d'accès au système | Mesures existantes |
|---|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

## 3. Scénarios stratégiques (chemins d'attaque)

{A_COMPLETER}

| Scénario stratégique | Acteurs concernés (écosystème) | Chemin d'attaque | Objectif de l'attaquant | Gravité estimée |
|---|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

## 4. Données d'entrée exploitées (verbatim)

### 00-description.md
```markdown
{description}
```

### 01-actifs.md
```markdown
{actifs}
```
"""
    if menaces:
        content += f"""
### 03-menaces.md
```markdown
{menaces}
```
"""
    out_path = out_dir / "A3-scenarios-strategiques.md"
    out_path.write_text(content, encoding='utf-8')
    return out_path


def generate_a4(cas_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère A4-scenarios-operationnels.md."""
    description = read_file_verbatim(cas_dir / "00-description.md")
    actifs = read_file_verbatim(cas_dir / "01-actifs.md")
    menaces = read_file_verbatim(cas_dir / "03-menaces.md") if (cas_dir / "03-menaces.md").exists() else ""
    evaluation = read_file_verbatim(cas_dir / "04-evaluation.md") if (cas_dir / "04-evaluation.md").exists() else ""

    threat_rows = [
        ("Exploitation de vulnérabilité (logicielle/config)", "Exploitation d'une faille connue", "1-4", "1-4", "(à calculer)", A_COMPLETER),
        ("Déni de service (DoS/DDoS)", "Saturation des ressources", "1-4", "1-4", "(à calculer)", A_COMPLETER),
        ("Compromission de compte / authentification", "Vol/cracking/reuse de credentials", "1-4", "1-4", "(à calculer)", A_COMPLETER),
        ("Fuite/divulgation de données", "Accès non autorisé aux données", "1-4", "1-4", "(à calculer)", A_COMPLETER),
        ("Injection (SQL/XSS/commande)", "Exécution non autorisée", "1-4", "1-4", "(à calculer)", A_COMPLETER),
        ("Escalade de privilèges", "Accès à privilèges supérieurs", "1-4", "1-4", "(à calculer)", A_COMPLETER),
    ]

    table_rows = []
    for mode_op, desc, grav, vraisem, niveau, rem in threat_rows:
        table_rows.append(f"| {mode_op} | {desc} | {grav} | {vraisem} | {niveau} | {rem} |")

    content = f"""{BANNER}

# A4 — Scénarios opérationnels

> Atelier 4 : modes opératoires techniques (scénarios opérationnels) avec évaluation gravité × vraisemblance (matrice EBIOS 4×4).

## 1. Informations générales

**Nom du cas :** {case_name}

{A_COMPLETER}

## 2. Matrice de référence (EBIOS 4×4)

{A_COMPLETER}

| Niveau | Signification |
|---|---|
| 1-2 | Faible |
| 3-5 | Moyen |
| 6-9 | Élevé |
| 10-16 | Très élevé |

*Gravité (1-4) × Vraisemblance (1-4)* — valeurs laissées à compléter selon l'analyse.

## 3. Scénarios opérationnels

| Mode opératoire technique | Description | Gravité (1-4) | Vraisemblance (1-4) | Niveau (matrice EBIOS 4×4) | Remarques |
|---|---|---|---|---|---|
""" + "\n".join(table_rows) + f"""

{A_COMPLETER}

## 4. Scénarios opérationnels détaillés

{A_COMPLETER}

| Scénario | Étapes techniques | Préconditions | Postconditions/Impact | Détectabilité |
|---|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

## 5. Données d'entrée exploitées (verbatim)

### 00-description.md
```markdown
{description}
```

### 01-actifs.md
```markdown
{actifs}
```
"""
    if menaces:
        content += f"""
### 03-menaces.md
```markdown
{menaces}
```
"""
    if evaluation:
        content += f"""
### 04-evaluation.md
```markdown
{evaluation}
```
"""
    out_path = out_dir / "A4-scenarios-operationnels.md"
    out_path.write_text(content, encoding='utf-8')
    return out_path


def generate_a5(cas_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère A5-traitement-risque.md."""
    description = read_file_verbatim(cas_dir / "00-description.md")
    actifs = read_file_verbatim(cas_dir / "01-actifs.md")
    menaces = read_file_verbatim(cas_dir / "03-menaces.md") if (cas_dir / "03-menaces.md").exists() else ""
    evaluation = read_file_verbatim(cas_dir / "04-evaluation.md") if (cas_dir / "04-evaluation.md").exists() else ""

    content = f"""{BANNER}

# A5 — Traitement du risque

> Atelier 5 : plan de traitement des risques (réduire / transférer / éviter / accepter) avec actions, responsables, échéances et risque résiduel.

## 1. Informations générales

**Nom du cas :** {case_name}

{A_COMPLETER}

## 2. Stratégies de traitement (selon skill analyse-risques)

| Stratégie | Définition | Quand l'utiliser |
|---|---|---|
| **Réduire** | Diminuer la vraisemblance ou la gravité | Risques acceptables avec mesures compensatoires |
| **Transférer** | Reporter le risque à un tiers (contrat/assurance) | Expertise/ressources externes |
| **Éviter** | Supprimer la cause (changer de solution) | Risque inacceptable, peu maîtrisable |
| **Accepter** | Accepter le risque résiduel (justifié) | Risque faible, coût > bénéfice |

## 3. Plan de traitement des risques

| Risque identifié | Niveau de risque | Traitement (réduire/transférer/éviter/accepter) | Actions proposées | Responsable | Échéance | Risque résiduel |
|---|---|---|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

{A_COMPLETER}

## 4. Suivi et validation

| Point de contrôle | Fréquence | Critère de validation |
|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

{A_COMPLETER}

## 5. Données d'entrée exploitées (verbatim)

### 00-description.md
```markdown
{description}
```

### 01-actifs.md
```markdown
{actifs}
```
"""
    if menaces:
        content += f"""
### 03-menaces.md
```markdown
{menaces}
```
"""
    if evaluation:
        content += f"""
### 04-evaluation.md
```markdown
{evaluation}
```
"""
    out_path = out_dir / "A5-traitement-risque.md"
    out_path.write_text(content, encoding='utf-8')
    return out_path


def generate_readme(case_name: str, out_dir: Path) -> Path:
    """Génère README.md."""
    content = f"""{BANNER}

# Ateliers EBIOS RM — {case_name}

Ce dossier contient les 5 ateliers de la méthode EBIOS Risk Manager (ANSSI, 2018), générés de manière opérationnelle. Ils sont **prêts à être complétés par l'analyste**.

## Déroulé des 5 ateliers

| Atelier | Fichier | Objectif |
|---|---|---|
| **A1** — Cadrage et socle | `A1-cadrage-socle.md` | Périmètre, valeurs métier, événements redoutés, socle de sécurité, parties prenantes |
| **A2** — Sources de risque | `A2-sources-risque.md` | Identification des sources de risque (accès, cibles, motivations) |
| **A3** — Scénarios stratégiques | `A3-scenarios-strategiques.md` | Scénarios d'attaque via l'écosystème (fournisseurs, hébergeurs, prestataires) |
| **A4** — Scénarios opérationnels | `A4-scenarios-operationnels.md` | Modes opératoires techniques, évaluation gravité × vraisemblance (matrice 4×4) |
| **A5** — Traitement du risque | `A5-traitement-risque.md` | Plan de traitement, actions, responsables, échéances et **risque résiduel** |

## Mode d'emploi

1. **Compléter progressivement** chaque atelier dans l'ordre A1 → A2 → A3 → A4 → A5
2. Les sections marquées `> _À compléter par l'analyste_` indiquent les éléments à renseigner
3. Les données issues des fichiers d'entrée (00-description.md, 01-actifs.md, etc.) sont reprises **verbatim** dans chaque fichier pour référence
4. **Valider** chaque atelier avant de passer au suivant
5. Le risque résiduel doit être explicitement renseigné dans l'atelier A5

## Règles d'utilisation

- Tout contenu généré est un **squelette opérationnel** à valider par l'analyste
- Les champs vides (`À compléter par l'analyste`) doivent être renseignés sur la base de l'analyse
- Les tableaux sont pré-remplis avec des suggestions à adapter au cas d'étude
"""
    out_path = out_dir / "README.md"
    out_path.write_text(content, encoding='utf-8')
    return out_path


def generate_ebios(case_dir: Path, out_dir: Path = None) -> Path:
    """Génère les 5 ateliers EBIOS RM pour un dossier d'analyse."""
    case_dir = case_dir.resolve()

    # Vérifier dossier d'entrée
    if not case_dir.exists() or not case_dir.is_dir():
        raise ValueError(f"Dossier d'analyse invalide : {case_dir}")

    description_path = case_dir / "00-description.md"
    actifs_path = case_dir / "01-actifs.md"

    if not description_path.exists():
        raise ValueError(f"Fichier requis manquant : {description_path}")

    # Déterminer répertoire de sortie
    if out_dir:
        out_dir = Path(out_dir).resolve()
    else:
        case_name_sanitized = case_dir.name.replace(' ', '-')
        out_dir = case_dir / f"ebios-{case_name_sanitized}" if False else case_dir / "ebios-ateliers"

    out_dir.mkdir(parents=True, exist_ok=True)

    case_name = get_case_name(case_dir, description_path)

    generate_a1(case_dir, case_name, out_dir)
    generate_a2(case_dir, case_name, out_dir)
    generate_a3(case_dir, case_name, out_dir)
    generate_a4(case_dir, case_name, out_dir)
    generate_a5(case_dir, case_name, out_dir)
    generate_readme(case_name, out_dir)

    return out_dir


def main():
    parser = argparse.ArgumentParser(
        description="Générateur opérationnel des 5 ateliers EBIOS Risk Manager (ANSSI 2018)"
    )
    parser.add_argument("dossier_analyse", help="Dossier d'analyse (ex. analyses/mon-cas/)")
    parser.add_argument("--out", help="Répertoire de sortie (défaut: analyses/<cas>/ebios-ateliers/)")
    args = parser.parse_args()

    try:
        result = generate_ebios(Path(args.dossier_analyse), Path(args.out) if args.out else None)
        print(f"Ateliers EBIOS RM générés dans : {result}")
        return 0
    except Exception as e:
        print(f"Erreur: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
