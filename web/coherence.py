"""Contrôles de cohérence par le CODE (aucun modèle) sur les livrables d'une analyse.

Pourquoi : sur le run réel du 2026-10-10 (Nordval), ces défauts n'étaient attrapés par rien — ou seulement par hasard par
un modèle relecteur : 8 identifiants utilisés sans être définis, 7 actifs cités par plusieurs documents mais absents du
tableau des actifs, 1 nombre inexistant dans les documents. Ils sont vérifiables par du code, donc rapidement, sans
erreur d'appréciation et sans occuper le GPU.

Deux niveaux de sévérité :
  - BLOQUANT : l'agent peut le corriger sans deviner (identifiant non défini, actif manquant, doublon, texte
    d'attente). Il part en reprise avec la liste précise ;
  - ALERTE : à relire par un humain (un nombre absent des documents est soit calculé, soit inventé : le code ne sait pas).
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

ORDRE = ("00-description.md", "01-actifs.md", "02-methodes.md", "03-menaces.md", "04-evaluation.md", "05-traitement.md",
         "06-validation.md", "registre-risques.md", "SYNTHESE.md")
# fichiers où des identifiants d'actif / de menace / de risque sont UTILISÉS (et doivent avoir été définis plus tôt)
FICHIERS_IDENTIFIANTS = ("03-menaces.md", "04-evaluation.md", "05-traitement.md", "06-validation.md", "registre-risques.md", "SYNTHESE.md")
FICHIERS_NOMBRES = ("00-description.md", "01-actifs.md", "02-methodes.md", "03-menaces.md", "05-traitement.md", "registre-risques.md", "SYNTHESE.md")
TYPES_ACTIFS = ("systeme", "materiel", "prestataire", "donnee", "site")
RE_ID = re.compile(r"(?<![\w.#/-])(?:[AMRTF]|MEN|RSK|ACT)-?\d{1,2}(?![\w.])")
RE_ID_DEFINITION = re.compile(r"^(?:[AMRTF]|MEN|RSK|ACT)-?\d{1,3}$")
RE_PLACEHOLDER = re.compile(r"à compléter|a completer|\bTBD\b|\bTODO\b|lorem ipsum|\bxxx+\b|à définir|à renseigner par l'agent|…{2,}", re.I)
RE_SEPARATEUR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


def lire(dossier: Path, nom: str) -> str:
    try:
        return (Path(dossier) / nom).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def tableaux(texte: str) -> list[dict]:
    """Tableaux Markdown : `{entete, lignes: [(numéro_de_ligne, cellules)]}` (hors séparateur)."""
    sortie, courant, debut = [], [], 0
    lignes = texte.splitlines()
    for i, l in enumerate(lignes + [""]):
        if l.lstrip().startswith("|"):
            if not courant:
                debut = i
            courant.append(l)
        elif courant:
            cellules = [[c.strip() for c in x.strip().strip("|").split("|")] for x in courant if not RE_SEPARATEUR.match(x)]
            if cellules:
                sortie.append({"entete": cellules[0], "lignes": [(debut + 2 + k, c) for k, c in enumerate(cellules[1:])]})
            courant = []
    return sortie


def _nettoyer(cellule: str) -> str:
    return re.sub(r"[*`_]", "", cellule).strip()


def identifiants_definis(dossier: Path) -> set[str]:
    """Identifiants posés en première colonne d'un tableau de n'importe quel livrable (A1, M3, R-07…)."""
    definis: set[str] = set()
    for nom in ORDRE:
        for t in tableaux(lire(dossier, nom)):
            for _n, cellules in t["lignes"]:
                if cellules and RE_ID_DEFINITION.match(_nettoyer(cellules[0])):
                    definis.add(_nettoyer(cellules[0]))
    return definis


def identifiants_non_definis(dossier: Path, fichiers: list[str] | tuple[str, ...] = FICHIERS_IDENTIFIANTS) -> dict[str, list[str]]:
    """`{identifiant: [fichiers où il est utilisé]}` pour les identifiants utilisés mais jamais définis dans un tableau."""
    definis = identifiants_definis(dossier)
    # un identifiant « A-3 » et « A3 » désignent la même chose
    canon = {re.sub(r"-", "", d) for d in definis}
    manquants: dict[str, list[str]] = {}
    for nom in fichiers:
        texte = re.sub(r"\[E\d+\]", " ", lire(dossier, nom))
        texte = re.sub(r"https?://\S+|`[^`]*ISO[^`]*`", " ", texte)
        for m in set(RE_ID.findall(texte)):
            if re.sub(r"-", "", m) not in canon and m not in definis:
                manquants.setdefault(m, []).append(nom)
    return manquants


def actifs_manquants(dossier: Path, base_index: Path, fichier: str = "01-actifs.md", minimum_docs: int = 2) -> list[tuple[str, str, int]]:
    """Entités (système, matériel, prestataire, donnée, site) citées par au moins `minimum_docs` documents et absentes du
    livrable `fichier`. Une entité est « présente » si l'un de ses noms (alias compris) y figure."""
    base_index = Path(base_index)
    if not base_index.is_file():
        return []
    texte = re.sub(r"[^0-9a-zàâäçéèêëîïôöùûüÿœ]+", " ", lire(dossier, fichier).lower())
    base = sqlite3.connect(f"file:{base_index}?mode=ro", uri=True)
    try:
        lignes = base.execute("SELECT nom, canonique, type, docs FROM entites").fetchall()
    finally:
        base.close()
    groupes: dict[str, dict] = {}
    for nom, canonique, type_, docs in lignes:
        g = groupes.setdefault(canonique, {"noms": set(), "types": set(), "docs": set()})
        g["noms"].add(nom)
        g["types"].add(type_)
        g["docs"].update(json.loads(docs or "[]"))
    manquants = []
    for canonique, g in groupes.items():
        if not (g["types"] & set(TYPES_ACTIFS)) or len(g["docs"]) < minimum_docs or len(canonique) < 3:
            continue
        variantes = {re.sub(r"[^0-9a-zàâäçéèêëîïôöùûüÿœ]+", " ", n.lower()).strip() for n in g["noms"] | {canonique}}
        if not any(v and (" " + v + " ") in (" " + texte + " ") for v in variantes):
            manquants.append((canonique, sorted(g["types"] & set(TYPES_ACTIFS))[0], len(g["docs"])))
    return sorted(manquants, key=lambda x: -x[2])


