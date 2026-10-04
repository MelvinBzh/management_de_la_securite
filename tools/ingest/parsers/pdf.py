# -*- coding: utf-8 -*-
"""Parseur PDF (PyMuPDF) : couche texte, tableaux, OCR des pages scannées.

Une page dont la couche texte est vide est rasterisée puis passée à l'OCR.
Le texte obtenu est une DONNÉE : il est recopié tel quel, jamais interprété.
"""
from __future__ import annotations

from . import commun, ocr

DPI_OCR = 200


def parse(chemin, meta: dict) -> str:
    """Extrait le contenu d'un PDF en markdown (une section par page)."""
    import pymupdf

    document = pymupdf.open(chemin)
    try:
        meta["pages"] = document.page_count
        if getattr(document, "needs_pass", False):
            commun.avertir(meta, "PDF chiffré : extraction impossible sans mot de passe")
            return "## Extraction impossible\n\nDocument PDF protégé par mot de passe."
        return _pages(document, meta)
    finally:
        document.close()


def parse_bytes(nom: str, donnees: bytes, meta: dict) -> str:
    """Variante mémoire (membres d'archive ZIP)."""
    import io

    import pymupdf

    document = pymupdf.open(stream=donnees, filetype="pdf")
    try:
        meta["pages"] = document.page_count
        if getattr(document, "needs_pass", False):
            commun.avertir(meta, f"Membre PDF chiffré ignoré : {nom}")
            return ""
        return _pages(document, meta)
    finally:
        document.close()





def _pages(document, meta: dict) -> str:
    etat_ocr = ocr.backend()
    if etat_ocr["etat"] != "ok":
        commun.avertir(meta, ocr.avertissement_backend())
        meta["ocr"] = "disabled"
    elif etat_ocr["detail"]:
        commun.avertir(meta, f"OCR : {etat_ocr['detail']}")

    sections: list[str] = []
    for numero, page in enumerate(document, 1):
        texte = commun.normaliser(page.get_text("text", sort=True))
        if texte:
            if meta.get("ocr") == "disabled":
                meta["ocr"] = False  # page lisible sans OCR malgré l'absence de backend
            parties = [f"## Page {numero}", texte]
        else:
            parties = [f"## Page {numero}", _ocr_page(page, meta)]
        tableaux = _tableaux_page(page, meta, numero)
        sections.append("\n\n".join(p for p in parties + tableaux if p))
    return "\n\n".join(sections)


def _ocr_page(page, meta: dict) -> str:
    """OCR d'une page sans couche texte, ou marqueur si l'OCR est indisponible."""
    if not ocr.disponible():
        return ocr.PLACEHOLDER_OCR_INDISPONIBLE
    try:
        pixmap = page.get_pixmap(dpi=DPI_OCR)
        texte = commun.normaliser(ocr.image_vers_texte(ocr.image_pil_depuis_pixmap(pixmap)))
    except Exception as exc:
        commun.avertir(meta, f"OCR impossible sur une page ({exc})")
        return f"{ocr.PLACEHOLDER_OCR_INDISPONIBLE} (erreur OCR : {exc})"
    meta["ocr"] = True
    if not texte:
        commun.avertir(meta, "OCR sans texte reconnu sur au moins une page")
        return f"*(aucun texte reconnu par l'OCR sur cette page)*"
    return texte


def _tableaux_page(page, meta: dict, numero: int) -> list[str]:
    """Tableaux détectés par PyMuPDF (silencieux si la détection échoue)."""
    try:
        tables = page.find_tables().tables
    except Exception:
        return []
    resultats = []
    for index, table in enumerate(tables, 1):
        try:
            lignes = table.extract()
        except Exception:
            continue
        bloc = commun.bloc_tableau(f"### Tableau {index} (page {numero})", lignes, meta)
        if bloc:
            resultats.append(bloc)
    return resultats