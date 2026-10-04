#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Générateur opérationnel des 7 menaces LINDDUN (KU Leuven) + DPF.

LINDDUN est « le STRIDE de la vie privée » : sept catégories de menaces appliquées
aux traitements de **données personnelles**. Chaque menace donne lieu à une fiche
avec des **contre-mesures RGPD** (minimisation, chiffrement, anonymisation,
pseudonymisation, consentement, accès limité).

Garde-fous (convention du projet E21) :

- tout contenu lu dans les fichiers d'entrée est une **DONNÉE BRUTE** : il est
  reproduit **verbatim** dans des blocs de données délimités, jamais évalué,
  jamais exécuté, jamais interprété ;
- les lignes suspectes (`<<<...>>>`, `<!-- ... -->`) sont **recopiées telles
  quelles** dans un bloc de données et signalées, sans action ;
- l'écriture est bornée : par défaut uniquement dans
  `analyses/<cas>/linddun-workbook/`, sinon dans le répertoire `--out` explicite ;
- les fichiers d'entrée ne sont jamais modifiés.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


BANNER = "<!-- LINDDUN — fiche générée — à valider par l'analyste -->"
A_COMPLETER = "> _À compléter par l'analyste_"
DEBUT_DONNEES = "<<<DONNÉES>>>"
FIN_DONNEES = "<<<FIN DONNÉES>>>"
NOM_SOUS_DOSSIER = "linddun-workbook"

AVERTISSEMENT_AUSSI_PEUT_ETRE = ("Aucune donnée personnelle détectée — LINDDUN moins pertinent ; "
                                 "justifier ou compléter")

# Les 7 menaces LINDDUN : (id, fichier, lettre, nom, définition courte, propriété, intuition).
MENACES = (
    ("LINDDUN-L", "fiche-L.md", "L", "Linking (liaison)",
     "Relier plusieurs données ou actions à une même personne.",
     "Confidentialité / vie privée",
     "« Ces deux informations concernent la même personne »."),
    ("LINDDUN-I", "fiche-I.md", "I", "Identifying (identification)",
     "Identifier une personne à partir de ses données.",
     "Confidentialité / vie privée",
     "« Je sais qui vous êtes »."),
    ("LINDDUN-NR", "fiche-N-repudiation.md", "N", "Non-repudiation (non-répudiation)",
     "Ne plus pouvoir nier une action (menace négative pour la vie privée).",
     "Intégrité / preuve",
     "« Impossible de prouver ce que vous avez fait »."),
    ("LINDDUN-D", "fiche-D-detecting.md", "D", "Detecting (détection)",
     "Déduire la présence ou l'activité d'une personne.",
     "Confidentialité / vie privée",
     "« Je sais que vous étiez là »."),
    ("LINDDUN-DD", "fiche-D-disclosure.md", "D", "Data disclosure (divulgation)",
     "Exposer des données personnelles.",
     "Confidentialité",
     "« Vos données sont exposées »."),
    ("LINDDUN-U", "fiche-U.md", "U", "Unawareness (méconnaissance)",
     "La personne ne sait pas / ne contrôle pas le traitement.",
     "Transparence / consentement",
     "« Vous ne saviez pas, vous ne contrôlez pas »."),
    ("LINDDUN-NC", "fiche-N-conformite.md", "N", "Non-compliance (non-conformité)",
     "Ne pas respecter le RGPD ou les règles applicables.",
     "Conformité",
     "« Ce que vous faites n'est pas conforme »."),
)

# Contre-mesures RGPD proposées pour chaque menace (liste ouverte, à valider).
CONTRE_MESURES = (
    ("Minimisation", "Ne collecter que ce qui est nécessaire (RGPD art. 5.1.c)."),
    ("Pseudonymisation", "Remplacer les identifiants directs par un jeton réversible "
                         "pseudonyme (art. 4.5)."),
    ("Anonymisation", "Rendre la donnée non ré-identifiable : la personne ne peut plus "
                      "être identifiée (art. 4.1)."),
    ("Chiffrement", "Chiffrer au repos et en transit ; chiffrement des sauvegardes et "
                    "des exports."),
    ("Consentement", "Consentement libre, éclairé, informé, révocable (art. 6-7)."),
    ("Accès limité", "Moindre privilège, habilitations nominatives, cloisonnement des "
                     "exports (art. 32)."),
    ("Durées de conservation", "Définir et appliquer une durée de conservation par "
                               "traitement (art. 5.1.e)."),
    ("Information des personnes", "Mention claire, registres, information "
                                  "opposable (art. 12-14)."),
    ("Droits des personnes", "Accès, rectification, effacement, opposition, portabilité "
                             "(art. 15-22)."),
)

