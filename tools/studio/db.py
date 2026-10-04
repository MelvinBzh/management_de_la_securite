# -*- coding: utf-8 -*-
r"""Base SQLite locale du Studio E21 : source de vérité des agents et des skills.

Le dossier `stockage_local/` est gitignoré (et un garde-fou interdit `*.sqlite3`
dans l'index git) : la base vit donc HORS git, sur la machine de l'analyste.
`.opencode/` reste la copie DÉPLOYÉE que lit opencode pour exécuter la chaîne E21 ;
cette base en est la copie maîtresse :

- `importer_depuis_opencode()` : bootstrap d'une machine (ou rafraîchissement) —
  les fichiers de `.opencode/` alimentent la base, source `opencode`.
- `sauvegarder()` / `supprimer()` : édition via le futur Studio web, source `studio`.
- `deployer_vers_opencode()` : après chaque modification, la base est réécrite
  vers `.opencode/agents/<nom>.md` et `.opencode/skills/<nom>/SKILL.md`.
- `exporter_json()` / `importer_json()` : sauvegarde / restauration portable.

Deux propriétés structurent tout le module :

- **Idempotence** : un import ou un déploiement dont le résultat est identique
  n'incrémente aucune version et n'écrit aucun fichier (`mis_a_jour == 0`,
  `ecrits == 0`). Relancer l'opération est donc sans risque et sans bruit.
- **Écriture bornée** : les noms d'entités sont validés (aucun séparateur de
  chemin, aucun `..`) avant tout usage, et le déploiement n'écrit que sous les
  dossiers `.opencode/agents` et `.opencode/skills` qui lui sont fournis.

Module sans dépendance externe (`sqlite3`, `json`, `pathlib`, `datetime`) :
il est importable aussi bien par les tests autonomes que par l'application web.
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]

# Base maîtresse : hors git, dans le dossier local privé de la machine.
DOSSIER_STOCKAGE = RACINE / "stockage_local"
CHEMIN_DB = DOSSIER_STOCKAGE / "e21.sqlite3"

# Copie déployée lue par opencode (`agents/<nom>.md`, `skills/<nom>/SKILL.md`).
DOSSIER_AGENTS = RACINE / ".opencode" / "agents"
DOSSIER_SKILLS = RACINE / ".opencode" / "skills"

TYPES_VALIDES = ("agent", "skill")
VERSION_SCHEMA = "1"

NOM_SKILL = "SKILL.md"
SUFFIXE_MD = ".md"
PREFIXE_EXPORT = "export-studio-"

# Nom d'entité : caractères sûrs uniquement. Un séparateur de chemin ou un `..`
# ferait sortir une écriture du dossier autorisé : c'est refusé en amont (fail
# closed), la contrainte CHECK de la table reste une seconde barrière.
RE_NOM_SUR = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS entites (
    type TEXT NOT NULL CHECK(type IN ('agent','skill')),
    nom TEXT NOT NULL,
    contenu TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    source TEXT NOT NULL DEFAULT 'studio',
    modifie_le TEXT NOT NULL,
    PRIMARY KEY (type, nom)
);
CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT NOT NULL);
"""

# Colonnes exposées par l'API, dans l'ordre des dictionnaires renvoyés.
COLONNES = "type, nom, version, source, modifie_le, contenu"

RELEVE_SQL = f"SELECT {COLONNES} FROM entites WHERE type = ? ORDER BY nom"

LECTURE_SQL = f"SELECT {COLONNES} FROM entites WHERE type = ? AND nom = ?"

ECRITURE_SQL = """
INSERT INTO entites (type, nom, contenu, version, source, modifie_le)
VALUES (?, ?, ?, ?, ?, ?)
ON CONFLICT(type, nom) DO UPDATE SET
    contenu = excluded.contenu,
    version = excluded.version,
    source = excluded.source,
    modifie_le = excluded.modifie_le
"""


def maintenant() -> str:
    """Horodatage ISO 8601 en UTC (format unique de `modifie_le`)."""
    return datetime.now(timezone.utc).isoformat()


