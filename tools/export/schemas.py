# -*- coding: utf-8 -*-
"""Réparation des schémas Mermaid écrits par les modèles.

Un petit modèle écrit des schémas qui « ressemblent » à du Mermaid mais que l'analyseur refuse : flèche Unicode (`-.→`),
nom d'étape avec espaces (`DMZ -->|VPN| Réseau interne`), parenthèses non guillemetées dans un libellé
(`E[Prioriser (DREAD/CVSS)]`), `subgraph "titre"`, citation `[E12]` collée dans le schéma… Le diagramme s'affiche alors comme
une erreur. Ces défauts sont réguliers : le code les corrige, sans rien changer à ce que le schéma dit.

    reparer_mermaid(code)   -> (code corrigé, [description de chaque correction])
    reparer_markdown(texte) -> (texte corrigé, [corrections])      # tous les blocs ```mermaid d'un livrable

Validé avec l'analyseur officiel de Mermaid (voir tools/export/tests/test_schemas.py et la page de contrôle du dépôt).
Ce qui ne peut pas être réparé sûrement est mis en commentaire (`%% …`) plutôt que d'invalider tout le schéma.
"""
from __future__ import annotations

import re
import unicodedata

TYPES_FLUX = ("flowchart", "graph")
RE_BLOC = re.compile(r"(```[ \t]*mermaid[ \t]*\n)(.*?)(```)", re.S | re.I)
RE_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
RE_FORME = re.compile(
    r"^(?P<id>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<ouv>\(\(|\(\[|\[\[|\[\(|\[|\(|\{|>)(?P<txt>.*?)(?P<fer>\)\)|\]\)|\]\]|\)\]|\]|\)|\})\s*$", re.S)
PAIRES = {"[": "]", "(": ")", "{": "}", "((": "))", "([": "])", "[[": "]]", "[(": ")]", ">": "]"}
RE_LIEN = re.compile(r"<?(?:-{2,}|={2,}|-\.+-?)(?:>|[xo](?![A-Za-z0-9_]))?")
MOTS_CLES = ("subgraph", "end", "style", "classDef", "class", "linkStyle", "direction", "click", "%%")


def _sans_accents(texte: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texte) if unicodedata.category(c) != "Mn")


def _identifiant(texte: str, deja: dict[str, str]) -> str:
    """Identifiant Mermaid sûr (ASCII, sans espace) pour un nom libre ; stable pour un même texte."""
    cle = texte.strip()
    if cle in deja:
        return deja[cle]
    base = re.sub(r"[^A-Za-z0-9]+", "_", _sans_accents(cle)).strip("_") or "noeud"
    if not re.match(r"[A-Za-z_]", base):
        base = "n_" + base
    base = base[:32]
    candidat, n = base, 2
    while candidat in deja.values() or candidat.lower() in MOTS_CLES:
        candidat = f"{base}_{n}"
        n += 1
    deja[cle] = candidat
    return candidat


RE_SIMPLE = re.compile(r"^[\w .,/'+%-]*$", re.UNICODE)


def _guillemets(texte: str, toujours: bool = False) -> str:
    """Libellé entre guillemets quand il contient ce qui casse l'analyseur ; un libellé simple reste tel quel."""
    t = texte.strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        return t
    sans_br = re.sub(r"<br\s*/?>", " ", t, flags=re.I)
    if not toujours and RE_SIMPLE.match(sans_br):
        return t
    return '"' + t.replace('"', "'") + '"'


def _normaliser_caracteres(ligne: str) -> str:
    # tirets insécables / typographiques dans les liens et les identifiants
    ligne = ligne.replace("‑", "-").replace("‐", "-").replace("‒", "-")
    # flèches Unicode utilisées comme liens
    ligne = re.sub(r"(-\.+|-{1,}|={1,})\s*[→⟶➔➜➝⇒]", lambda m: ("-.->" if "." in m.group(1) else ("==>" if "=" in m.group(1) else "-->")), ligne)
    ligne = re.sub(r"\s[—–]+>\s", " --> ", ligne)
    ligne = re.sub(r"(?<![-=.<])\s->\s", " --> ", ligne)
    ligne = re.sub(r"\s[→⟶➔➜➝⇒]\s", " --> ", ligne)
    # citation utilisée comme NOM de nœud en tête d'arête (« [E12] --> DSI ») : on garde le lien avec un nœud « Preuve E12 »
    ligne = re.sub(r"^(\s*)\[E(\d+)\](?=\s*(?:<?-{2}|={2}|-\.))",
                   lambda m: f'{m.group(1)}E{m.group(2)}["Preuve E{m.group(2)}"]', ligne)
    ligne = re.sub(r"(?<![A-Za-z0-9_])\[E\d+\]", "", ligne)   # citation collée dans un libellé ou une arête
    return ligne.rstrip()