def _normaliser_nombre(n: str) -> str:
    return re.sub(r"[\s  ]", "", n).replace(",", ".")


def nombres_introuvables(texte: str, corpus: str) -> list[tuple[str, str]]:
    """`[(nombre, ligne)]` : nombres du livrable qui ne figurent dans AUCUN document.

    Écartés : années, références de normes (5.15, 8.22…), identifiants, scores ≤ 10 avec décimale (niveaux calculés),
    nombres devant risque(s) / menace(s) / actif(s) / étape (comptages du livrable lui-même)."""
    base = _normaliser_nombre(re.sub(r"(?<=\d)[\s  ](?=\d{3}\b)", "", corpus))
    corpus_nombres = set(re.findall(r"\d+(?:\.\d+)?", base))
    trouves = []
    for ligne in texte.splitlines():
        if re.match(r"\s*(?:#|style |classDef |class |linkStyle |graph |flowchart |subgraph |end|```|[-=]{3,})", ligne):
            continue  # titre, schéma Mermaid, séparateur : pas de contenu factuel
        if re.search(r"fin du document|page \d+ sur \d+|^\s*\d+[.)]\s", ligne, re.I):
            continue  # pied de page, numérotation de liste
        brut = re.sub(r"\[E\d+\]|`\[E\d+\]`", " ", ligne)
        brut = re.sub(r"0\d(?=\s*[—–-])|^\s*[#*\d. -]*\d{2}\s*[—–-]", " ", brut)  # « 00 — Description » : numéro d'étape
        brut = re.sub(r"§\s*\d+(?:\.\d+)*|(?:section|annexe|chapitre|art(?:icle)?\.?)\s*\d+(?:\.\d+)*|A\.\d+(?:\.\d+)*", " ", brut, flags=re.I)
        # codes à tiret (ISO27002-8.22, STRIDE-S, ANSSI-HYGIENE-3.2…) et identifiants : jamais des valeurs à retrouver
        brut = re.sub(r"\b[A-Za-z][A-Za-z0-9&]*(?:-[A-Za-z0-9.&]+)+\b", " ", brut)
        brut = re.sub(r"\bISO[\s/]*(?:IEC[\s/]*)?\d+(?:[-:\s]+\d+(?:\.\d+)*)?|\b[AMRTF]-?\d{1,3}\b", " ", brut)
        iso = bool(re.search(r"ISO|27002|ANSSI|annexe|contrôle|mesure|NIST|CIS|OWASP|ASVS|§", brut, re.I))
        for m in re.finditer(r"(?<![\w.,])\d{1,3}(?:[  ]\d{3})*(?:[.,]\d+)?(?![\w.,]*\d)", brut):
            n = _normaliser_nombre(m.group(0))
            chiffres = re.sub(r"\D", "", n)
            suite = brut[m.end():m.end() + 14].lower()
            if re.search(r"(?:\bsur|/)\s*$", brut[max(0, m.start() - 6):m.start()].lower()):
                continue  # « 4,5 sur 10 », « 3/5 » : échelle de notation, pas une donnée du cas
            if len(chiffres) < 2 and "." not in n:
                continue
            if re.fullmatch(r"(?:19|20)\d\d", n) or (iso and re.fullmatch(r"\d{1,2}\.\d{1,2}", n)):
                continue
            if re.fullmatch(r"\d{1,2}\.\d{1,2}", n) and re.search(r"(?:LINDDUN|STRIDE|EBIOS|DREAD|ATT&CK|MITRE|knowledge_base)", brut):
                continue  # référence de grille ou de mesure dans une ligne de menace / de traitement
            if re.fullmatch(r"\d\.\d", n) and float(n) <= 10:
                continue  # score calculé (niveau, DREAD, CVSS)
            if re.match(r"\s*(?:risques?|menaces?|actifs?|étapes?|lignes?|mesures?|points?|documents?|sites?)\b", suite):
                continue
            if n not in corpus_nombres:
                trouves.append((m.group(0), ligne.strip()))
    vus, resultat = set(), []
    for n, l in trouves:
        if (n, l) not in vus:
            vus.add((n, l))
            resultat.append((n, l))
    return resultat


