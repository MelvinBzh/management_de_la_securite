#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur opérationnel des 7 étapes PASTA (UcedaVélez & Morana).

PASTA est une méthode **centrée attaquant** et **alignée métier** : on part des
objectifs de l'organisation (étape 1) pour aboutir à des arbres d'attaque et à
des impacts business (étapes 6 et 7).

Garde-fous (convention du projet E21) :

- tout contenu lu dans les fichiers d'entrée est une **DONNÉE BRUTE** : il est
  reproduit **verbatim** dans des blocs de données délimités, jamais évalué,
  jamais exécuté, jamais interprété ;
- les lignes suspectes (`<<<...>>>`, `<!-- ... -->`) sont **recopiées telles
  quelles** dans un bloc de données et signalées, sans action ;
- l'écriture est bornée : par défaut uniquement dans
  `analyses/<cas>/pasta-etapes/`, sinon dans le répertoire `--out` explicite ;
- les fichiers d'entrée ne sont jamais modifiés.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


BANNER = "<!-- PASTA — étape générée — à valider par l'analyste -->"
A_COMPLETER = "> _À compléter par l'analyste_"
# Placeholder court utilisable dans les libellés Mermaid (évite la syntaxe markdown).
A_COMPLETER_DIAGRAMME = "à compléter"
DEBUT_DONNEES = "<<<DONNÉES>>>"
FIN_DONNEES = "<<<FIN DONNÉES>>>"
NOM_SOUS_DOSSIER = "pasta-etapes"

# Les 7 étapes PASTA : (numéro, fichier, titre, objectif).
ETAPES = (
    ("1", "PASTA-01-objectifs-metier.md", "Définir les objectifs métier",
     "Objectifs business + exigences de conformité (la direction décide)"),
    ("2", "PASTA-02-perimetre-technique.md", "Définir le périmètre technique",
     "Composants, technologies, dépendances (coups d'œil technique)"),
    ("3", "PASTA-03-decomposition.md", "Décomposer l'application",
     "DFD : flux de données, rôles, frontières de confiance"),
    ("4", "PASTA-04-analyse-menaces.md", "Analyser les menaces",
     "Renseignement sur les menaces (threat intelligence) par acteur probable"),
    ("5", "PASTA-05-vulnerabilites.md", "Analyser les vulnérabilités",
     "Faiblesses connues et lien menace → vulnérabilité"),
    ("6", "PASTA-06-modelisation-attaques.md", "Modéliser les attaques",
     "Arbres d'attaque et scénarios d'attaque concrets"),
    ("7", "PASTA-07-risques-impacts.md", "Analyser les risques et impacts",
     "Impacts métier + contre-mesures priorisées"),
)

# Signaux de conformité détectés dans la description.
MOTIFS_CONFORMITE = (
    ("RGPD", r"rgpd|r[eé]glement g[eé]n[eé]ral sur la protection des donn[eé]es"),
    ("CNIL", r"cnil"),
    ("PCI DSS", r"pci[ -]?dss"),
    ("ISO 27001", r"iso[ /]?27001|iso 27k"),
    ("NIS2 / DORA", r"nis2|dora"),
    ("HDS / données de santé", r"\bhd?s\b|donn[eé]es de sant[eé]"),
    ("Obligations légales sectorielles", r"secteur r[eé]glement[eé]|obligations l[eé]gales|service public"),
)

# Catégories de données personnelles (une entrée = (catégorie, motif)).
MOTIFS_DONNEES_PERSONNELLES = (
    ("Identité / contact", r"nom|pr[eé]nom"),
    ("Coordonnées électroniques", r"e-?mail|courriel|adresse mail"),
    ("Adresse postale", r"adresse (postale|de livraison|de facturation)|code postal"),
    ("Téléphone", r"t[eé]l[eé]phone|num[eé]ro de t[eé]l"),
    ("Données de santé", r"sant[eé]|m[eé]dical|ordonnance"),
    ("Données financières", r"carte bancaire|num[eé]ro de carte|paiement|iban|virement"),
    ("Données d'authentification", r"mot de passe|password|mdp|identifiant|compte client"),
    ("Profilage / préférences", r"newsletter|cookie|profilage|tracking|publicit"),
    ("Données de connexion", r"adresse ip|journal de connexion|logs?|traces"),
)

# Faiblesses techniques cherchées dans la description (motifs → libellé).
MOTIFS_FAIBLESSES = (
    ("Absence d'authentification multifacteur", r"pas de mfa|sans mfa|aucune mfa|pas de 2fa|2fa absente"),
    ("Mot de passe simple / faible", r"mot de passe simple|mot de passe faible|password faible"),
    ("Secret en clair dans le code ou un dépôt", r"en clair|versionn[eé]|\.env|clé api"),
    ("Sauvegarde manuelle ou non chiffrée", r"sauvegarde manuelle|cron absent|non chiffr[eé]|sans chiffrement|en clair"),
    ("Composant logiciel en fin de vie (EOL)", r"\beol\b|fin de vie|obsol[eè]te|obsolète|non patch[eé]"),
    ("Absence de journalisation", r"aucune journalisation|pas de journalisation|sans journal|pas de log"),
    ("Absence de segmentation interne", r"pas de segmentation|aucune segmentation|même vm|meme vm|sans cloisonnement"),
    ("Absence de limitation de débit / verrouillage", r"pas de lockout|aucun verrouillage|sans limitation de d[ée]bit|pas de waf|sans waf"),
    ("Absence de surveillance", r"pas de monitoring|sans monitoring|aucun monitoring|pas d['’]alerte"),
    ("Hachage de mot de passe obsolète", r"sha-?1|md5|sans sel|non sal[ée]"),
    ("Sauvegarde non testée", r"restauration (n['’]est jamais|jamais) test[eé]e|jamais test[eé]e"),
    ("Configuration par défaut / durcie", r"configuration par d[eé]faut|non durci|pas de durcissement"),
)