RE_OUVERTURE = re.compile(r"^(?P<id>[A-Za-z_][A-Za-z0-9_]*)\s*(?P<ouv>\(\(|\(\[|\[\[|\[\(|\[|\(|\{|>)(?P<reste>.*)$", re.S)


def _forme(t: str) -> tuple[str, str, str, str] | None:
    """`(id, ouverture, texte, fermeture)` d'un nœud `id[texte]`, `id(texte)`, `id{texte}`… ; la fermeture attendue est celle
    de l'OUVERTURE (le texte peut contenir des parenthèses : `A[Base (SQL)]`). `None` si le nœud n'est pas de cette forme."""
    m = RE_OUVERTURE.match(t)
    if not m:
        return None
    ouv, reste = m.group("ouv"), m.group("reste").rstrip()
    fer = PAIRES[ouv]
    if not reste.endswith(fer):
        return None
    return m.group("id"), ouv, reste[: -len(fer)], fer


def _noeud(texte: str, labels: dict[str, str], definis: set[str]) -> tuple[str, str]:
    """`(texte_du_noeud_pour_la_ligne, id)` : forme guillemetée, ou identifiant seul si déjà défini."""
    t = texte.strip().rstrip(";").strip()
    forme = _forme(t)
    if forme:
        ident, ouv, txt, fer = forme
        definis.add(ident)
        return f"{ident}{ouv}{_guillemets(txt)}{fer}", ident
    if RE_ID.match(t):
        return t, t
    ident = _identifiant(t, labels)
    if ident in definis:
        return ident, ident
    definis.add(ident)
    return f"{ident}[{_guillemets(t)}]", ident


def _aretes(ligne: str) -> tuple[list[str], list[str]] | None:
    """`(noeuds, liens)` d'une ligne d'arêtes, en respectant guillemets et parenthèses ; `None` si pas d'arête."""
    noeuds, liens, debut, i, profondeur, guillemets = [], [], 0, 0, 0, False
    while i < len(ligne):
        c = ligne[i]
        if c == '"':
            guillemets = not guillemets
        elif not guillemets:
            if c in "([{":
                profondeur += 1
            elif c in ")]}":
                profondeur = max(0, profondeur - 1)
            elif profondeur == 0:
                m = RE_LIEN.match(ligne, i)
                if m and (i == 0 or ligne[i - 1] in " \t" or ligne[i - 1] in ")]}\""):
                    noeuds.append(ligne[debut:i])
                    lien = m.group(0)
                    j = m.end()
                    etiquette = ""
                    k = j
                    while k < len(ligne) and ligne[k] == " ":
                        k += 1
                    if k < len(ligne) and ligne[k] == "|":
                        fin = ligne.find("|", k + 1)
                        if fin != -1:
                            etiquette = ligne[k + 1:fin]
                            j = fin + 1
                    liens.append((lien, etiquette))
                    debut, i = j, j
                    continue
        i += 1
    if not liens:
        return None
    noeuds.append(ligne[debut:])
    return noeuds, liens