def horodatage_fichier() -> str:
    """Suffixe `AAAAMMJJ-HHMMSS` (UTC) utilisé pour nommer un export."""
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _chemin(chemin_db: Path | None) -> Path:
    """Chemin de base effectif : celui fourni, sinon `CHEMIN_DB`."""
    return Path(chemin_db) if chemin_db is not None else CHEMIN_DB


def _verifier_type(type_: str) -> str:
    """Valide le type d'entité (`agent` ou `skill`), fail closed."""
    if type_ not in TYPES_VALIDES:
        raise ValueError(
            f"Type d'entité refusé : « {type_} » — valeurs acceptées : "
            f"{', '.join(TYPES_VALIDES)}."
        )
    return type_


def _verifier_nom(nom: str) -> str:
    """Valide un nom d'entité (lettres, chiffres, point, tiret, tiret bas).

    Un nom est une partie de chemin : il ne peut donc contenir ni `/` ni `\\`,
    ni commencer par un point (`..`, `.`), afin que tout déploiement reste
    borné à `.opencode/agents/` ou `.opencode/skills/`.
    """
    if not isinstance(nom, str) or not nom.strip():
        raise ValueError("Nom d'entité vide : donnez le nom de l'agent ou du skill.")
    nom = nom.strip()
    if not RE_NOM_SUR.match(nom):
        raise ValueError(
            f"Nom d'entité refusé : « {nom} » — formats acceptés : « e21-menaces », "
            "« analyse-risques ». Ni séparateur de chemin (`/`, `\\`), ni « .. », "
            "ni espace ne sont tolérés (une entrée doit rester dans son dossier)."
        )
    return nom


def _connecter(chemin_db: Path | None = None) -> sqlite3.Connection:
    """Ouvre la base (dossier créé au besoin) en rows `sqlite3.Row`."""
    chemin = _chemin(chemin_db)
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(chemin))
    except (OSError, sqlite3.Error) as exc:
        raise sqlite3.Error(
            f"Studio : base SQLite inaccessible ({chemin}) — {exc}"
        ) from exc
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def _session(chemin_db: Path | None = None):
    """Connexion éphémère (schéma à jour, commit puis fermeture garantie)."""
    conn = init(chemin_db)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _vers_dict(ligne: sqlite3.Row | None) -> dict | None:
    """Convertit une ligne SQLite en dictionnaire, ou `None` si absente."""
    return None if ligne is None else {cle: ligne[cle] for cle in ligne.keys()}


def _ecrire(
    conn: sqlite3.Connection,
    type_: str,
    nom: str,
    contenu: str,
    source: str,
    version: int,
    modifie_le: str | None = None,
) -> None:
    """Écrit une entité en fixant explicitement sa version (upsert)."""
    try:
        conn.execute(
            ECRITURE_SQL,
            (type_, nom, contenu, int(version), source, modifie_le or maintenant()),
        )
    except sqlite3.Error as exc:
        raise sqlite3.Error(
            f"Studio : écriture impossible de « {type_}/{nom} » — {exc}"
        ) from exc


def init(chemin_db: Path | None = None) -> sqlite3.Connection:
    """Crée (au besoin) la base et son schéma, puis renvoie la connexion.

    `init()` est idempotent : `CREATE TABLE IF NOT EXISTS` et
    `INSERT OR IGNORE` garantissent qu'un appel répété ne perd aucune donnée et
    ne réécrit pas la version du schéma. Le dossier de la base est créé si
    nécessaire (`stockage_local/` à la création, un dossier temporaire en test).

    L'appelant est responsable de la fermeture de la connexion renvoyée ; les
    fonctions de ce module utilisent `_session()` et ne l'exposent pas.
    """
    conn = _connecter(chemin_db)
    try:
        conn.executescript(SCHEMA_SQL)
        conn.execute(
            "INSERT OR IGNORE INTO meta(cle, valeur) VALUES('schema_version', ?)",
            (VERSION_SCHEMA,),
        )
        conn.commit()
    except sqlite3.Error as exc:
        conn.close()
        raise sqlite3.Error(
            f"Studio : schéma inapplicable sur {_chemin(chemin_db)} — {exc}"
        ) from exc
    return conn


