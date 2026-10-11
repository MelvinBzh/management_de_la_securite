"""Production d'un livrable PAR PETITES PARTIES (lots), assemblées par le code.

Pourquoi : un agent de 9 milliards de paramètres qui écrit en une fois un livrable de 15 000 caractères perd le fil,
déborde sa fenêtre (résumé automatique d'opencode), oublie des éléments et recopie ce qu'on lui a dit de corriger.
Chaque lot est une tâche BORNÉE :

  - il reçoit un petit nombre d'éléments à traiter (« liste de contrôle ») et UN dossier de preuves taillé pour eux ;
  - il écrit seulement des LIGNES de tableau, dans un fichier à part (`parties/…`) ;
  - le code vérifie la partie (colonnes, éléments couverts), pose les identifiants, puis ASSEMBLE le livrable
    avec l'en-tête et l'ordre voulus ;
  - une reprise ne refait QUE les lots concernés par les corrections.

Quatre livrables sont produits ainsi : 01-actifs.md (par thème), 03-menaces.md (par groupe d'actifs),
04-evaluation.md (par groupe de menaces), 05-traitement.md (par groupe de risques). Les autres restent en une passe.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

ETAPES_PAR_LOTS = {1: ("01-actifs.md",), 3: ("03-menaces.md",), 4: ("04-evaluation.md",), 5: ("05-traitement.md",)}
TAILLE_LOT = {"03-menaces.md": 5, "04-evaluation.md": 8, "05-traitement.md": 8}
BUDGET_PREUVES_LOT = 14000
MAX_LIGNES_LOT_ACTIFS = 16      # un lot d'inventaire regroupe les éléments de même nature (mesuré : 115 actifs sans plafond)
SEUIL_EXCES_ACTIFS = 40          # mesuré : le modèle rend 24 à 25 lignes malgré « au plus 16 » ; refaire un lot coûte plus cher
MAX_LOTS = 12                    # au-delà, la taille des lots grandit : la durée de la chaîne reste bornée

ENTETES: dict[str, tuple[str, list[str]]] = {
    "01-actifs.md": ("# Inventaire des actifs (étape 1)",
                     ["ID", "Actif", "Type", "Description, périmètre et valeur", "Sensibilité", "Preuve source"]),
    "03-menaces.md": ("# Menaces (étape 3)",
                      ["ID", "Actif concerné", "Catégorie (grille)", "Description", "CVE si connue", "Source"]),
    "04-evaluation.md": ("# Évaluation des risques (étape 4)",
                         ["ID", "Menace", "Probabilité", "Justification probabilité", "Impact", "Justification impact", "Niveau",
                          "Justification globale"]),
    "05-traitement.md": ("# Traitement des risques (étape 5)",
                         ["ID", "Actif", "Menace/Catégorie", "Proba·Impact·Niveau", "Traitement", "Contre-mesures", "Sources",
                          "Risque résiduel estimé"]),
}
MATRICE = ("Matrice probabilité × impact — Élevée : Faible→Moyen, Moyen→Élevé, Élevé→Critique ; Moyenne : Faible→Faible, "
           "Moyen→Moyen, Élevé→Élevé ; Faible : Faible→Faible, Moyen→Faible, Élevé→Moyen.")
PREFIXE_ID = {"01-actifs.md": "A", "03-menaces.md": "M"}   # identifiants posés par le CODE (jamais par le modèle)

REGLES = {
    "01-actifs.md": (
        "Écris une ligne par ACTIF réel du système (logiciel, service, donnée, matériel, site, prestataire, rôle). Type ∈ "
        "{Logiciel / Service, Donnée, Matériel, Site, Prestataire, Rôle / Organisation}. « Description, périmètre et valeur » : ce "
        "qu'est l'actif, puis son enjeu concret (disponibilité, confidentialité, coût) d'après les preuves, ou « valeur non "
        "documentée » : tout dans UNE cellule, sans barre verticale. Sensibilité ∈ {Publique, Interne, Sensible, Critique}. « Preuve "
        "source » : les [E…] qui établissent l'actif. Les éléments de la liste « À examiner » "
        "sont des CANDIDATS issus de l'index : ignore ceux qui ne sont pas des actifs (personne, norme, date, nom de l'entreprise) ; "
        "ajoute tout actif important que les preuves montrent et que la liste ne contient pas. Écris AU PLUS " + str(MAX_LIGNES_LOT_ACTIFS) +
        " lignes : REGROUPE les éléments de même nature en une seule ligne (ex. « Postes portables (126 unités) », « Capteurs de "
        "température IoT », « Comptes de service ») et garde séparés ceux qui diffèrent par leur rôle ou leur criticité."),
    "03-menaces.md": (
        "Pour CHAQUE actif de la liste de contrôle, écris les menaces réalistes de la grille retenue (voir 02-methodes.md) : une "
        "ligne par menace, AU MOINS une et AU PLUS trois par actif (les plus réalistes d'abord). « Actif concerné » = l'ID de l'actif "
        "suivi de son nom. « Catégorie » toujours "
        "préfixée par la grille (STRIDE-S, LINDDUN-L…). « Description » : qui attaque, comment, pour quel objectif, en citant les "
        "[E…] qui montrent l'exposition. « CVE si connue » : « — » si aucune. « Source » : un identifiant de grille autorisé."),
    "04-evaluation.md": (
        "Écris UNE ligne par menace de la liste de contrôle, avec exactement son ID en première colonne. Probabilité et Impact ∈ "
        "{Faible, Moyen, Élevé}. Niveau selon la matrice : " + MATRICE + " Justifie chaque note en une phrase appuyée sur les [E…] "
        "(exposition, mesures existantes) ; si l'information manque, écris-le au lieu de deviner."),
    "05-traitement.md": (
        "Écris UNE ligne par risque de la liste de contrôle, avec exactement son ID en première colonne. « Proba·Impact·Niveau » "
        "reprend l'évaluation donnée. Traitement ∈ {Réduire, Transférer, Éviter, Accepter}. « Contre-mesures » concrètes, chacune "
        "avec un identifiant de source autorisé. « Risque résiduel estimé » : jamais nul."),
}
RE_SEPARATEUR = re.compile(r"^\s*\|[\s:|-]+\|\s*$")


@dataclass(frozen=True)
class Lot:
    cle: str                     # « 01-actifs:2 »
    fichier: str                 # livrable final
    index: int                   # rang du lot (à partir de 1) : nom du fichier de partie
    theme: str                   # libellé affiché
    entrees: tuple[str, ...]     # lignes de la liste de contrôle (texte lisible)
    attendus: tuple[str, ...]    # identifiants qui DOIVENT apparaître dans la partie (vide = liste indicative)
    requetes: tuple[str, ...]    # questions pour tailler le dossier de preuves du lot
    types: tuple[str, ...] = field(default_factory=tuple)   # types d'entités couverts (pour cibler une reprise)
    pieces_en_plus: tuple[str, ...] = field(default_factory=tuple)   # livrables à joindre (02-methodes.md…)


# ----------------------------------------------------------------------------------------------- lecture
def lignes_de_donnees(texte: str) -> list[list[str]]:
    """Cellules de chaque ligne de tableau de `texte`, hors séparateur et hors ligne d'en-tête (première cellule « ID »)."""
    sortie = []
    for l in texte.splitlines():
        # un modèle écrit parfois « 1: | … », « - | … » ou « > | … » : le préfixe n'est pas du contenu (mesuré le 2026-10-11)
        l = re.sub(r"^\s*(?:\d+\s*[:.)]|[-*•>])\s*(?=\|)", "", l)
        if not l.lstrip().startswith("|") or RE_SEPARATEUR.match(l):
            continue
        cellules = [c.strip() for c in l.strip().strip("|").split("|")]
        if cellules and re.sub(r"[*`_\s]", "", cellules[0]).lower() in ("id", "identifiant"):
            continue
        if any(cellules):
            sortie.append(cellules)
    return sortie