def _reparer_flux(lignes: list[str], corrections: list[str]) -> list[str]:
    labels: dict[str, str] = {}
    definis: set[str] = set()
    sortie: list[str] = []
    n_sg = 0
    for brute in lignes:
        indentation = re.match(r"^\s*", brute).group(0)
        ligne = _normaliser_caracteres(brute).strip()
        if brute.strip() and _normaliser_caracteres(brute).strip() != brute.strip():
            pass
        if not ligne:
            sortie.append("")
            continue
        if ligne.startswith("%%") or re.match(r"^(flowchart|graph)\b", ligne, re.I) or re.match(r"^(end|direction)\b", ligne) \
                or re.match(r"^(style|classDef|class|linkStyle|click)\b", ligne):
            sortie.append(indentation + ligne)
            continue
        m = re.match(r"^subgraph\s+(.*)$", ligne)
        if m:
            reste = m.group(1).strip()
            forme = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\[(.*)\]\s*$", reste)
            if forme:
                nouveau = f'subgraph {forme.group(1)}[{_guillemets(forme.group(2))}]'
            else:
                n_sg += 1
                nouveau = f"subgraph sg{n_sg}[{_guillemets(reste.strip().strip(chr(34)), toujours=True)}]"
            if nouveau != ligne:
                corrections.append(f"titre de zone mis en forme : {reste[:50]}")
            sortie.append(indentation + nouveau)
            continue
        # « A -- texte --> B »  →  « A -->|texte| B »
        ligne = re.sub(r"\s--\s+([^->|][^|]*?)\s+-->\s", lambda mm: f" -->|{mm.group(1).strip()}| ", ligne)
        decoupe = _aretes(ligne)
        if decoupe is None:
            # définition de nœud seule, ou texte libre
            t = ligne.rstrip(";")
            if RE_FORME.match(t) or RE_ID.match(t):
                nouveau, _ = _noeud(t, labels, definis)
            else:
                corrections.append("ligne ni nœud ni lien, mise en commentaire : " + ligne[:60])
                sortie.append(indentation + "%% " + ligne)
                continue
            if nouveau != t:
                corrections.append(f"libellé guillemeté : {t[:50]}")
            sortie.append(indentation + nouveau)
            continue
        noeuds, liens = decoupe
        sans_forme = [re.sub(r"<br\s*/?>", " ", x, flags=re.I) for x in noeuds]
        if any(not x.strip() for x in noeuds) or any(re.search(r"--|[<>](?![^\[\]\"]*[\]\"])", x) for x in sans_forme):
            # nœud manquant, ou lien mal formé collé à un nom (« A <----B--- C ») : impossible à réparer sans deviner
            corrections.append("lien incomplet ou mal formé, mis en commentaire : " + ligne[:60])
            sortie.append(indentation + "%% " + ligne)
            continue
        morceaux = []
        for k, txt in enumerate(noeuds):
            cibles = [p.strip() for p in re.split(r"\s+&\s+", txt)]
            normalises = [_noeud(p, labels, definis)[0] for p in cibles]
            morceaux.append(" & ".join(normalises))
            if k < len(liens):
                lien, etiquette = liens[k]
                lien = re.sub(r"^-{3,}>$", "-->", lien) if lien.endswith(">") and lien.startswith("---") and False else lien
                morceaux.append(lien if not etiquette.strip() else f'{lien}|{_guillemets(etiquette)}|')
        nouveau = " ".join(morceaux)
        if re.sub(r"\s+", "", nouveau) != re.sub(r"\s+", "", ligne):
            corrections.append("lien réparé : " + ligne[:70])
        sortie.append(indentation + nouveau)
    # les corrections sont comptées par DIFFÉRENCE avec le texte d'origine (une flèche Unicode remplacée en est une aussi)
    corrections.clear()
    for avant, apres in zip(lignes, sortie):
        if avant.strip() != apres.strip():
            corrections.append(("mise en commentaire : " if apres.strip().startswith("%%") else "corrigée : ") + avant.strip()[:70])
    return sortie


def reparer_mermaid(code: str) -> tuple[str, list[str]]:
    """Code Mermaid réparé et la liste des corrections ; un schéma déjà correct est rendu inchangé."""
    corrections: list[str] = []
    lignes = code.replace("\r", "").split("\n")
    premiere = next((l.strip() for l in lignes if l.strip() and not l.strip().startswith("%%")), "")
    est_flux = premiere.split()[:1] and premiere.split()[0].lower() in TYPES_FLUX
    if est_flux:
        propres = _reparer_flux(lignes, corrections)
    else:
        propres = [_normaliser_caracteres(l) for l in lignes]
        if propres != [l.rstrip() for l in lignes]:
            corrections.append("caractères typographiques ou citations retirés")
    resultat = "\n".join(propres)
    if code.endswith("\n") and not resultat.endswith("\n"):
        resultat += "\n"
    return resultat, corrections


def reparer_markdown(texte: str) -> tuple[str, list[str]]:
    """Répare tous les blocs ```mermaid d'un texte Markdown."""
    toutes: list[str] = []

    def remplacer(m: re.Match) -> str:
        code, c = reparer_mermaid(m.group(2))
        toutes.extend(c)
        return m.group(1) + code + m.group(3)

    return RE_BLOC.sub(remplacer, texte), toutes


def reparer_fichier(chemin) -> int:
    """Répare les schémas Mermaid d'un livrable, sur place. Renvoie le nombre de corrections (0 : rien n'a été écrit).

    L'ancienne version est gardée à côté (`<nom>.avant-correction-schema.md`) la première fois."""
    from pathlib import Path
    chemin = Path(chemin)
    try:
        texte = chemin.read_text(encoding="utf-8")
    except OSError:
        return 0
    nouveau, corrections = reparer_markdown(texte)
    if not corrections or nouveau == texte:
        return 0
    copie = chemin.with_name(chemin.stem + ".avant-correction-schema" + chemin.suffix)
    if not copie.exists():
        copie.write_text(texte, encoding="utf-8")
    temporaire = chemin.with_suffix(chemin.suffix + ".tmp")
    temporaire.write_text(nouveau, encoding="utf-8")
    temporaire.replace(chemin)
    return len(corrections)
