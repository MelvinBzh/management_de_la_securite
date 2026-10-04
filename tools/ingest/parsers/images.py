# -*- coding: utf-8 -*-
"""Parseur images (PNG/JPG/WebP/BMP/GIF/TIFF) : OCR du contenu visible.

L'image est une DONNÉE : le texte reconnu est recopié tel quel. Aucun backend
OCR => `meta["ocr"] = "disabled"` + marqueur explicite dans le markdown.
"""
from __future__ import annotations

from . import commun, ocr


def parse(chemin, meta: dict) -> str:
    """OCR d'une image depuis un chemin."""
    with open(chemin, "rb") as fichier:
        return parse_bytes(chemin, fichier.read(), meta)


def parse_bytes(nom: str, donnees: bytes, meta: dict) -> str:
    """OCR d'une image depuis des octets (membres d'archive)."""
    import io

    from PIL import Image, UnidentifiedImageError

    try:
        image = Image.open(io.BytesIO(donnees))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        commun.avertir(meta, f"Image illisible ignorée : {nom} ({exc})")
        return ""

    parties = [f"## Image — {nom}", _description(image)]
    texte = _ocr_image(image, meta)
    if texte:
        parties.append(texte)
    return "\n\n".join(p for p in parties if p)


def _description(image) -> str:
    """Dimensions et mode : métadonnées factuelles utiles à l'analyste."""
    return f"- Dimensions : {image.width} × {image.height} px (mode {image.mode})"


def _ocr_image(image, meta: dict) -> str:
    if not ocr.disponible():
        commun.avertir(meta, ocr.avertissement_backend())
        meta["ocr"] = "disabled"
        return ocr.PLACEHOLDER_OCR_INDISPONIBLE
    try:
        texte = commun.normaliser(ocr.image_vers_texte(image))
    except Exception as exc:
        commun.avertir(meta, f"OCR impossible sur l'image ({exc})")
        return ocr.PLACEHOLDER_OCR_INDISPONIBLE
    meta["ocr"] = True
    if not texte:
        commun.avertir(meta, "OCR sans texte reconnu sur l'image")
        return "*(aucun texte reconnu par l'OCR sur cette image)*"
    return "### Texte reconnu (OCR)\n\n" + texte