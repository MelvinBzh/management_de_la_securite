"""Propagation d'une décision humaine : on ne réécrit QUE les lignes qui en dépendent.

Règles :
- une décision « accepté tel quel » ne change rien ;
- une décision « refusé » ne réécrit aucune ligne (la synthèse la présente comme écartée) mais elle est tracée ;
- une décision « accepté avec modification » retrouve les lignes liées au risque (même identifiant dans les
  menaces, l'évaluation, le traitement et le registre), demande à un modèle de ne modifier que ce que la décision
  impose — avec les preuves de l'index sous les yeux — puis le CODE contrôle chaque ligne réécrite avant de
  l'accepter : même nombre de colonnes, identifiant de risque conservé, identifiants de preuve existants, aucun
  composant inventé, colonnes `valide_par` et date intactes. Une ligne qui échoue au contrôle reste telle quelle
  et est signalée « à valider ».
- tout est tracé dans `PROPAGATION.md` (avant → après, preuves, motifs de refus).

Le commentaire de l'analyste est une information HUMAINE (fiable) ; le reste du modèle ne l'est pas.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

NOM_DECISIONS = "decisions-analyste.json"
NOM_TRACE = "PROPAGATION.md"
FICHIERS_LIES = ("03-menaces.md", "04-evaluation.md", "05-traitement.md", "registre-risques.md")
MAX_LIGNES = 12
MODELE = "qwen3.5:9b"

SCHEMA = {"type": "object", "properties": {"lignes": {"type": "array", "items": {"type": "object", "properties": {
    "numero": {"type": "integer"}, "nouvelle": {"type": "string"}}, "required": ["numero", "nouvelle"]}}},
    "required": ["lignes"]}

CONSIGNE = (
    "Tu mets à jour des lignes d'un livrable d'analyse de risques après une DÉCISION HUMAINE.\n"
    "RISQUE : {risque}\nDÉCISION DE L'ANALYSTE (information fiable, c'est un humain) : {commentaire}\n\n"
    "LIGNES LIÉES (numérotées) :\n{lignes}\n\nPREUVES DISPONIBLES (identifiants [E…]) :\n{preuves}\n\n"
    "Règles : modifie UNIQUEMENT ce que la décision de l'analyste impose ; garde le même nombre de colonnes (séparées par |), "
    "les mêmes identifiants et la colonne valide_par telle quelle ; cite [E…] pour tout fait qui vient d'une preuve ; "
    "une information qui ne vient que de l'analyste est suivie de « (analyste) » ; n'invente rien. Réponds en JSON : "
    "lignes = liste de {{numero, nouvelle}} ; OMETS les lignes qui n'ont pas à changer."
)


def enregistrer_decision(dossier: Path, risque: str, decision: str, commentaire: str, analyste: str) -> None:
    """Journal des décisions à propager (écrit par `lib.enregistrer_decisions`)."""
    chemin = Path(dossier) / NOM_DECISIONS
    try:
        liste = json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        liste = []
    liste.append({"risque": risque, "decision": decision, "commentaire": commentaire, "analyste": analyste,
                  "date": time.strftime("%Y-%m-%d %H:%M"), "propage": False})
    chemin.write_text(json.dumps(liste, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def en_attente(dossier: Path) -> list[dict]:
    """Décisions « modifié » ou « refusé » pas encore propagées."""
    try:
        liste = json.loads((Path(dossier) / NOM_DECISIONS).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return [d for d in liste if not d.get("propage") and d.get("decision") in ("modifie", "refuse")]


def _cellules(ligne: str) -> list[str]:
    return [c.strip() for c in ligne.strip().strip("|").split("|")]


def lignes_liees(dossier: Path, risque: str) -> list[tuple[str, int, str]]:
    """Lignes de tableau (fichier, n° de ligne, texte) qui mentionnent l'identifiant du risque."""
    motif = re.compile(r"(?<![A-Za-z0-9])" + re.escape(risque) + r"(?![A-Za-z0-9])")
    trouvees = []
    for nom in FICHIERS_LIES:
        try:
            lignes = (Path(dossier) / nom).read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for numero, ligne in enumerate(lignes):
            if ligne.lstrip().startswith("|") and motif.search(ligne) and not set(ligne.replace("|", "").strip()) <= set("-: "):
                trouvees.append((nom, numero, ligne))
    return trouvees[:MAX_LIGNES]


