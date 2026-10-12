# -*- coding: utf-8 -*-
"""Export « DOSSIER D'ANALYSE COMPLET » : tous les livrables, reliés entre eux, avec leurs preuves.

Le rapport exécutif (`export.py`) ne contient que la synthèse et le registre. Ici on produit le dossier entier :

  - **HTML** : un seul fichier autonome, navigable. Chaque identifiant d'actif (`A05`) ou de risque (`M012`) est cliquable vers sa
    ligne et vers sa fiche de traçabilité ; chaque preuve `[E123]` renvoie à l'annexe « Preuves citées » (document + extrait exact)
    qui, en retour, liste les risques qui s'appuient sur elle ;
  - **PDF** : le même document, paginé, avec liens internes (WeasyPrint) ;
  - **ZIP** : tout — HTML, PDF, livrables d'origine (.md), registre en tableur (.xlsx, .csv), preuves et graphe de traçabilité
    (.json), historique des décisions.

Chaîne de liaison reconstituée : document → preuve [E…] → actif (A…) → menace (M…) → évaluation → traitement → registre → décision.
Rien n'est inventé : tout vient des livrables, de l'index des preuves et de `validations.json`. Les documents d'origine
(`intrants/`) ne sont PAS inclus : seuls les extraits cités le sont.
"""
from __future__ import annotations

import csv
import html
import io
import json
import re
import sqlite3
import time
import unicodedata
import zipfile
from pathlib import Path

# (fichier, ancre, titre) : ordre de lecture du dossier
LIVRABLES = [
    ("SYNTHESE.md", "synthese", "Synthèse"),
    ("registre-risques.md", "registre", "Registre des risques"),
    ("00-description.md", "description", "Description du système"),
    ("01-actifs.md", "actifs", "Inventaire des actifs"),
    ("02-methodes.md", "methodes", "Méthodes retenues"),
    ("03-menaces.md", "menaces", "Menaces"),
    ("04-evaluation.md", "evaluation", "Évaluation des risques"),
    ("05-traitement.md", "traitement", "Traitement des risques"),
    ("06-validation.md", "validation", "Validation et suivi"),
    ("recherches-contradictions-questions.md", "contradictions", "Contradictions entre documents et questions ouvertes"),
    ("PROPAGATION.md", "propagation", "Propagation des décisions de l'analyste"),
    ("MISE-A-JOUR.md", "maj", "Mises à jour après ajout de documents"),
    ("RAPPORT-CONTROLE.md", "controle", "Rapport de contrôle"),
]
ANCRE_DE = {f: a for f, a, _t in LIVRABLES}
RE_PREUVE = re.compile(r"\[E(\d+)\]")
RE_ID = re.compile(r"[AM]-?\d{1,4}")
RE_SEPARATEUR = re.compile(r"^\s*\|?[\s:|-]+\|?\s*$")

CSS = """
:root { --fond:#ffffff; --texte:#1f2933; --discret:#52606d; --trait:#d9e2ec; --accent:#0b5cad; --bandeau:#f0f4f8; }
* { box-sizing: border-box; }
body { font: 15px/1.55 -apple-system, "Segoe UI", Roboto, Arial, sans-serif; color: var(--texte); background: var(--fond);
       margin: 0; }
header.page { padding: 28px 40px 12px; border-bottom: 3px solid var(--accent); }
header.page h1 { margin: 0 0 6px; font-size: 26px; }
header.page p { margin: 2px 0; color: var(--discret); }
nav.sommaire { background: var(--bandeau); padding: 14px 40px; border-bottom: 1px solid var(--trait); }
nav.sommaire h2 { margin: 0 0 6px; font-size: 15px; }
nav.sommaire ol { margin: 0; padding-left: 20px; columns: 2; }
main { padding: 8px 40px 60px; max-width: 1200px; }
section { margin-top: 34px; }
section > h2 { border-bottom: 2px solid var(--trait); padding-bottom: 4px; font-size: 21px; }
.source { color: var(--discret); font-size: 12px; margin-top: -6px; }
h3, h4, h5 { margin: 18px 0 6px; }
table { border-collapse: collapse; width: 100%; margin: 10px 0 16px; font-size: 12.5px; }
th, td { border: 1px solid var(--trait); padding: 5px 7px; vertical-align: top; text-align: left; }
th { background: var(--bandeau); }
tr:target td { background: #fff7cc; }
a { color: var(--accent); }
a.preuve { font-size: 11px; vertical-align: super; text-decoration: none; }
a.inconnue { color: #b42318; }
code { background: var(--bandeau); padding: 0 3px; border-radius: 3px; font-size: 0.92em; }
blockquote { margin: 8px 0; padding: 4px 12px; border-left: 4px solid var(--trait); color: var(--discret); }
pre { background: var(--bandeau); padding: 10px; overflow-x: auto; }
.fiche { border: 1px solid var(--trait); border-radius: 6px; margin: 14px 0; padding: 4px 14px 10px; break-inside: avoid; }
.fiche h3 { margin: 8px 0; font-size: 16px; }
.fiche td.k { width: 150px; font-weight: 600; background: var(--bandeau); }
.niveau-Critique { color: #b42318; font-weight: 700; } .niveau-Élevé { color: #b54708; font-weight: 700; }
.preuve-bloc { border-left: 4px solid var(--accent); background: var(--bandeau); padding: 6px 12px; margin: 8px 0; break-inside: avoid; }
.preuve-bloc .doc { color: var(--discret); font-size: 12px; }
.retour { font-size: 12px; color: var(--discret); }
@media print {
  header.page { padding: 0 0 8px; } nav.sommaire { padding: 6px 0; } main { padding: 0; max-width: none; }
  a { color: inherit; text-decoration: none; }
  section > h2 { break-after: avoid; }
  table { font-size: 9.5px; } tr { break-inside: avoid; }
  @page { size: A4; margin: 16mm 14mm; @bottom-center { content: counter(page) " / " counter(pages); font-size: 9px; color: #52606d; } }
}
"""