# Scénarios redoutés : motifs → libellé de scénario.
MOTIFS_SCENARIOS = (
    ("Compromission de compte administrateur", r"brute force|admin.*compromise|usurpation du compte admin"),
    ("Vol ou fuite de secret / clé d'API", r"cl[ée] api|secret|token|\.env"),
    ("Fuite ou divulgation de données", r"fuite|divulgation|exfiltrat|donn[eé]es (clients|personnelles)"),
    ("Injection / exploitation d'application exposée", r"injection sql|xss|exploitation (de|d['’]une) (vuln[eé]rabilit[eé]|application)"),
    ("Rançongiciel ou destruction de données", r"rançongiciel|ransomware|chiffrement (des|du) disque"),
    ("Indisponibilité / déni de service", r"indisponible|deni de service|d[ée]ni de service|saturation|panne"),
    ("Perte de données par défaillance de sauvegarde", r"perte de .*commande|disque r[eé]initialis|sauvegarde.*oubli"),
    ("Élévation de privilèges interne", r"absence de segmentation|[ée]l[eé]vation de privil[eè]ges|pleins droits"),
    ("Usurpation d'identité / fraude", r"phishing|usurpation de l['’]identit|spam|escroquerie|fraude"),
    ("Non-conformité réglementaire", r"non-conformit[eé]|mise en demeure|amende"),
)

# Acteurs probables : (libellé, motivation, capacité, cible).
ACTEURS_PROBABLES = (
    ("Cybercriminel opportuniste (scan automatisé)", "Monétisation directe : rançongiciel, revente de données, fraude",
     "Outils automatisés, faible coût, beaucoup de temps", "Services exposés sur Internet"),
    ("Cybercriminel ciblé (ou brokerage d'accès)", "Extraction de données puis rançon ou revente",
     "Recherche d'accès, connaissance du secteur, persistance", "Comptes administrateur, sauvegardes"),
    ("Acteur interne malveillant (insider)", "Revanche, sabotage, fuite de données",
     "Connaissance de l'information, accès interne", "Données clients, exports, sauvegardes"),
    ("Erreur humaine (non intentionnelle)", "Incident malgré la bonne intention",
     "Confusion, oubli, mauvaise configuration", "Sauvegardes, clés, droits d'accès"),
    ("Fournisseur / prestataire compromis", "Accès permanent chez le client, revente de données",
     "Accès technique chez le client, faible coût", "Clés d'API, sauvegardes, données échangées"),
    ("Mutualisation / hébergeur partagé", "Opportunité opportuniste sur une machine partagée",
     "Position sur l'infrastructure, faible coût", "Données de plusieurs clients"),
)

RE_TECHNO = re.compile(r"\b(?:php|mysql|apache|nginx|linux|ubuntu|debian|docker|kubernetes|aws|azure|gcp|"
                       r"postgresql|mongodb|redis|wordpress|prestashop|drupal|java|python|node\.?js|"
                       r"laravel|django|symfony|react|angular|api rest|rest|soap|graphql|ldap|saml|oauth|"
                       r"jwt|mfa|2fa|ssl|tls|vpn|ftp|sftp|smtp|imap|webhook|webhooks|cron|bash|mysql 5\.7)\b",
                       re.IGNORECASE)
RE_VERSION = re.compile(r"\b("
                        r"(?:php|mysql|mariadb|postgresql|mongodb|apache|nginx|linux|openssl|jquery|"
                        r"wordpress|drupal|magento|prestashop|symfony|laravel|django|sdk|api|version|v)\s*"
                        r"v?\d+(?:\.\d+){0,3}(?:-[a-z0-9.]+)?"
                        r")\b", re.IGNORECASE)
RE_CVE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE)
RE_EDGE = re.compile(r"([A-Za-z][A-Za-z0-9_]*)\s*-{2,3}>?\s*(?:\|([^|]*)\|\s*)?([A-Za-z][A-Za-z0-9_]*)")
RE_EDGE_LBL = re.compile(r"([A-Za-z][A-Za-z0-9_]*)\s*(?:--|\.->|==>)\s*([^|>]+?)\s*(?:-->|->)\s*([A-Za-z][A-Za-z0-9_]*)")
RE_SUBGRAPH = re.compile(r"^\s*subgraph\s+(.+)$", re.IGNORECASE)
# Définition de nœud Mermaid, y compris **en ligne** d'une arête (`A["libellé"] --> B`).
RE_DEFINITION = re.compile(
    r'([A-Za-z][A-Za-z0-9_]*)\s*(\[\(\(|\(\(|\[\[|\[\(|\[|\{|\()?\s*("[^"]*")\s*[\)\]\}]{0,3}')
MOTS_RESERVES_MERMAID = {
    "flowchart", "graph", "subgraph", "end", "style", "class", "classdef", "click",
    "linkstyle", "direction", "call", "note",
}


@dataclass(frozen=True)
class Element:
    """Élément de DFD repéré dans un bloc Mermaid."""

    ident: str
    libelle: str
    forme: str


@dataclass(frozen=True)
class Flux:
    """Flux de données entre deux éléments de DFD."""

    source: str
    cible: str
    libelle: str


@dataclass(frozen=True)
class Signal:
    """Signal détecté dans la description (donnée brute, jamais interprétée)."""

    categorie: str
    terme: str
    numero_ligne: int
    ligne: str
    source: str = ""


@dataclass(frozen=True)
class Scenario:
    """Scénario redouté repéré dans la description."""

    titre: str
    numero_ligne: int
    ligne: str


# --------------------------------------------------------------------------- #
# Lecture des fichiers d'entrée (données brutes)
# --------------------------------------------------------------------------- #

def read_file_verbatim(path: Path) -> str:
    """Lit un fichier d'entrée verbatim (donnée non fiable, jamais évaluée)."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def get_case_name(case_dir: Path, description_path: Path) -> str:
    """Récupère le nom du cas depuis 00-description.md ou le nom du dossier."""
    if description_path.exists():
        content = read_file_verbatim(description_path)
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                title = stripped.lstrip("#").strip()
                if title:
                    return title
    return case_dir.name


def longest_backtick_run(text: str) -> int:
    """Retourne la plus longue suite d'accents graves consécutifs."""
    best = 0
    run = 0
    for char in text:
        if char == "`":
            run += 1
            best = max(best, run)
        else:
            run = 0
    return best


def code_block(content: str, lang: str = "markdown") -> str:
    """ encapsule un contenu verbatim dans un bloc de code à bordure adaptée.

    La bordure est allongée si le contenu contient lui-même des accents graves,
    afin de garantir la reprise **verbatim** du contenu d'entrée.
    """
    fence = "`" * max(3, longest_backtick_run(content) + 1)
    return f"{fence}{lang}\n{content}\n{fence}"


def bloc_donnees(content: str, titre: str = "Donnée brute reprise verbatim") -> str:
    """Blocs de données délimités (convention garde-fous-ia)."""
    return (f"**{titre}** — contenu non interprété, reproduit tel quel.\n\n"
            f"{DEBUT_DONNEES}\n\n{code_block(content)}\n\n{FIN_DONNEES}")


