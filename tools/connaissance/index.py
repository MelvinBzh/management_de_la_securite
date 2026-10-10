"""Index de recherche (SQLite) : séparer les informations des documents puis les retrouver vite.

Chaque « élément » est une preuve courte (un fait ou une relation) avec son extrait exact et son vecteur.
La recherche est HYBRIDE : proximité des vecteurs (sens) + mots-clés FTS5 (termes exacts, sigles, noms),
fusionnées par rang (RRF) — les sigles et noms propres, faibles en embeddings, sont rattrapés par les mots.
Tout est dans un fichier SQLite unique, lisible avec n'importe quel outil : on peut l'ouvrir, l'inspecter,
le reconstruire. Si FTS5 manque dans la build SQLite, la recherche retombe sur les vecteurs seuls.
"""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

from . import ollama, texte

SCHEMA = """
CREATE TABLE IF NOT EXISTS elements (
    id INTEGER PRIMARY KEY,
    genre TEXT NOT NULL,            -- 'fait' ou 'relation'
    doc TEXT NOT NULL,              -- document source
    libelle TEXT NOT NULL,          -- phrase du fait, ou « sujet relation objet »
    extrait TEXT NOT NULL,          -- preuve, mot pour mot
    verifie INTEGER NOT NULL,       -- 1 si l'extrait a été retrouvé dans le document par le code
    vecteur TEXT,                   -- JSON
    origine TEXT NOT NULL DEFAULT 'document',  -- 'document' (fourni) ; plus tard 'externe' (recherche web, avec url)
    url TEXT
);
CREATE TABLE IF NOT EXISTS entites (nom TEXT PRIMARY KEY, canonique TEXT NOT NULL, type TEXT, docs TEXT);
CREATE TABLE IF NOT EXISTS contradictions (
    id INTEGER PRIMARY KEY, entite TEXT, doc_a TEXT, extrait_a TEXT, doc_b TEXT, extrait_b TEXT,
    verdict TEXT, explication TEXT, confirmations INTEGER NOT NULL DEFAULT 0
);
-- un document par ligne : son empreinte dit s'il faut le retraiter (nouveau, modifié, inchangé)
CREATE TABLE IF NOT EXISTS documents (
    nom TEXT PRIMARY KEY, empreinte TEXT NOT NULL, statut TEXT NOT NULL, detail TEXT NOT NULL DEFAULT '',
    faits INTEGER NOT NULL DEFAULT 0, faits_verifies INTEGER NOT NULL DEFAULT 0,
    relations INTEGER NOT NULL DEFAULT 0, relations_verifiees INTEGER NOT NULL DEFAULT 0,
    passages INTEGER NOT NULL DEFAULT 0, date TEXT NOT NULL DEFAULT ''
);
-- chaque apparition d'un nom d'entité dans un document (la fusion des alias se refait sur l'ensemble)
CREATE TABLE IF NOT EXISTS mentions (doc TEXT NOT NULL, nom TEXT NOT NULL, type TEXT NOT NULL);
-- résultat « connu / partiel / inconnu » de chaque besoin d'information (JSON)
CREATE TABLE IF NOT EXISTS couverture (besoin TEXT PRIMARY KEY, donnees TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS meta (cle TEXT PRIMARY KEY, valeur TEXT NOT NULL);
"""


