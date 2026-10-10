"""Boîte de validation unique d'un projet : tout ce qui demande l'avis d'un humain, avec son contexte.

Cinq sortes de points, chacun avec POURQUOI il est là, QUOI vérifier, le CONTEXTE (section ou tableau en cause, ligne
concernée) et les PREUVES citées (extrait exact) :

  risque         un risque du registre (accepté / modifié / refusé)
  etape          une étape dont le contrôle automatique n'a pas pu trancher (« nécessite une validation humaine »)
  ligne          une ligne dont la preuve citée n'est pas établie (les deux vérificateurs la rejettent ou divergent)
  contradiction  deux documents qui se contredisent (priorité haute : un second modèle confirme)
  question       une information que le dossier ignore ou que deux documents contestent
  aval           IMPACT d'une de vos corrections : une ligne plus loin dans l'analyse cite la même preuve

Les décisions sont gardées dans `validations.json`. Une correction ou un retrait de ligne est ensuite propagé par
`web/propagation.py` (réécriture contrôlée, trace), qui crée à son tour des points « aval » à revoir.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from web import controles, lib, propagation

NOM_JSON = "validations.json"
FICHIERS_ORDRE = propagation.FICHIERS_ORDRE
ETAPE_DE_FICHIER = {"00-description.md": 1, "01-actifs.md": 1, "02-methodes.md": 2, "03-menaces.md": 3, "04-evaluation.md": 4,
                    "05-traitement.md": 5, "registre-risques.md": 6, "06-validation.md": 6, "SYNTHESE.md": 7}
MAX_CONTRADICTIONS = 15
MAX_QUESTIONS = 20
MAX_LIGNES = 60

TYPES = {
    "risque": "Risques du registre",
    "etape": "Étapes à valider",
    "ligne": "Lignes à relire",
    "contradiction": "Contradictions entre documents",
    "question": "Questions sans réponse",
    "aval": "Impacts de vos corrections",
}
CHOIX = {
    "risque": [("accepte", "Accepté tel quel"), ("modifie", "Accepté avec modification"), ("refuse", "Refusé")],
    "etape": [("verifie", "J'ai vérifié : c'est correct"), ("corrige", "À corriger (voir mon commentaire)"),
              ("ecarte", "Écarter ce qui est signalé")],
    "ligne": [("ok", "La preuve suffit : la ligne est correcte"), ("corrige", "La ligne est à corriger (voir mon commentaire)"),
              ("retire", "Retirer la ligne")],
    "contradiction": [("source_a", "La première source fait foi"), ("source_b", "La seconde source fait foi"),
                      ("deux", "Les deux sont vraies (cas différents)"), ("clarifier", "À clarifier avec l'entreprise")],
    "question": [("repondu", "Je fournis la réponse (voir mon commentaire)"), ("demander", "À demander à l'entreprise"),
                 ("sans_objet", "Sans objet pour cette analyse")],
    "aval": [("ok", "L'impact est correct"), ("corrige", "À corriger (voir mon commentaire)")],
}
COMMENTAIRE_OBLIGATOIRE = {("risque", "modifie"), ("risque", "refuse"), ("etape", "corrige"), ("ligne", "corrige"),
                           ("question", "repondu"), ("aval", "corrige"), ("contradiction", "clarifier")}
RE_CITATION = re.compile(r"`?\[E(\d+)\]`?")


def identifiant(type_: str, cle: str) -> str:
    return type_[:3] + "-" + hashlib.sha1(f"{type_}|{' '.join(str(cle).split())}".encode("utf-8")).hexdigest()[:10]


def lire_fichier(dossier: Path) -> dict:
    try:
        donnees = json.loads((Path(dossier) / NOM_JSON).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"decisions": {}, "aval": []}
    donnees.setdefault("decisions", {})
    donnees.setdefault("aval", [])
    return donnees


def _ecrire_fichier(dossier: Path, donnees: dict) -> None:
    (Path(dossier) / NOM_JSON).write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------------------------------- contexte
def _lignes(dossier: Path, fichier: str) -> list[str]:
    try:
        return (Path(dossier) / fichier).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def trouver_ligne(dossier: Path, ligne: str, fichiers: tuple[str, ...] | list[str] | None = None) -> tuple[str, int] | None:
    """`(fichier, indice)` de la ligne `ligne` (comparaison sans les marqueurs de citation) ; None si introuvable."""
    cible = " ".join(RE_CITATION.sub("", ligne).split())
    if not cible:
        return None
    for nom in (fichiers or FICHIERS_ORDRE):
        for i, l in enumerate(_lignes(dossier, nom)):
            if " ".join(RE_CITATION.sub("", l).split()) == cible:
                return nom, i
    return None


def contexte_ligne(dossier: Path, fichier: str, indice: int) -> str:
    """Markdown de contexte : titre de section, en-tête du tableau, puis la ligne (et ses voisines directes)."""
    lignes = _lignes(dossier, fichier)
    if not 0 <= indice < len(lignes):
        return ""
    titre = next((lignes[j].lstrip("# ").strip() for j in range(indice, -1, -1) if lignes[j].startswith("#")), "")
    debut = indice
    while debut > 0 and lignes[debut - 1].lstrip().startswith("|"):
        debut -= 1
    entete = lignes[debut:debut + 2] if lignes[indice].lstrip().startswith("|") and debut < indice else []
    voisines = lignes[max(indice - 1, debut):indice + 2] if lignes[indice].lstrip().startswith("|") else lignes[max(indice - 1, 0):indice + 2]
    morceaux = ([f"*{fichier}* — section « {titre} »"] if titre else [f"*{fichier}*"]) + [""]
    morceaux += [l for l in entete if l not in voisines] + [l for l in voisines if l.strip()]
    return "\n".join(morceaux)


def preuves_de(dossier: Path, texte: str) -> list[dict]:
    """Preuves `[E…]` citées dans `texte`, avec document et extrait exact (liste vide sans index)."""
    ids = [int(m.group(1)) for m in RE_CITATION.finditer(texte)]
    if not ids:
        return []
    from tools.connaissance import travail
    from tools.connaissance.index import Index
    base = travail.chemins(dossier)[1]
    if not base.is_file():
        return []
    index = Index(base)
    try:
        marques = ",".join("?" * len(set(ids)))
        lignes = index.base.execute(f"SELECT id, doc, extrait FROM elements WHERE id IN ({marques})", list(set(ids))).fetchall()
    finally:
        index.fermer()
    par_id = {i: (doc, extrait) for i, doc, extrait in lignes}
    return [{"id": i, "doc": par_id[i][0], "extrait": par_id[i][1]} for i in dict.fromkeys(ids) if i in par_id]


# ----------------------------------------------------------------------------------------------- construction
def _item(type_: str, cle: str, etape, titre: str, pourquoi: str, quoi: str, contexte: str = "", preuves: list | None = None,
          fichier: str = "", ligne: str = "", extra: dict | None = None) -> dict:
    item = {"id": identifiant(type_, cle), "type": type_, "etape": etape, "titre": titre, "pourquoi": pourquoi, "quoi": quoi,
            "contexte": contexte, "preuves": preuves or [], "fichier": fichier, "ligne": ligne, "choix": CHOIX[type_]}
    item.update(extra or {})
    return item


def _items_risques(dossier: Path) -> list[dict]:
    colonnes, risques = lib.lire_registre(dossier)
    items = []
    admin = {"id", "valide_par", "date validation"}
    for r in risques:
        rid = r["ID"]
        resume = " · ".join(str(r[c]) for c in colonnes[1:3] if c.lower() not in admin and r.get(c))
        champs = "\n".join(f"- **{c}** : {r[c]}" for c in colonnes[1:] if c.lower() not in admin and r.get(c))
        liees = [(f, l) for f, _p, l in propagation.lignes_liees(dossier, rid) if f != "registre-risques.md"]
        contexte = champs + ("\n\n**Lignes liées dans les autres livrables**\n\n" + "\n".join(f"- *{f}* : {l}" for f, l in liees) if liees else "")
        etat = str(r.get("valide_par", ""))
        items.append(_item("risque", rid, 6, f"{rid} — {resume[:130]}",
                           "Le registre propose ce risque : la décision d'accepter, de modifier ou de refuser vous appartient.",
                           "Le risque est-il réaliste pour cette entreprise ? Probabilité et impact vous semblent-ils justes ? "
                           "La mesure proposée est-elle applicable ?", contexte,
                           preuves_de(dossier, contexte), "registre-risques.md", "",
                           {"etat_actuel": etat if any(m in etat for m in ("accepté", "REFUSÉ")) else ""}))
    return items


def _items_etapes(dossier: Path) -> list[dict]:
    items = []
    for e in controles.a_valider(dossier):
        etape = e.get("etape")
        fichiers = [n for n, num in ETAPE_DE_FICHIER.items() if str(num) == str(etape)] if str(etape) != "finale" else ["registre-risques.md", "SYNTHESE.md"]
        extrait = []
        for nom in fichiers:
            tableaux = [l for l in _lignes(dossier, nom) if l.strip()][:14]
            if tableaux:
                extrait.append(f"*{nom}* (début) :\n\n" + "\n".join(tableaux))
        contexte = ("**Points relevés par le contrôle** : " + (e.get("corrections") or "—") + "\n\n" + "\n\n".join(extrait)).strip()
        items.append(_item("etape", f"{etape}|{e.get('libelle')}", etape, str(e.get("libelle")),
                           e["humaine"]["pourquoi"], e["humaine"]["quoi"], contexte, preuves_de(dossier, contexte),
                           ", ".join(fichiers), "", {"controle": e.get("numero")}))
    return items


def _items_lignes(dossier: Path) -> list[dict]:
    items = []
    for e in controles.a_relire(dossier):
        etape = e.get("etape")
        fichiers = [n for n, num in ETAPE_DE_FICHIER.items() if str(num) == str(etape)] or list(FICHIERS_ORDRE)
        for brut in e.get("doutes", []):
            kind = "non_soutenue" if brut.startswith("[non soutenue]") else "doute"
            texte = re.sub(r"^\[(non soutenue|doute)\]\s*", "", brut)
            place = trouver_ligne(dossier, texte, fichiers) or trouver_ligne(dossier, texte)
            if place is None:
                continue  # la ligne a été corrigée depuis : plus rien à relire
            fichier, indice = place
            actuelle = _lignes(dossier, fichier)[indice]
            pourquoi = ("Les deux vérificateurs indépendants estiment que la preuve citée ne soutient pas cette ligne."
                        if kind == "non_soutenue" else "Les deux vérificateurs indépendants ne sont pas d'accord sur cette ligne.")
            items.append(_item("ligne", f"{fichier}|{actuelle}", etape, f"{fichier} — {' '.join(RE_CITATION.sub('', actuelle).split())[:110]}",
                               pourquoi,
                               "Comparer la partie de la ligne qui cite une preuve avec l'extrait exact ci-dessous ; "
                               "les colonnes de jugement (probabilité, impact…) ne sont pas portées par l'extrait.",
                               contexte_ligne(dossier, fichier, indice), preuves_de(dossier, actuelle), fichier, actuelle,
                               {"gravite": 0 if kind == "non_soutenue" else 1}))
    items.sort(key=lambda i: i["gravite"])
    return items[:MAX_LIGNES]


def _index(dossier: Path):
    from tools.connaissance import travail
    from tools.connaissance.index import Index
    base = travail.chemins(dossier)[1]
    return Index(base) if base.is_file() else None


def _items_contradictions_questions(dossier: Path) -> list[dict]:
    index = _index(dossier)
    if index is None:
        return []
    try:
        contradictions = [c for c in index.contradictions() if c["confirmations"] >= 1][:MAX_CONTRADICTIONS]
        couvertures = index.couvertures()
    finally:
        index.fermer()
    items = []
    for c in contradictions:
        contexte = (f"**{c['doc_a']}** : « {c['extrait_a']} »\n\n**{c['doc_b']}** : « {c['extrait_b']} »")
        items.append(_item("contradiction", c["extrait_a"] + c["extrait_b"], "-", f"{c['doc_a'][:34]} ≠ {c['doc_b'][:34]}",
                           c["explication"] or "Deux documents semblent dire des choses incompatibles (confirmé par un second modèle).",
                           "Une règle écrite (politique) peut différer de la pratique constatée (audit) : décidez laquelle fait foi pour l'analyse.",
                           contexte, [], "", ""))
    ouvertes = [d for d in couvertures if d["statut"] == "inconnu" or d.get("contestations") or d.get("a_valider")]
    ouvertes.sort(key=lambda d: -d.get("priorite", 0))
    for d in ouvertes[:MAX_QUESTIONS]:
        etat = "CONTESTÉ par un autre document" if d.get("contestations") else ("non documenté" if d["statut"] == "inconnu" else d["statut"])
        contexte = (f"**Réponse tirée des documents** : {d['reponse'] or '—'}\n\n" if d.get("reponse") else "") + \
            "\n".join(f"- ({p['doc'][:34]}) « {p['extrait'][:220]} »" for p in d.get("preuves", []))
        if d.get("contestations"):
            contexte += "\n\n**Source qui contredit** : " + " ; ".join(f"{c['doc_b'][:30]} : « {c['extrait_b'][:160]} »" for c in d["contestations"][:2])
        items.append(_item("question", d["besoin"], "-", f"{d['question']} — {etat}",
                           ((d.get("pourquoi") + " ") if d.get("pourquoi") else "") + (
                               "Les documents n'en parlent pas : ce n'est pas une preuve que la mesure n'existe pas."
                               if d["statut"] == "inconnu" else ""),
                           "Fournir la réponse si vous la connaissez, ou noter qu'il faut la demander à l'entreprise.",
                           contexte.strip(), [], "", ""))
    return items


def _items_aval(dossier: Path) -> list[dict]:
    items = []
    for a in lire_fichier(dossier).get("aval", []):
        contexte = (f"**Modification en amont** (*{a['fichier_source']}*) :\n\n- avant : {a['avant']}\n- après : {a['apres']}\n\n"
                    f"**Ligne concernée plus loin** (*{a['fichier']}*) :\n\n{a['ligne']}")
        items.append(_item("aval", a["fichier"] + "|" + a["ligne"], ETAPE_DE_FICHIER.get(a["fichier"], "-"),
                           f"{a['fichier']} — {' '.join(RE_CITATION.sub('', a['ligne']).split())[:100]}",
                           "Cette ligne s'appuie sur la même preuve qu'une ligne que vous avez modifiée : elle peut devoir suivre.",
                           "Vérifier que cette ligne reste vraie après votre correction, sinon la corriger.", contexte,
                           preuves_de(dossier, a["ligne"]), a["fichier"], a["ligne"]))
    return items


def construire(dossier: Path) -> list[dict]:
    """Tous les points à valider du projet, chacun avec son état (`decision`, `commentaire`, `analyste`) déjà enregistré."""
    dossier = Path(dossier)
    items = (_items_risques(dossier) + _items_etapes(dossier) + _items_lignes(dossier)
             + _items_contradictions_questions(dossier) + _items_aval(dossier))
    decisions = lire_fichier(dossier)["decisions"]
    for item in items:
        d = decisions.get(item["id"], {})
        item["decision"] = d.get("decision", "")
        item["commentaire"] = d.get("commentaire", "")
        item["analyste"] = d.get("analyste", "")
        if item["type"] == "risque" and not item["decision"] and item.get("etat_actuel"):
            item["decision"] = "refuse" if "REFUSÉ" in item["etat_actuel"] else ("modifie" if "modification" in item["etat_actuel"] else "accepte")
    return items


def resume(items: list[dict]) -> dict:
    total = len(items)
    decides = sum(1 for i in items if i["decision"])
    par_type = {t: (sum(1 for i in items if i["type"] == t and i["decision"]), sum(1 for i in items if i["type"] == t)) for t in TYPES}
    return {"total": total, "decides": decides, "restants": total - decides, "par_type": par_type}


# ----------------------------------------------------------------------------------------------- enregistrement
def enregistrer(dossier: Path, analyste: str, saisies: dict[str, dict], items: list[dict]) -> dict:
    """Enregistre les décisions saisies (`{id: {decision, commentaire}}`). Refuse un commentaire manquant là où il est requis.

    Les risques passent par `lib.enregistrer_decisions` (registre, `06-validation.md`) ; une ligne à corriger ou à retirer,
    une étape à corriger et un impact aval à corriger sont mis en file pour la propagation."""
    nom = " ".join(str(analyste).split())
    if not nom:
        raise ValueError("Votre nom est requis : il est inscrit avec chaque décision.")
    par_id = {i["id"]: i for i in items}
    manque = []
    retenues = {}
    for ident, saisie in (saisies or {}).items():
        item = par_id.get(ident)
        decision = (saisie or {}).get("decision", "")
        if not item or not decision:
            continue
        if decision not in {c for c, _ in CHOIX[item["type"]]}:
            raise ValueError(f"Décision inconnue pour « {item['titre']} » : {decision}")
        commentaire = " ".join(str((saisie or {}).get("commentaire", "")).split())
        if (item["type"], decision) in COMMENTAIRE_OBLIGATOIRE and not commentaire:
            manque.append(item["titre"])
        retenues[ident] = {"decision": decision, "commentaire": commentaire[:600]}
    if manque:
        raise ValueError("Un commentaire est obligatoire pour : " + " ; ".join(manque[:6]))
    if not retenues:
        raise ValueError("Aucune décision à enregistrer : choisissez au moins un point.")
    dossier = Path(dossier)
    donnees = lire_fichier(dossier)
    date = time.strftime("%Y-%m-%d %H:%M")
    risques = {}
    for ident, d in retenues.items():
        item = par_id[ident]
        donnees["decisions"][ident] = {**d, "analyste": nom, "date": date, "type": item["type"], "titre": item["titre"]}
        if item["type"] == "risque":
            rid = item["titre"].split(" — ")[0]
            risques[rid] = d
        elif item["type"] in ("ligne", "aval") and d["decision"] in ("corrige", "retire"):
            propagation.enregistrer_decision(dossier, "", "retire" if d["decision"] == "retire" else "modifie", d["commentaire"], nom,
                                             cible={"fichier": item["fichier"], "ligne": item["ligne"], "type": item["type"]})
        elif item["type"] == "etape" and d["decision"] == "corrige":
            propagation.enregistrer_decision(dossier, "", "modifie", d["commentaire"], nom,
                                             cible={"fichier": item["fichier"].split(", ")[0], "ligne": "", "type": "etape"})
    _ecrire_fichier(dossier, donnees)
    bilan = {}
    if risques:
        bilan = lib.enregistrer_decisions(dossier, nom, risques)
    return {"enregistres": len(retenues), "risques": bilan}


def exporter_markdown(items: list[dict], titre: str = "Points à valider") -> str:
    """Liste lisible de tous les points (avec décision si prise) : un document de travail, pas l'outil de validation."""
    sortie = [f"# {titre}", ""]
    for type_, libelle in TYPES.items():
        lot = [i for i in items if i["type"] == type_]
        if not lot:
            continue
        sortie += [f"## {libelle} ({len(lot)})", ""]
        for i in lot:
            etat = dict(i["choix"]).get(i["decision"], "à décider") if i["decision"] else "à décider"
            sortie += [f"### {i['titre']}", f"- **État** : {etat}" + (f" — {i['commentaire']}" if i.get("commentaire") else ""),
                       f"- **Pourquoi** : {i['pourquoi']}", f"- **Quoi vérifier** : {i['quoi']}"]
            if i.get("contexte"):
                sortie += ["- **Contexte** :", "", i["contexte"], ""]
            for p in i.get("preuves", []):
                sortie.append(f"  - preuve [E{p['id']}] ({p['doc']}) : « {p['extrait'][:300]} »")
            sortie.append("")
    return "\n".join(sortie) + "\n"
