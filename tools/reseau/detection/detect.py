#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Détecteur de menaces local-only du homelab E21 (règles DET-01 → DET-12).

Usage :
    python3 -m tools.reseau.detection.detect evenements.jsonl [--regles PATH] [--out rapport.md]

Garde-fous :
* **aucun accès réseau** : le seul fichier lu est celui passé en argument (plus
  le fichier de règles) ; aucune résolution de nom, aucun enrichissement ;
* les données lues restent **brutes** : ni corrigées ni réécrites, l'événement
  déclencheur est repris **verbatim** (ligne source exacte) ;
* l'évaluation est **déterministe** : mêmes entrées → mêmes octets de rapport.
  Aucun horodatage d'exécution n'est inscrit dans le rapport ; la date affichée
  est celle du dernier événement lu ;
* le contenu des fichiers est traité comme une **donnée** : jamais de `eval` /
  `exec` ; les seules expressions régulières utilisées sont celles déclarées
  dans le fichier de règles.

Comment une règle se lit
------------------------
Chaque entrée de la liste `regles` du fichier de règles décrit une règle :

* `id`, `famille`, `intitule`, `tactique` : métadonnées (tableau de synthèse) ;
* `techniques_mitre` : liste de `{"id": "T1046", "nom": ...}` ; la **première**
  est la technique principale affichée dans la liste des alertes, toutes sont
  citées dans le tableau des occurrences ;
* `signaux` : **documentation en langage naturel** (pourquoi la règle existe) ;
  ce n'est pas une liste de conditions ;
* `menaces` : traceability (registre E21, grilles STRIDE/LINDDUN, sources) ;
* `regle` : la **seule logique exécutable**, avec un champ `type` :
  - `evenement` : alerte dès qu'un événement satisfait **toutes** les
    `conditions` ;
  - `compteur` : fenêtre glissante de `fenetre_s` secondes, groupée par la
    valeur du champ `cle`. Un événement n'est **admis** dans la fenêtre que s'il
    satisfait les conditions portant sur ses **propres champs** ; les conditions
    portant sur un **champ calculé** (`n_destinations`, `n_ports`, `n_sources`,
    `n_utilisateurs`, `total_octets`, `nb_evenements`) sont évaluées sur les
    agrégats de la fenêtre **candidat compris**. Alerte puis **réarmement**
    dès que la fenêtre atteint `seuil` événements ;
  - `sequence` : les `etapes` doivent être rencontrées **dans l'ordre du
    fichier** ; la dernière étape appariée déclenche l'alerte et réarme.
    `fenetre_s` borne l'écart entre la première et la dernière étape. L'état
    est suivi par valeur de `cle` si la règle en déclare une, sinon il est
    global à la règle.

Chaque condition est un dict `{"champ", "operateur", "valeur"}` avec les
opérateurs décrits par le fichier de règles : `egale`, `different`, `dans`,
`hors`, `contient`, `ne-contient-pas`, `regex`, `sup`, `inf`, `sup-ou-egal`,
`inf-ou-egal`, `present`, `absent`. Les comparaisons textuelles sont insensibles
à la casse ; dès que les deux operands sont des nombres la comparaison est
numérique. Pour une règle de type `evenement`, un champ calculé est évalué sur
le seul événement (tous ses agrégats valent donc 1 ou 0).
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

# Fichier de règles utilisé par défaut (résolu depuis ce module, pas depuis le
# répertoire courant) : le CLI fonctionne donc depuis n'importe où.
CHEMIN_REGLES_DEFAUT = Path(__file__).resolve().parent / "regles" / "regles-detection.json"

OPERATEURS = (
    "egale",
    "different",
    "dans",
    "hors",
    "contient",
    "ne-contient-pas",
    "regex",
    "sup",
    "inf",
    "sup-ou-egal",
    "inf-ou-egal",
    "present",
    "absent",
)

TYPES_REGLE = ("evenement", "compteur", "sequence")

CHAMPS_CALCULES = (
    "n_destinations",
    "n_ports",
    "n_utilisateurs",
    "n_sources",
    "total_octets",
    "nb_evenements",
)

OPERATEURS_SANS_VALEUR = ("present", "absent")

SUFFIXES_FORMAT = {
    ".jsonl": "jsonl",
    ".ndjson": "jsonl",
    ".json": "json",
    ".csv": "csv",
}

LIBELLE_FORMAT = {
    "jsonl": "JSON Lines",
    "json": "JSON (tableau d'objets)",
    "csv": "CSV",
    "vide": "fichier vide",
}