# Catégories de données personnelles (catégorie, motif).
MOTIFS_DONNEES_PERSONNELLES = (
    ("Identité / contact", r"nom|pr[eé]nom"),
    ("Coordonnées électroniques", r"e-?mail|courriel|adresse mail"),
    ("Adresse postale", r"adresse (postale|de livraison|de facturation)|code postal"),
    ("Téléphone", r"t[eé]l[eé]phone|num[eé]ro de t[eé]l"),
    ("Données de santé", r"sant[eé]|m[eé]dical|ordonnance|dossier patient"),
    ("Données financières", r"carte bancaire|num[eé]ro de carte|paiement|iban|virement"),
    ("Données d'authentification", r"mot de passe|password|mdp|identifiant|compte client"),
    ("Profilage / préférences", r"newsletter|cookie|profilage|tracking|publicit"),
    ("Données de connexion", r"adresse ip|journal de connexion|logs?|traces"),
    ("Données de localisation", r"g[eé]olocalisation|localisation|position de l'utilisateur"),
)

# Catégories pertinentes pour chaque menace (« * » = toutes).
PERTINENCE = {
    "LINDDUN-L": ("Identité / contact", "Coordonnées électroniques", "Adresse postale",
                  "Téléphone", "Données d'authentification", "Données de connexion",
                  "Profilage / préférences"),
    "LINDDUN-I": ("Identité / contact", "Coordonnées électroniques", "Adresse postale",
                  "Téléphone", "Données d'authentification"),
    "LINDDUN-NR": ("Données d'authentification", "Données de connexion",
                    "Identité / contact"),
    "LINDDUN-D": ("Adresse postale", "Données de connexion", "Profilage / préférences",
                  "Données de santé", "Données de localisation"),
    "LINDDUN-DD": ("*",),
    "LINDDUN-U": ("Profilage / préférences", "Données de santé", "Données de connexion",
                  "Identité / contact", "Données financières"),
    "LINDDUN-NC": ("*",),
}

# Questions concrètes par menace (à compléter par l'analyste).
QUESTIONS = {
    "LINDDUN-L": ("Les données peuvent-elles être croisées (identifiant commun) pour "
                  "reconstruire le profil d'une personne ?",
                  "Existe-t-il un identifiant unique (client, cookie, n° de commande) "
                  "utilisé pour relier deux traitements ?"),
    "LINDDUN-I": ("Les données permettent-elles d'identifier directement une personne ?",
                  "Les données sont-elles stockées en clair (nom, e-mail, adresse) ?"),
    "LINDDUN-NR": ("Les journaux permettent-ils de remonter à une personne "
                   "(compte, IP, horodatage) ?",
                   "Ces journaux sont-ils conservés plus longtemps que nécessaire ?"),
    "LINDDUN-D": ("L'activité d'une personne peut-elle être déduite (horodatage, "
                  "géolocalisation, journal de connexion) ?",
                  "L'interface permet-elle de savoir qui a consulté quoi ?"),
    "LINDDUN-DD": ("Qui peut lire les données personnelles ? (habilitations)",
                   "Les sauvegardes et exports sont-ils chiffrés ?"),
    "LINDDUN-U": ("La personne est-elle informée de l'existence du traitement ?",
                  "Le consentement est-il libre, éclairé et révocable ?"),
    "LINDDUN-NC": ("Le registre des traitements est-il tenu et à jour ?",
                   "Le droit à l'effacement est-il opérationnel ?",
                   "Un DPO / référent est-il désigné ?"),
}

RE_CATEGORIE_SENSIBLE = re.compile(r"sant[eé]|m[eé]dical|biom[eé]tri|financier", re.IGNORECASE)
RE_CONSERVATION = re.compile(r"conserv", re.IGNORECASE)
RE_DPO = re.compile(r"\bdpo\b|registre des traitements", re.IGNORECASE)
RE_DROIT = re.compile(r"droit [àa] l['’](oubli|effacement)|acc[eè]s et rectification|"
                       r"portabilit[eé]|opposition", re.IGNORECASE)