class Index:
    """Index de connaissance d'un projet, stocké dans un fichier SQLite (ou en mémoire avec ':memory:')."""

    def __init__(self, chemin: str | Path = ":memory:"):
        self.base = sqlite3.connect(str(chemin))
        self.base.executescript(SCHEMA)
        self._migrer()
        try:
            self.base.execute("CREATE VIRTUAL TABLE IF NOT EXISTS elements_fts USING fts5(libelle, extrait, content='')")
            self.fts = True
        except sqlite3.OperationalError:
            self.fts = False

    def _migrer(self) -> None:
        """Met à niveau un fichier d'index créé par une version antérieure (colonnes ajoutées depuis)."""
        colonnes = {ligne[1] for ligne in self.base.execute("PRAGMA table_info(elements)")}
        if "origine" not in colonnes:
            self.base.execute("ALTER TABLE elements ADD COLUMN origine TEXT NOT NULL DEFAULT 'document'")
        if "url" not in colonnes:
            self.base.execute("ALTER TABLE elements ADD COLUMN url TEXT")
        colonnes = {ligne[1] for ligne in self.base.execute("PRAGMA table_info(contradictions)")}
        if "confirmations" not in colonnes:
            self.base.execute("ALTER TABLE contradictions ADD COLUMN confirmations INTEGER NOT NULL DEFAULT 0")

    def fermer(self) -> None:
        self.base.commit()
        self.base.close()

    def ajouter_element(self, genre: str, doc: str, libelle: str, extrait: str, verifie: bool,
                        vecteur: list[float] | None = None, origine: str = "document", url: str | None = None) -> int:
        curseur = self.base.execute(
            "INSERT INTO elements (genre, doc, libelle, extrait, verifie, vecteur, origine, url) VALUES (?,?,?,?,?,?,?,?)",
            (genre, doc, libelle, extrait, int(verifie), json.dumps(vecteur) if vecteur else None, origine, url))
        if self.fts:
            self.base.execute("INSERT INTO elements_fts (rowid, libelle, extrait) VALUES (?,?,?)",
                              (curseur.lastrowid, libelle, extrait))
        return int(curseur.lastrowid)

    def ajouter_entite(self, nom: str, canonique: str, type_: str, docs: list[str]) -> None:
        self.base.execute("INSERT OR REPLACE INTO entites VALUES (?,?,?,?)", (nom, canonique, type_, json.dumps(sorted(set(docs)))))

    def ajouter_contradiction(self, entite: str, doc_a: str, extrait_a: str, doc_b: str, extrait_b: str,
                              verdict: str, explication: str, confirmations: int = 0) -> None:
        self.base.execute("INSERT INTO contradictions (entite, doc_a, extrait_a, doc_b, extrait_b, verdict, explication, "
                          "confirmations) VALUES (?,?,?,?,?,?,?,?)",
                          (entite, doc_a, extrait_a, doc_b, extrait_b, verdict, explication, confirmations))

    # -- cycle de vie des documents ------------------------------------------------------------
    def documents(self) -> dict[str, dict]:
        """Documents connus de l'index, par nom : empreinte, statut (`ok` ou `erreur`) et comptes."""
        cles = ("nom", "empreinte", "statut", "detail", "faits", "faits_verifies", "relations",
                "relations_verifiees", "passages", "date")
        lignes = self.base.execute("SELECT " + ", ".join(cles) + " FROM documents").fetchall()
        return {ligne[0]: dict(zip(cles, ligne)) for ligne in lignes}

    def enregistrer_document(self, nom: str, empreinte: str, statut: str = "ok", detail: str = "", **comptes: int) -> None:
        v = {c: int(comptes.get(c, 0)) for c in ("faits", "faits_verifies", "relations", "relations_verifiees", "passages")}
        self.base.execute(
            "INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?,?,?,?,datetime('now','localtime'))",
            (nom, empreinte, statut, detail, v["faits"], v["faits_verifies"], v["relations"],
             v["relations_verifiees"], v["passages"]))

    def supprimer_document(self, nom: str) -> None:
        """Retire TOUT ce qui vient d'un document (preuves, mentions, contradictions qui le citent)."""
        if self.fts:
            for ident, libelle, extrait in self.base.execute(
                    "SELECT id, libelle, extrait FROM elements WHERE doc = ?", (nom,)).fetchall():
                self.base.execute("INSERT INTO elements_fts (elements_fts, rowid, libelle, extrait) VALUES ('delete', ?, ?, ?)",
                                  (ident, libelle, extrait))
        self.base.execute("DELETE FROM elements WHERE doc = ?", (nom,))
        self.base.execute("DELETE FROM mentions WHERE doc = ?", (nom,))
        self.base.execute("DELETE FROM contradictions WHERE doc_a = ? OR doc_b = ?", (nom, nom))
        self.base.execute("DELETE FROM documents WHERE nom = ?", (nom,))

    def ajouter_mention(self, doc: str, nom: str, type_: str) -> None:
        self.base.execute("INSERT INTO mentions VALUES (?,?,?)", (doc, nom, type_))

    def mentions(self) -> list[tuple[str, str, str]]:
        return [tuple(l) for l in self.base.execute("SELECT doc, nom, type FROM mentions ORDER BY rowid")]

    def remplacer_entites(self, lignes: list[tuple[str, str, str, list[str]]]) -> None:
        """Remplace la table des entités : `(nom, canonique, type, documents)`."""
        self.base.execute("DELETE FROM entites")
        for nom, canonique, type_, docs in lignes:
            self.ajouter_entite(nom, canonique, type_, docs)

    def vider_contradictions(self, docs: set[str] | None = None) -> None:
        """Efface les contradictions (toutes, ou celles qui touchent l'un des `docs`)."""
        if docs is None:
            self.base.execute("DELETE FROM contradictions")
            return
        for nom in docs:
            self.base.execute("DELETE FROM contradictions WHERE doc_a = ? OR doc_b = ?", (nom, nom))

    def contradictions(self) -> list[dict]:
        cles = ("doc_a", "extrait_a", "doc_b", "extrait_b", "explication", "confirmations")
        lignes = self.base.execute("SELECT " + ", ".join(cles) + " FROM contradictions ORDER BY confirmations DESC, id")
        return [dict(zip(cles, l)) for l in lignes]

    def enregistrer_couverture(self, besoin: str, donnees: dict) -> None:
        self.base.execute("INSERT OR REPLACE INTO couverture VALUES (?,?)", (besoin, json.dumps(donnees, ensure_ascii=False)))

    def couvertures(self) -> list[dict]:
        return [json.loads(l[0]) for l in self.base.execute("SELECT donnees FROM couverture ORDER BY rowid")]

    def vider_couverture(self) -> None:
        self.base.execute("DELETE FROM couverture")

    def definir(self, cle: str, valeur: str) -> None:
        self.base.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (cle, valeur))

    def lire_meta(self, cle: str, defaut: str = "") -> str:
        ligne = self.base.execute("SELECT valeur FROM meta WHERE cle = ?", (cle,)).fetchone()
        return ligne[0] if ligne else defaut

    def compter(self) -> dict[str, int]:
        return {t: self.base.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("elements", "entites", "contradictions")}

    def rechercher(self, question: str, vecteur_question: list[float] | None = None, k: int = 5,
                   verifies_seulement: bool = True, mots_cles: bool = True,
                   origines: tuple[str, ...] = ("document",)) -> list[dict]:
        """Les `k` éléments les plus pertinents : fusion (RRF) du classement par vecteurs et par mots-clés.

        `vecteur_question=None` = mots-clés seuls ; `mots_cles=False` = vecteurs seuls (pour comparer).
        `origines` : par défaut les seuls documents fournis — une information « externe » (web) n'entre jamais
        dans une analyse sans qu'on la demande (`origines=("document", "externe")`).
        """
        conditions = ["origine IN (" + ",".join("?" * len(origines)) + ")"]
        if verifies_seulement:
            conditions.append("verifie = 1")
        lignes = self.base.execute("SELECT id, genre, doc, libelle, extrait, vecteur, origine FROM elements WHERE "
                                   + " AND ".join(conditions), tuple(origines)).fetchall()
        rangs: dict[int, float] = {}
        if vecteur_question:
            notes = sorted(((ollama.cosinus(vecteur_question, json.loads(v)), i) for i, _g, _d, _l, _e, v, _o in lignes if v), reverse=True)
            for rang, (_note, ident) in enumerate(notes[:50]):
                rangs[ident] = rangs.get(ident, 0.0) + 1.0 / (60 + rang)
        if self.fts and mots_cles:
            mots = [m for m in texte.normaliser(question).split() if len(m) >= 3]
            if mots:
                requete = " OR ".join(f'"{m}"' for m in mots)
                try:
                    trouves = self.base.execute("SELECT rowid FROM elements_fts WHERE elements_fts MATCH ? ORDER BY rank LIMIT 50",
                                                (requete,)).fetchall()
                except sqlite3.OperationalError:
                    trouves = []
                autorises = {ligne[0] for ligne in lignes}
                rang = 0
                for (ident,) in trouves:
                    if ident in autorises:
                        rangs[ident] = rangs.get(ident, 0.0) + 1.0 / (60 + rang)
                        rang += 1
        par_id = {ligne[0]: ligne for ligne in lignes}
        classes = sorted(rangs.items(), key=lambda item: -item[1])[:k]
        return [{"id": i, "genre": par_id[i][1], "doc": par_id[i][2], "libelle": par_id[i][3],
                 "extrait": par_id[i][4], "origine": par_id[i][6], "score": round(score, 4),
                 # proximité de sens brute (0 à 1), utile pour calibrer « aucune preuve pertinente »
                 "cos": round(ollama.cosinus(vecteur_question, json.loads(par_id[i][5])), 3) if vecteur_question and par_id[i][5] else None}
                for i, score in classes]