# ---------------------------------------------------------------------------------------------------------- lecture
def _norm(texte: str) -> str:
    sans = "".join(c for c in unicodedata.normalize("NFD", str(texte).lower()) if unicodedata.category(c) != "Mn")
    return " ".join(sans.split())


def _propre(cellule: str) -> str:
    return re.sub(r"[*`_]", "", cellule).strip()


def _net(cellule: str) -> str:
    """Cellule sans marques Markdown de gras ou de code (les soulignés des noms comme valide_par sont conservés)."""
    return str(cellule).replace("**", "").replace("`", "").strip()


def _lire(dossier: Path, nom: str) -> str:
    try:
        return (dossier / nom).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def tableaux(texte: str) -> list[dict]:
    """Tableaux Markdown d'un texte : `{entete: [..], lignes: [[..], ..]}`."""
    sortie, courant = [], []
    for ligne in texte.splitlines() + [""]:
        if ligne.lstrip().startswith("|"):
            courant.append(ligne)
            continue
        if courant:
            lignes = [[c.strip() for c in l.strip().strip("|").split("|")] for l in courant if not RE_SEPARATEUR.match(l)]
            if lignes:
                sortie.append({"entete": lignes[0], "lignes": lignes[1:]})
            courant = []
    return sortie


def _table_par_id(texte: str) -> tuple[list[str], dict[str, list[str]]]:
    """Premier tableau dont la 1re colonne est un identifiant : (en-tête, `{identifiant: cellules}`)."""
    for t in tableaux(texte):
        if _norm(_propre(t["entete"][0])) in ("id", "identifiant") if t["entete"] else False:
            lignes = {}
            for cellules in t["lignes"]:
                ident = _propre(cellules[0]) if cellules else ""
                if RE_ID.fullmatch(ident) or re.fullmatch(r"[A-Z]-?\d+", ident):
                    lignes.setdefault(ident, cellules)
            return t["entete"], lignes
    return [], {}


def _champ(entete: list[str], cellules: list[str], *mots: str) -> str:
    for i, e in enumerate(entete):
        n = _norm(_propre(e))
        if any(m in n for m in mots) and i < len(cellules):
            return cellules[i].replace("**", "").strip()
    return ""


def preuves_de_l_index(dossier: Path, ids: set[int]) -> dict[int, dict]:
    """`{id: {doc, extrait}}` des preuves citées, lues dans l'index du projet (éléments actuels, puis retirés)."""
    chemin = dossier / "connaissance" / "index.sqlite"
    if not ids or not chemin.is_file():
        return {}
    sortie: dict[int, dict] = {}
    try:
        base = sqlite3.connect(f"file:{chemin}?mode=ro", uri=True)
    except sqlite3.Error:
        return {}
    try:
        for table in ("elements", "elements_retires"):
            try:
                for i, doc, libelle, extrait in base.execute(f"SELECT id, doc, libelle, extrait FROM {table}"):
                    if int(i) in ids and int(i) not in sortie:
                        sortie[int(i)] = {"doc": doc, "libelle": libelle, "extrait": " ".join(str(extrait).split()),
                                          "retiree": table == "elements_retires"}
            except sqlite3.Error:
                continue
    finally:
        base.close()
    return sortie