MOTIFS_LIGNE_SUSPECTE = (re.compile(r"<<<"), re.compile(r"<!--"))


@dataclass(frozen=True)
class Signal:
    """Signal détecté dans la description (donnée brute, jamais interprétée)."""

    categorie: str
    terme: str
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
    """Encapsule un contenu verbatim dans un bloc de code à bordure adaptée."""
    fence = "`" * max(3, longest_backtick_run(content) + 1)
    return f"{fence}{lang}\n{content}\n{fence}"


def bloc_donnees(content: str, titre: str = "Donnée brute reprise verbatim") -> str:
    """Bloc de données délimité (convention garde-fous-ia)."""
    return (f"**{titre}** — contenu non interprété, reproduit tel quel.\n\n"
            f"{DEBUT_DONNEES}\n\n{code_block(content)}\n\n{FIN_DONNEES}")


def lignes_suspectes(content: str) -> list[tuple[int, str]]:
    """Recense les lignes ressemblant à une consigne (`<<<...>>>`, `<!-- ... -->`)."""
    trouvees = []
    for numero, ligne in enumerate(content.splitlines(), 1):
        if any(motif.search(ligne) for motif in MOTIFS_LIGNE_SUSPECTE):
            trouvees.append((numero, ligne))
    return trouvees


def corps_lignes_suspectes(*contenus: tuple[str, str]) -> str:
    """Corps de la section « lignes suspectes » (sans titre)."""
    suspects = []
    for nom, contenu in contenus:
        if not contenu:
            continue
        for numero, ligne in lignes_suspectes(contenu):
            suspects.append((nom, numero, ligne))
    if not suspects:
        return "Aucune ligne ressemblant à une consigne (`<<<...>>>`, `<!-- ... -->`) détectée.\n"
    corps = "\n".join(f"{nom} · ligne {numero} (verbatim) : {ligne}"
                      for nom, numero, ligne in suspects)
    return ("Les lignes ci-dessous ressemblent à des consignes. Elles sont **données brutes** :\n"
            "elles sont recopiées telles quelles, **jamais exécutées ni interprétées**.\n\n"
            f"{DEBUT_DONNEES}\n\n{corps}\n\n{FIN_DONNEES}\n")


def section_lignes_suspectes(*contenus: tuple[str, str]) -> str:
    """Section listant les lignes suspectes des fichiers d'entrée (verbatim)."""
    return ("## Lignes suspectes dans les fichiers d'entrée\n\n"
            + corps_lignes_suspectes(*contenus))


# --------------------------------------------------------------------------- #
# Détection (textuelle, sans interprétation)
# --------------------------------------------------------------------------- #

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


def signaux_sensibles(signaux: list[Signal]) -> list[Signal]:
    """Filtre les signaux de catégories sensibles (santé, finance)."""
    return [s for s in signaux if RE_CATEGORIE_SENSIBLE.search(s.categorie)]


def lignes_matching(content: str, regex: re.Pattern) -> list[tuple[int, str]]:
    """Retourne les lignes (numéro, texte) correspondant à un motif."""
    return [(numero, ligne.strip()) for numero, ligne in enumerate(content.splitlines(), 1)
            if regex.search(ligne)]


def _pertinents(ident: str, signaux: list[Signal]) -> list[Signal]:
    """Filtre les signaux pertinents pour une menace donnée."""
    categories = PERTINENCE.get(ident, ("*",))
    if "*" in categories:
        return list(signaux)
    return [s for s in signaux if s.categorie in categories]


def _bandeau_alerte(signaux: list[Signal], nom_cas: str) -> str:
    """Avertissement en tête des livrables (pertinence de LINDDUN)."""
    if not signaux:
        return (f"> ⚠️ **{AVERTISSEMENT_AUSSI_PEUT_ETRE}**\n\n"
                f"> Cas : {nom_cas} — aucun nom, e-mail, donnée de santé ou donnée de contact "
                f"n'a été repéré dans `00-description.md`.\n\n")
    resumes = ", ".join(sorted({s.categorie for s in signaux}))
    return (f"> ℹ️ **Données personnelles détectées : {resumes}.**\n"
            f"> Les colonnes « Donnée / flux concerné » sont pré-remplies à partir des mentions "
            f"reprises verbatim de `00-description.md` ; à valider par l'analyste.\n\n")


