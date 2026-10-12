# -*- coding: utf-8 -*-
"""Registre des risques, validation et synthèse ÉTABLIS PAR LE CODE à partir des étapes 3, 4 et 5.

Pourquoi : à l'étape 6, un agent qui relit à la main 151 lignes de traitement les résume, en oublie et en réinvente (mesuré le
2026-10-11 : 9 risques sur 151, trois résumés automatiques d'opencode). Le registre n'est qu'une REPRISE ligne à ligne de
03-menaces.md, 04-evaluation.md et 05-traitement.md : le code le fait sans erreur et sans modèle. De même les chiffres de la
synthèse sont calculés. Le modèle n'écrit plus qu'un court texte de lecture, vérifié par le code (aucun nombre hors des chiffres
fournis) ; sans lui le document est complet.

Rien n'est décidé ici : `valide_par` reste vide, seule une personne le renseigne (page ④). Une reconstruction CONSERVE les
décisions déjà prises (colonne `valide_par`, sections « Validation humaine » de 06-validation.md).
"""
from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from web import coherence, lib

# étape → livrables établis par le code
ETAPES_PAR_CODE = {6: ("registre-risques.md", "06-validation.md"), 7: ("SYNTHESE.md",)}
NIVEAUX = ("Critique", "Élevé", "Moyen", "Faible")
STATUT_A_VALIDER = "À valider par l'analyste"
STATUT_DECIDE = "Décidé par l'analyste"
STATUT_A_CONFIRMER = "À confirmer — ligne modifiée depuis votre décision"
CHAMPS_CONTENU = ("actif", "menace", "niveau", "probabilite", "impact", "traitement", "mesures", "residuel")
COLONNES = ["ID", "Actif", "Menace", "Niveau", "Probabilité", "Impact", "Justification", "Traitement", "Contre-mesures",
            "Risque résiduel", "Sources", "valide_par", "Statut"]
RE_ID = re.compile(r"[MR]-?\d{1,4}")
RE_ID_ACTIF = re.compile(r"A-?\d{1,4}")
TOP_RISQUES = 10
TOP_ACTIFS = 8
# fréquence de revue proposée par niveau (proposition par défaut, à valider par la direction)
REVUE = {"Critique": "tous les mois, jusqu'à la mise en œuvre de la mesure, puis tous les trimestres",
         "Élevé": "tous les trimestres", "Moyen": "tous les semestres", "Faible": "une fois par an"}
REVUE_COURTE = {"Critique": "mensuelle", "Élevé": "trimestrielle", "Moyen": "semestrielle", "Faible": "annuelle"}
DECLENCHEURS = [
    "changement de périmètre (nouveau site, nouvelle application, nouveau service) ;",
    "incident de sécurité significatif, y compris chez un fournisseur ou un client ;",
    "arrivée d'un nouveau fournisseur ou d'un nouveau prestataire ayant accès au système ;",
    "évolution d'une obligation réglementaire ou contractuelle (RGPD, NIS2, exigences clients) ;",
    "modification d'un document d'origine de l'analyse (le site le signale : les livrables sont alors « périmés »).",
]


# ------------------------------------------------------------------------------------------------ lecture des étapes 3, 4, 5
def _norm(texte: str) -> str:
    sans = "".join(c for c in unicodedata.normalize("NFD", str(texte).lower()) if unicodedata.category(c) != "Mn")
    return " ".join(sans.split())


def _cel(texte: object) -> str:
    """Texte rendu sûr pour une cellule de tableau Markdown (pas de `|`, pas de saut de ligne)."""
    return " ".join(str(texte or "").replace("|", "/").split())


def _lire_fichier(dossier: Path, nom: str, motif: re.Pattern = RE_ID) -> dict[str, dict[str, str]]:
    """`{identifiant: {en-tête normalisé: cellule}}` des lignes de données du fichier (premier tableau de chaque identifiant)."""
    try:
        texte = (Path(dossier) / nom).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    sortie: dict[str, dict[str, str]] = {}
    for tableau in coherence.tableaux(texte):
        entete = [_norm(c) for c in tableau["entete"]]
        for _num, cellules in tableau["lignes"]:
            if not cellules:
                continue
            ident = cellules[0].strip("*` ")
            if motif.fullmatch(ident) and ident not in sortie:
                sortie[ident] = {entete[i]: cellules[i].strip() for i in range(min(len(entete), len(cellules)))}
    return sortie


def _prend(ligne: dict[str, str], *mots: str) -> str:
    for cle, valeur in ligne.items():
        if any(m in cle for m in mots):
            return valeur
    return ""