class ErreurRegles(ValueError):
    """Fichier de règles introuvable, illisible ou structurellement invalide."""

    def __init__(self, problemes: Sequence[str]) -> None:
        self.problemes = list(problemes)
        super().__init__(" ; ".join(self.problemes) or "fichier de règles invalide")


class ErreurEvenements(ValueError):
    """Fichier d'événements illisible ou mal formé."""


# ---------------------------------------------------------------------------
# Opérateurs : evaluation d'une condition sur une valeur brute
# ---------------------------------------------------------------------------


def _texte_ou_vide(brut: Any) -> str:
    """Représentation textuelle d'une valeur brute (jamais réécrite)."""
    if brut is None or isinstance(brut, (list, tuple, set, dict)):
        return ""
    return str(brut).strip()


def _nombre(brut: Any) -> float | None:
    """Valeur numérique d'une donnée brute, ou None si elle n'en est pas une."""
    if isinstance(brut, bool) or brut is None:
        return None
    if isinstance(brut, (int, float)):
        return float(brut)
    texte = _texte_ou_vide(brut)
    if not texte:
        return None
    try:
        return float(texte)
    except ValueError:
        return None


def _egal(brut: Any, valeur: Any) -> bool:
    """Égalité numérique si les deux operands sont des nombres, sinon textuelle."""
    nombre_brut = _nombre(brut)
    nombre_valeur = _nombre(valeur)
    if nombre_brut is not None and nombre_valeur is not None:
        return nombre_brut == nombre_valeur
    return _texte_ou_vide(brut).lower() == _texte_ou_vide(valeur).lower()


def _dans(brut: Any, valeur: Any) -> bool:
    """Appartenance à une liste de valeurs (ou égalité si `valeur` est scalaire)."""
    if isinstance(valeur, (list, tuple, set)):
        return any(_egal(brut, candidat) for candidat in valeur)
    return _egal(brut, valeur)


def appliquer_operateur(
    operateur: str,
    brut: Any,
    valeur: Any,
    motif: re.Pattern[str] | None = None,
) -> bool:
    """Applique un opérateur de `regles-detection.json` à une valeur brute.

    Une donnée absente ne satisfait que `absent` : toute autre condition est
    fausse (aucune valeur n'est inventée). Une comparaison numérique impossible
    (opérande non numérique) est également fausse.
    """
    if operateur == "present":
        return _texte_ou_vide(brut) != ""
    if operateur == "absent":
        return _texte_ou_vide(brut) == ""
    if brut is None:
        return False
    if operateur == "egale":
        return _egal(brut, valeur)
    if operateur == "different":
        return not _egal(brut, valeur)
    if operateur == "dans":
        return _dans(brut, valeur)
    if operateur == "hors":
        return not _dans(brut, valeur)
    if operateur == "contient":
        return _texte_ou_vide(valeur).lower() in _texte_ou_vide(brut).lower()
    if operateur == "ne-contient-pas":
        return _texte_ou_vide(valeur).lower() not in _texte_ou_vide(brut).lower()
    if operateur == "regex":
        return motif is not None and motif.search(_texte_ou_vide(brut)) is not None
    nombre_brut = _nombre(brut)
    nombre_valeur = _nombre(valeur)
    if nombre_brut is None or nombre_valeur is None:
        return False
    if operateur == "sup":
        return nombre_brut > nombre_valeur
    if operateur == "inf":
        return nombre_brut < nombre_valeur
    if operateur == "sup-ou-egal":
        return nombre_brut >= nombre_valeur
    if operateur == "inf-ou-egal":
        return nombre_brut <= nombre_valeur
    raise ErreurRegles([f"opérateur inconnu : {operateur}"])


def _analyser_ts(texte: str) -> datetime | None:
    """Horodatage ISO 8601 → datetime UTC (sans fuseau : supposé UTC)."""
    candidat = _texte_ou_vide(texte)
    if not candidat:
        return None
    if candidat.endswith(("Z", "z")):
        candidat = candidat[:-1] + "+00:00"
    try:
        instant = datetime.fromisoformat(candidat)
    except ValueError:
        return None
    if instant.tzinfo is None:
        return instant.replace(tzinfo=timezone.utc)
    return instant


def _hors_fenetre(debut: datetime | None, fin: datetime | None, fenetre_s: float) -> bool:
    """Vrai si `fin` sort de la fenêtre de `fenetre_s` secondes ouverte sur `debut`."""
    if debut is None or fin is None:
        return False
    return (fin - debut).total_seconds() > fenetre_s