def doublons(texte: str) -> list[str]:
    """Lignes de tableau en double (mêmes deux premières cellules significatives)."""
    vus, dup = {}, []
    for t in tableaux(texte):
        for _n, c in t["lignes"]:
            cle = tuple(_nettoyer(x).lower() for x in c[:3])
            if not any(cle):
                continue
            if cle in vus:
                dup.append(" | ".join(_nettoyer(x) for x in c[:3]))
            vus[cle] = True
    return dup


def textes_d_attente(texte: str) -> list[str]:
    """Lignes qui contiennent un texte d'attente (« à compléter », TBD…) au lieu d'une information."""
    return [l.strip()[:140] for l in texte.splitlines() if l.lstrip().startswith("|") and RE_PLACEHOLDER.search(l)]


def controler(dossier: Path, fichiers: list[str], *, base_index: Path | None = None, corpus: str = "",
              numero: int | None = None) -> tuple[str, list[str]]:
    """Contrôle les livrables `fichiers` d'une étape. Renvoie `(corrections_bloquantes, alertes)`.

    Les corrections sont un texte prêt à redonner à l'agent ; les alertes (nombres sans source) vont à la relecture."""
    corrections, alertes = [], []
    dossier = Path(dossier)
    manquants_id = identifiants_non_definis(dossier, [f for f in fichiers if f in FICHIERS_IDENTIFIANTS])
    if manquants_id:
        liste = "; ".join(f"{i} ({', '.join(f)})" for i, f in sorted(manquants_id.items())[:12])
        corrections.append("Identifiants utilisés mais jamais définis dans un tableau — définis-les ou utilise un identifiant existant : " + liste + ".")
    if "01-actifs.md" in fichiers and base_index is not None:
        manque = actifs_manquants(dossier, base_index)
        if manque:
            corrections.append("Actifs cités par plusieurs documents et ABSENTS du tableau des actifs — ajoute une ligne pour chacun (ou "
                               "explique pourquoi il est hors périmètre) : " + "; ".join(f"{n} ({t}, {d} documents)" for n, t, d in manque[:12]) + ".")
    for nom in fichiers:
        texte = lire(dossier, nom)
        dup = doublons(texte)
        if dup:
            corrections.append(f"{nom} : lignes en double à fusionner : " + "; ".join(dup[:5]) + ".")
        attente = textes_d_attente(texte)
        if attente:
            corrections.append(f"{nom} : texte d'attente à remplacer par l'information ou par « non documenté » : " + " | ".join(attente[:3]))
        if corpus and nom in FICHIERS_NOMBRES:
            alertes += [f"[nombre introuvable:{n}] {l}" for n, l in nombres_introuvables(texte, corpus)[:15]]
    return " ".join(corrections), alertes