def lire_lignes(dossier: Path, fichier: str) -> list[list[str]]:
    try:
        return lignes_de_donnees((Path(dossier) / fichier).read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return []


def _propre(c: str) -> str:
    return re.sub(r"[*`_]", "", c).strip()


# ----------------------------------------------------------------------------------------------- plan
THEMES_ACTIFS = (
    ("Applications, services et données", ("systeme", "donnee"),
     ("Applications, logiciels, ERP, SaaS et services en ligne du système d'information",
      "Données sensibles ou personnelles traitées : RH, paie, clients, géolocalisation, comptes",
      "Hébergement des applications, authentification, droits d'accès et comptes d'administration")),
    ("Matériel, réseau et sites", ("materiel", "site"),
     ("Serveurs, postes de travail, équipements réseau, pare-feu, sauvegardes et stockage",
      "Sites, locaux, salles serveurs, énergie, protection physique",
      "Matériel obsolète, hors support, durée de vie et renouvellement")),
    ("Prestataires, rôles et processus", ("prestataire", "role", "contrat", "processus"),
     ("Prestataires, fournisseurs, télémaintenance, contrats et clauses de sécurité",
      "Rôles et responsabilités de sécurité : DSI, RSSI, DPO, comités, procédures",
      "Processus d'arrivée et de départ, sensibilisation, gestion des incidents")),
)


def entites_candidates(index, types: tuple[str, ...], maximum: int = 18) -> list[str]:
    """Noms canoniques des entités de ces types, les plus citées (nombre de documents) d'abord."""
    import json
    groupes: dict[str, dict] = {}
    for nom, canonique, type_, docs in index.base.execute("SELECT nom, canonique, type, docs FROM entites").fetchall():
        g = groupes.setdefault(canonique, {"types": set(), "docs": set()})
        g["types"].add(type_)
        g["docs"].update(json.loads(docs or "[]"))
    choisis = [(c, len(g["docs"])) for c, g in groupes.items() if g["types"] & set(types) and len(c) >= 3]
    choisis.sort(key=lambda x: (-x[1], x[0]))
    return [f"{c} (cité par {n} document{'s' if n > 1 else ''})" for c, n in choisis[:maximum]]


def _lots_actifs(index) -> list[Lot]:
    lots = []
    for i, (theme, types, requetes) in enumerate(THEMES_ACTIFS, start=1):
        entrees = tuple(entites_candidates(index, types)) if index is not None else ()
        lots.append(Lot(f"01-actifs:{i}", "01-actifs.md", i, theme, entrees, (), requetes, types))
    return lots


def _decouper(lignes: list[list[str]], taille: int) -> list[list[list[str]]]:
    # la taille grandit avec le volume pour ne pas dépasser MAX_LOTS lots (durée de la chaîne bornée)
    taille = max(taille, -(-len(lignes) // MAX_LOTS)) if lignes else taille
    return [lignes[i:i + taille] for i in range(0, len(lignes), taille)]


def _lots_menaces(actifs: list[list[str]]) -> list[Lot]:
    reels = [r for r in actifs if r and r[0] and "hors périmètre" not in " ".join(r).lower()]
    lots = []
    for i, groupe in enumerate(_decouper(reels, TAILLE_LOT["03-menaces.md"]), start=1):
        entrees = tuple(" — ".join(_propre(c) for c in r[:4]) for r in groupe)
        attendus = tuple(_propre(r[0]) for r in groupe)
        requetes = tuple(f"{_propre(r[1]) if len(r) > 1 else ''} {_propre(r[2]) if len(r) > 2 else ''} : exposition, vulnérabilités, accès, incidents"
                         for r in groupe)
        lots.append(Lot(f"03-menaces:{i}", "03-menaces.md", i, f"Menaces des actifs {attendus[0]} à {attendus[-1]}", entrees, attendus,
                        requetes, (), ("02-methodes.md",)))
    n = len(lots) + 1
    lots.append(Lot(f"03-menaces:{n}", "03-menaces.md", n, "Frontières de confiance et menaces organisationnelles",
                    ("Frontières de confiance et flux décrits dans 00-description.md (Internet, DMZ, réseau interne, prestataires, sites)",),
                    (), ("Frontières de confiance, flux entre zones, accès à distance et prestataires",
                         "Gouvernance de sécurité, comités, rôles cumulés, procédures non appliquées, incidents passés"),
                    (), ("02-methodes.md", "00-description.md")))
    return lots


def _lots_depuis_lignes(fichier: str, lignes: list[list[str]], libelle: str) -> list[Lot]:
    lots = []
    reels = [r for r in lignes if r and re.match(r"^[A-Za-z]{1,3}-?\d{1,3}$", _propre(r[0]))]
    for i, groupe in enumerate(_decouper(reels, TAILLE_LOT[fichier]), start=1):
        entrees = tuple(" — ".join(_propre(c) for c in r) for r in groupe)
        attendus = tuple(_propre(r[0]) for r in groupe)
        requetes = tuple(" ".join(_propre(c) for c in r[1:4]) for r in groupe)
        lots.append(Lot(f"{fichier[:-3]}:{i}", fichier, i, f"{libelle} {attendus[0]} à {attendus[-1]}", entrees, attendus, requetes))
    return lots


def plan_etape(dossier: Path, numero: int, index=None) -> dict[str, list[Lot]]:
    """`{livrable: [lots]}` pour l'étape ; `{}` si l'étape se fait en une passe (ou si l'entrée du lot manque)."""
    dossier = Path(dossier)
    if numero == 1:
        return {"01-actifs.md": _lots_actifs(index)} if index is not None else {}
    if numero == 3:
        actifs = lire_lignes(dossier, "01-actifs.md")
        return {"03-menaces.md": _lots_menaces(actifs)} if actifs else {}
    if numero == 4:
        lots = _lots_depuis_lignes("04-evaluation.md", lire_lignes(dossier, "03-menaces.md"), "Menaces")
        return {"04-evaluation.md": lots} if lots else {}
    if numero == 5:
        lots = _lots_depuis_lignes("05-traitement.md", lire_lignes(dossier, "04-evaluation.md"), "Risques")
        return {"05-traitement.md": lots} if lots else {}
    return {}


# ----------------------------------------------------------------------------------------------- consigne, contrôle
ENTREE_DU_LIVRABLE = {"03-menaces.md": "01-actifs.md", "04-evaluation.md": "03-menaces.md", "05-traitement.md": "04-evaluation.md"}


def partie_reutilisable(dossier: Path, lot: Lot) -> bool:
    """Une partie déjà écrite est réutilisée si elle est VALIDE et plus récente que ce dont elle dépend (le livrable
    d'entrée, ou l'index pour l'inventaire) : une analyse reprise ne refait pas des lots déjà bons."""
    partie = fichier_partie(dossier, lot)
    try:
        mtime = partie.stat().st_mtime
        if lot.attendus and valider_partie(lot, partie.read_text(encoding="utf-8", errors="replace"))[1]:
            return False
        if not lot.attendus and not valider_partie(lot, partie.read_text(encoding="utf-8", errors="replace"))[0]:
            return False
        entree = ENTREE_DU_LIVRABLE.get(lot.fichier)
        reference = (Path(dossier) / entree) if entree else (Path(dossier) / "connaissance" / "index.sqlite")
        return mtime >= reference.stat().st_mtime
    except OSError:
        return False


def fichier_partie(dossier: Path, lot: Lot) -> Path:
    return Path(dossier) / "parties" / f"{lot.fichier[:-3]}.{lot.index}.md"


def contenu_entrees(lot: Lot, total: int, supplements: list[str] | None = None, corrections: str = "") -> str:
    """Fichier joint au lot : ce qu'il doit couvrir (liste de contrôle)."""
    lignes = [f"# Lot {lot.index}/{total} — {lot.theme}", ""]
    if lot.attendus:
        lignes += ["## Éléments à traiter (OBLIGATOIRE : chacun doit apparaître)", ""] + [f"- {e}" for e in lot.entrees]
    elif lot.entrees:
        titre = "## À examiner (candidats issus de l'index : ignore ce qui n'est pas un actif)"
        lignes += [titre, ""] + [f"- {e}" for e in lot.entrees]
    if supplements:
        lignes += ["", "## À AJOUTER OBLIGATOIREMENT (absents de la version précédente)", ""] + [f"- {s}" for s in supplements]
    if corrections:
        lignes += ["", "## Corrections demandées par le contrôle (à vérifier dans les preuves avant de les appliquer)", "", corrections]
    return "\n".join(lignes) + "\n"


def consigne_lot(lot: Lot, total: int, dossier_nom: str, sources: str = "", manquants: list[str] | None = None) -> str:
    """Consigne FIXE d'un lot : aucun contenu de document, seulement des noms de fichiers et des règles."""
    titre, colonnes = ENTETES[lot.fichier]
    partie = f"analyses/{dossier_nom}/parties/{lot.fichier[:-3]}.{lot.index}.md"
    id_code = lot.fichier in PREFIXE_ID
    exemple = "| " + " | ".join(("-" if (i == 0 and id_code) else f"<{c}>") for i, c in enumerate(colonnes)) + " |"
    texte = (
        f"Étape — lot {lot.index}/{total} : {lot.theme}. Écris le fichier {partie} (outil write) qui contient UNIQUEMENT des "
        f"lignes de tableau Markdown : aucun titre, aucune phrase, aucune ligne d'en-tête ni de séparateur. Chaque ligne tient sur "
        f"UNE seule ligne, commence et finit par « | » et a exactement {len(colonnes)} colonnes séparées par « | », dans cet "
        f"ordre : {' | '.join(colonnes)}. EXEMPLE de ligne valide (remplace chaque <…> par le contenu) : {exemple} "
        + ("Mets « - » dans la colonne ID : le programme attribue les identifiants. " if id_code else
           "La colonne ID reprend EXACTEMENT l'identifiant de l'élément traité. ")
        + "Pièces jointes : la liste du lot et le dossier de preuves taillé pour ce lot ; n'ouvre aucun autre fichier. "
        + REGLES[lot.fichier] + " "
        "CITATIONS : cite l'identifiant de preuve [E…] après chaque fait ; un fait absent des preuves est « non documenté ». "
        "LECTURE : un nombre se lit avec l'en-tête de sa colonne (un montant en k€ n'est pas une quantité). ÉCARTS : si deux "
        "documents diffèrent, retiens la valeur proposée et cite l'autre avec son document, « écart à valider ». "
    )
    if lot.fichier in ("03-menaces.md", "05-traitement.md") and sources:
        texte += "SOURCES : cite uniquement ces identifiants exacts : " + sources + ". "
    if manquants:
        texte += ("REPRISE : la partie précédente est incomplète ou invalide ; réécris-la EN ENTIER. Manquent ou à corriger : "
                  + "; ".join(manquants[:12]) + ". ")
    return texte


def _normaliser_cellules(cellules: list[str], nb: int, fichier: str) -> list[list[str]]:
    """Ramène les cellules d'une ligne lue à des lignes de `nb` colonnes, quand c'est SANS ambiguïté :

    - plusieurs lignes écrites bout à bout sur une seule (mesuré : « 111 colonnes ») : redécoupées tous les `nb` cellules
      si chaque morceau commence par « - » (identifiant posé par le code) ;
    - une ligne d'actif à 4 ou 5 cellules (ID, actif, type, description[, sensibilité]) : complétée par « à préciser » et
      une preuve vide (le contrôle des citations la signalera). Les autres cas restent invalides."""
    n = len(cellules)
    if n == nb:
        return [cellules]
    if n == nb + 1 and len(cellules) > 2 and re.fullmatch(r"[A-Za-z]{1,3}-?\d{1,3}", _propre(cellules[1])) \
            and not re.fullmatch(r"[A-Za-z]{1,3}-?\d{1,3}", _propre(cellules[2])):
        # « - | A16 | Baie onduleurs | … » : l'identifiant de l'actif a été séparé de son nom par une barre de la liste
        return [[cellules[0], cellules[1] + " " + cellules[2]] + cellules[3:]]
    if n > nb:
        # lignes collées : chaque ligne commence par la cellule « - » (identifiant posé par le code) ; une cellule vide
        # issue de « || » en fin de morceau est retirée. Accepté seulement si CHAQUE morceau a au moins 4 cellules.
        debuts = [i for i, c in enumerate(cellules) if c.strip() == "-"]
        if len(debuts) >= 2 and debuts[0] == 0:
            morceaux = [cellules[a:b] for a, b in zip(debuts, debuts[1:] + [n])]
            morceaux = [m[:-1] if m and not m[-1].strip() else m for m in morceaux]
            if all(4 <= len(m) <= nb for m in morceaux):
                return [x for m in morceaux for x in _normaliser_cellules(m, nb, fichier)]
    if fichier == "01-actifs.md" and 4 <= n < nb:
        return [cellules + ["à préciser", ""][: nb - n] + [""] * max(0, nb - n - 2)]
    return [cellules]


def valider_partie(lot: Lot, texte: str) -> tuple[list[list[str]], list[str]]:
    """`(lignes_valides, problèmes)` d'une partie écrite par l'agent.

    Problèmes : aucune ligne, mauvais nombre de colonnes, élément attendu absent."""
    sans_cloture = "\n".join(l for l in texte.splitlines() if not l.strip().startswith("```"))
    nb = len(ENTETES[lot.fichier][1])
    lignes, problemes = [], []
    brutes = [c for cellules in lignes_de_donnees(sans_cloture) for c in _normaliser_cellules(cellules, nb, lot.fichier)]
    for cellules in brutes:
        if len(cellules) == nb:
            if lot.attendus and lot.fichier not in PREFIXE_ID and _propre(cellules[0]) not in lot.attendus:
                problemes.append(f"identifiant inattendu : {_propre(cellules[0])[:30]} (attendus : {', '.join(lot.attendus)[:80]})")
                continue
            lignes.append(cellules)
        else:
            problemes.append(f"ligne à {len(cellules)} colonnes au lieu de {nb} : {' | '.join(cellules)[:80]}")
    if not lignes:
        problemes.insert(0, "aucune ligne de tableau valide")
    elif not lot.attendus:
        # lot indicatif (inventaire des actifs) : quelques lignes mal formées ne justifient pas de tout refaire, les
        # lignes valides sont gardées ; le contrôle d'ensemble signale les actifs qui manqueraient
        problemes = [p for p in problemes if not p.startswith("ligne à ")]
        if len(lignes) > SEUIL_EXCES_ACTIFS:   # le plafond est un CONSEIL ; seul un excès manifeste justifie un nouvel essai
            problemes.append(f"trop de lignes ({len(lignes)}) : au plus {MAX_LIGNES_LOT_ACTIFS}, regroupe les éléments de même nature")
    corps = " ".join(" ".join(l) for l in lignes)
    for a in lot.attendus:
        if not re.search(r"(?<![A-Za-z0-9])" + re.escape(a) + r"(?![A-Za-z0-9])", corps):
            problemes.append(f"élément non traité : {a}")
    return lignes, problemes


def recuperer_depuis_sortie(lot: Lot, sortie: str) -> str:
    """Lignes de tableau valides trouvées dans la RÉPONSE de l'agent, quand il les a écrites dans son message au lieu
    d'appeler l'outil d'écriture (mesuré le 2026-10-11 : qwen3.5 imprime un appel `<tool_call>` mal formé que opencode
    n'exécute pas, le fichier n'existe donc pas alors que le tableau est complet). Renvoie le texte de la partie, ou « »."""
    nb = len(ENTETES[lot.fichier][1])
    vues: set[str] = set()
    gardees: list[str] = []
    for cellules in (c for brut in lignes_de_donnees(sortie) for c in _normaliser_cellules(brut, nb, lot.fichier)):
        if len(cellules) != nb:
            continue
        ligne = "| " + " | ".join(cellules) + " |"
        if ligne not in vues:
            vues.add(ligne)
            gardees.append(ligne)
    return "\n".join(gardees) + "\n" if gardees else ""


def manquants_de(problemes: list[str]) -> list[str]:
    return [p for p in problemes]


def lots_concernes(lots: list[Lot], corrections: str, supplements: dict[str, list[str]] | None = None) -> list[Lot]:
    """Lots à refaire d'après le texte des corrections : ceux dont un identifiant attendu ou un nom d'élément y figure,
    plus ceux qui reçoivent un supplément (actif manquant ciblé par type)."""
    bas = corrections.lower()
    cibles = []
    for lot in lots:
        trouve = any(re.search(r"(?<![A-Za-z0-9])" + re.escape(a) + r"(?![A-Za-z0-9])", corrections) for a in lot.attendus)
        if not trouve:
            for e in lot.entrees:
                nom = _propre(e.split("|")[1] if "|" in e and len(e.split("|")) > 1 else e.split(" (cité")[0]).lower()
                if len(nom) >= 5 and nom in bas:
                    trouve = True
                    break
        if trouve or (supplements and supplements.get(lot.cle)):
            cibles.append(lot)
    return cibles


def supplements_actifs(manquants: list[tuple[str, str, int]], lots: list[Lot]) -> dict[str, list[str]]:
    """Affecte chaque actif manquant (nom, type, nb de documents) au lot dont les types le couvrent."""
    par_lot: dict[str, list[str]] = {}
    for nom, type_, nb in manquants:
        for lot in lots:
            if type_ in lot.types:
                par_lot.setdefault(lot.cle, []).append(f"{nom} ({type_}, cité par {nb} documents)")
                break
    return par_lot


# ----------------------------------------------------------------------------------------------- assemblage
def _cle_nom(cellule: str) -> str:
    """Nom d'actif normalisé (sans gras, ponctuation ni casse) pour reconnaître le MÊME actif décrit par deux lots."""
    return re.sub(r"[^0-9a-zàâäçéèêëîïôöùûüÿœ]+", " ", _propre(cellule).lower()).strip()


def fusionner_doublons(lignes: list[list[str]]) -> tuple[list[list[str]], int]:
    """Fusionne les lignes du MÊME actif (deux lots qui décrivent FleetTrack, Microsoft 365…) : on garde la première
    description et on réunit les preuves citées. Renvoie `(lignes, nombre_fusionnées)`."""
    vus: dict[str, int] = {}
    sortie: list[list[str]] = []
    fusionnees = 0
    for cellules in lignes:
        cle = _cle_nom(cellules[1]) if len(cellules) > 1 else ""
        if cle and cle in vus:
            gardee = sortie[vus[cle]]
            existantes = set(re.findall(r"\[E\d+\]", gardee[-1]))
            en_plus = [e for e in re.findall(r"\[E\d+\]", " ".join(cellules)) if e not in existantes]
            if en_plus:
                gardee[-1] = (gardee[-1] + " " + " ".join(dict.fromkeys(en_plus))).strip()
            fusionnees += 1
            continue
        if cle:
            vus[cle] = len(sortie)
        sortie.append(list(cellules))
    return sortie, fusionnees


DERNIER_ASSEMBLAGE: dict[str, int] = {}   # fichier -> nombre de lignes fusionnées au dernier assemblage (pour le journal)


DERNIER_NETTOYAGE: dict[str, int] = {}   # fichier -> nombre d'éléments inventés retirés au dernier assemblage


def assembler(dossier: Path, fichier: str, lots: list[Lot], nettoyer=None) -> int:
    """Écrit le livrable final : titre, en-tête, lignes de toutes les parties (identifiants posés par le code).

    Renvoie le nombre de lignes. Une partie absente ou invalide est ignorée (le contrôle d'ensemble le signalera)."""
    titre, colonnes = ENTETES[fichier]
    prefixe = PREFIXE_ID.get(fichier)
    toutes: list[list[str]] = []
    for lot in lots:
        partie = fichier_partie(dossier, lot)
        try:
            texte = partie.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lignes, _problemes = valider_partie(lot, texte)
        toutes += lignes
    DERNIER_ASSEMBLAGE[fichier] = 0
    if fichier == "01-actifs.md":
        toutes, DERNIER_ASSEMBLAGE[fichier] = fusionner_doublons(toutes)
    largeur = 2 if len(toutes) < 100 else 3
    corps = []
    retires = 0
    for n, cellules in enumerate(toutes, start=1):
        c = list(cellules)
        if nettoyer is not None:  # `nettoyer(texte) -> (texte, nb_retires)` : identifiants de source ou CVE inventés
            for i in range(1, len(c)):
                c[i], r = nettoyer(c[i])
                retires += r
        if prefixe:
            c[0] = f"{prefixe}{n:0{largeur}d}"
        corps.append("| " + " | ".join(x.replace("\n", " ") for x in c) + " |")
    sortie = [titre, ""]
    if fichier == "04-evaluation.md":
        sortie += [MATRICE, ""]
    sortie += ["| " + " | ".join(colonnes) + " |", "|" + "|".join("---" for _ in colonnes) + "|"] + corps
    DERNIER_NETTOYAGE[fichier] = retires
    (Path(dossier) / fichier).write_text("\n".join(sortie) + "\n", encoding="utf-8")
    return len(corps)
