# -*- coding: utf-8 -*-
"""Parseur d'archives ZIP : extraction **en mémoire** et analyse récursive.

Sécurité (zip-slip) : un membre dont le chemin est absolu, contient « .. » ou
pointe un lien symbolique est refusé et journalisé. Rien n'est jamais écrit
sur le disque par ce module — l'extraction reste en mémoire, avec des limites
dures (nombre de membres et taille totale décompressée).
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

from . import commun

LIMITE_MEMBRES = 200
LIMITE_TAILLE_TOTALE = 50 * 1024 * 1024  # 50 Mo décompressés
PROFONDEUR_MAX = 2

RE_ABSOLU_WINDOWS = re.compile(r"^[A-Za-z]:")

# Fichiers parasites ignorés sans bruit (métadonnées d'OS / d'archivage).
NOMS_IGNORES = ("__macosx/", ".ds_store", "thumbs.db", ".gitkeep")


def chemin_sur(nom: str) -> bool:
    """Vrai si le chemin d'un membre est sûr : relatif, sans « .. », sans absolu.

    Séparateurs Windows tolérés (`\\` convertis en `/`) car un ZIP peut être
    produit sous Windows puis extrait sous Linux.
    """
    if not isinstance(nom, str) or not nom.strip() or "\x00" in nom:
        return False
    candidat = nom.replace("\\", "/")
    if candidat.startswith("/") or RE_ABSOLU_WINDOWS.match(candidat):
        return False
    morceaux = [m for m in candidat.split("/") if m not in ("", ".")]
    if not morceaux or any(m == ".." for m in morceaux):
        return False
    return True


def _est_lien_symbolique(info: zipfile.ZipInfo) -> bool:
    """Détecte un membre de type lien symbolique (unix) dans l'archive."""
    import stat

    return stat.S_ISLNK(info.external_attr >> 16)


def _ignorable(nom: str) -> bool:
    minuscule = nom.replace("\\", "/").lower()
    return any( minuscule.startswith(nom_ignore) or minuscule.endswith("/" + nom_ignore.lstrip("/"))
               for nom_ignore in NOMS_IGNORES)


def lire_membres(zf: zipfile.ZipFile, meta: dict) -> list[tuple[str, bytes]]:
    """Décompresse les membres admissibles en mémoire.

    Renvoie la liste `(nom, données)`. Les membres dangereux (zip-slip, liens
    symboliques), trop nombreux ou trop volumineux sont **refusés** et
    journalisés dans `meta["avertissements"]` — ils ne sont jamais écrits.
    """
    membres: list[tuple[str, bytes]] = []
    infos = [i for i in zf.infolist() if not i.is_dir()]
    if len(infos) > LIMITE_MEMBRES:
        commun.avertir(
            meta,
            f"Archive tronquée : {len(infos)} membres (limite {LIMITE_MEMBRES}), "
            f"seuls les {LIMITE_MEMBRES} premiers sont analysés",
        )
        infos = infos[:LIMITE_MEMBRES]
    total = 0
    for info in infos:
        nom = info.filename
        if _ignorable(nom):
            continue
        if _est_lien_symbolique(info):
            commun.avertir(meta, f"Membre refusé (lien symbolique) : {nom}")
            continue
        if not chemin_sur(nom):
            commun.avertir(meta, f"Membre refusé (chemin non sûr, zip-slip) : {nom}")
            continue
        if info.file_size > LIMITE_TAILLE_TOTALE - total:
            commun.avertir(
                meta,
                f"Membre ignoré (limite de 50 Mo décompressés atteinte) : {nom}",
            )
            continue
        try:
            donnees = zf.read(nom)
        except Exception as exc:
            commun.avertir(meta, f"Membre illisible ignoré : {nom} ({exc})")
            continue
        # Contrôle a posteriori : un en-tête mentant ne doit pas passer.
        if len(donnees) > LIMITE_TAILLE_TOTALE - total:
            commun.avertir(meta, f"Membre ignoré (taille réelle excessive) : {nom}")
            continue
        total += len(donnees)
        membres.append((nom, donnees))
    return membres