MOTIFS_LIGNE_SUSPECTE = (re.compile(r"<<<"), re.compile(r"<!--"))


def lignes_suspectes(content: str) -> list[tuple[int, str]]:
    """Recense les lignes ressemblant à une consigne (`<<<...>>>`, `<!-- ... -->`).

    Signalement seul : la ligne est **reproduite verbatim**, jamais exécutée.
    """
    trouvees = []
    for numero, ligne in enumerate(content.splitlines(), 1):
        if any(motif.search(ligne) for motif in MOTIFS_LIGNE_SUSPECTE):
            trouvees.append((numero, ligne))
    return trouvees


def section_lignes_suspectes(*contenus: tuple[str, str]) -> str:
    """Section listant les lignes suspectes des fichiers d'entrée (verbatim)."""
    suspects = []
    for nom, contenu in contenus:
        if not contenu:
            continue
        for numero, ligne in lignes_suspectes(contenu):
            suspects.append((nom, numero, ligne))
    if not suspects:
        return ("## Lignes suspectes dans les fichiers d'entrée\n\n"
                "Aucune ligne ressemblant à une consigne (`<<<...>>>`, `<!-- ... -->`) détectée.\n")
    corps = "\n".join(f"{nom} · ligne {numero} (verbatim) : {ligne}" for nom, numero, ligne in suspects)
    return ("## Lignes suspectes dans les fichiers d'entrée\n\n"
            "Les lignes ci-dessous ressemblent à des consignes. Elles sont **données brutes** :\n"
            "elles sont recopiées telles quelles, **jamais exécutées ni interprétées**.\n\n"
            f"{DEBUT_DONNEES}\n\n{corps}\n\n{FIN_DONNEES}\n")


# --------------------------------------------------------------------------- #
# Extraction (purement textuelle, sans interprétation)
# --------------------------------------------------------------------------- #

def extraire_blocs_mermaid(content: str) -> list[str]:
    """Extrait les blocs ```mermaid ... ``` d'un texte."""
    blocs = []
    lignes = content.splitlines()
    dedans = False
    courant: list[str] = []
    for ligne in lignes:
        if not dedans and ligne.strip().lower().startswith("```mermaid"):
            dedans = True
            courant = []
            continue
        if dedans and ligne.strip() == "```":
            blocs.append("\n".join(courant))
            dedans = False
            continue
        if dedans:
            courant.append(ligne)
    if dedans and courant:
        blocs.append("\n".join(courant))
    return blocs


def extraire_zones(mermaid: str) -> list[str]:
    """Repère les frontières de confiance (subgraph) d'un DFD Mermaid.

    Retourne l'étiquette de la zone si elle est entre guillemets, sinon l'identifiant.
    """
    zones: list[str] = []
    for ligne in mermaid.splitlines():
        match = RE_SUBGRAPH.match(ligne)
        if not match:
            continue
        brut = match.group(1).strip()
        etiquete = re.search(r'"([^"]*)"', brut)
        nom = etiquete.group(1).strip() if etiquete else brut.split("[")[0].strip()
        if nom and nom not in zones:
            zones.append(nom)
    return zones


def preparer_ligne(ligne: str) -> tuple[list[Element], str]:
    """Sépare les définitions de nœuds et normalise la ligne pour l'analyse des flux.

    Les libellés Mermaid peuvent être écrits **en ligne** d'une arête : la ligne est
    alors normalisée (`ID["libellé"]` → `ID`) pour que l'arête reste analysable.
    """
    elements: list[Element] = []

    def remplacement(match: re.Match) -> str:
        ident = match.group(1)
        if ident.lower() in MOTS_RESERVES_MERMAID:
            return ident
        elements.append(Element(ident, (match.group(3) or "").strip('"') or ident,
                                 match.group(2) or ""))
        return ident

    return elements, RE_DEFINITION.sub(remplacement, ligne)


def ligne_ignorable(ligne: str) -> bool:
    """Indique si la ligne ne contient ni nœud ni flux (zone, style, commentaire)."""
    debut = ligne.strip().lower()
    return (not debut
            or debut.startswith(("subgraph", "end", "style", "class", "classdef", "click",
                                 "linkstyle", "%%")))


def extraire_elements(mermaid: str) -> list[Element]:
    """Repère les éléments (acteurs, processus, stockages) d'un DFD Mermaid."""
    elements: list[Element] = []
    vus: set[str] = set()
    for ligne in mermaid.splitlines():
        if ligne_ignorable(ligne):
            continue
        trouves, _normalisee = preparer_ligne(ligne)
        for element in trouves:
            if element.ident not in vus:
                vus.add(element.ident)
                elements.append(element)
    return elements


def extraire_flux(mermaid: str) -> list[Flux]:
    """Repère les flux de données (arêtes Mermaid) et leur étiquette.

    L'étiquette est reprise verbatim entre les barres verticales, guillemets exclus.
    """
    flux: list[Flux] = []
    vus: set[tuple[str, str, str]] = set()
    for ligne in mermaid.splitlines():
        if ligne_ignorable(ligne):
            continue
        _elements, normalisee = preparer_ligne(ligne)
        match = RE_EDGE.search(normalisee)
        if match:
            source, cible = match.group(1), match.group(3)
            libelle = (match.group(2) or "").strip()
        else:
            match = RE_EDGE_LBL.search(normalisee)
            if not match:
                continue
            source, libelle, cible = match.group(1), match.group(2).strip(), match.group(3)
        libelle = libelle.strip('"').strip()
        cle = (source, cible, libelle)
        if cle in vus:
            continue
        vus.add(cle)
        flux.append(Flux(source, cible, libelle))
    return flux


def detecter_signaux_conformite(*fichiers: tuple[str, str]) -> list[Signal]:
    """Repère les exigences de conformité mentionnées (regex, aucun jugement).

    Chaque argument est un couple (nom du fichier, contenu) : le numéro de ligne
    renvoie donc au fichier réellement cité.
    """
    signaux: list[Signal] = []
    for categorie, motif in MOTIFS_CONFORMITE:
        regex = re.compile(motif, re.IGNORECASE)
        for nom, contenu in fichiers:
            trouve = None
            for numero, ligne in enumerate(contenu.splitlines(), 1):
                correspondance = regex.search(ligne)
                if correspondance:
                    trouve = Signal(categorie, correspondance.group(0), numero,
                                    ligne.strip(), nom)
                    break
            if trouve:
                signaux.append(trouve)
                break
    return signaux