def lister(type_: str, chemin_db: Path | None = None) -> list[dict]:
    """Toutes les entités d'un type, triées par nom.

    Chaque dictionnaire contient `type`, `nom`, `version`, `source`,
    `modifie_le` et `contenu`. Un type inconnu est refusé (ValueError).
    """
    _verifier_type(type_)
    with _session(chemin_db) as conn:
        lignes = conn.execute(RELEVE_SQL, (type_,)).fetchall()
    return [_vers_dict(ligne) for ligne in lignes]


def lire(type_: str, nom: str, chemin_db: Path | None = None) -> dict | None:
    """Entité (`type`, `nom`) ou `None` si elle n'existe pas en base."""
    _verifier_type(type_)
    nom = _verifier_nom(nom)
    with _session(chemin_db) as conn:
        ligne = conn.execute(
            LECTURE_SQL,
            (type_, nom),
        ).fetchone()
    return _vers_dict(ligne)


def sauvegarder(
    type_: str,
    nom: str,
    contenu: str,
    source: str = "studio",
    chemin_db: Path | None = None,
) -> dict:
    """Crée ou met à jour une entité et renvoie l'enregistrement stocké.

    Une création démarre en `version` 1 ; une mise à jour d'une entité déjà
    présente incrémente sa version et réécrit `source` et `modifie_le`
    (horodatage ISO UTC). `contenu` est stocké tel quel (le contenu est une
    donnée, jamais une consigne interprétée).
    """
    _verifier_type(type_)
    nom = _verifier_nom(nom)
    if not isinstance(contenu, str):
        raise ValueError(f"Contenu de « {type_}/{nom} » : une chaîne est attendue.")
    with _session(chemin_db) as conn:
        ligne = conn.execute(
            "SELECT version FROM entites WHERE type = ? AND nom = ?", (type_, nom)
        ).fetchone()
        version = (ligne["version"] + 1) if ligne is not None else 1
        _ecrire(conn, type_, nom, contenu, source, version)
        stocke = _vers_dict(
            conn.execute(
                LECTURE_SQL,
                (type_, nom),
            ).fetchone()
        )
    return stocke


def supprimer(type_: str, nom: str, chemin_db: Path | None = None) -> bool:
    """Supprime une entité ; renvoie `True` si une ligne a été retirée."""
    _verifier_type(type_)
    nom = _verifier_nom(nom)
    with _session(chemin_db) as conn:
        curseur = conn.execute(
            "DELETE FROM entites WHERE type = ? AND nom = ?", (type_, nom)
        )
        supprime = curseur.rowcount > 0
    return supprime


def _fichiers_opencode() -> list[tuple[str, str, Path]]:
    """Inventaire des fichiers opencode présents : `(type, nom, chemin)`.

    Seuls les fichiers réellement présents sont listés : un agent ou un skill
    sans fichier n'est jamais inventé. Un `.opencode/` absent ou vide donne
    simplement une liste vide (fonction sûre).
    """
    trouves: list[tuple[str, str, Path]] = []
    if DOSSIER_AGENTS.is_dir():
        for chemin in sorted(DOSSIER_AGENTS.glob(f"*{SUFFIXE_MD}")):
            if chemin.is_file():
                trouves.append(("agent", chemin.stem, chemin))
    if DOSSIER_SKILLS.is_dir():
        for dossier in sorted(DOSSIER_SKILLS.iterdir()):
            chemin = dossier / NOM_SKILL
            if dossier.is_dir() and chemin.is_file():
                trouves.append(("skill", dossier.name, chemin))
    return trouves