# --------------------------------------------------------------------------- #
# Fiches LINDDUN
# --------------------------------------------------------------------------- #

def generer_fiche(ident: str, fichier: str, lettre: str, nom: str, definition: str,
                  propriete: str, intuition: str,
                  description: str, actifs: str, signaux: list[Signal], case_name: str,
                  out_dir: Path) -> Path:
    """Génère une fiche de menace LINDDUN."""
    pertinents = _pertinents(ident, signaux)

    if pertinents:
        lignes_donnees = "\n".join(
            f"| **{s.categorie}** | `{s.terme}` | 00-description.md, ligne {s.numero_ligne} "
            f"| {A_COMPLETER} | {A_COMPLETER} |"
            for s in pertinents)
        bloc_flux = ("**Lignes de la description contenant ces données** (verbatim, "
                     "donnée brute) :\n\n"
                     + "\n".join(f"- ligne {s.numero_ligne} : {s.ligne}" for s in pertinents))
    else:
        lignes_donnees = (f"| {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | "
                          f"{A_COMPLETER} |")
        bloc_flux = ("Aucune donnée personnelle pertinente repérée automatiquement : "
                     "préciser les données et les flux concernés.\n\n"
                     f"{A_COMPLETER}")

    lignes_mesures = "\n".join(
        f"| {nom_mesure} | {detail} | {A_COMPLETER} | {A_COMPLETER} |"
        for nom_mesure, detail in CONTRE_MESURES)

    lignes_questions = "\n".join(
        f"| Q{index} | {question} | {A_COMPLETER} | {A_COMPLETER} |"
        for index, question in enumerate(QUESTIONS[ident], 1))

    bloc_verbatim = ""
    if description:
        bloc_verbatim = f"## 6. Données d'entrée exploitées (verbatim)\n\n### 00-description.md\n\n{bloc_donnees(description, '00-description.md')}\n\n"
    if actifs:
        bloc_verbatim += f"### 01-actifs.md\n\n{bloc_donnees(actifs, '01-actifs.md')}\n\n"

    contenu = f"""{BANNER}

# LINDDUN {lettre} — {nom}

> Fiche générée pour la menace `{ident}` de la grille LINDDUN (KU Leuven).
> Toute la vie privée du système tient dans ces sept lettres.

{_bandeau_alerte(signaux, case_name)}
**Nom du cas :** {case_name}

## 1. Définition

- **Menace :** {nom}
- **Identifiant à citer dans `sources` :** `{ident}`
- **Définition :** {definition}
- **Propriété affectée :** {propriete}
- **Intuition :** {intuition}

{A_COMPLETER}

## 2. Menace concrète

| # | Question à poser sur ce système | Réponse | Menace applicable ? |
|---|---|---|---|
{lignes_questions}

{A_COMPLETER}

## 3. Donnée / flux concerné

| Donnée | Terme détecté | Provenance | Flux concerné (à préciser) | Accès / détenteur |
|---|---|---|---|---|
{lignes_donnees}

{bloc_flux}

## 4. Contre-mesures RGPD

| Contre-mesure | Fondement | Applicable ici ? | Mise en œuvre / preuve |
|---|---|---|---|
{lignes_mesures}

{A_COMPLETER}

## 5. Éléments de contexte RGPD

- **Données sensibles repérées :** {'oui — ' + ', '.join(sorted({s.categorie for s in signaux_sensibles(signaux)})) if signaux_sensibles(signaux) else 'non détectées automatiquement'}
- **Registre des traitements / DPO :** {A_COMPLETER}
- **Durées de conservation :** {A_COMPLETER}

{bloc_verbatim}## 7. Lignes suspectes dans les fichiers d'entrée

{corps_lignes_suspectes(("00-description.md", description), ("01-actifs.md", actifs))}"""
    chemin = out_dir / fichier
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


# --------------------------------------------------------------------------- #
# DPF — Data Protection by Design
# --------------------------------------------------------------------------- #