def _jetons_sources(*textes: str) -> list[str]:
    """Identifiants de source cités (ISO27002-8.15, ANSSI-HYGIENE-3…), dédoublonnés, dans l'ordre."""
    vus: dict[str, None] = {}
    for t in textes:
        for jeton in re.split(r"[,;\s\[\]()]+", t or ""):
            jeton = jeton.strip(".")
            if re.fullmatch(r"[A-Za-z][A-Za-z0-9]*(?:-[A-Za-z0-9.]+)+", jeton) and not re.fullmatch(r"E\d+", jeton):
                vus.setdefault(jeton, None)
    return list(vus)


def lire_risques(dossier: Path) -> tuple[list[dict], list[str]]:
    """Risques reconstitués ligne à ligne depuis les étapes 3, 4 et 5, et les problèmes de correspondance relevés."""
    dossier = Path(dossier)
    menaces = _lire_fichier(dossier, "03-menaces.md")
    evaluations = _lire_fichier(dossier, "04-evaluation.md")
    traitements = _lire_fichier(dossier, "05-traitement.md")
    problemes: list[str] = []
    if not menaces:
        problemes.append("03-menaces.md est absent ou ne contient aucune ligne de menace identifiée.")
        return [], problemes
    risques: list[dict] = []
    for ident, m in menaces.items():
        e, t = evaluations.get(ident, {}), traitements.get(ident, {})
        if not e:
            problemes.append(f"{ident} : aucune évaluation à l'étape 4.")
        if not t:
            problemes.append(f"{ident} : aucun traitement à l'étape 5.")
        categorie, description = _prend(m, "categorie"), _prend(m, "description")
        menace = " — ".join(x for x in (categorie, description) if x and x != "—")
        risques.append({
            "id": ident,
            "actif": _prend(m, "actif") or "—",
            "categorie": categorie,
            "menace": menace or "—",
            "niveau": _prend(e, "niveau") or "Non évalué",
            "probabilite": _prend(e, "probabilite") or "—",
            "impact": _prend(e, "impact") or "—",
            "justification": _prend(e, "justification") or "—",
            "traitement": _prend(t, "traitement") or "Non traité",
            "mesures": _prend(t, "contre") or "—",
            "residuel": _prend(t, "residuel") or "—",
            "sources": _jetons_sources(_prend(m, "source"), _prend(t, "source")),
        })
    en_plus = [i for i in list(evaluations) + list(traitements) if i not in menaces]
    if en_plus:
        problemes.append("Identifiants évalués ou traités mais absents de l'étape 3 : " + ", ".join(dict.fromkeys(en_plus)) + ".")
    return risques, problemes


def decision_de(valide_par: str) -> str:
    """`accepte` / `modifie` / `refuse` d'après la colonne `valide_par` ; « » si le risque n'est pas décidé."""
    t = str(valide_par or "")
    if "REFUSÉ" in t:
        return "refuse"
    if "avec modification" in t:
        return "modifie"
    if "accepté" in t.lower() or "accepte" in t.lower():
        return "accepte"
    return ""


def _rang(niveau: str) -> int:
    n = _norm(niveau)
    for i, nom in enumerate(("critique", "eleve", "moyen", "faible")):
        if n == nom or n.startswith(nom):
            return i
    return 9


def _tri_priorite(r: dict) -> tuple:
    return (_rang(r.get("niveau", "")), _rang(r.get("impact", "")), _rang(r.get("probabilite", "")), r.get("id", ""))


# ------------------------------------------------------------------------------------------------------- registre + 06
def _decisions_existantes(dossier: Path) -> tuple[dict[str, str], str]:
    """(`valide_par` par risque, sections « Validation humaine » de 06-validation.md) d'une version précédente."""
    decisions: dict[str, str] = {}
    try:
        _col, lignes = lib.lire_registre(dossier)
        for r in lignes:
            v = str(r.get("valide_par", "")).strip()
            if v and v.lower() not in ("null", "none", "—", "-", ""):
                decisions[r["ID"]] = v
    except Exception:  # noqa: BLE001 — l'ancien registre peut être illisible : on repart sans décision plutôt que d'échouer
        pass
    sections = ""
    try:
        ancien = (Path(dossier) / "06-validation.md").read_text(encoding="utf-8", errors="replace")
        debut = ancien.find("## Validation humaine")
        sections = ancien[debut:].rstrip() + "\n" if debut >= 0 else ""
    except OSError:
        pass
    return decisions, sections