def importer_depuis_opencode(chemin_db: Path | None = None) -> dict:
    """Alimente la base depuis `.opencode/` (bootstrap ou rafraîchissement).

    Chaque `.opencode/agents/<nom>.md` et `.opencode/skills/<nom>/SKILL.md` est
    enregistré avec la source `opencode`. **Idempotent** : si le contenu lu est
    identique à celui déjà en base, ni la version ni `modifie_le` ne changent et
    l'entité est comptée `inchangees` — un second appel renvoie donc
    `mis_a_jour == 0`.

    Renvoie `importes` (entités créées), `mis_a_jour` (contenus modifiés),
    `inchangees` (déjà conformes) et `total` (entités en base après l'import,
    qui peut donc dépasser le nombre de fichiers si la base contient une entrée
    sans fichier — signal utile d'une entrée obsolète).
    """
    compteurs = {"importes": 0, "mis_a_jour": 0, "inchangees": 0}
    with _session(chemin_db) as conn:
        for type_, nom, chemin in _fichiers_opencode():
            try:
                contenu = chemin.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise sqlite3.Error(
                    f"Studio : lecture impossible de {chemin} — {exc}"
                ) from exc
            ligne = conn.execute(
                "SELECT contenu FROM entites WHERE type = ? AND nom = ?", (type_, nom)
            ).fetchone()
            if ligne is not None and ligne["contenu"] == contenu:
                compteurs["inchangees"] += 1
                continue
            version = 1
            if ligne is not None:
                version = conn.execute(
                    "SELECT version FROM entites WHERE type = ? AND nom = ?",
                    (type_, nom),
                ).fetchone()["version"] + 1
                compteurs["mis_a_jour"] += 1
            else:
                compteurs["importes"] += 1
            _ecrire(conn, type_, nom, contenu, "opencode", version)
        total = conn.execute("SELECT COUNT(*) AS n FROM entites").fetchone()["n"]
    return {**compteurs, "total": total}


def _chemin_cible(
    type_: str, nom: str, dossier_agents: Path, dossier_skills: Path
) -> Path:
    """Fichier cible du déploiement.

    Un agent devient `<dossier_agents>/<nom>.md`, un skill devient
    `<dossier_skills>/<nom>/SKILL.md`.
    """
    if type_ == "agent":
        return dossier_agents / f"{nom}{SUFFIXE_MD}"
    return dossier_skills / nom / NOM_SKILL


def deployer_vers_opencode(
    dossier_agents: Path | None = None,
    dossier_skills: Path | None = None,
    chemin_db: Path | None = None,
) -> dict:
    """Écrit la base vers les fichiers opencode que lit la chaîne E21.

    Pour chaque entité, le fichier cible est écrit **uniquement si son contenu
    diffère** de celui déjà sur disque (idempotent) : un déploiement sans
    changement renvoie `ecrits == 0`. Les dossiers de skill sont créés au besoin.

    `dossier_agents` / `dossier_skills` permettent de déployer vers un autre
    emplacement (tests en dossier temporaire) ; par défaut `.opencode/`.

    Renvoie `ecrits`, `inchangees` et `chemins` (fichiers réellement écrits).
    """
    dossier_agents = Path(dossier_agents) if dossier_agents is not None else DOSSIER_AGENTS
    dossier_skills = Path(dossier_skills) if dossier_skills is not None else DOSSIER_SKILLS
    ecrits: list[Path] = []
    inchangees = 0
    for type_ in TYPES_VALIDES:
        for entite in lister(type_, chemin_db):
            cible = _chemin_cible(type_, entite["nom"], dossier_agents, dossier_skills)
            try:
                deja_a_jour = (
                    cible.is_file() and cible.read_text(encoding="utf-8") == entite["contenu"]
                )
            except (OSError, UnicodeDecodeError):
                deja_a_jour = False  # fichier illisible : on réécrit
            if deja_a_jour:
                inchangees += 1
                continue
            try:
                cible.parent.mkdir(parents=True, exist_ok=True)
                cible.write_text(entite["contenu"], encoding="utf-8")
            except OSError as exc:
                raise sqlite3.Error(
                    f"Studio : déploiement impossible vers {cible} — {exc}"
                ) from exc
            ecrits.append(cible)
    return {"ecrits": len(ecrits), "inchangees": inchangees, "chemins": ecrits}