# ---------------------------------------------------------------------------
# Modèle de données
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Condition:
    """Condition `{"champ", "operateur", "valeur"}` d'une règle."""

    champ: str
    operateur: str
    valeur: Any = None
    motif: re.Pattern[str] | None = None

    def evaluer(self, donnees: dict[str, Any], agregats: dict[str, Any]) -> bool:
        """Évalue la condition sur un événement et ses agrégats de fenêtre."""
        brut = agregats.get(self.champ) if self.champ in CHAMPS_CALCULES else donnees.get(self.champ)
        return appliquer_operateur(self.operateur, brut, self.valeur, self.motif)


@dataclass(frozen=True)
class Regle:
    """Règle de détection exécutable, construite depuis le fichier de règles."""

    identifiant: str
    famille: str
    intitule: str
    tactique: str
    techniques: tuple[dict[str, Any], ...]
    signaux: tuple[str, ...]
    type_regle: str
    conditions: tuple[Condition, ...]
    conditions_evenement: tuple[Condition, ...] = field(default=())
    conditions_agregats: tuple[Condition, ...] = field(default=())
    cle: str | None = None
    fenetre_s: float = 0.0
    seuil: int = 1
    etapes: tuple[tuple[str, tuple[Condition, ...]], ...] = ()

    def technique_principale(self) -> str:
        """Première technique MITRE de la règle (`T#### Nom`), ou « - »."""
        if not self.techniques:
            return "-"
        return _libelle_technique(self.techniques[0])

    def libelle_techniques(self) -> str:
        """Toutes les techniques MITRE de la règle, séparées par des virgules."""
        if not self.techniques:
            return "-"
        return ", ".join(_libelle_technique(technique) for technique in self.techniques)


def _libelle_technique(technique: dict[str, Any]) -> str:
    identifiant = _texte_ou_vide(technique.get("id"))
    nom = _texte_ou_vide(technique.get("nom"))
    return " ".join(partie for partie in (identifiant, nom) if partie) or "-"


@dataclass(frozen=True)
class Evenement:
    """Événement lu tel quel : données brutes + ligne source verbatim."""

    donnees: dict[str, Any]
    brut: str
    numero: int

    @property
    def ts(self) -> str:
        """Horodatage brut de l'événement."""
        return _texte_ou_vide(self.donnees.get("ts"))

    @property
    def instant(self) -> datetime | None:
        """Horodatage analysé (None si absent ou illisible)."""
        return _analyser_ts(self.ts)

    def rendre_json(self) -> str:
        """Rendu compact de l'événement, ordre des champs d'origine conservé."""
        return json.dumps(self.donnees, ensure_ascii=False)


@dataclass(frozen=True)
class Alerte:
    """Alerte : une règle qui a été déclenchée par un événement."""

    regle: Regle
    evenement: Evenement
    raison: str


# ---------------------------------------------------------------------------
# Lecture du fichier de règles
# ---------------------------------------------------------------------------


def _construire_conditions(
    bruts: Any,
    champs_autorises: set[str],
    contexte: str,
    problemes: list[str],
) -> tuple[Condition, ...]:
    """Transforme une liste de conditions brutes en objets `Condition` validés."""
    if not isinstance(bruts, list) or not bruts:
        problemes.append(f"{contexte} : « conditions » doit être une liste non vide")
        return ()
    conditions: list[Condition] = []
    for index, brut in enumerate(bruts):
        where = f"{contexte} condition #{index + 1}"
        if not isinstance(brut, dict):
            problemes.append(f"{where} : objet JSON attendu")
            continue
        champ = _texte_ou_vide(brut.get("champ"))
        operateur = _texte_ou_vide(brut.get("operateur"))
        if champ not in champs_autorises:
            problemes.append(f"{where} : champ inconnu « {champ} »")
            continue
        if operateur not in OPERATEURS:
            problemes.append(f"{where} : opérateur inconnu « {operateur} »")
            continue
        if "valeur" not in brut and operateur not in OPERATEURS_SANS_VALEUR:
            problemes.append(f"{where} : champ « valeur » manquant")
            continue
        valeur = brut.get("valeur")
        motif: re.Pattern[str] | None = None
        if operateur == "regex":
            motif = _compiler_motif(valeur, where, problemes)
        conditions.append(Condition(champ=champ, operateur=operateur, valeur=valeur, motif=motif))
    return tuple(conditions)


def _compiler_motif(valeur: Any, where: str, problemes: list[str]) -> re.Pattern[str] | None:
    """Compile une expression régulière (insensible à la casse) ou signale l'erreur."""
    if not isinstance(valeur, str):
        problemes.append(f"{where} : « regex » attend une chaîne, reçu {type(valeur).__name__}")
        return None
    try:
        return re.compile(valeur, re.IGNORECASE)
    except re.error as exc:
        problemes.append(f"{where} : expression régulière invalide ({exc})")
        return None