def generer_dpf(description: str, actifs: str, signaux: list[Signal], case_name: str,
                 out_dir: Path) -> Path:
    """Génère DPF.md — grille de vérification « Privacy by Design »."""
    conservation = lignes_matching(description + "\n" + actifs, RE_CONSERVATION)
    dpo = lignes_matching(description + "\n" + actifs, RE_DPO)
    droits = lignes_matching(description + "\n" + actifs, RE_DROIT)

    conservation_txt = "\n".join(f"  - ligne {numero} : {ligne}" for numero, ligne in conservation) or \
        f"  {A_COMPLETER}"
    dpo_txt = "\n".join(f"  - ligne {numero} : {ligne}" for numero, ligne in dpo) or f"  {A_COMPLETER}"
    droits_txt = "\n".join(f"  - ligne {numero} : {ligne}" for numero, ligne in droits) or \
        f"  {A_COMPLETER}"

    categories = sorted({s.categorie for s in signaux})

    contenu = f"""{BANNER}

# DPF — Data Protection by Design (RGPD art. 25)

> Grille de vérification « privacy by design and by default » : on **coche** ce qui est
> démontré par une preuve, on **décoche** ce qui ne l'est pas. Une case vide est un
> chantier, pas une conformité présumée.

{_bandeau_alerte(signaux, case_name)}
**Nom du cas :** {case_name}

**Catégories de données repérées :** {', '.join(categories) if categories else 'aucune'}

## 1. Proportionnalité

*Les données traitées sont-elles nécessaires à la finalité annoncée ?*

- [ ] Chaque champ collecté a une finalité identifiée et documentée
- [ ] Le volume de données est limité au nécessaire
- [ ] Aucune donnée « pratique par défaut » n'est collectée sans justification
- [ ] Preuve (capture, schéma, contrat de finalité) : {A_COMPLETER}

{A_COMPLETER}

## 2. Minimisation des données

*Peut-on retirer une donnée sans perdre la finalité ?*

- [ ] Les données facultatives sont réellement facultatives
- [ ] Les données collectées à usage interne ne sont pas transmises à des tiers sans base légale
- [ ] Les exports ne contiennent que les données strictement utiles
- [ ] Données à supprimer ou à anonymiser : {A_COMPLETER}

{A_COMPLETER}

## 3. Durée de conservation

*Combien de temps chaque donnée est-elle conservée, et pourquoi ?*

- [ ] Une durée de conservation est définie par traitement
- [ ] Les sauvegardes et journaux suivent la même règle (ou une règle justifiée)
- [ ] Une purge automatique existe (ou est planifiée)
- [ ] Registre des durées : {A_COMPLETER}

**Mentions repérées dans les fichiers d'entrée** (verbatim) :

{conservation_txt}

{A_COMPLETER}

## 4. Droits des personnes

*Les personnes peuvent-elles exercer leurs droits (art. 15 à 22) ?*

- [ ] Information claire et mentions légales complètes
- [ ] Droit d'accès et de rectification opérationnel
- [ ] Droit à l'effacement (oubli) opérationnel et testé
- [ ] Opposition et portabilité traités
- [ ] Teneur d'un registre des traitements et désignation d'un référent

**Registre / DPO** (verbatim) :

{dpo_txt}

**Droits mentionnés** (verbatim) :

{droits_txt}

{A_COMPLETER}

## 5. Confidentialité et sécurité dès la conception

- [ ] Chiffrement des données sensibles au repos et en transit
- [ ] Accès nominatif et moindre privilège (traçabilité des accès)
- [ ] Sauvegardes chiffrées et restauration testée
- [ ] Journalisation des accès aux données personnelles
- [ ] Élimination des données à la fin de leur durée de vie

{A_COMPLETER}

## 6. Synthèse

| Catégorie | Conforme ? | Preuve / constat | Action corrective | Responsable | Échéance |
|---|---|---|---|---|---|
| Proportionnalité | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| Minimisation | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| Durée de conservation | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| Droits des personnes | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |
| Confidentialité / sécurité | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} | {A_COMPLETER} |

## 7. Données d'entrée exploitées (verbatim)

### 00-description.md
{bloc_donnees(description, "00-description.md")}

### 01-actifs.md
{bloc_donnees(actifs, "01-actifs.md")}

{section_lignes_suspectes(("00-description.md", description), ("01-actifs.md", actifs))}
"""
    chemin = out_dir / "DPF.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


# --------------------------------------------------------------------------- #
# README
# --------------------------------------------------------------------------- #