def exporter_json(chemin: Path | None = None, chemin_db: Path | None = None) -> Path:
    """Exporte la base entière en JSON et renvoie le chemin écrit.

    Le document contient la version de schéma (`meta`), l'horodatage
    d'export et toutes les entités (agents puis skills, par nom). Sans `chemin`,
    le fichier est écrit dans `stockage_local/export-studio-<AAAAMMJJ-HHMMSS>.json`
    (dossier local privé, hors git) ; UTF-8, `indent=2`, `ensure_ascii=False`.
    `chemin_db` permet d'exporter une autre base que `CHEMIN_DB` (tests).
    """
    if chemin is None:
        chemin = DOSSIER_STOCKAGE / f"{PREFIXE_EXPORT}{horodatage_fichier()}.json"
    chemin = Path(chemin)
    entites = lister("agent", chemin_db) + lister("skill", chemin_db)
    document = {
        "schema_version": VERSION_SCHEMA,
        "exporte_le": maintenant(),
        "entites": entites,
    }
    try:
        chemin.parent.mkdir(parents=True, exist_ok=True)
        chemin.write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    except (OSError, TypeError) as exc:
        raise sqlite3.Error(f"Studio : export impossible vers {chemin} — {exc}") from exc
    return chemin


def importer_json(chemin: Path, chemin_db: Path | None = None) -> dict:
    """Restaure un export JSON et renvoie `{"restaures": n}`.

    Les entités de lichier remplacent celles de même `(type, nom)` avec la
    **version exacte de l'export** (pas d'incrément : l'état restauré est celui
    qui a été exporté). Les entrées absentes de l'export sont laissées intactes ;
    la version de schéma lue dans le fichier est recopiée dans `meta`.

    Un fichier illisible ou mal formé est refusé par une `ValueError` explicite
    en français : mieux vaut un import échoué qu'une base silencieusement fausse.
    """
    chemin = Path(chemin)
    try:
        brut = chemin.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"Studio : export illisible ({chemin}) — {exc}") from exc
    try:
        document = json.loads(brut)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Studio : export JSON invalide ({chemin}) — {exc}") from exc
    if not isinstance(document, dict) or not isinstance(document.get("entites"), list):
        raise ValueError(
            f"Studio : export JSON non conforme ({chemin}) — clé « entites » attendue "
            "(liste d'entités avec type, nom, contenu)."
        )
    restaures = 0
    with _session(chemin_db) as conn:
        for entite in document["entites"]:
            if not isinstance(entite, dict):
                raise ValueError(
                    f"Studio : entité non conforme dans {chemin} — objet attendu."
                )
            type_ = _verifier_type(entite.get("type", ""))
            nom = _verifier_nom(entite.get("nom", ""))
            contenu = entite.get("contenu", "")
            if not isinstance(contenu, str):
                raise ValueError(
                    f"Studio : contenu non conforme pour « {type_}/{nom} » "
                    f"dans {chemin} — chaîne attendue."
                )
            version = entite.get("version", 1)
            if not isinstance(version, int) or version < 1:
                raise ValueError(
                    f"Studio : version non conforme pour « {type_}/{nom} » "
                    f"dans {chemin} — entier ≥ 1 attendu."
                )
            source = entite.get("source", "studio")
            _ecrire(
                conn,
                type_,
                nom,
                contenu,
                source if isinstance(source, str) and source else "studio",
                version,
                entite.get("modifie_le") if isinstance(entite.get("modifie_le"), str) else None,
            )
            restaures += 1
        schema = document.get("schema_version", VERSION_SCHEMA)
        conn.execute(
            "INSERT INTO meta(cle, valeur) VALUES('schema_version', ?) "
            "ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur",
            (str(schema),),
        )
    return {"restaures": restaures}


__all__ = [
    "RACINE",
    "DOSSIER_STOCKAGE",
    "CHEMIN_DB",
    "DOSSIER_AGENTS",
    "DOSSIER_SKILLS",
    "TYPES_VALIDES",
    "VERSION_SCHEMA",
    "NOM_SKILL",
    "SUFFIXE_MD",
    "PREFIXE_EXPORT",
    "maintenant",
    "horodatage_fichier",
    "init",
    "lister",
    "lire",
    "sauvegarder",
    "supprimer",
    "importer_depuis_opencode",
    "deployer_vers_opencode",
    "exporter_json",
    "importer_json",
]