def _construire_regle(brut: Any, index: int, champs_autorises: set[str], problemes: list[str]) -> Regle | None:
    """Valide une règle brute et renvoie l'objet `Regle` correspondant."""
    if not isinstance(brut, dict):
        problemes.append(f"règle #{index + 1} : objet JSON attendu")
        return None
    identifiant = _texte_ou_vide(brut.get("id"))
    where = f"règle {identifiant or f'#{index + 1}'}"
    if not identifiant:
        problemes.append(f"{where} : « id » manquant")
    famille = _texte_ou_vide(brut.get("famille"))
    if not famille:
        problemes.append(f"{where} : « famille » manquante")
    type_regle = _texte_ou_vide((brut.get("regle") or {}).get("type")) if isinstance(brut.get("regle"), dict) else ""
    if type_regle not in TYPES_REGLE:
        problemes.append(f"{where} : « regle.type » doit valoir {', '.join(TYPES_REGLE)}")
        return None

    corps = brut["regle"]
    techniques = tuple(t for t in brut.get("techniques_mitre") or [] if isinstance(t, dict))
    signaux = tuple(s for s in brut.get("signaux") or [] if isinstance(s, str))
    # Une règle `sequence` porte ses conditions dans `etapes` : `conditions`
    # n'est attendu que pour les règles `evenement` et `compteur`.
    conditions: tuple[Condition, ...] = ()
    if "conditions" in corps or type_regle in ("evenement", "compteur"):
        conditions = _construire_conditions(corps.get("conditions"), champs_autorises, where, problemes)
    conditions_evenement = tuple(c for c in conditions if c.champ not in CHAMPS_CALCULES)
    conditions_agregats = tuple(c for c in conditions if c.champ in CHAMPS_CALCULES)

    cle: str | None = None
    fenetre_s = 0.0
    seuil = 1
    etapes: tuple[tuple[str, tuple[Condition, ...]], ...] = ()

    if type_regle == "compteur":
        cle = _texte_ou_vide(corps.get("cle")) or None
        if cle is None:
            problemes.append(f"{where} : « regle.cle » manquante pour une règle compteur")
        fenetre_s = _nombre(corps.get("fenetre_s")) or 0.0
        seuil_brut = _nombre(corps.get("seuil"))
        if seuil_brut is None or seuil_brut < 1:
            problemes.append(f"{where} : « regle.seuil » doit être un entier ≥ 1")
            seuil_brut = 1
        seuil = int(seuil_brut)
        if not conditions_evenement and not conditions_agregats:
            problemes.append(f"{where} : règle compteur sans condition")
    elif type_regle == "sequence":
        cle = _texte_ou_vide(corps.get("cle")) or None
        fenetre_s = _nombre(corps.get("fenetre_s")) or 0.0
        bruts_etapes = corps.get("etapes")
        if not isinstance(bruts_etapes, list) or not bruts_etapes:
            problemes.append(f"{where} : « regle.etapes » doit être une liste non vide")
        else:
            liste: list[tuple[str, tuple[Condition, ...]]] = []
            for position, etape in enumerate(bruts_etapes, start=1):
                if not isinstance(etape, dict):
                    problemes.append(f"{where} étape #{position} : objet JSON attendu")
                    continue
                nom = _texte_ou_vide(etape.get("nom")) or f"étape {position}"
                conditions_etape = _construire_conditions(
                    etape.get("conditions"), champs_autorises, f"{where} étape {position} ({nom})", problemes
                )
                if not conditions_etape:
                    problemes.append(f"{where} étape {position} : aucune condition exploitable")
                    continue
                liste.append((nom, conditions_etape))
            etapes = tuple(liste)

    return Regle(
        identifiant=identifiant,
        famille=famille,
        intitule=_texte_ou_vide(brut.get("intitule")),
        tactique=_texte_ou_vide(brut.get("tactique")),
        techniques=techniques,
        signaux=signaux,
        type_regle=type_regle,
        conditions=conditions,
        conditions_evenement=conditions_evenement,
        conditions_agregats=conditions_agregats,
        cle=cle,
        fenetre_s=fenetre_s,
        seuil=seuil,
        etapes=etapes,
    )