def collecter(dossier: Path) -> dict:
    """Tout ce qui sert à relier les livrables : lignes par identifiant, preuves citées, décisions."""
    dossier = Path(dossier)
    textes = {f: _lire(dossier, f) for f, _a, _t in LIVRABLES}
    e_act, actifs = _table_par_id(textes["01-actifs.md"])
    e_men, menaces = _table_par_id(textes["03-menaces.md"])
    e_eva, evaluations = _table_par_id(textes["04-evaluation.md"])
    e_tra, traitements = _table_par_id(textes["05-traitement.md"])
    e_reg, registre = _table_par_id(textes["registre-risques.md"])
    risques = sorted(set(menaces) | set(registre) | set(evaluations) | set(traitements), key=_cle_id)
    # preuves : celles que citent les livrables (quel que soit le fichier)
    cites_par_fichier = {f: {int(i) for i in RE_PREUVE.findall(t)} for f, t in textes.items()}
    toutes = set().union(*cites_par_fichier.values()) if cites_par_fichier else set()
    preuves = preuves_de_l_index(dossier, toutes)
    try:
        validations = json.loads(_lire(dossier, "validations.json") or "{}")
    except ValueError:
        validations = {}
    return {"dossier": dossier, "textes": textes, "actifs": (e_act, actifs), "menaces": (e_men, menaces),
            "evaluations": (e_eva, evaluations), "traitements": (e_tra, traitements), "registre": (e_reg, registre),
            "risques": risques, "preuves": preuves, "cites_par_fichier": cites_par_fichier, "validations": validations}


def _cle_id(ident: str) -> tuple[str, int]:
    m = re.fullmatch(r"([A-Za-z]+)-?(\d+)", ident)
    return (m.group(1), int(m.group(2))) if m else (ident, 0)


def _risque(c: dict, ident: str) -> dict:
    """Fiche d'un risque : tout ce que les livrables disent de lui, relié."""
    e_m, m = c["menaces"]
    e_e, e = c["evaluations"]
    e_t, t = c["traitements"]
    e_r, r = c["registre"]
    lm, le, lt, lr = m.get(ident, []), e.get(ident, []), t.get(ident, []), r.get(ident, [])
    actif_cell = _champ(e_m, lm, "actif") if lm else ""
    actif_id = (RE_ID.search(actif_cell) or [None])[0] if actif_cell else None
    if actif_id and not actif_id.startswith("A"):
        actif_id = None
    texte = " ".join(" ".join(x) for x in (lm, le, lt, lr))
    return {
        "id": ident, "actif_id": actif_id, "actif": actif_cell,
        "categorie": _champ(e_m, lm, "categorie", "categorie"), "menace": _champ(e_m, lm, "description"),
        "probabilite": _champ(e_e, le, "probabilite"), "impact": _champ(e_e, le, "impact"),
        "niveau": _champ(e_e, le, "niveau") or _champ(e_r, lr, "niveau"), "justification": _champ(e_e, le, "justification"),
        "traitement": _champ(e_t, lt, "traitement") or _champ(e_r, lr, "traitement"),
        "mesures": _champ(e_t, lt, "contre", "mesure"), "sources": _champ(e_t, lt, "source"),
        "residuel": _champ(e_t, lt, "residuel") or _champ(e_r, lr, "residuel"),
        "valide_par": _champ(e_r, lr, "valide_par"), "statut": _champ(e_r, lr, "statut"),
        "preuves": sorted({int(i) for i in RE_PREUVE.findall(texte)}),
        "presence": {"menaces": bool(lm), "evaluation": bool(le), "traitement": bool(lt), "registre": bool(lr)},
    }


