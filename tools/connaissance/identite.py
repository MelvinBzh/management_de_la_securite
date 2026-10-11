"""Carte d'identité d'un document : de quel TYPE il est, de quand il date, et donc à quel point on s'y fie.

Sert à départager deux documents qui se contredisent (46,8 M€ dans un diaporama, 47,2 M€ dans le rapport financier) :
on propose la valeur du document le plus FIABLE pour ce genre d'information, puis, à fiabilité égale, le plus RÉCENT.
La proposition est toujours accompagnée de sa raison et reste une décision humaine : le code ne tranche jamais seul.

Fiabilité (rang 1 à 5), par TYPE de document, pour des faits sur le système et ses chiffres :
  5  données de référence : inventaire, budget, matrice, cartographie, registre, effectifs, journal, rapport financier, audit
  4  organigramme, compte rendu
  3  politique, charte, procédure, plan (PRA / PCA), note de direction : décrit l'intention, pas forcément la pratique
  2  présentation : synthèse commerciale ou de direction, arrondie, souvent plus ancienne ou plus optimiste
Les règles sont simples et lisibles à dessein : on peut les corriger sans toucher au reste.
"""
from __future__ import annotations

import re
import time

# (motif sur « nom du fichier + début du texte », type affiché, rang) — le premier qui correspond gagne
TYPES = (
    (r"rapport[ _-]?financier|bilan|comptes? annuels?", "rapport financier", 5),
    (r"audit|pentest|test[ _-]d.intrusion", "audit", 5),
    (r"inventaire|budget|matrice|cartographie|registre|effectifs?|journal|incidents?|mouvements|sch[ée]ma|zones", "données de référence", 5),
    (r"organigramme|compte[ _-]rendu|cr[ _-]", "organigramme / compte rendu", 4),
    (r"(?<![a-z])pssi(?![a-z])|politique|charte|proc[ée]dure|(?<![a-z])pra(?![a-z])|(?<![a-z])pca(?![a-z])|plan de (?:reprise|continuit)|note|orientations?", "politique ou procédure", 3),
    (r"pr[ée]sentation|comex|diapositive|powerpoint|\.pptx|readme|institutionnelle|sensibilisation|plaquette", "présentation", 2),
)
RANG_DEFAUT, TYPE_DEFAUT = 3, "document"
MOIS = {"janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4, "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
        "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12}
RE_ISO = re.compile(r"(?<![A-Za-z0-9])(20\d\d)[-/](0[1-9]|1[0-2])(?:[-/](0[1-9]|[12]\d|3[01]))?(?![0-9])")
RE_FR = re.compile(r"(?<![A-Za-z0-9])(0?[1-9]|[12]\d|3[01])[/.](0?[1-9]|1[0-2])[/.](20\d\d)(?![0-9])")
RE_MOIS = re.compile(r"(?<![A-Za-z0-9])(" + "|".join(MOIS) + r")[\s_-]+(20\d\d)(?![0-9])", re.I)
RE_ANNEE = re.compile(r"(?<![A-Za-z0-9])(20[12]\d)(?![0-9])")


def _corps(contenu: str) -> str:
    """Texte utile : sans l'en-tête technique de l'ingestion (nom du fichier, type, taille…)."""
    i = contenu.find("<<<DONNÉES>>>")
    return contenu[i + len("<<<DONNÉES>>>"):] if i >= 0 else contenu


def type_et_rang(nom: str, contenu: str = "") -> tuple[str, int]:
    """(type, rang) d'après le nom du fichier d'abord, puis le début du texte."""
    for source in (nom.lower(), (_corps(contenu)[:400]).lower()):
        for motif, type_, rang in TYPES:
            if re.search(motif, source):
                return type_, rang
    return TYPE_DEFAUT, RANG_DEFAUT


def date_du_document(nom: str, contenu: str = "") -> str:
    """Date la plus RÉCENTE trouvée dans le nom du fichier et le début du texte, « AAAA-MM » (ou « AAAA »), sinon « »."""
    candidats: list[tuple[int, int]] = []
    zone = nom + " " + _corps(contenu)[:2500]
    for m in RE_ISO.finditer(zone):
        candidats.append((int(m.group(1)), int(m.group(2))))
    for m in RE_FR.finditer(zone):
        candidats.append((int(m.group(3)), int(m.group(2))))
    for m in RE_MOIS.finditer(zone):
        candidats.append((int(m.group(2)), MOIS[m.group(1).lower()]))
    if not candidats:
        # une année SEULE n'est retenue que si elle n'est pas dans le futur (« 2026-2028 » est un horizon, pas une date)
        annees = [int(a) for a in RE_ANNEE.findall(zone) if int(a) <= time.localtime().tm_year]
        return str(max(annees)) if annees else ""
    a, mois = max(candidats)
    return f"{a:04d}-{mois:02d}"


def carte(nom: str, contenu: str = "") -> dict:
    type_, rang = type_et_rang(nom, contenu)
    return {"type": type_, "rang": rang, "date": date_du_document(nom, contenu)}


def proposer(a: dict, b: dict) -> tuple[str, str]:
    """Pour deux documents qui se contredisent : `("a" | "b" | "", raison)`.

    D'abord la fiabilité du type ; à égalité, la date la plus récente ; sinon aucune proposition (« à trancher »)."""
    ra, rb = int(a.get("rang") or 0), int(b.get("rang") or 0)
    if ra != rb and ra and rb:
        gagnant, perdant, cote = (a, b, "a") if ra > rb else (b, a, "b")
        return cote, (f"un document de type « {gagnant['type']} » est plus fiable qu'un document de type « {perdant['type']} » "
                      f"pour un chiffre ou un fait de ce genre")
    da, db = a.get("date") or "", b.get("date") or ""
    if da and db and da != db:
        cote = "a" if da > db else "b"
        return cote, f"à fiabilité égale, le document le plus récent ({max(da, db)} contre {min(da, db)})"
    return "", "aucune règle ne permet de départager : à trancher"