def charger_regles(chemin: Path) -> tuple[list[Regle], dict[str, Any]]:
    """Charge et valide le fichier de règles.

    Renvoie la liste des règles (dans l'ordre du fichier) et l'en-tête du
    document (nom, version). Lève `ErreurRegles` si le fichier est inaccessible,
    illisible ou si une règle est structurellement invalide (toutes les anomalies
    sont signalées d'un coup).
    """
    try:
        texte = chemin.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ErreurRegles([f"fichier de règles illisible : {chemin} ({exc.strerror or exc})"]) from exc
    try:
        document = json.loads(texte)
    except json.JSONDecodeError as exc:
        raise ErreurRegles([f"fichier de règles illisible (JSON invalide) : {exc}"]) from exc
    if not isinstance(document, dict):
        raise ErreurRegles(["fichier de règles invalide : objet JSON attendu à la racine"])
    brutes = document.get("regles")
    if not isinstance(brutes, list) or not brutes:
        raise ErreurRegles(["fichier de règles invalide : clé « regles » absente ou vide"])

    champs_autorises = set(CHAMPS_CALCULES) | set(document.get("schema_evenement") or {})
    problemes: list[str] = []
    regles: list[Regle] = []
    identifiants: set[str] = set()
    for index, brut in enumerate(brutes, start=1):
        regle = _construire_regle(brut, index, champs_autorises, problemes)
        if regle is None:
            continue
        if regle.identifiant in identifiants:
            problemes.append(f"règle {regle.identifiant} : identifiant dupliqué")
        identifiants.add(regle.identifiant)
        regles.append(regle)
    if problemes:
        raise ErreurRegles(problemes)
    return regles, document


# ---------------------------------------------------------------------------
# Lecture du fichier d'événements
# ---------------------------------------------------------------------------


def _contenu_evenements(bruts: Any) -> list[dict[str, Any]]:
    """Extrait la liste d'objets-événements d'un document JSON."""
    if isinstance(bruts, list):
        return [elt for elt in bruts if isinstance(elt, dict)]
    if isinstance(bruts, dict):
        for cle in ("evenements", "events", "logs"):
            valeur = bruts.get(cle)
            if isinstance(valeur, list):
                return [elt for elt in valeur if isinstance(elt, dict)]
    raise ErreurEvenements("objet JSON inattendu : tableau d'événements attendu")


def _lire_jsonl(texte: str) -> list[Evenement]:
    """JSON Lines : une ligne non vide = un événement."""
    evenements: list[Evenement] = []
    for numero, ligne in enumerate(texte.splitlines(), start=1):
        contenu = ligne.strip()
        if not contenu:
            continue
        try:
            charge = json.loads(contenu)
        except json.JSONDecodeError as exc:
            raise ErreurEvenements(f"ligne {numero} : JSON invalide ({exc.msg})") from exc
        if not isinstance(charge, dict):
            raise ErreurEvenements(f"ligne {numero} : objet JSON attendu")
        evenements.append(Evenement(donnees=charge, brut=contenu, numero=len(evenements)))
    return evenements


def _lire_csv(texte: str) -> list[Evenement]:
    """CSV : première ligne = en-tête, une ligne = un événement.

    La ligne source est conservée telle quelle dans `brut` (verbatim) et les
    valeurs ne subissent aucun nettoyage : le CSV est un format texte, les
    champs restent donc des chaînes, y compris `port` et `octets` que les
    opérateurs numériques normalisent au moment de l'évaluation.
    """
    lignes = list(csv.reader(io.StringIO(texte)))
    if not lignes:
        return []
    entete = lignes[0]
    if not any(colonne.strip() for colonne in entete):
        return []
    evenements: list[Evenement] = []
    for numero, ligne in enumerate(lignes[1:], start=2):
        if not any(colonne.strip() for colonne in ligne):
            continue
        if len(ligne) < len(entete):
            ligne = ligne + [""] * (len(entete) - len(ligne))
        donnees = {nom: valeur for nom, valeur in zip(entete, ligne) if nom}
        # `brut` reprend la ligne d'origine, pas une re-sérialisation : c'est
        # ce qui garantit le caractère verbatim dans le rapport.
        brut = texte.splitlines()[numero - 1] if numero - 1 < len(texte.splitlines()) else ",".join(ligne)
        evenements.append(Evenement(donnees=donnees, brut=brut, numero=len(evenements)))
    return evenements


def lire_evenements(chemin: Path) -> tuple[list[Evenement], str]:
    """Lit un fichier d'événements local et renvoie (événements, format lu).

    Formats acceptés : JSON Lines (`.jsonl`), JSON (tableau d'objets, `.json`)
    et CSV (`.csv`). Le format est déduit de l'extension, du suffixe absent
    tombant sur la première ligne non vide.
    """
    try:
        texte = chemin.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise ErreurEvenements(f"fichier d'événements illisible : {chemin} ({exc.strerror or exc})") from exc
    if not texte.strip():
        return [], "vide"

    format_suffixe = SUFFIXES_FORMAT.get(chemin.suffix.lower())
    if format_suffixe is None:
        premiere = next((ligne.strip() for ligne in texte.splitlines() if ligne.strip()), "")
        if premiere.startswith("{"):
            format_suffixe = "jsonl"
        elif premiere.startswith("["):
            format_suffixe = "json"
        else:
            format_suffixe = "csv"
        return _decoder_evenements(texte, format_suffixe)
    return _decoder_evenements(texte, format_suffixe)