# ---------------------------------------------------------------------------------------------------------- rendu
class Rendu:
    """Convertit du Markdown en HTML en reliant identifiants et preuves (tout est échappé avant d'être interprété)."""

    def __init__(self, c: dict):
        self.c = c
        self.preuves = set(c["preuves"])
        self.risques = set(c["risques"])
        self.actifs = set(c["actifs"][1])
        self.cites_par: dict[int, set[str]] = {}

    def cible(self, ident: str) -> str | None:
        if ident in self.risques:
            return f"fiche-{ident}"
        if ident in self.actifs:
            return f"actifs-{ident}"
        return None

    def inline(self, texte: str, soi: str | None = None) -> str:
        s = html.escape(texte, quote=False)

        def lier(m: re.Match) -> str:
            if m.group(1):
                i = int(m.group(1))
                if i in self.preuves:
                    return f'<a class="preuve" href="#preuve-{i}">[E{i}]</a>'
                return f'<a class="preuve inconnue" title="preuve introuvable dans l\'index">[E{i}]</a>'
            ident = m.group(2)
            cible = self.cible(ident)
            if cible and ident != soi:
                return f'<a href="#{cible}">{ident}</a>'
            return ident

        s = re.sub(r"\[E(\d+)\]|(?<![A-Za-z0-9])([AM]-?\d{1,4})(?![A-Za-z0-9])", lier, s)
        morceaux = s.split("`")
        s = "".join(f"<code>{x}</code>" if i % 2 else x for i, x in enumerate(morceaux)) if len(morceaux) % 2 == 1 else s
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        return s

    def markdown(self, texte: str, fichier: str, ancre: str) -> str:
        lignes = texte.split("\n")
        sortie: list[str] = []
        i = 0
        premier_titre = True
        while i < len(lignes):
            ligne = lignes[i]
            brut = ligne.strip()
            if brut.startswith("```"):
                bloc = []
                i += 1
                while i < len(lignes) and not lignes[i].strip().startswith("```"):
                    bloc.append(html.escape(lignes[i]))
                    i += 1
                i += 1
                sortie.append("<pre><code>" + "\n".join(bloc) + "</code></pre>")
                continue
            m = re.match(r"^(#{1,6})\s+(.*)$", brut)
            if m:
                niveau = len(m.group(1))
                if premier_titre and niveau == 1:
                    premier_titre = False
                    i += 1
                    continue
                premier_titre = False
                n = min(niveau + 2, 5)
                sortie.append(f"<h{n}>{self.inline(m.group(2))}</h{n}>")
                i += 1
                continue
            if brut in ("---", "***", "___"):
                sortie.append("<hr>")
                i += 1
                continue
            if brut.startswith("|"):
                bloc = []
                while i < len(lignes) and lignes[i].strip().startswith("|"):
                    bloc.append(lignes[i].strip())
                    i += 1
                sortie.append(self._tableau(bloc, fichier, ancre))
                continue
            if brut.startswith(">"):
                bloc = []
                while i < len(lignes) and lignes[i].strip().startswith(">"):
                    bloc.append(lignes[i].strip().lstrip(">").strip())
                    i += 1
                sortie.append("<blockquote>" + "<br>".join(self.inline(x) for x in bloc) + "</blockquote>")
                continue
            if re.match(r"^([-*]|\d+[.)])\s+", brut):
                ordonne = bool(re.match(r"^\d+[.)]\s+", brut))
                bloc = []
                while i < len(lignes) and re.match(r"^([-*]|\d+[.)])\s+", lignes[i].strip()):
                    bloc.append(re.sub(r"^([-*]|\d+[.)])\s+", "", lignes[i].strip()))
                    i += 1
                balise = "ol" if ordonne else "ul"
                sortie.append(f"<{balise}>" + "".join(f"<li>{self.inline(x)}</li>" for x in bloc) + f"</{balise}>")
                continue
            if brut == "":
                i += 1
                continue
            bloc = []
            while i < len(lignes) and lignes[i].strip() and not re.match(r"^(#{1,6}\s|\||>|```|[-*]\s|\d+[.)]\s|---)", lignes[i].strip()):
                bloc.append(lignes[i].strip())
                i += 1
            if not bloc:  # ligne inclassable : on la rend telle quelle pour ne jamais boucler
                bloc = [brut]
                i += 1
            sortie.append("<p>" + self.inline(" ".join(bloc)) + "</p>")
        return "\n".join(sortie)

    def _tableau(self, bloc: list[str], fichier: str, ancre: str) -> str:
        lignes = [[c.strip() for c in l.strip().strip("|").split("|")] for l in bloc if not RE_SEPARATEUR.match(l)]
        if not lignes:
            return ""
        entete, corps = lignes[0], lignes[1:]
        est_id = bool(entete) and _norm(_propre(entete[0])) in ("id", "identifiant")
        out = ["<table><thead><tr>" + "".join(f"<th>{self.inline(c)}</th>" for c in entete) + "</tr></thead><tbody>"]
        for cellules in corps:
            ident = _propre(cellules[0]) if cellules else ""
            ancre_ligne = f' id="{ancre}-{html.escape(ident)}"' if est_id and re.fullmatch(r"[A-Z]-?\d+", ident) else ""
            cases = []
            for k, cellule in enumerate(cellules):
                if k == 0 and est_id and ident in self.risques and ancre != "fiche":
                    cases.append(f'<td><a href="#fiche-{ident}">{html.escape(ident)}</a></td>')
                else:
                    cases.append(f"<td>{self.inline(cellule, soi=ident if k == 0 else None)}</td>")
            out.append(f"<tr{ancre_ligne}>" + "".join(cases) + "</tr>")
        out.append("</tbody></table>")
        return "".join(out)