def _indices_admin(dossier: Path) -> list[int]:
    """Positions des colonnes `valide_par` et date dans l'en-tête du registre (jamais réécrites)."""
    try:
        lignes = (Path(dossier) / "registre-risques.md").read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    for ligne in lignes:
        if ligne.lstrip().startswith("|"):
            return [i for i, c in enumerate(_cellules(ligne)) if "valide_par" in c.lower() or "date" in c.lower()]
    return []


def controler_ligne(originale: str, nouvelle: str, risque: str, *, ids_existants, base: str, termes, admin: list[int],
                    est_registre: bool) -> tuple[str, str]:
    """`(ligne_acceptée, motif_de_refus)` : la ligne réécrite si elle passe tous les contrôles du code, sinon l'originale."""
    nouvelle = nouvelle.strip()
    if not nouvelle.startswith("|"):
        return originale, "la ligne réécrite n'est plus une ligne de tableau"
    avant, apres = _cellules(originale), _cellules(nouvelle)
    if len(avant) != len(apres):
        return originale, f"nombre de colonnes modifié ({len(avant)} → {len(apres)})"
    if risque not in nouvelle:
        return originale, "l'identifiant du risque a disparu"
    inconnus = [i for i in re.findall(r"\[E(\d+)\]", nouvelle) if not ids_existants(int(i))]
    if inconnus:
        return originale, "preuve inexistante : " + ", ".join(f"[E{i}]" for i in inconnus)
    inventes = termes(nouvelle, base)
    if inventes:
        return originale, "composants absents des documents et de la décision : " + ", ".join(inventes)
    if est_registre:
        for i in admin:
            if i < len(avant) and apres[i] != avant[i]:
                apres[i] = avant[i]  # la validation n'est jamais réécrite par un modèle
        nouvelle = "| " + " | ".join(apres) + " |"
    return nouvelle, ""


def _reecrire_ollama(consigne: str) -> dict:
    from tools.connaissance import ollama
    return ollama.discuter_json(MODELE, consigne, SCHEMA, contexte=16384, max_sortie=2500)