def _decoder_evenements(texte: str, format_lu: str) -> tuple[list[Evenement], str]:
    """Aiguille le texte lu vers le décodeur correspondant au format."""
    if format_lu == "csv":
        return _lire_csv(texte), format_lu
    if format_lu == "jsonl":
        return _lire_jsonl(texte), format_lu
    try:
        document = json.loads(texte)
    except json.JSONDecodeError as exc:
        raise ErreurEvenements(f"JSON invalide ({exc.msg}, ligne {exc.lineno})") from exc
    return [_envelopper_evenement(elt, numero) for numero, elt in enumerate(_contenu_evenements(document))], format_lu


def _envelopper_evenement(donnees: dict[str, Any], numero: int) -> Evenement:
    """Enveloppe un objet-événement en `Evenement` (brut = sérialisation stable)."""
    return Evenement(
        donnees=donnees,
        brut=json.dumps(donnees, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        numero=numero,
    )


# ---------------------------------------------------------------------------
# Champs calculés et évaluation des règles
# ---------------------------------------------------------------------------


def calculer_agregats(evenements: Sequence[Evenement]) -> dict[str, Any]:
    """Champs calculés d'un ensemble d'événements (fenêtre ou événement seul)."""
    destinations = {e.donnees.get("dest") for e in evenements if e.donnees.get("dest") is not None}
    ports = {e.donnees.get("port") for e in evenements if e.donnees.get("port") not in (None, "")}
    utilisateurs = {e.donnees.get("utilisateur") for e in evenements if e.donnees.get("utilisateur")}
    sources = {e.donnees.get("source") for e in evenements if e.donnees.get("source")}
    total_octets = 0
    for evenement in evenements:
        nombre = _nombre(evenement.donnees.get("octets"))
        if nombre is not None:
            total_octets += int(nombre)
    return {
        "n_destinations": len(destinations),
        "n_ports": len(ports),
        "n_utilisateurs": len(utilisateurs),
        "n_sources": len(sources),
        "total_octets": total_octets,
        "nb_evenements": len(evenements),
    }


def _respecte(conditions: Sequence[Condition], evenement: Evenement, agregats: dict[str, Any]) -> bool:
    """Vrai si l'événement satisfait **toutes** les conditions."""
    return all(condition.evaluer(evenement.donnees, agregats) for condition in conditions)


def evaluer_evenement(regle: Regle, evenements: Sequence[Evenement]) -> list[Alerte]:
    """Règle `evenement` : une alerte par événement conforme.

    Les champs calculés éventuels sont évalués sur le seul événement candidat.
    """
    alertes: list[Alerte] = []
    for evenement in evenements:
        agregats = {} if not regle.conditions_agregats else calculer_agregats([evenement])
        if _respecte(regle.conditions, evenement, agregats):
            detail = regle.conditions[0].champ if regle.conditions else "-"
            alertes.append(
                Alerte(regle=regle, evenement=evenement, raison=f"toutes les conditions sont satisfaites (déclencheur : {detail})")
            )
    return alertes


def evaluer_compteur(regle: Regle, evenements: Sequence[Evenement]) -> list[Alerte]:
    """Règle `compteur` : fenêtre glissante par valeur de `cle`, réarmement après alerte.

    Seuls les événements conformes aux conditions **propres** entrent dans la
    fenêtre ; la fenêtre est purgée des événements de plus de `fenetre_s`
    secondes. L'alerte part quand la fenêtre contient au moins `seuil`
    événements conformes **et** que les conditions calculées sont satisfaites
    sur les agrégats de la fenêtre (candidat compris).
    """
    alertes: list[Alerte] = []
    if regle.cle is None:
        return alertes
    fenetres: dict[str, deque[Evenement]] = {}
    for evenement in evenements:
        valeur_cle = _texte_ou_vide(evenement.donnees.get(regle.cle))
        if not valeur_cle:
            continue
        if not _respecte(regle.conditions_evenement, evenement, {}):
            continue
        fenetre = fenetres.setdefault(valeur_cle, deque())
        instant = evenement.instant
        while fenetre and _hors_fenetre(fenetre[0].instant, instant, regle.fenetre_s):
            fenetre.popleft()
        fenetre.append(evenement)
        if regle.conditions_agregats:
            agregats = calculer_agregats(fenetre)
            if not _respecte(regle.conditions_agregats, evenement, agregats):
                continue
        if len(fenetre) >= regle.seuil:
            resume = ", ".join(
                f"{condition.champ}={agregats[condition.champ]}" for condition in regle.conditions_agregats
            )
            alertes.append(
                Alerte(
                    regle=regle,
                    evenement=evenement,
                    raison=f"seuil atteint : {len(fenetre)} événements conformes en {regle.fenetre_s:g} s "
                    f"(clé {regle.cle}={valeur_cle}"
                    + (f", {resume}" if regle.conditions_agregats else "")
                    + ")",
                )
            )
            fenetre.clear()  # réarmement
    return alertes


def evaluer_sequence(regle: Regle, evenements: Sequence[Evenement]) -> list[Alerte]:
    """Règle `sequence` : étapes dans l'ordre du fichier, la dernière déclenche.

    L'état de progression est suivi par valeur de `cle` si la règle en déclare
    une, sinon globalement. Au-delà de `fenetre_s` depuis la première étape
    appariée, la progression repart de zéro. Après une alerte, la progression est
    réarmée.
    """
    alertes: list[Alerte] = []
    if not regle.etapes:
        return alertes
    progressions: dict[str, list[Evenement]] = {}
    for evenement in evenements:
        valeur_cle = _texte_ou_vide(evenement.donnees.get(regle.cle)) if regle.cle else ""
        if regle.cle and not valeur_cle:
            continue
        progression = progressions.setdefault(valeur_cle, [])
        if progression and _hors_fenetre(progression[0].instant, evenement.instant, regle.fenetre_s):
            progression.clear()
        position = len(progression)
        if position >= len(regle.etapes):
            progression.clear()
            position = 0
        conditions = regle.etapes[position][1]
        agregats = {} if not any(c.champ in CHAMPS_CALCULES for c in conditions) else calculer_agregats([evenement])
        if not _respecte(conditions, evenement, agregats):
            continue
        progression.append(evenement)
        if len(progression) == len(regle.etapes):
            noms = " → ".join(nom for nom, _ in regle.etapes)
            alertes.append(
                Alerte(regle=regle, evenement=evenement, raison=f"étapes respectées dans l'ordre du fichier : {noms}")
            )
            progression.clear()  # réarmement
    return alertes


EVALUATEURS = {
    "evenement": evaluer_evenement,
    "compteur": evaluer_compteur,
    "sequence": evaluer_sequence,
}


def evaluer(regles: Sequence[Regle], evenements: Sequence[Evenement]) -> list[Alerte]:
    """Évalue toutes les règles sur tous les événements (déterministe)."""
    alertes: list[Alerte] = []
    for regle in regles:
        try:
            alertes.extend(EVALUATEURS[regle.type_regle](regle, evenements))
        except ErreurRegles:
            raise
        except (TypeError, ValueError) as exc:  # donnée d'événement inattendue
            raise ErreurEvenements(f"règle {regle.identifiant} : évaluation impossible ({exc})") from exc
    return alertes


# ---------------------------------------------------------------------------
# Rapport Markdown
# ---------------------------------------------------------------------------


def _cellule(texte: str) -> str:
    """Échappe une valeur pour la cellule d'un tableau Markdown."""
    return texte.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").strip()


def _techniques(regle: Regle) -> str:
    """Liste des identifiants MITRE de la règle (pour le tableau d'occurrences)."""
    identifiants = [
        identifiant
        for identifiant in (_texte_ou_vide(technique.get("id")) for technique in regle.techniques)
        if identifiant
    ]
    return ", ".join(identifiants) or "-"


def date_rapport(evenements: Sequence[Evenement]) -> str:
    """Date (YYYY-MM-DD) du dernier événement horodaté, ou `inconnue`."""
    dates = sorted(e.ts[:10] for e in evenements if re.match(r"^\d{4}-\d{2}-\d{2}", e.ts))
    return dates[-1] if dates else "inconnue"


def generer_rapport(
    evenements: Sequence[Evenement],
    regles: Sequence[Regle],
    alertes: Sequence[Alerte],
    nom_regles: str,
    format_lu: str,
) -> str:
    """Produit le rapport Markdown complet (déterministe, sans horloge système)."""
    occurrences: dict[str, list[Alerte]] = {regle.identifiant: [] for regle in regles}
    for alerte in alertes:
        occurrences.setdefault(alerte.regle.identifiant, []).append(alerte)

    lignes = [
        f"# Rapport de détection E21 — {date_rapport(evenements)}",
        "",
        f"- Date de référence : {date_rapport(evenements)} (date du dernier événement analysé)",
        f"- Règles : `{nom_regles}` ({len(regles)} règles chargées)",
        f"- Événements analysés : {len(evenements)} (format : {LIBELLE_FORMAT.get(format_lu, format_lu)})",
        f"- Alertes déclenchées : {len(alertes)}",
        "",
        "> Détection local-only : aucun accès réseau, aucun enrichissement ; les événements",
        "> déclencheurs sont repris verbatim dans le tableau des alertes.",
        "",
        "## Occurrences par règle",
        "",
        "| Règle | Famille | Alertes | Techniques MITRE |",
        "|---|---|---|---|",
    ]
    for regle in regles:
        trouvees = occurrences.get(regle.identifiant, [])
        lignes.append(
            f"| {regle.identifiant} | {_cellule(regle.famille)} | {len(trouvees)} | {_cellule(_techniques(regle))} |"
        )
    if not alertes:
        lignes += ["", "Aucune alerte : aucun seuil de détection atteint sur ce flux."]
        return "\n".join(lignes) + "\n"

    lignes += [
        "",
        "## Alertes",
        "",
        "| ts | Règle | Famille | Technique | Détail (verbatim) |",
        "|---|---|---|---|---|",
    ]
    for alerte in alertes:
        lignes.append(
            f"| {_cellule(alerte.evenement.ts or '-')} | {alerte.regle.identifiant} "
            f"| {_cellule(alerte.regle.famille)} | {_cellule(alerte.regle.technique_principale())} "
            f"| `{_cellule(alerte.evenement.brut)}` |"
        )
    lignes += ["", "## Motifs", ""]
    for alerte in alertes:
        lignes.append(
            f"- **{alerte.regle.identifiant}** ({alerte.regle.intitule or 'sans intitulé'}) "
            f"— {alerte.regle.tactique or 'tactique inconnue'} — {alerte.raison}."
        )
    return "\n".join(lignes) + "\n"


def resume_console(evenements: Sequence[Evenement], regles: Sequence[Regle], alertes: Sequence[Alerte]) -> None:
    """Affiche un résumé court sur la sortie standard."""
    print(f"Événements analysés : {len(evenements)}")
    print(f"Règles chargées    : {len(regles)}")
    print(f"Alertes déclenchées: {len(alertes)}")
    familles = sorted({alerte.regle.famille for alerte in alertes})
    if familles:
        print(f"Familles concernées: {len(familles)}")
        for famille in familles:
            identifiants = sorted({a.regle.identifiant for a in alertes if a.regle.famille == famille})
            print(f"  - {famille} ({', '.join(identifiants)})")
    else:
        print("Familles concernées: aucune")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    """Point d'entrée du CLI : évalue un flux et produit un rapport."""
    analyseur = argparse.ArgumentParser(
        prog="python3 -m tools.reseau.detection.detect",
        description="Détection de menaces local-only : évalue des événements du homelab contre les règles E21.",
    )
    analyseur.add_argument("fichier_evenements", help="fichier d'événements (JSON Lines, JSON ou CSV)")
    analyseur.add_argument(
        "--regles",
        default=str(CHEMIN_REGLES_DEFAUT),
        help="fichier de règles JSON (défaut : regles/regles-detection.json)",
    )
    analyseur.add_argument("--out", default=None, help="écrit le rapport Markdown dans ce fichier")
    args = analyseur.parse_args(argv)

    chemin_regles = Path(args.regles)
    try:
        regles, document = charger_regles(chemin_regles)
    except ErreurRegles as exc:
        for probleme in exc.problemes:
            print(f"erreur : {probleme}", file=sys.stderr)
        return 2

    try:
        evenements, format_lu = lire_evenements(Path(args.fichier_evenements))
    except ErreurEvenements as exc:
        print(f"erreur : {exc}", file=sys.stderr)
        return 2

    alertes = evaluer(regles, evenements)
    rapport = generer_rapport(evenements, regles, alertes, chemin_regles.name, format_lu)

    if args.out:
        chemin_rapport = Path(args.out)
        if chemin_rapport.parent != Path(""):
            chemin_rapport.parent.mkdir(parents=True, exist_ok=True)
        chemin_rapport.write_text(rapport, encoding="utf-8")
        print(f"Rapport écrit : {chemin_rapport}")
    else:
        print("Aucun --out fourni : rapport non écrit sur disque. Utiliser --out <fichier> pour l'obtenir.")

    resume_console(evenements, regles, alertes)
    nom_regles_doc = _texte_ou_vide(document.get("nom")) or chemin_regles.name
    print(f"Référentiel de règles : {nom_regles_doc} v{_texte_ou_vide(document.get('version')) or '?'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())