def detecter_donnees_personnelles(content: str) -> list[Signal]:
    """Repère les catégories de données personnelles citées dans la description."""
    signaux: list[Signal] = []
    for categorie, motif in MOTIFS_DONNEES_PERSONNELLES:
        regex = re.compile(motif, re.IGNORECASE)
        for numero, ligne in enumerate(content.splitlines(), 1):
            trouve = regex.search(ligne)
            if trouve:
                signaux.append(Signal(categorie, trouve.group(0), numero, ligne.strip()))
                break
    return signaux


def detecter_faiblesses(content: str) -> list[Signal]:
    """Repère les faiblesses techniques citées dans la description."""
    faiblnesses: list[Signal] = []
    for libelle, motif in MOTIFS_FAIBLESSES:
        regex = re.compile(motif, re.IGNORECASE)
        for numero, ligne in enumerate(content.splitlines(), 1):
            trouve = regex.search(ligne)
            if trouve:
                faiblnesses.append(Signal(libelle, trouve.group(0), numero, ligne.strip()))
                break
    return faiblnesses


def detecter_scenarios(content: str) -> list[Scenario]:
    """Repère les scénarios redoutés évoqués dans la description."""
    scenarios: list[Scenario] = []
    for titre, motif in MOTIFS_SCENARIOS:
        regex = re.compile(motif, re.IGNORECASE)
        for numero, ligne in enumerate(content.splitlines(), 1):
            trouve = regex.search(ligne)
            if trouve:
                scenarios.append(Scenario(titre, numero, ligne.strip()))
                break
    return scenarios


def detecter_technologies(content: str) -> list[str]:
    """Liste les technologies citées (occurrences uniques, ordre du document)."""
    trouvees: list[str] = []
    for ligne in content.splitlines():
        for match in RE_TECHNO.finditer(ligne):
            terme = match.group(0).strip()
            if terme.lower() not in {t.lower() for t in trouvees}:
                trouvees.append(terme)
    return trouvees


def detecter_versions(content: str) -> list[str]:
    """Liste les technologies versionnées citées (ordre du document)."""
    trouvees: list[str] = []
    for ligne in content.splitlines():
        for match in RE_VERSION.finditer(ligne):
            terme = " ".join(match.group(1).split())
            if terme.lower() not in {t.lower() for t in trouvees}:
                trouvees.append(terme)
    return trouvees


def detecter_cves(content: str) -> list[str]:
    """Liste les identifiants CVE cités (texte verbatim, aucune invention)."""
    trouvees: list[str] = []
    for match in RE_CVE.finditer(content):
        ident = match.group(0)
        if ident not in trouvees:
            trouvees.append(ident)
    return trouvees


def detecter_type_systeme(content: str) -> str:
    """Détermine un type de système à partir de mots-clés (suggestion, pas verdict)."""
    bas = content.lower()
    if "boutique" in bas or "e-commerce" in bas or "site web public" in bas or "panier" in bas:
        return "web_public"
    if "santé" in bas or "medical" in bas or "hopital" in bas or "données sensibles" in bas:
        return "sante"
    if "intranet" in bas or "réseau interne" in bas or "back-office interne" in bas:
        return "interne"
    return "general"


def detecter_rgpd(content: str) -> bool:
    """Indique si le RGPD (ou la protection des données personnelles) est cité."""
    bas = content.lower()
    return "rgpd" in bas or "données personnelles" in bas or "donnees personnelles" in bas


def type_stockage(forme: str) -> bool:
    """Indique si la forme Mermaid correspond à un stockage (cylindre / disque)."""
    return forme in ("[(", "[((")


# --------------------------------------------------------------------------- #
# Étape 1 — objectifs métier
# --------------------------------------------------------------------------- #