def empreinte_contenu(r: dict) -> str:
    """Empreinte de CE QUE DIT un risque (actif, menace, niveau, probabilité, impact, traitement, mesures, résiduel).

    Enregistrée avec la décision de l'analyste : si elle change plus tard (mise à jour des documents), la décision n'est plus
    valable telle quelle et revient « à confirmer »."""
    import hashlib
    brut = "¤".join(" ".join(_cel(r.get(c, "")).split()) for c in CHAMPS_CONTENU)
    return hashlib.sha1(brut.encode("utf-8")).hexdigest()[:12]


def empreinte_ligne_registre(ligne: dict) -> str:
    """Empreinte d'une ligne LUE dans registre-risques.md (colonnes Actif, Menace, Niveau…) : même valeur que celle calculée
    depuis les étapes 3 à 5 par `empreinte_contenu`."""
    return empreinte_contenu({
        "actif": ligne.get("Actif", ""), "menace": ligne.get("Menace", ""), "niveau": ligne.get("Niveau", ""),
        "probabilite": ligne.get("Probabilité", ""), "impact": ligne.get("Impact", ""), "traitement": ligne.get("Traitement", ""),
        "mesures": ligne.get("Contre-mesures", ""), "residuel": ligne.get("Risque résiduel", "")})


def adopter_decisions(dossier: Path) -> int:
    """Donne une empreinte aux décisions enregistrées avant ce suivi, d'après le registre ACTUEL (avant toute modification).

    À appeler avant une mise à jour ou une nouvelle analyse : ensuite, toute ligne qui change est détectée. Renvoie le nombre
    de décisions adoptées."""
    donnees = _charger_validations(dossier)
    decisions = donnees.get("decisions", {})
    if not any(d.get("type") == "risque" and d.get("decision") and not d.get("contenu") for d in decisions.values()):
        return 0
    try:
        _col, lignes = lib.lire_registre(dossier)
    except Exception:  # noqa: BLE001
        return 0
    par_id = {r["ID"]: empreinte_ligne_registre(r) for r in lignes}
    adoptees = 0
    for d in decisions.values():
        if d.get("type") == "risque" and d.get("decision") and not d.get("contenu"):
            rid = str(d.get("titre", "")).split(" — ")[0].strip()
            if rid in par_id:
                d["contenu"] = par_id[rid]
                adoptees += 1
    if adoptees:
        (Path(dossier) / "validations.json").write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return adoptees