def propager(dossier: Path, *, reecrire=None, index=None, base: str = "", termes=None, journal=print) -> list[dict]:
    """Propage les décisions en attente. Renvoie la trace (une entrée par décision) et l'écrit dans PROPAGATION.md.

    `reecrire(consigne) -> {"lignes": [{"numero", "nouvelle"}]}`, `index` (Index de connaissance, pour les preuves),
    `base` (texte des documents d'origine, minuscules) et `termes(texte, base)` sont injectables pour les tests."""
    dossier = Path(dossier)
    reecrire = reecrire or _reecrire_ollama
    if termes is None:
        from web.chaine import termes_non_fondes as termes  # import tardif : chaine importe ce module
    admin = _indices_admin(dossier)
    traces = []
    for decision in en_attente(dossier):
        risque, choix, commentaire = decision["risque"], decision["decision"], decision.get("commentaire", "")
        trace = {"risque": risque, "decision": choix, "commentaire": commentaire, "analyste": decision.get("analyste", ""),
                 "modifiees": [], "refusees": [], "message": ""}
        liees = lignes_liees(dossier, risque)
        if choix == "refuse":
            trace["message"] = "Risque refusé : aucune ligne n'est réécrite ; la synthèse le présente comme écarté, avec le motif."
        elif not liees:
            trace["message"] = "Aucune ligne liée trouvée dans les livrables : rien à réécrire."
        else:
            numerotees = "\n".join(f"{i + 1}. [{nom}] {ligne}" for i, (nom, _n, ligne) in enumerate(liees))
            preuves_txt = "(aucun index de connaissance)"
            if index is not None:
                _, _, requete = liees[0]
                try:
                    from tools.connaissance import ollama
                    vec = ollama.vecteurs([f"{risque} {commentaire}"], prefixe="search_query: ")[0] if reecrire is _reecrire_ollama else None
                except Exception:  # noqa: BLE001 — sans vecteur, la recherche par mots-clés suffit
                    vec = None
                trouves = index.rechercher(f"{risque} {commentaire} {requete}", vec, k=6)
                preuves_txt = "\n".join(f"[E{e['id']}] ({e['doc'][:30]}) {' '.join(e['extrait'].split())[:300]}" for e in trouves) or "(aucune)"
            try:
                reponse = reecrire(CONSIGNE.format(risque=risque, commentaire=commentaire or "(aucun commentaire)",
                                                   lignes=numerotees, preuves=preuves_txt))
            except Exception as exc:  # noqa: BLE001
                reponse = {"lignes": []}
                trace["message"] = f"Réécriture impossible ({type(exc).__name__}) : lignes laissées telles quelles, à valider à la main."
            existants = (lambda i: bool(index.base.execute("SELECT 1 FROM elements WHERE id = ?", (i,)).fetchone())) if index is not None else (lambda i: False)
            contenu = {}
            for brut in reponse.get("lignes", []):
                numero = brut.get("numero") if isinstance(brut, dict) else None
                if not isinstance(numero, int) or not 1 <= numero <= len(liees):
                    continue
                nom, position, originale = liees[numero - 1]
                acceptee, motif = controler_ligne(originale, str(brut.get("nouvelle", "")), risque, ids_existants=existants,
                                                  base=(base + " " + commentaire.lower()), termes=termes, admin=admin,
                                                  est_registre=nom == "registre-risques.md")
                if motif:
                    trace["refusees"].append({"fichier": nom, "avant": originale, "motif": motif})
                elif acceptee != originale:
                    contenu.setdefault(nom, {})[position] = acceptee
                    trace["modifiees"].append({"fichier": nom, "avant": originale, "apres": acceptee})
            for nom, remplacements in contenu.items():
                chemin = dossier / nom
                lignes = chemin.read_text(encoding="utf-8").split("\n")
                for position, texte in remplacements.items():
                    lignes[position] = texte
                chemin.write_text("\n".join(lignes), encoding="utf-8")
            if not trace["message"]:
                trace["message"] = (f"{len(trace['modifiees'])} ligne(s) réécrite(s), {len(trace['refusees'])} laissée(s) telle(s) quelle(s) "
                                    "après contrôle (à valider à la main).") if (trace["modifiees"] or trace["refusees"]) else \
                    "Les lignes liées n'avaient pas à changer."
        journal(f"[propagation] {risque} : {trace['message']}")
        traces.append(trace)
    if traces:
        _marquer(dossier, {t["risque"] for t in traces})
        _ecrire_trace(dossier, traces)
    return traces


def _marquer(dossier: Path, risques: set[str]) -> None:
    chemin = dossier / NOM_DECISIONS
    liste = json.loads(chemin.read_text(encoding="utf-8"))
    for d in liste:
        if not d.get("propage") and d.get("risque") in risques and d.get("decision") in ("modifie", "refuse"):
            d["propage"] = True
    chemin.write_text(json.dumps(liste, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ecrire_trace(dossier: Path, traces: list[dict]) -> None:
    chemin = dossier / NOM_TRACE
    sortie = [chemin.read_text(encoding="utf-8").rstrip() + "\n"] if chemin.is_file() else [
        "# Propagation des décisions de l'analyste\n\nSeules les lignes liées à un risque modifié sont réécrites ; "
        "chaque réécriture est contrôlée par le programme avant d'être acceptée.\n"]
    sortie.append(f"\n## {time.strftime('%Y-%m-%d %H:%M')}\n")
    for t in traces:
        sortie.append(f"### {t['risque']} — {'accepté avec modification' if t['decision'] == 'modifie' else 'refusé'} ({t['analyste'] or 'analyste'})\n")
        sortie.append(f"- Décision : {t['commentaire'] or '—'}\n- {t['message']}\n")
        for m in t["modifiees"]:
            sortie.append(f"- **Réécrit** dans `{m['fichier']}` :\n  - avant : {m['avant']}\n  - après : {m['apres']}\n")
        for r in t["refusees"]:
            sortie.append(f"- **Laissé tel quel** dans `{r['fichier']}` ({r['motif']}) — à valider à la main : {r['avant']}\n")
    chemin.write_text("\n".join(sortie), encoding="utf-8")