def generer_p1(case_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère PASTA-01-objectifs-metier.md."""
    description = read_file_verbatim(case_dir / "00-description.md")
    actifs = read_file_verbatim(case_dir / "01-actifs.md")

    conformite = detecter_signaux_conformite(
        ("00-description.md", description), ("01-actifs.md", actifs))
    rgpd = detecter_rgpd(description + "\n" + actifs)

    if conformite:
        lignes_conformite = "\n".join(
            f"| {s.categorie} | `{s.terme}` | {s.source}, ligne {s.numero_ligne} | {A_COMPLETER} |"
            for s in conformite)
    else:
        lignes_conformite = (f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |")
    if rgpd and not any(s.categorie == "RGPD" for s in conformite):
        lignes_conformite += (f"\n| **RGPD** | `rgpd` / données personnelles | "
                              f"détecté dans 00-description.md | {A_COMPLETER} |")

    contenu = f"""{BANNER}

# PASTA étape 1 — Définir les objectifs métier

> Étape PASTA n°1 : on **part du business**, pas de la technique. La direction valide
> les objectifs et les exigences de conformité ; le reste de la méthode en découle.

**Nom du cas :** {case_name}

## 1. Objectifs métier de l'organisation

*Aucune conclusion business n'est inventée ici : les objectifs sont à formuler avec
la direction, puis à relier aux événements redoutés de l'étape 7.*

| # | Objectif métier (du point de vue de la direction) | Actifs concernés | Événement redouté associé | Critère de succès mesurable |
|---|---|---|---|---|
| 1 | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| 2 | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| 3 | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

{A_COMPLETER}

## 2. Exigences de conformité

*Signaux détectés automatiquement dans la description (recherche textuelle, sans
interprétation) : la formulation juridique reste à valider.*

| Exigence | Terme détecté | Origine | Contrainte imposée au système |
|---|---|---|---|
{lignes_conformite}

**RGPD détecté :** {'oui' if rgpd else 'non — à confirmer avec la direction'}

{A_COMPLETER}

## 3. Contraintes et arbitrages/business case

*Budget, contraintes d'hébergement, délais, exigences de disponibilité : ces éléments
contraignent le traitement du risque à l'étape 7.*

| Contrainte | Origine | Conséquence sur la sécurité | Arbitrage demandé |
|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

{A_COMPLETER}

## 4. Données d'entrée exploitées (verbatim)

### 00-description.md
{bloc_donnees(description, "00-description.md")}

### 01-actifs.md
{bloc_donnees(actifs, "01-actifs.md")}

{section_lignes_suspectes(("00-description.md", description), ("01-actifs.md", actifs))}
"""
    chemin = out_dir / "PASTA-01-objectifs-metier.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


# --------------------------------------------------------------------------- #
# Étape 2 — périmètre technique
# --------------------------------------------------------------------------- #

def generer_p2(case_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère PASTA-02-perimetre-technique.md."""
    description = read_file_verbatim(case_dir / "00-description.md")
    actifs = read_file_verbatim(case_dir / "01-actifs.md")
    analyse = description + "\n" + actifs

    zones: list[str] = []
    elements: list[Element] = []
    for bloc in extraire_blocs_mermaid(analyse):
        for zone in extraire_zones(bloc):
            if zone not in zones:
                zones.append(zone)
        for element in extraire_elements(bloc):
            if element.ident not in {e.ident for e in elements}:
                elements.append(element)

    technologies = detecter_technologies(analyse)
    versions = detecter_versions(analyse)
    type_systeme = detecter_type_systeme(analyse)

    lignes_composants = "\n".join(
        f"| `{e.ident}` | {'stockage' if type_stockage(e.forme) else ('processus' if 'Processus' in e.libelle else 'acteur / composant')} "
        f"| {' '.join(e.libelle.split()) or e.ident} | {A_COMPLETER} | {A_COMPLETER} |"
        for e in elements) or f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"

    lignes_tech = "\n".join(
        f"| {tech} | {ver if ver else A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"
        for tech, ver in _coupler_technologies_versions(technologies, versions))

    lignes_dependances = "\n".join(
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |" for _ in range(3))

    lignes_zones = "\n".join(f"| {zone} | {A_COMPLETER} | {A_COMPLETER} |" for zone in zones) or \
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"

    contenu = f"""{BANNER}

# PASTA étape 2 — Définir le périmètre technique

> Étape PASTA n°2 : le « regard technique » — composants, technologies, dépendances.
> C'est le premier moment où l'on **s'intéresse aux places d'attaque**.

**Nom du cas :** {case_name}

**Type de système détecté (indicatif) :** {type_systeme}

## 1. Composants du système

*Éléments repérés dans les schémas Mermaid de la description. Libellés repris verbatim.*

| ID | Type | Libellé (verbatim du DFD) | Frontière / zone | criticité à compléter |
|---|---|---|---|---|
{lignes_composants}

{A_COMPLETER}

## 2. Technologies et versions

| Technologie | Version repérée | Fin de vie / support ? | Source |
|---|---|---|---|
{lignes_tech}

*Aucune version n'est inventée : seules les mentions écrites dans la description sont reprises.*

{A_COMPLETER}

## 3. Dépendances

*Services externes, fournisseurs, bibliothèques, intégrations.*

| Dépendance | Type (service externe / librairie / prestataire) | criticité | Accès / secret associé |
|---|---|---|---|
{lignes_dependances}

{A_COMPLETER}

## 4. Frontières techniques repérées

| Zone (verbatim du DFD) | Contenu | Commentaire de l'analyste |
|---|---|---|
{lignes_zones}

{A_COMPLETER}

## 5. Données d'entrée exploitées (verbatim)

### 00-description.md
{bloc_donnees(description, "00-description.md")}

### 01-actifs.md
{bloc_donnees(actifs, "01-actifs.md")}

{section_lignes_suspectes(("00-description.md", description), ("01-actifs.md", actifs))}
"""
    chemin = out_dir / "PASTA-02-perimetre-technique.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


def _coupler_technologies_versions(technologies: list[str], versions: list[str]) -> list[tuple[str, str]]:
    """Associe chaque technologie à la version citée si elle est repérée (texte)."""
    couples: list[tuple[str, str]] = []
    for tech in technologies:
        version = ""
        for candidate in versions:
            if candidate.lower().startswith(tech.lower()):
                version = candidate
                break
        couples.append((tech, version))
    return couples


# --------------------------------------------------------------------------- #
# Étape 3 — décomposition (DFD)
# --------------------------------------------------------------------------- #

def generer_p3(case_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère PASTA-03-decomposition.md."""
    description = read_file_verbatim(case_dir / "00-description.md")
    blocs = extraire_blocs_mermaid(description)
    zones: list[str] = []
    elements: list[Element] = []
    flux: list[Flux] = []
    for bloc in blocs:
        for zone in extraire_zones(bloc):
            if zone not in zones:
                zones.append(zone)
        for element in extraire_elements(bloc):
            if element.ident not in {e.ident for e in elements}:
                elements.append(element)
        for flux_item in extraire_flux(bloc):
            if (flux_item.source, flux_item.cible, flux_item.libelle) not in {
                    (f.source, f.cible, f.libelle) for f in flux}:
                flux.append(flux_item)

    if blocs:
        corps_dfd = "\n\n".join(code_block(bloc, "mermaid") for bloc in blocs)
        origine = "DFD **repris verbatim** depuis la description du cas."
    else:
        corps_dfd = code_block(
            'flowchart LR\n'
            '    subgraph ZONE_A["Frontière : à nommer"]\n'
            '        ACTEUR["Acteur : à nommer"]\n'
            '    end\n'
            '    ACTEUR -->|"donnée : à étiqueter"| PROCESSUS["Processus : à nommer"]\n',
            "mermaid")
        origine = ("Aucun bloc Mermaid trouvé dans 00-description.md : "
                   "le squelette ci-dessous est **à compléter**.")

    lignes_elements = "\n".join(
        f"| `{e.ident}` | {'stockage' if type_stockage(e.forme) else 'processus / acteur'} "
        f"| {' '.join(e.libelle.split()) or e.ident} | {A_COMPLETER} |"
        for e in elements) or f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"

    lignes_flux = "\n".join(
        f"| `{f.source}` | `{f.cible}` | {f.libelle if f.libelle else A_COMPLETER} | {A_COMPLETER} |"
        for f in flux) or f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"

    lignes_zones = "\n".join(
        f"| {zone} | {A_COMPLETER} | {A_COMPLETER} |" for zone in zones) or \
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"

    lignes_roles = "\n".join(f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |" for _ in range(4))

    contenu = f"""{BANNER}

# PASTA étape 3 — Décomposer l'application

> Étape PASTA n°3 : on dessine le **DFD** (flux de données, rôles, frontières de
> confiance). PASTA attaque ensuite **chaque flux** à l'étape 6.

**Nom du cas :** {case_name}

## 1. DFD (reprise verbatim de la description)

{origine}

{corps_dfd}

## 2. Éléments du DFD

| ID | Type | Libellé | Rôle dans le système |
|---|---|---|---|
{lignes_elements}

{A_COMPLETER}

## 3. Rôles

| Rôle | Description / droits | Accès aux éléments du DFD |
|---|---|---|
{lignes_roles}

*Aucun rôle n'est inventé : reprendre le tableau « Acteurs et rôles » de 00-description.md.*

{A_COMPLETER}

## 4. Flux de données

| Source | Cible | Donnée transportée (étiquette du DFD) | Sens / fréquence |
|---|---|---|---|
{lignes_flux}

## 5. Frontières de confiance

| Frontière (verbatim du DFD) | Éléments de part et d'autre | Menaces attendues au passage |
|---|---|---|
{lignes_zones}

**Règle PASTA** : les attaques se concentrent **au passage des frontières**.

{A_COMPLETER}

## 6. Données d'entrée exploitées (verbatim)

### 00-description.md
{bloc_donnees(description, "00-description.md")}

{section_lignes_suspectes(("00-description.md", description))}
"""
    chemin = out_dir / "PASTA-03-decomposition.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


# --------------------------------------------------------------------------- #
# Étape 4 — analyse des menaces (renseignement)
# --------------------------------------------------------------------------- #

def generer_p4(case_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère PASTA-04-analyse-menaces.md."""
    description = read_file_verbatim(case_dir / "00-description.md")
    type_systeme = detecter_type_systeme(description)

    if type_systeme == "web_public":
        pravite = "Exposition Internet : le bruit de fond automatisé est permanent."
    elif type_systeme == "sante":
        pravite = "Données sensibles : la motivation des acteurs est élevée et organisée."
    elif type_systeme == "interne":
        pravite = "Système interne : le vecteur dominant est l'accès interne et le fournisseur."
    else:
        pravite = "Périmètre non qualifié : justifier l'évaluation du profil de menace."

    lignes_acteurs = "\n".join(
        f"| {acteur} | {motivation} | {capacite} | {cible} | {A_COMPLETER} |"
        for acteur, motivation, capacite, cible in ACTEURS_PROBABLES)

    lignes_cibles = "\n".join(
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |" for _ in range(3))

    contenu = f"""{BANNER}

# PASTA étape 4 — Analyser les menaces (threat intelligence)

> Étape PASTA n°4 : **renseignement**, pas spéculation. On recense les acteurs
> probables et ce qu'ils cherchent **dans ce secteur**, pour ce type de système.

**Nom du cas :** {case_name}

**Profil de menace indicatif :** {type_systeme} — {pravite}

## 1. Acteurs probables

*Suggestions de départ, à confirmer ou retirer par l'analyste.*

| Acteur probable | Motivation / bénéfice pour l'acteur | Capacités / TTPs | Cible probable sur ce système | Source (base de connaissances, CERT) |
|---|---|---|---|---|
{lignes_acteurs}

{A_COMPLETER}

## 2. Cibles privilégiées sur ce système

| Cible | Pourquoi elle attire l'acteur | Valeur (données / argent / disponibilité) | Menace associée |
|---|---|---|---|
{lignes_cibles}

{A_COMPLETER}

## 3. Menaces externes et tendances observées

*Campagnes observées dans le secteur, sources publiques (ANSSI / CERT-FR, CISA, Europol).*

| Menace / campagne | Secteur visé | Éléments de ce cas concernés | Source |
|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

{A_COMPLETER}

## 4. Menaces internes

| Menace interne | Vecteur | Impact attendu | Contrôle existant |
|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

{A_COMPLETER}

## 5. Renseignement disponible et manquant

- **Collecté pour ce cas :** {A_COMPLETER}
- **À obtenir (CVE, statistiques deCERT, retours d'expérience) :** {A_COMPLETER}
- **Aucune source inventée** : toute référence doit pointer vers une source
  autorisée de la base de connaissances.

{A_COMPLETER}

## 6. Données d'entrée exploitées (verbatim)

### 00-description.md
{bloc_donnees(description, "00-description.md")}

{section_lignes_suspectes(("00-description.md", description))}
"""
    chemin = out_dir / "PASTA-04-analyse-menaces.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


# --------------------------------------------------------------------------- #
# Étape 5 — vulnérabilités
# --------------------------------------------------------------------------- #

def generer_p5(case_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère PASTA-05-vulnerabilites.md."""
    description = read_file_verbatim(case_dir / "00-description.md")
    actifs = read_file_verbatim(case_dir / "01-actifs.md")
    analyse = description + "\n" + actifs

    faiblnesses = detecter_faiblesses(analyse)
    versions = detecter_versions(analyse)
    cves = detecter_cves(analyse)

    lignes_versions = "\n".join(
        f"| {version} | {A_COMPLETER} | {A_COMPLETER} |" for version in versions) or \
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"

    lignes_cve = "\n".join(
        f"| `{cve}` | {A_COMPLETER} | {A_COMPLETER} |" for cve in cves) or \
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"

    lignes_lien = "\n".join(
        f"| V-{index:02d} | {f.categorie} | {A_COMPLETER} | {A_COMPLETER} |"
        for index, f in enumerate(faiblnesses, 1)) or \
        f"| V-01 | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"

    contenu = f"""{BANNER}

# PASTA étape 5 — Analyser les vulnérabilités

> Étape PASTA n°5 : on relie chaque **faiblesse** à la **menace** de l'étape 4.
> Une vulnérabilité sans menace reliée n'est pas priorisée en PASTA.

**Nom du cas :** {case_name}

## 1. Faiblesses connues repérées dans la description

*Recherche textuelle dans 00-description.md / 01-actifs.md. Extraits verbatim.*

| ID | Faiblesse | Extrait verbatim | Localisation | Gravité (à compléter) |
|---|---|---|---|---|
{_numeroter(faiblnesses)}

## 2. Versions et fin de vie

| Version citée | Fin de vie (EOL) ? | Conséquence |
|---|---|---|
{lignes_versions}

{A_COMPLETER}

## 3. CVE citées dans la description

*Aucune CVE n'est inventée : seules les références écrites dans les fichiers d'entrée
sont reprises. Les CVE à rechercher restent à compléter.*

| CVE | Élément affecté | Remarque |
|---|---|---|
{lignes_cve}

{A_COMPLETER}

## 4. Lien menace (étape 4) → vulnérabilité (étape 5)

| Faiblesse | Menace / acteur concerné (PASTA-04) | Scénario d'attaque (PASTA-06) | Contre-mesure |
|---|---|---|---|
{lignes_lien}

{A_COMPLETER}

## 5. Données d'entrée exploitées (verbatim)

### 00-description.md
{bloc_donnees(description, "00-description.md")}

### 01-actifs.md
{bloc_donnees(actifs, "01-actifs.md")}

{section_lignes_suspectes(("00-description.md", description), ("01-actifs.md", actifs))}
"""
    chemin = out_dir / "PASTA-05-vulnerabilites.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


def _numeroter(faiblnesses: list[Signal]) -> str:
    """Construit le tableau des faiblesses avec un identifiant V-xx."""
    if not faiblnesses:
        return f"| V-01 | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"
    lignes_finales = []
    for index, f in enumerate(faiblnesses, 1):
        lignes_finales.append(
            f"| V-{index:02d} | {f.categorie} | `{f.terme}` | 00-description.md / 01-actifs.md, "
            f"ligne {f.numero_ligne} | {A_COMPLETER} |")
    return "\n".join(lignes_finales)


# --------------------------------------------------------------------------- #
# Étape 6 — modélisation des attaques
# --------------------------------------------------------------------------- #

def generer_p6(case_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère PASTA-06-modelisation-attaques.md."""
    description = read_file_verbatim(case_dir / "00-description.md")
    scenarios = detecter_scenarios(description)

    if scenarios:
        arbres = []
        for index, scenario in enumerate(scenarios, 1):
            arbre = (
                f"### Arbre A-{index:02d} — {scenario.titre}\n\n"
                "```mermaid\n"
                "graph TD\n"
                f"    A[\"Objectif de l'attaquant : {scenario.titre}\"]\n"
                f"    A --> B[\"Étape 1 : {A_COMPLETER_DIAGRAMME}\"]\n"
                f"    B --> C[\"Étape 2 : {A_COMPLETER_DIAGRAMME}\"]\n"
                f"    C --> D[\"Étape 3 : {A_COMPLETER_DIAGRAMME}\"]\n"
                f"    D --> E[\"Impact métier : {A_COMPLETER_DIAGRAMME}\"]\n"
                "```\n\n"
                f"**Ancre dans la description** (verbatim, ligne {scenario.numero_ligne}) :\n\n"
                f"{DEBUT_DONNEES}\n{scenario.ligne}\n{FIN_DONNEES}\n\n"
                "| Prérequis | Outillage / technique | Détection possible | Contre-mesure |\n"
                "|---|---|---|---|\n"
                f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |\n"
            )
            arbres.append(arbre)
        corps_arbres = "\n---\n\n".join(arbres)
    else:
        corps_arbres = (
            "Aucun scénario redouté n'a été détecté automatiquement dans la description.\n\n"
            "```mermaid\n"
            'graph TD\n'
            '    A["Objectif de l\'attaquant : à compléter"]\n'
            '    A --> B["Étape 1 : à compléter"]\n'
            '    B --> C["Impact métier : à compléter"]\n'
            "```\n")

    lignes_scenarios = "\n".join(
        f"| A-{index:02d} | {scenario.titre} | {A_COMPLETER} | {A_COMPLETER} |"
        for index, scenario in enumerate(scenarios, 1)) or \
        f"| A-01 | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"

    contenu = f"""{BANNER}

# PASTA étape 6 — Modéliser les attaques

> Étape PASTA n°6 : on **simule** l'attaque. On descend d'un objectif d'attaquant
> vers les étapes techniques, en partant des flux de l'étape 3.

**Nom du cas :** {case_name}

## 1. Scénarios d'attaque modélisés

| ID | Scénario redouté (étape 1) | Objectif de l'attaquant | Effet sur le business |
|---|---|---|---|
{lignes_scenarios}

{A_COMPLETER}

## 2. Arbres d'attaque

{corps_arbres}

## 3. Simulation d'attaque (à jouer en atelier)

*Pour chaque arbre : qui exécute, avec quels moyens, quelle est la première barrière
rencontrée ?*

| Arbre | Assaillant simulé | Barrière n°1 | Barrière suivante | Ralentit l'attaque ? |
|---|---|---|---|---|
| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

{A_COMPLETER}

## 4. Données d'entrée exploitées (verbatim)

### 00-description.md
{bloc_donnees(description, "00-description.md")}

{section_lignes_suspectes(("00-description.md", description))}
"""
    chemin = out_dir / "PASTA-06-modelisation-attaques.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


# --------------------------------------------------------------------------- #
# Étape 7 — risques et impacts
# --------------------------------------------------------------------------- #

def generer_p7(case_dir: Path, case_name: str, out_dir: Path) -> Path:
    """Génère PASTA-07-risques-impacts.md."""
    description = read_file_verbatim(case_dir / "00-description.md")
    actifs = read_file_verbatim(case_dir / "01-actifs.md")
    analyse = description + "\n" + actifs
    type_systeme = detecter_type_systeme(analyse)

    lignes_finances = "\n".join(
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |" for _ in range(3))
    lignes_reputation = "\n".join(
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |" for _ in range(3))

    conformite = detecter_signaux_conformite(
        ("00-description.md", description), ("01-actifs.md", actifs))
    lignes_conformite = "\n".join(
        f"| {s.categorie} (`{s.terme}`, {s.source} ligne {s.numero_ligne}) | {A_COMPLETER} "
        f"| {A_COMPLETER} | {A_COMPLETER} |"
        for s in conformite) or \
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"
    lignes_risques = "\n".join(
        f"| {A_COMPLETER} |  |  |  | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"
        for _ in range(4))
    lignes_mesures = "\n".join(
        f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |"
        for _ in range(4))

    contenu = f"""{BANNER}

# PASTA étape 7 — Analyser les risques et impacts

> Étape PASTA n°7 : retour au **business**. Les colonnes Gravité / Vraisemblance /
> Niveau sont **laissées vides** : elles sont renseignées à l'étape 4 de la chaîne
> E21 (évaluation), pas ici.

**Nom du cas :** {case_name}

**Type de système détecté (indicatif) :** {type_systeme}

## 1. Impacts métier

### 1.1 Impacts financiers

| Impact | Valeur estimée (€) | Fenêtre de temps | Commentaire |
|---|---|---|---|
{lignes_finances}

{A_COMPLETER}

### 1.2 Impacts réputationnels

| Impact | Partie prenante affectée | Effet sur la confiance | Durée de l'effet |
|---|---|---|---|
{lignes_reputation}

{A_COMPLETER}

### 1.3 Impacts de conformité

| Impact | Obligation enfreinte | Sanction / recours possible | Délai |
|---|---|---|---|
{lignes_conformite}

{A_COMPLETER}

## 2. Synthèse des risques

*Gravité / Vraisemblance / Niveau : colonnes volontairement vides (étape 4 de la
chaîne E21). Le traitement (réduire / transférer / éviter / accepter) suit la
matrice du skill `analyse-risques`.*

| Risque (scénario d'attaque étape 6) | Gravité | Vraisemblance | Niveau | Contre-mesure | Responsable | Échéance | Risque résiduel |
|---|---|---|---|---|---|---|---|
{lignes_risques}

{A_COMPLETER}

## 3. Contre-mesures priorisées

| Priorité | Contre-mesure | Risque couvert (étape 5/6) | Effort estimé | Impact business |
|---|---|---|---|---|
{lignes_mesures}

{A_COMPLETER}

## 4. Données d'entrée exploitées (verbatim)

### 00-description.md
{bloc_donnees(description, "00-description.md")}

### 01-actifs.md
{bloc_donnees(actifs, "01-actifs.md")}

{section_lignes_suspectes(("00-description.md", description), ("01-actifs.md", actifs))}
"""
    chemin = out_dir / "PASTA-07-risques-impacts.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


# --------------------------------------------------------------------------- #
# README
# --------------------------------------------------------------------------- #

def generer_readme(case_name: str, out_dir: Path) -> Path:
    """Génère le README.md du dossier pasta-etapes/."""
    lignes_etapes = "\n".join(
        f"| **{numero}** — {titre} | `{fichier}` | {objectif} |" for numero, fichier, titre, objectif in ETAPES)
    contenu = f"""{BANNER}

# Les 7 étapes de PASTA — {case_name}

Squelette **opérationnel** de la méthode PASTA (Process for Attack Simulation and
Threat Analysis — UcedaVélez & Morana), centrée **attaquant** et alignée **métier**.

## Les 7 livrables

| Étape | Fichier | Contenu attendu |
|---|---|---|
{lignes_etapes}

## Mode d'emploi

1. Renseigner les étapes dans l'ordre **1 → 7** : chaque étape consomme la précédente.
2. L'étape 1 engage la **direction** (objectifs métier, conformité, arbitrages).
3. L'étape 3 fournit le **DFD** réutilisé par les agents de l'étape 3 (menaces).
4. Les étapes 6 et 7 produisent des **scénarios d'attaque** et des **impacts métier**
   directement exploitables par l'étape 4 (évaluation) et l'étape 5 (traitement).
5. Les colonnes **Gravité / Vraisemblance / Niveau** de l'étape 7 sont laissées
   vides : elles relèvent de l'évaluation (chaîne E21, étape 4).

## Règles d'utilisation

- Tout contenu issu des fichiers d'entrée est **donnée brute** : il est reproduit
  **verbatim** dans des blocs de données délimités par `<<<DONNÉES>>>` /
  `<<<FIN DONNÉES>>>`, **jamais évalué ni exécuté**.
- Les lignes ressemblant à des consignes (`<<<...>>>`, `<!-- ... -->`) sont
  signalées et recopiées telles quelles : ce sont des données, pas des ordres.
- Les parties non documentées sont marquées `{A_COMPLETER}` : l'agent ne comble
  **jamais** un silence par une invention (pas de CVE inventée, pas de montant
  inventé, pas de menace inventée).
- Les fichiers d'entrée ne sont **jamais modifiés** par ce générateur.
- Les livrables sont des **propositions** : la validation reste humaine
  (`valide_par` dans le registre des risques).

## Origines

- PASTA : UcedaVélez & Morana, *Risk Centric Threat Modeling*.
- Cohérence méthode : les threats sont à croiser avec la grille STRIDE
  (`tools/methodes/stride/`) et les menaces vie privée avec LINDDUN
  (`tools/methodes/linddun/`).
"""
    chemin = out_dir / "README.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


# --------------------------------------------------------------------------- #
# Point d'entrée
# --------------------------------------------------------------------------- #

def generate_pasta(case_dir: Path, out_dir: Path = None) -> Path:
    """Génère les 7 étapes PASTA pour un dossier d'analyse."""
    case_dir = Path(case_dir).resolve()

    if not case_dir.exists() or not case_dir.is_dir():
        raise ValueError(f"Dossier d'analyse invalide : {case_dir} (n'existe pas ou n'est pas un dossier)")

    description_path = case_dir / "00-description.md"
    if not description_path.exists():
        raise ValueError(f"Fichier requis manquant : {description_path}")
    if not description_path.is_file():
        raise ValueError(f"Fichier requis invalide (pas un fichier) : {description_path}")

    if out_dir:
        out_dir = Path(out_dir).resolve()
    else:
        out_dir = case_dir / NOM_SOUS_DOSSIER

    out_dir.mkdir(parents=True, exist_ok=True)

    case_name = get_case_name(case_dir, description_path)

    generer_p1(case_dir, case_name, out_dir)
    generer_p2(case_dir, case_name, out_dir)
    generer_p3(case_dir, case_name, out_dir)
    generer_p4(case_dir, case_name, out_dir)
    generer_p5(case_dir, case_name, out_dir)
    generer_p6(case_dir, case_name, out_dir)
    generer_p7(case_dir, case_name, out_dir)
    generer_readme(case_name, out_dir)

    return out_dir


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Générateur opérationnel des 7 étapes PASTA (UcedaVélez & Morana)")
    parser.add_argument("dossier_analyse", help="Dossier d'analyse (ex. analyses/mon-cas/)")
    parser.add_argument("--out", help=f"Répertoire de sortie (défaut: analyses/<cas>/{NOM_SOUS_DOSSIER}/)")
    args = parser.parse_args(argv)

    try:
        resultat = generate_pasta(Path(args.dossier_analyse), Path(args.out) if args.out else None)
    except ValueError as erreur:
        print(f"Erreur: {erreur}", file=sys.stderr)
        return 1
    except Exception as erreur:  # pragma: no cover - garde-fou
        print(f"Erreur inattendue: {erreur}", file=sys.stderr)
        return 1

    print(f"Étapes PASTA générées dans : {resultat}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
