# -*- coding: utf-8 -*-
"""Couche OCR (pytesseract + binaire tesseract) avec dégradation gracieuse.

Si le backend est absent, l'ingestion ne s'arrête pas : la couche texte est
quand même extraite et les pages sans texte sont marquées par un marqueur
explicite (`PLACEHOLDER_OCR_INDISPONIBLE`) dans le markdown produit.
"""
from __future__ import annotations

import io
import shutil

# Texte inséré dans le markdown quand aucun backend OCR n'est disponible.
PLACEHOLDER_OCR_INDISPONIBLE = "[OCR indisponible — installer tesseract-ocr + tesseract-ocr-fra]"

LANG_PAR_DEFAUT = "fra+eng"
_CACHE: dict | None = None


def backend() -> dict:
    """Détecte (une seule fois) le backend OCR. Renvoie un dict d'état.

    Clés : `etat` (« ok » / « disabled »), `detail` (raison), `langs` (disponibles),
    `lang` (combinaison utilisée).
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    etat = {"etat": "disabled", "detail": "", "langs": [], "lang": LANG_PAR_DEFAUT}
    try:
        import pytesseract
    except ImportError:
        etat["detail"] = "module pytesseract absent"
        _CACHE = etat
        return etat
    if shutil.which("tesseract") is None:
        etat["detail"] = "binaire tesseract absent du PATH"
        _CACHE = etat
        return etat
    try:
        etat["langs"] = list(pytesseract.get_languages(config=""))
        pytesseract.get_tesseract_version()
    except Exception as exc:  # binaire présent mais inutilisable
        etat["detail"] = f"binaire tesseract inutilisable ({exc})"
        _CACHE = etat
        return etat
    etat["etat"] = "ok"
    if "fra" not in etat["langs"]:
        etat["lang"] = "eng"
        etat["detail"] = "langue fra absente : OCR limité à « eng »"
    elif "eng" not in etat["langs"]:
        etat["lang"] = "fra"
        etat["detail"] = "langue eng absente : OCR limité à « fra »"
    _CACHE = etat
    return etat


def disponible() -> bool:
    """Vrai si l'OCR est réellement utilisable."""
    return backend()["etat"] == "ok"


def avertissement_backend() -> str:
    """Message utilisateur expliquant la dégradation, ou chaîne vide."""
    etat = backend()
    if etat["etat"] == "ok":
        return ""
    raison = etat["detail"] or "backend OCR non détecté"
    return (
        f"OCR indisponible ({raison}) : seul le texte déjà présent dans le document "
        f"est extrait. {PLACEHOLDER_OCR_INDISPONIBLE}"
    )


def image_vers_texte(image, lang: str | None = None) -> str:
    """OCR une image PIL. Lève l'exception d'origine en cas d'échec (traitée par l'appelant)."""
    import pytesseract

    return pytesseract.image_to_string(image, lang=lang or backend()["lang"])


def image_pil_depuis_pixmap(pixmap):
    """Convertit un `pymupdf.Pixmap` en image PIL (pour l'OCR d'une page PDF)."""
    from PIL import Image

    return Image.open(io.BytesIO(pixmap.tobytes("png")))