def parse(chemin, meta: dict) -> str:
    """Ouvre une archive et analyse chaque membre (récursivement)."""
    try:
        zf = zipfile.ZipFile(chemin)
    except zipfile.BadZipFile as exc:
        return f"## Archive illisible\n\nFichier ZIP invalide ou corrompu : {exc}"
    with zf:
        try:
            membres = lire_membres(zf, meta)
        except Exception as exc:
            return f"## Archive illisible\n\nLecture impossible : {exc}"
    return _rendre(nom_archive=Path(chemin).name, membres=membres, meta=meta, profondeur=0)


def parse_bytes(nom: str, donnees: bytes, meta: dict) -> str:
    """Variante mémoire (archive imbriquée dans une archive)."""
    try:
        zf = zipfile.ZipFile(io.BytesIO(donnees))
    except zipfile.BadZipFile as exc:
        return f"## Archive illisible\n\nFichier ZIP invalide ou corrompu : {exc}"
    with zf:
        try:
            membres = lire_membres(zf, meta)
        except Exception as exc:
            return f"## Archive illisible\n\nLecture impossible : {exc}"
    return _rendre(nom_archive=nom, membres=membres, meta=meta, profondeur=0)


def _rendre(nom_archive: str, membres: list[tuple[str, bytes]], meta: dict, profondeur: int) -> str:
    sections = [f"## Archive — {nom_archive}"]
    if profondeur >= PROFONDEUR_MAX:
        commun.avertir(meta, f"Archive imbriquée non analysée (profondeur max {PROFONDEUR_MAX}) : {nom_archive}")
        return "\n\n".join(sections + ["*(archives imbriquées au-delà de la limite non analysées)*"])
    if not membres:
        sections.append("*(aucun membre admissible : voir les avertissements)*")
    for nom, donnees in membres:
        type_membre = detecter_type_interne(nom, donnees)
        if type_membre is None:
            commun.avertir(meta, f"Membre ignoré (type non pris en charge) : {nom}")
            sections.append(f"### Membre ignoré — {nom}\n\n*(type non pris en charge)*")
            continue
        module = commun.charger_parseur(type_membre)
        if type_membre == "zip":
            corps = _rendre(nom, _recharger(donnees, meta), meta, profondeur + 1)
        elif type_membre == "txt":
            corps = module.parse_txt_bytes(nom, donnees, meta)
        elif type_membre == "csv":
            corps = module.parse_csv_bytes(nom, donnees, meta)
        else:
            corps = module.parse_bytes(nom, donnees, meta)
        if not corps.strip():
            commun.avertir(meta, f"Membre sans contenu exploitable : {nom}")
        sections.append(f"### Membre — {nom}\n\n{corps}".rstrip())
    return "\n\n".join(sections)


def _recharger(donnees: bytes, meta: dict) -> list[tuple[str, bytes]]:
    """Relit les membres d'un ZIP imbriqué (déjà validé par chemin_sur)."""
    with zipfile.ZipFile(io.BytesIO(donnees)) as zf:
        return lire_membres(zf, meta)


def detecter_type_interne(nom: str, donnees: bytes) -> str | None:
    """Type d'un membre : extension, puis signature, puis contenu OOXML."""
    type_doc = commun.detecter_type(nom, donnees[:4096])
    if type_doc == "zip":
        return _type_ooxml(donnees)
    return type_doc


def _type_ooxml(donnees: bytes) -> str | None:
    """Un ZIP sans extension utile peut être un .docx/.xlsx/.pptx : on regarde l'intérieur."""
    try:
        with zipfile.ZipFile(io.BytesIO(donnees)) as zf:
            entrees = set(zf.namelist())
    except Exception:
        return None
    if any(n.startswith("word/") for n in entrees):
        return "docx"
    if any(n.startswith("xl/") for n in entrees):
        return "xlsx"
    if any(n.startswith("ppt/") for n in entrees):
        return "pptx"
    return "zip"