def _charger_validations(dossier: Path) -> dict:
    try:
        return json.loads((Path(dossier) / "validations.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def risques_a_confirmer(dossier: Path, risques: list[dict], adopter: bool = True) -> set[str]:
    """Identifiants des risques DÉCIDÉS dont le contenu a changé depuis la décision.

    Une décision enregistrée avant ce suivi n'a pas d'empreinte : on l'ADOPTE (empreinte du contenu actuel), à partir de là
    toute modification est suivie."""
    donnees = _charger_validations(dossier)
    decisions = donnees.get("decisions", {})
    par_id = {r["id"]: empreinte_contenu(r) for r in risques}
    changes: set[str] = set()
    modifie = False
    for d in decisions.values():
        if d.get("type") != "risque" or not d.get("decision"):
            continue
        rid = str(d.get("titre", "")).split(" — ")[0].strip()
        if rid not in par_id:
            continue
        if not d.get("contenu"):
            if adopter:
                d["contenu"] = par_id[rid]
                modifie = True
        elif d["contenu"] != par_id[rid]:
            changes.add(rid)
    if modifie:
        try:
            (Path(dossier) / "validations.json").write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except OSError:
            pass
    return changes


def _ligne_registre(r: dict, valide_par: str, a_confirmer: bool = False) -> str:
    statut = STATUT_A_CONFIRMER if a_confirmer else (STATUT_DECIDE if valide_par else STATUT_A_VALIDER)
    cellules = [r["id"], r["actif"], r["menace"], r["niveau"], r["probabilite"], r["impact"], r["justification"], r["traitement"],
                r["mesures"], r["residuel"], ", ".join(r["sources"]) or "—", valide_par, statut]
    return "| " + " | ".join(_cel(c) for c in cellules) + " |"


def _repartition(risques: list[dict], cle: str = "niveau") -> Counter:
    return Counter(r.get(cle, "") for r in risques)


def construire_registre(risques: list[dict], decisions: dict[str, str], a_confirmer: frozenset | set = frozenset()) -> str:
    comptes = _repartition(risques)
    repart = " · ".join(f"{n} : {comptes.get(n, 0)}" for n in NIVEAUX)
    autres = sum(v for k, v in comptes.items() if k not in NIVEAUX)
    if autres:
        repart += f" · Non évalué : {autres}"
    haut = [
        "# Registre des risques (étape 6)",
        "",
        "> Registre établi par le programme, ligne à ligne, à partir des étapes 3 (menaces), 4 (évaluation) et 5 (traitement) : "
        "aucune valeur n'est modifiée ni inventée, et chaque risque garde le même identifiant (M001…) d'un livrable à l'autre. "
        "La colonne `valide_par` reste vide tant qu'une personne n'a pas décidé (page ④ du site).",
        "",
        f"**{len(risques)} risques** — {repart}.",
        "",
        "| " + " | ".join(COLONNES) + " |",
        "|" + "|".join("---" for _ in COLONNES) + "|",
    ]
    return "\n".join(haut + [_ligne_registre(r, decisions.get(r["id"], ""), r["id"] in a_confirmer) for r in risques]) + "\n"


def construire_validation(risques: list[dict], decisions: dict[str, str], sections_humaines: str,
                          a_confirmer: frozenset | set = frozenset()) -> str:
    comptes = _repartition(risques)
    decisions = {k: ("" if k in a_confirmer else v) for k, v in decisions.items()}   # « à confirmer » = pas encore décidé
    decides = Counter(decision_de(decisions.get(r["id"], "")) for r in risques)
    n_decides = sum(v for k, v in decides.items() if k)
    sortie = [
        "# Validation et suivi (étape 6)",
        "",
        "> Document établi par le programme à partir du registre des risques. Il ne contient AUCUNE décision : les décisions sont "
        "prises par une personne dans la page ④ du site, puis ajoutées en bas de ce document (qui, quand, pourquoi).",
        "",
        "## 1. État de la validation",
        "",
        f"- Risques au registre : **{len(risques)}**.",
        f"- Décidés par un analyste : **{n_decides}** ({decides.get('accepte', 0)} acceptés, {decides.get('modifie', 0)} acceptés "
        f"avec modification, {decides.get('refuse', 0)} refusés).",
        f"- Restant à valider : **{len(risques) - n_decides}**"
        + (f", dont **{len(a_confirmer)}** à confirmer (la ligne a changé depuis votre décision)." if a_confirmer else "."),
        "",
        "| Niveau | Risques | Dont décidés |",
        "|---|---|---|",
    ]
    for n in NIVEAUX:
        sortie.append(f"| {n} | {comptes.get(n, 0)} | "
                      f"{sum(1 for r in risques if r['niveau'] == n and decision_de(decisions.get(r['id'], '')))} |")
    prioritaires = sorted((r for r in risques if r["niveau"] in ("Critique", "Élevé")), key=_tri_priorite)
    sortie += ["", "## 2. Risques à décider en priorité (niveaux Critique et Élevé)", ""]
    if prioritaires:
        sortie += ["La colonne « Décision » se remplit dans le site (page ④) ; elle est ici pour mémoire.", "",
                   "| ID | Actif | Niveau | Traitement proposé | Risque résiduel | Décision | Responsable |", "|---|---|---|---|---|---|---|"]
        for r in prioritaires:
            d = decision_de(decisions.get(r["id"], ""))
            sortie.append("| " + " | ".join(_cel(c) for c in (
                r["id"], r["actif"], r["niveau"], r["traitement"], r["residuel"],
                {"accepte": "Accepté", "modifie": "Accepté avec modification", "refuse": "Refusé"}.get(d, "À décider"),
                "À désigner")) + " |")
    else:
        sortie.append("Aucun risque de niveau Critique ou Élevé.")
    sortie += [
        "", "## 3. Acceptation du risque résiduel", "",
        "Un risque résiduel n'est accepté que **par écrit**, par une personne qui en a la responsabilité (autorité d'homologation) : "
        "qui, quand, pourquoi (référentiel `ANSSI-HOMOLOGATION`). Dans le site, la décision « accepté tel quel », « accepté avec "
        "modification » ou « refusé » et son commentaire sont consignés à la fin de ce document.",
        "", "## 4. Plan de suivi (proposition par défaut, à valider par la direction)", "",
        "| Niveau du risque | Revue proposée |", "|---|---|",
    ]
    sortie += [f"| {n} | {REVUE[n]} |" for n in NIVEAUX]
    sortie += ["", "Déclencheurs d'une nouvelle analyse, quel que soit le niveau :", ""] + [f"- {d}" for d in DECLENCHEURS]
    sortie += ["", "## Décisions enregistrées", "",
               "Les décisions prises dans le site s'ajoutent ci-dessous, dans l'ordre où elles sont enregistrées.", ""]
    texte = "\n".join(sortie)
    return texte + ("\n" + sections_humaines if sections_humaines else "\n")


def registre_json(risques: list[dict], decisions: dict[str, str], a_confirmer: frozenset | set = frozenset()) -> list[dict]:
    return [{
        "id": r["id"], "actif": r["actif"], "menace": r["menace"], "categorie": r["categorie"],
        "probabilite": r["probabilite"], "impact": r["impact"], "niveau": r["niveau"], "traitement": r["traitement"],
        "mesures": [m.strip() for m in re.split(r"\s\+\s", r["mesures"]) if m.strip()], "sources": r["sources"],
        "risque_residuel": r["residuel"], "valide_par": (None if r["id"] in a_confirmer else decisions.get(r["id"])) or None,
    } for r in risques]


def ecrire_registre_et_validation(dossier: Path) -> tuple[int, list[str]]:
    """Écrit `registre-risques.md`, `06-validation.md` et `registre_risques.json`. Renvoie (nombre de risques, problèmes).

    Sans menace identifiée, RIEN n'est écrit (on n'écrase pas un registre existant par un registre vide)."""
    dossier = Path(dossier)
    risques, problemes = lire_risques(dossier)
    if not risques:
        return 0, problemes
    decisions, sections = _decisions_existantes(dossier)
    a_confirmer = risques_a_confirmer(dossier, risques)
    (dossier / "registre-risques.md").write_text(construire_registre(risques, decisions, a_confirmer), encoding="utf-8")
    (dossier / "06-validation.md").write_text(construire_validation(risques, decisions, sections, a_confirmer), encoding="utf-8")
    (dossier / lib.NOM_JSON_REGISTRE).write_text(
        json.dumps({"risques": registre_json(risques, decisions, a_confirmer)}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return len(risques), problemes


# ------------------------------------------------------------------------------------------------------------- synthèse
def risques_du_registre(dossier: Path) -> list[dict]:
    """Risques lus dans `registre-risques.md` (la référence de la synthèse), clés normalisées ; justification reprise de l'étape 4."""
    colonnes, lignes = lib.lire_registre(Path(dossier))
    if not lignes:
        return []
    evaluations = _lire_fichier(Path(dossier), "04-evaluation.md")
    sortie = []
    for ligne in lignes:
        norm = {_norm(k): v for k, v in ligne.items()}

        def champ(*mots: str, norm=norm) -> str:
            return _prend(norm, *mots)
        ident = ligne["ID"]
        sortie.append({
            "id": ident, "actif": champ("actif") or "—", "menace": champ("menace") or "—", "niveau": champ("niveau") or "Non évalué",
            "probabilite": champ("probabilite") or "—", "impact": champ("impact") or "—",
            "justification": champ("justification") or _prend(evaluations.get(ident, {}), "justification") or "—",
            "traitement": champ("traitement") or "—", "mesures": champ("contre-mesure", "mesure") or "—",
            "residuel": champ("residuel") or "—",
            "valide_par": "" if "a confirmer" in _norm(champ("statut")) else champ("valide_par"),
            "a_confirmer": "a confirmer" in _norm(champ("statut")),
        })
    return sortie


def _pct(n: int, total: int) -> str:
    return f"{round(100 * n / total)} %" if total else "—"


def _types_traitement(risques: list[dict]) -> Counter:
    c: Counter = Counter()
    for r in risques:
        n = _norm(r["traitement"])
        c[next((nom for nom in ("reduire", "eviter", "accepter", "transferer") if n.startswith(nom)), "autre")] += 1
    return c


def _actifs_exposes(risques: list[dict]) -> list[tuple[str, int, int, int]]:
    par: dict[str, list[dict]] = {}
    for r in risques:
        par.setdefault(r["actif"], []).append(r)
    lignes = [(a, len(rs), sum(1 for r in rs if r["niveau"] == "Critique"), sum(1 for r in rs if r["niveau"] == "Élevé"))
              for a, rs in par.items()]
    return sorted(lignes, key=lambda x: (-x[2], -x[3], -x[1], x[0]))[:TOP_ACTIFS]


def chiffres(dossier: Path, risques: list[dict]) -> dict:
    """Tous les chiffres de la synthèse, calculés."""
    comptes = _repartition(risques)
    decides = Counter(decision_de(r.get("valide_par", "")) for r in risques)
    trait = _types_traitement(risques)
    return {
        "n_risques": len(risques),
        "n_actifs": len(_lire_fichier(Path(dossier), "01-actifs.md", RE_ID_ACTIF)),
        "niveaux": {n: comptes.get(n, 0) for n in NIVEAUX},
        "non_evalues": sum(v for k, v in comptes.items() if k not in NIVEAUX),
        "traitements": {"Réduire": trait.get("reduire", 0), "Éviter": trait.get("eviter", 0), "Accepter": trait.get("accepter", 0),
                        "Transférer": trait.get("transferer", 0), "Autre": trait.get("autre", 0)},
        "decides": {"accepte": decides.get("accepte", 0), "modifie": decides.get("modifie", 0), "refuse": decides.get("refuse", 0)},
        "n_decides": sum(v for k, v in decides.items() if k),
        "actifs_exposes": _actifs_exposes(risques),
        "prioritaires": sorted(risques, key=_tri_priorite)[:TOP_RISQUES],
    }


def faits_pour_le_modele(f: dict) -> str:
    """Les seuls chiffres que le modèle a le droit d'utiliser (et que le code recontrôle ensuite)."""
    n = f["n_risques"]
    lignes = ["# Chiffres de l'analyse (calculés par le programme)", "",
              f"- Actifs analysés : {f['n_actifs']}", f"- Risques au registre : {n}"]
    lignes += [f"- Niveau {k} : {v} risques ({_pct(v, n)})" for k, v in f["niveaux"].items()]
    lignes += [f"- Traitement {k} : {v}" for k, v in f["traitements"].items() if v]
    lignes += [f"- Risques déjà décidés par un analyste : {f['n_decides']} sur {n}", "", "## Actifs les plus exposés", ""]
    lignes += [f"- {a} : {t} risques dont {c} critiques et {e} élevés" for a, t, c, e in f["actifs_exposes"]]
    lignes += ["", "## Risques prioritaires", ""]
    lignes += [f"- {r['id']} ({r['actif']}) — niveau {r['niveau']}, traitement {r['traitement']} : {r['menace'][:160]}"
               for r in f["prioritaires"]]
    return "\n".join(lignes) + "\n"


def _resume_deterministe(f: dict, dossier: Path) -> str:
    n, niv, trait = f["n_risques"], f["niveaux"], f["traitements"]
    phrases = [
        f"L'analyse porte sur **{f['n_actifs']} actifs** et **{n} risques**. "
        f"{niv['Critique']} risques sont évalués au niveau Critique ({_pct(niv['Critique'], n)}), {niv['Élevé']} Élevé, "
        f"{niv['Moyen']} Moyen et {niv['Faible']} Faible."]
    parts = [f"{v} à {k.lower()}" for k, v in trait.items() if v and k != "Autre"]
    if parts:
        phrases.append("Traitement proposé : " + ", ".join(parts) + ".")
    if f["n_decides"]:
        phrases.append(f"{f['n_decides']} risque(s) sur {n} ont déjà été décidés par un analyste ; "
                       f"{n - f['n_decides']} restent à valider.")
    else:
        phrases.append(f"Aucun risque n'a encore été décidé : les {n} risques sont proposés et attendent la validation d'un analyste.")
    if f["actifs_exposes"]:
        a, t, c, _e = f["actifs_exposes"][0]
        phrases.append(f"L'actif le plus exposé est **{a}** ({t} risques dont {c} critiques).")
    return " ".join(phrases)


def _limites(dossier: Path, f: dict) -> list[str]:
    from web import controles
    sortie: list[str] = []
    n = f["n_risques"]
    part_critique = f["niveaux"]["Critique"]
    if n and part_critique / n >= 0.3:
        sortie.append(
            f"**Niveaux à relire en priorité** : {part_critique} risques sur {n} ({_pct(part_critique, n)}) sont évalués Critique. "
            "Le niveau est CALCULÉ par le programme (matrice probabilité × impact) à partir des valeurs proposées par le modèle ; "
            "quand presque tout est critique, la hiérarchie ne guide plus : relisez d'abord les probabilités et les impacts.")
    try:
        entrees = controles.lire(Path(dossier))
    except Exception:  # noqa: BLE001
        entrees = []
    derniere: dict[str, dict] = {}
    for e in entrees:
        if str(e.get("etape")) in ("6", "7", "finale"):
            continue  # établis par le programme (ou rendus après lui) : la synthèse ne parle pas de son propre contrôle
        derniere[str(e.get("etape"))] = e
    a_valider = [k for k, e in derniere.items() if e.get("humaine")]
    doutes = sum(len(e.get("doutes") or []) for e in derniere.values())
    if a_valider:
        sortie.append(f"**Étapes à valider par une personne** : {', '.join(sorted(a_valider))} ; {doutes} ligne(s) dont la preuve "
                      "citée n'a pas pu être établie par la machine (page ④, « Lignes à relire », par pages de dix).")
    try:
        from tools.connaissance import travail
        manquants = coherence.actifs_manquants(Path(dossier), travail.chemins(Path(dossier))[1])
    except Exception:  # noqa: BLE001
        manquants = []
    if manquants:
        sortie.append("**Actifs cités par plusieurs documents mais absents du tableau des actifs** : "
                      + "; ".join(m[0] for m in manquants[:10]) + ". Les ajouter ou dire pourquoi ils sont hors périmètre.")
    if f["non_evalues"]:
        sortie.append(f"**{f['non_evalues']} risque(s) sans niveau** : l'évaluation de l'étape 4 est incomplète pour eux.")
    return sortie


def construire_synthese(dossier: Path, risques: list[dict], lecture: str = "") -> str:
    f = chiffres(dossier, risques)
    n = f["n_risques"]
    sortie = [
        "# Synthèse (étape 7)", "",
        "> Document d'orientation pour une décision de direction (structure inspirée du guide `ANSSI-PSSI` : faits, décisions, "
        "actions). Les chiffres sont CALCULÉS par le programme à partir du registre des risques, pas écrits par un modèle ; chaque "
        "risque garde l'identifiant du registre.", "",
        "## 1. Résumé exécutif", "", _resume_deterministe(f, dossier)]
    if lecture:
        sortie += ["", "**Lecture** (rédigée par le modèle, dont les chiffres ont été recontrôlés par le programme) :", "", lecture.strip()]
    sortie += ["", "## 2. Chiffres clés", "", "| Indicateur | Valeur |", "|---|---|",
               f"| Actifs analysés | {f['n_actifs']} |", f"| Risques au registre | {n} |"]
    sortie += [f"| Niveau {k} | {v} ({_pct(v, n)}) |" for k, v in f["niveaux"].items()]
    sortie += [f"| Traitement : {k} | {v} |" for k, v in f["traitements"].items() if v]
    sortie += [f"| Risques décidés par un analyste | {f['n_decides']} sur {n} |"]
    sortie += ["", "## 3. Où se concentre le risque", "", "| Actif | Risques | Dont Critique | Dont Élevé |", "|---|---|---|---|"]
    sortie += [f"| {_cel(a)} | {t} | {c} | {e} |" for a, t, c, e in f["actifs_exposes"]] or ["| — | — | — | — |"]
    sortie += ["", f"## 4. Risques prioritaires (les {len(f['prioritaires'])} premiers par niveau, impact puis probabilité)", ""]
    if f["prioritaires"]:
        sortie += ["| ID | Actif | Menace | Niveau | Pourquoi (étape 4) | Traitement | Risque résiduel |", "|---|---|---|---|---|---|---|"]
        sortie += ["| " + " | ".join(_cel(c) for c in (r["id"], r["actif"], r["menace"], r["niveau"], r["justification"], r["traitement"],
                                                       r["residuel"])) + " |" for r in f["prioritaires"]]
    else:
        sortie.append("Aucun risque dans le registre.")
    sortie += ["", "## 5. Actions recommandées", ""]
    if f["prioritaires"]:
        sortie += ["Chaque action vient du traitement de l'étape 5 pour le risque indiqué ; la revue suit le plan de "
                   "`06-validation.md`.", "", "| Priorité | Risque | Action (contre-mesures proposées) | Prochaine revue |", "|---|---|---|---|"]
        sortie += ["| " + " | ".join(_cel(c) for c in (r["niveau"], r["id"], r["mesures"],
                                                       REVUE_COURTE.get(r["niveau"], "à fixer"))) + " |" for r in f["prioritaires"]]
    sortie += ["", "## 6. Décisions de l'analyste", ""]
    decides = [r for r in risques if decision_de(r.get("valide_par", ""))]
    if decides:
        sortie += ["| ID | Actif | Niveau | Décision |", "|---|---|---|---|"]
        sortie += ["| " + " | ".join(_cel(c) for c in (r["id"], r["actif"], r["niveau"], r["valide_par"])) + " |" for r in decides[:60]]
        if len(decides) > 60:
            sortie.append(f"\n… et {len(decides) - 60} autres décisions, visibles dans `registre-risques.md`.")
    else:
        sortie.append(f"Aucune décision enregistrée : les {n} risques restent « {STATUT_A_VALIDER} ».")
    limites = _limites(dossier, f)
    sortie += ["", "## 7. Limites et points à vérifier", ""] + ([f"- {x}" for x in limites] or ["- Aucune limite signalée par le contrôle."])
    sortie += ["", "## 8. Comment lire ce dossier", "",
               "- `registre-risques.md` : tous les risques, une ligne chacun, de la menace au traitement.",
               "- `06-validation.md` : ce qui reste à décider, le plan de suivi, et les décisions prises.",
               "- `03-menaces.md`, `04-evaluation.md`, `05-traitement.md` : le détail et les preuves `[E…]`.",
               "- `RAPPORT-CONTROLE.md` : ce que le contrôle a relevé, étape par étape.", ""]
    return "\n".join(sortie)


def ecrire_synthese(dossier: Path, lecture: str = "") -> tuple[int, list[str]]:
    """Écrit `SYNTHESE.md` depuis le registre. Renvoie (nombre de risques, problèmes)."""
    dossier = Path(dossier)
    risques = risques_du_registre(dossier)
    if not risques:
        return 0, ["registre-risques.md est absent ou ne contient aucune ligne de risque : la synthèse n'a pas pu être établie."]
    (dossier / "SYNTHESE.md").write_text(construire_synthese(dossier, risques, lecture), encoding="utf-8")
    return len(risques), []


# ---------------------------------------------------------------------------------------------------- contrôles du code
def verifier_registre(dossier: Path) -> list[str]:
    """Le registre reprend-il exactement les menaces, les niveaux et les traitements des étapes 3, 4 et 5 ?"""
    dossier = Path(dossier)
    risques, problemes = lire_risques(dossier)
    lus = risques_du_registre(dossier)
    if not lus:
        return problemes + ["registre-risques.md ne contient aucune ligne de risque."]
    ids_registre = [r["id"] for r in lus]
    doubles = [i for i, k in Counter(ids_registre).items() if k > 1]
    if doubles:
        problemes.append("Identifiants en double dans le registre : " + ", ".join(doubles) + ".")
    attendus = {r["id"] for r in risques}
    manquants = sorted(attendus - set(ids_registre))
    if manquants:
        problemes.append("Menaces absentes du registre : " + ", ".join(manquants[:12]) + ".")
    niveaux_04 = {r["id"]: r["niveau"] for r in risques}
    differents = [r["id"] for r in lus if r["id"] in niveaux_04 and niveaux_04[r["id"]] != r["niveau"]]
    if differents:
        problemes.append("Niveau différent de l'étape 4 : " + ", ".join(differents[:12]) + ".")
    return problemes


def verifier_synthese(dossier: Path) -> list[str]:
    try:
        texte = (Path(dossier) / "SYNTHESE.md").read_text(encoding="utf-8")
    except OSError:
        return ["SYNTHESE.md est absente."]
    risques = risques_du_registre(dossier)
    problemes = []
    if risques and f"| Risques au registre | {len(risques)} |" not in texte:
        problemes.append("Le nombre de risques de la synthèse ne correspond pas au registre.")
    # identifiants en 1re ou 2e cellule d'un tableau seulement : « M365 » dans une phrase est un produit, pas un risque
    ids = (set(re.findall(r"^\|\s*([MR]-?\d{1,4})\s*\|", texte, re.M))
           | set(re.findall(r"^\|[^|]*\|\s*([MR]-?\d{1,4})\s*\|", texte, re.M)))
    inconnus = sorted(ids - {r["id"] for r in risques})
    if inconnus:
        problemes.append("Identifiants de la synthèse absents du registre : " + ", ".join(inconnus[:10]) + ".")
    return problemes


# ------------------------------------------------------------------------------------- texte de lecture rédigé par le modèle
def lecture_valide(texte: str, faits: str) -> tuple[bool, str]:
    """Le texte de lecture est-il utilisable ? Aucun nombre hors des chiffres fournis, pas de source ni de preuve inventée."""
    t = (texte or "").strip()
    if len(t) < 200:
        return False, "trop court"
    if len(t) > 2200:
        return False, "trop long"
    if re.search(r"\[E\d+\]|ISO27002-|ANSSI-|STRIDE-|LINDDUN-|CVE-\d|\|", t):
        return False, "contient une source, une preuve ou un tableau"
    autorises = set(re.findall(r"\d+(?:[.,]\d+)?", faits))
    inconnus = sorted({n for n in re.findall(r"\d+(?:[.,]\d+)?", t) if n not in autorises})
    if inconnus:
        return False, "nombre(s) absent(s) des chiffres fournis : " + ", ".join(inconnus[:6])
    return True, ""