def _fiche(r: Rendu, f: dict) -> str:
    def lien(ident: str | None, libelle: str) -> str:
        return f'<a href="#{r.cible(ident)}">{html.escape(libelle)}</a>' if ident and r.cible(ident) else html.escape(libelle)

    lignes = []
    if f["actif"]:
        lignes.append(("Actif", lien(f["actif_id"], f["actif"]) if f["actif_id"] else r.inline(f["actif"])))
    if f["categorie"] or f["menace"]:
        lignes.append(("Menace", r.inline(" — ".join(x for x in (f["categorie"], f["menace"]) if x))))
    if f["probabilite"] or f["impact"] or f["niveau"]:
        niveau = f'<span class="niveau-{html.escape(_propre(f["niveau"]))}">{html.escape(f["niveau"])}</span>' if f["niveau"] else "—"
        lignes.append(("Évaluation", f"Probabilité : {html.escape(f['probabilite'] or '—')} · Impact : {html.escape(f['impact'] or '—')}"
                                       f" · Niveau : {niveau}"))
    if f["justification"]:
        lignes.append(("Justification", r.inline(f["justification"])))
    if f["traitement"] or f["mesures"]:
        lignes.append(("Traitement", r.inline(" — ".join(x for x in (f["traitement"], f["mesures"]) if x))))
    if f["sources"]:
        lignes.append(("Sources", r.inline(f["sources"])))
    if f["residuel"]:
        lignes.append(("Risque résiduel", r.inline(f["residuel"])))
    if f["valide_par"] or f["statut"]:
        lignes.append(("Validation", r.inline(" — ".join(x for x in (f["valide_par"], f["statut"]) if x))))
    if f["preuves"]:
        lignes.append(("Preuves", " ".join(f'<a class="preuve" href="#preuve-{i}">[E{i}]</a>' if i in r.preuves
                                           else f'<a class="preuve inconnue">[E{i}]</a>' for i in f["preuves"])))
    liens = []
    for cle, fichier, ancre in (("menaces", "03-menaces.md", "menaces"), ("evaluation", "04-evaluation.md", "evaluation"),
                                ("traitement", "05-traitement.md", "traitement"), ("registre", "registre-risques.md", "registre")):
        if f["presence"][cle]:
            liens.append(f'<a href="#{ancre}-{f["id"]}">{html.escape(fichier)}</a>')
    if liens:
        lignes.append(("Dans les livrables", " · ".join(liens)))
    titre = f["id"] + (" — " + re.sub(r"\[E\d+\]", "", f["menace"])[:110] if f["menace"] else "")
    return (f'<div class="fiche" id="fiche-{html.escape(f["id"])}"><h3>{html.escape(titre)}</h3><table>'
            + "".join(f'<tr><td class="k">{k}</td><td>{v}</td></tr>' for k, v in lignes) + "</table></div>")


def _annexe_preuves(c: dict, r: Rendu, citeurs: dict[int, list[str]]) -> str:
    docs: dict[str, list[int]] = {}
    blocs = []
    for i in sorted(c["preuves"]):
        p = c["preuves"][i]
        docs.setdefault(p["doc"], []).append(i)
        par = " ".join(f'<a href="#{r.cible(x)}">{x}</a>' if r.cible(x) else html.escape(x) for x in citeurs.get(i, [])[:40])
        etat = " (document retiré ou modifié depuis)" if p.get("retiree") else ""
        blocs.append(f'<div class="preuve-bloc" id="preuve-{i}"><strong>[E{i}]</strong> <span class="doc">{html.escape(p["doc"])}{etat}</span>'
                     f'<br>« {html.escape(p["extrait"][:900])} »<br><span class="retour">Cité par : {par or "—"}</span></div>')
    absentes = sorted({i for t in c["cites_par_fichier"].values() for i in t} - set(c["preuves"]))
    resume = "".join(f"<li><strong>{html.escape(d)}</strong> : {len(v)} preuve(s) citée(s)</li>" for d, v in sorted(docs.items()))
    note = (f"<p class='retour'>{len(absentes)} identifiant(s) de preuve cités dans les livrables sont introuvables dans l'index : "
            + ", ".join(f"[E{i}]" for i in absentes[:30]) + ("…" if len(absentes) > 30 else "") + ".</p>") if absentes else ""
    return f"<h3>Documents d'origine cités</h3><ul>{resume or '<li>Aucune preuve résolue.</li>'}</ul>{note}<h3>Preuves</h3>" + "".join(blocs)