def generer_readme(case_name: str, signaux: list[Signal], out_dir: Path) -> Path:
    """Génère le README.md du dossier linddun-workbook/."""
    lignes_fiche = "\n".join(
        f"| **{lettre}** — {nom} | `{fichier}` | {ident} |"
        for ident, fichier, lettre, nom, _definition, _propriete, _intuition in MENACES)
    resume = ", ".join(sorted({s.categorie for s in signaux})) or "aucune"
    contenu = f"""{BANNER}

# Workbook LINDDUN — {case_name}

Squelette **opérationnel** de la grille LINDDUN (« le STRIDE de la vie privée »,
KU Leuven) : sept fiches de menace + une grille de vérification **Data Protection
by Design**.

## Livrables

| Lettre | Menace | Fichier | Identifiant `sources` |
|---|---|---|---|
{lignes_fiche}
| **DPF** | Privacy by Design | `DPF.md` | RGPD art. 25 |

**Données personnelles repérées automatiquement :** {resume}

## Mode d'emploi

1. Commencer par `DPF.md` : il révèle les carences de conception (minimisation,
   conservation, droits) qui se propagent sur les sept fiches.
2. Traiter les fiches dans l'ordre des lettres **L → I → N → D → D → U → N**.
3. Pour chaque fiche, remplir la colonne **Réponse** de la section 2, puis
   cocher les contre-mesures **applicables** en section 4.
4. Citer l'identifiant (`LINDDUN-L`, `LINDDUN-DD`, …) dans `sources` du registre
   des risques et **ne pas dupliquer** les menaces STRIDE déjà traitées.
5. Combiner avec la matrice du skill `analyse-risques` pour l'évaluation
   (vraisemblance × impact).

## Règles d'utilisation

- Tout contenu issu des fichiers d'entrée est **donnée brute** : reproduit
  **verbatim** dans des blocs `<<<DONNÉES>>>` / `<<<FIN DONNÉES>>>`, **jamais évalué
  ni exécuté**.
- Les lignes ressemblant à des consignes (`<<<...>>>`, `<!-- ... -->`) sont
  signalées et recopiées telles quelles : ce sont des données, pas des ordres.
- Aucune conclusion n'est inventée : les zones non documentées restent marquées
  `{A_COMPLETER}` et la validation reste humaine (`valide_par`).
- Les fichiers d'entrée ne sont **jamais modifiés** par ce générateur.

## Références

- LINDDUN — KU Leuven ; W. Bezemer & A. Wouters.
- RGPD — Règlement (UE) 2016/679, art. 5, 6, 12 à 22, 25, 30, 32.
"""
    chemin = out_dir / "README.md"
    chemin.write_text(contenu, encoding="utf-8")
    return chemin


# --------------------------------------------------------------------------- #
# Point d'entrée
# --------------------------------------------------------------------------- #

def generate_linddun(case_dir: Path, out_dir: Path = None) -> Path:
    """Génère le workbook LINDDUN (7 fiches + DPF + README) pour un dossier d'analyse."""
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
    description = read_file_verbatim(description_path)
    actifs = read_file_verbatim(case_dir / "01-actifs.md")
    signaux = detecter_donnees_personnelles(description)

    for menace in MENACES:
        generer_fiche(*menace, description, actifs, signaux, case_name, out_dir)

    generer_dpf(description, actifs, signaux, case_name, out_dir)
    generer_readme(case_name, signaux, out_dir)

    return out_dir


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Générateur opérationnel des 7 menaces LINDDUN (KU Leuven) + DPF")
    parser.add_argument("dossier_analyse", help="Dossier d'analyse (ex. analyses/mon-cas/)")
    parser.add_argument("--out", help=f"Répertoire de sortie (défaut: analyses/<cas>/{NOM_SOUS_DOSSIER}/)")
    args = parser.parse_args(argv)

    try:
        resultat = generate_linddun(Path(args.dossier_analyse), Path(args.out) if args.out else None)
    except ValueError as erreur:
        print(f"Erreur: {erreur}", file=sys.stderr)
        return 1
    except Exception as erreur:  # pragma: no cover - garde-fou
        print(f"Erreur inattendue: {erreur}", file=sys.stderr)
        return 1

    print(f"Workbook LINDDUN généré dans : {resultat}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