def _annexe_decisions(c: dict) -> str:
    decisions = [d for d in (c["validations"].get("decisions") or {}).values() if d.get("decision")]
    if not decisions:
        return "<p>Aucune décision n'a encore été enregistrée par un analyste.</p>"
    lignes = "".join(
        f"<tr><td>{html.escape(str(d.get('type', '')))}</td><td>{html.escape(str(d.get('titre', ''))[:140])}</td>"
        f"<td>{html.escape(str(d.get('libelle_decision') or d.get('decision')))}</td><td>{html.escape(str(d.get('analyste', '')))}</td>"
        f"<td>{html.escape(str(d.get('date', '')))}</td><td>{html.escape(str(d.get('commentaire', '')))}</td></tr>"
        for d in sorted(decisions, key=lambda d: str(d.get("date", ""))))
    return ("<table><thead><tr><th>Type</th><th>Élément</th><th>Décision</th><th>Analyste</th><th>Date</th><th>Motif</th></tr></thead>"
            f"<tbody>{lignes}</tbody></table>")


# ---------------------------------------------------------------------------------------------------------- exports
def html_complet(dossier: str | Path, titre: str | None = None) -> str:
    """Le dossier d'analyse complet en un seul fichier HTML (autonome, navigable)."""
    dossier = Path(dossier)
    c = collecter(dossier)
    r = Rendu(c)
    nom = titre or dossier.name
    sommaire, sections = [], []
    for fichier, ancre, libelle in LIVRABLES:
        texte = c["textes"][fichier]
        if not texte.strip():
            continue
        sommaire.append(f'<li><a href="#doc-{ancre}">{html.escape(libelle)}</a></li>')
        sections.append(f'<section id="doc-{ancre}"><h2>{html.escape(libelle)}</h2><p class="source">Fichier : {html.escape(fichier)}</p>'
                        + r.markdown(texte, fichier, ancre) + "</section>")
    fiches = [_risque(c, i) for i in c["risques"]]
    if fiches:
        sommaire.append('<li><a href="#annexe-fiches">Fiches de traçabilité des risques</a></li>')
        sections.append('<section id="annexe-fiches"><h2>Fiches de traçabilité des risques</h2>'
                        "<p class='source'>Pour chaque risque : l'actif, la menace, l'évaluation, le traitement, la validation et les preuves, "
                        "avec un lien vers chaque ligne d'origine.</p>" + "".join(_fiche(r, f) for f in fiches) + "</section>")
    citeurs: dict[int, list[str]] = {}
    for f in fiches:
        for i in f["preuves"]:
            citeurs.setdefault(i, []).append(f["id"])
    for ident, ligne in c["actifs"][1].items():
        for i in {int(x) for x in RE_PREUVE.findall(" ".join(ligne))}:
            citeurs.setdefault(i, []).append(ident)
    if c["preuves"] or any(c["cites_par_fichier"].values()):
        sommaire.append('<li><a href="#annexe-preuves">Preuves citées</a></li>')
        sections.append('<section id="annexe-preuves"><h2>Preuves citées</h2>'
                        "<p class='source'>Chaque identifiant [E…] cité dans les livrables, avec le document d'origine et l'extrait exact, "
                        "et les actifs et risques qui s'appuient sur lui.</p>" + _annexe_preuves(c, r, citeurs) + "</section>")
    sommaire.append('<li><a href="#annexe-decisions">Historique des décisions de l\'analyste</a></li>')
    sections.append('<section id="annexe-decisions"><h2>Historique des décisions de l\'analyste</h2>' + _annexe_decisions(c) + "</section>")
    entete = (f'<header class="page"><h1>Dossier d\'analyse des risques — {html.escape(nom)}</h1>'
              f"<p>Généré le {time.strftime('%d/%m/%Y à %H:%M')} · {len(c['actifs'][1])} actif(s) · {len(c['risques'])} risque(s) · "
              f"{len(c['preuves'])} preuve(s) citée(s)</p>"
              "<p>Les identifiants (A05, M012) et les preuves [E123] sont des liens : cliquez pour passer d'un livrable à l'autre. "
              "Les décisions de l'analyste sont indiquées telles qu'enregistrées ; rien n'est validé par le programme.</p></header>")
    return ("<!DOCTYPE html><html lang=\"fr\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>Dossier d'analyse — {html.escape(nom)}</title><style>{CSS}</style></head><body>{entete}"
            f"<nav class=\"sommaire\"><h2>Sommaire</h2><ol>{''.join(sommaire)}</ol></nav><main>{''.join(sections)}</main></body></html>")


def graphe(dossier: str | Path) -> dict:
    """Graphe de traçabilité : nœuds (documents, preuves, actifs, risques) et liens, en données."""
    c = collecter(Path(dossier))
    noeuds: dict[str, dict] = {}
    liens: list[dict] = []
    for ident, ligne in c["actifs"][1].items():
        noeuds[ident] = {"id": ident, "type": "actif", "nom": _propre(ligne[1]) if len(ligne) > 1 else ident}
    for i in c["risques"]:
        f = _risque(c, i)
        noeuds[i] = {"id": i, "type": "risque", "categorie": f["categorie"], "niveau": f["niveau"], "traitement": f["traitement"],
                     "valide_par": f["valide_par"], "statut": f["statut"]}
        if f["actif_id"]:
            liens.append({"source": i, "cible": f["actif_id"], "type": "concerne"})
        for p in f["preuves"]:
            liens.append({"source": i, "cible": f"E{p}", "type": "s_appuie_sur"})
    for ident, ligne in c["actifs"][1].items():
        for p in {int(x) for x in RE_PREUVE.findall(" ".join(ligne))}:
            liens.append({"source": ident, "cible": f"E{p}", "type": "s_appuie_sur"})
    for i, p in c["preuves"].items():
        noeuds[f"E{i}"] = {"id": f"E{i}", "type": "preuve", "document": p["doc"], "extrait": p["extrait"]}
        noeuds[f"doc:{p['doc']}"] = {"id": f"doc:{p['doc']}", "type": "document", "nom": p["doc"]}
        liens.append({"source": f"E{i}", "cible": f"doc:{p['doc']}", "type": "extrait_de"})
    return {"genere_le": time.strftime("%Y-%m-%d %H:%M:%S"), "dossier": Path(dossier).name, "noeuds": list(noeuds.values()), "liens": liens}


def _lignes_registre(c: dict) -> tuple[list[str], list[list[str]]]:
    entete, lignes = c["registre"]
    if lignes:
        extra = ["Preuves", "Documents d'origine"]
        corps = []
        for ident in sorted(lignes, key=_cle_id):
            cellules = [_net(x) for x in lignes[ident]]
            ids = sorted({int(i) for i in RE_PREUVE.findall(" ".join(lignes[ident]))} | set(_risque(c, ident)["preuves"]))
            docs = sorted({c["preuves"][i]["doc"] for i in ids if i in c["preuves"]})
            corps.append(cellules + [" ".join(f"[E{i}]" for i in ids), " ; ".join(docs)])
        return [_net(e) for e in entete] + extra, corps
    # pas de registre : on le reconstitue depuis les fiches
    cols = ["ID", "Actif", "Menace", "Niveau", "Probabilité", "Impact", "Traitement", "Contre-mesures", "Risque résiduel", "Preuves"]
    corps = []
    for i in c["risques"]:
        f = _risque(c, i)
        corps.append([i, f["actif"], f["menace"], f["niveau"], f["probabilite"], f["impact"], f["traitement"], f["mesures"],
                      f["residuel"], " ".join(f"[E{p}]" for p in f["preuves"])])
    return cols, corps


def csv_registre(dossier: str | Path) -> str:
    entete, corps = _lignes_registre(collecter(Path(dossier)))
    sortie = io.StringIO()
    w = csv.writer(sortie, delimiter=";", lineterminator="\r\n")
    w.writerow(entete)
    w.writerows(corps)
    return "﻿" + sortie.getvalue()   # BOM : Excel lit l'UTF-8 correctement


def xlsx_registre(dossier: str | Path, chemin: Path) -> Path | None:
    """Tableur : registre, actifs, preuves, liens. `None` si openpyxl est absent."""
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font
    except ImportError:
        return None
    c = collecter(Path(dossier))
    g = graphe(dossier)
    wb = Workbook()
    ws = wb.active
    ws.title = "Registre"
    entete, corps = _lignes_registre(c)
    ws.append(entete)
    for ligne in corps:
        ws.append(ligne)
    feuilles = (
        ("Actifs", [_net(e) for e in c["actifs"][0]], [[_net(x) for x in l] for l in c["actifs"][1].values()]),
        ("Preuves", ["Preuve", "Document", "Extrait", "Citée par"],
         [[f"E{i}", p["doc"], p["extrait"], ", ".join(sorted({l["source"] for l in g["liens"] if l["cible"] == f"E{i}"}))]
          for i, p in sorted(c["preuves"].items())]),
        ("Liens", ["Source", "Cible", "Type"], [[l["source"], l["cible"], l["type"]] for l in g["liens"]]),
    )
    for nom, cols, lignes in feuilles:
        s = wb.create_sheet(nom)
        s.append(cols)
        for l in lignes:
            s.append(l)
    for s in wb.worksheets:
        for cell in s[1]:
            cell.font = Font(bold=True)
        s.freeze_panes = "A2"
    wb.save(chemin)
    return chemin


def pdf_complet(dossier: str | Path, chemin: Path) -> Path:
    """Le dossier complet en PDF (WeasyPrint) ; lève ImportError / OSError si la bibliothèque est absente."""
    import weasyprint
    weasyprint.HTML(string=html_complet(dossier)).write_pdf(str(chemin))
    return chemin


LISEZ_MOI = """DOSSIER D'ANALYSE COMPLET — {nom}
Généré le {date}

Contenu de cette archive
------------------------
dossier-complet.html        Le dossier entier dans un seul fichier, navigable : les identifiants (A05, M012) et les preuves
                            [E123] sont des liens. À ouvrir dans un navigateur.
dossier-complet.pdf         Le même dossier paginé, avec liens internes{pdf}.
livrables/                  Les livrables d'origine (.md) : description, actifs, méthodes, menaces, évaluation, traitement,
                            registre, validation, synthèse, contradictions et questions, contrôle.
donnees/registre-risques.xlsx   Registre en tableur (feuilles : Registre, Actifs, Preuves, Liens).
donnees/registre-risques.csv    Le registre en CSV (séparateur « ; », UTF-8).
donnees/registre_risques.json   Le registre structuré tel que produit par la chaîne (s'il existe).
donnees/graphe-tracabilite.json Nœuds (documents, preuves, actifs, risques) et liens, pour un autre outil.
donnees/decisions.json      Les décisions de l'analyste (qui, quand, motif).

Chaîne de liaison : document → preuve [E…] → actif (A…) → menace (M…) → évaluation → traitement → registre → décision.
Les documents d'origine ne sont pas inclus : seuls les extraits cités le sont.
"""


def exporter_dossier(dossier: str, format: str = "html", out: str | None = None) -> Path:
    """`format` : « html », « pdf » ou « zip ». Écrit dans `out` (dossier temporaire par défaut) et renvoie le fichier."""
    dossier_path = Path(dossier).resolve()
    if not dossier_path.is_dir():
        raise ValueError(f"Le dossier d'analyse n'existe pas : {dossier}")
    sortie = Path(out).resolve() if out else dossier_path
    sortie.mkdir(parents=True, exist_ok=True)
    base = "dossier-complet"
    fmt = format.lower()
    if fmt == "html":
        chemin = sortie / f"{base}.html"
        chemin.write_text(html_complet(dossier_path), encoding="utf-8")
        return chemin
    if fmt == "pdf":
        return pdf_complet(dossier_path, sortie / f"{base}.pdf")
    if fmt == "zip":
        chemin = sortie / f"{base}.zip"
        pdf_ok = ""
        with zipfile.ZipFile(chemin, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("dossier-complet.html", html_complet(dossier_path))
            try:
                tmp_pdf = sortie / ".tmp-dossier.pdf"
                pdf_complet(dossier_path, tmp_pdf)
                z.write(tmp_pdf, "dossier-complet.pdf")
                tmp_pdf.unlink()
            except Exception:  # noqa: BLE001 — le PDF est un plus : l'archive reste complète sans lui
                pdf_ok = " (non généré : bibliothèque PDF indisponible)"
            for fichier, _a, _t in LIVRABLES:
                if (dossier_path / fichier).is_file():
                    z.write(dossier_path / fichier, f"livrables/{fichier}")
            if (dossier_path / "registre_risques.json").is_file():
                z.write(dossier_path / "registre_risques.json", "donnees/registre_risques.json")
            z.writestr("donnees/registre-risques.csv", csv_registre(dossier_path))
            tmp_xlsx = sortie / ".tmp-registre.xlsx"
            if xlsx_registre(dossier_path, tmp_xlsx):
                z.write(tmp_xlsx, "donnees/registre-risques.xlsx")
                tmp_xlsx.unlink()
            z.writestr("donnees/graphe-tracabilite.json", json.dumps(graphe(dossier_path), ensure_ascii=False, indent=1))
            decisions = (collecter(dossier_path)["validations"].get("decisions") or {})
            z.writestr("donnees/decisions.json", json.dumps(list(decisions.values()), ensure_ascii=False, indent=1))
            z.writestr("LISEZ-MOI.txt", LISEZ_MOI.format(nom=dossier_path.name, date=time.strftime("%d/%m/%Y %H:%M"), pdf=pdf_ok))
        return chemin
    raise ValueError(f"Format non supporté : {format}")
