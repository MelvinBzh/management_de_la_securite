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
    verdict TEXT, explication TEXT
);
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
                              verdict: str, explication: str) -> None:
        self.base.execute("INSERT INTO contradictions (entite, doc_a, extrait_a, doc_b, extrait_b, verdict, explication) "
                          "VALUES (?,?,?,?,?,?,?)", (entite, doc_a, extrait_a, doc_b, extrait_b, verdict, explication))

    def compter(self) -> dict[str, int]:
        return {t: self.base.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("elements", "entites", "contradictions")}

    def rechercher(self, question: str, vecteur_question: list[float] | None = None, k: int = 5,
                   verifies_seulement: bool = True, mots_cles: bool = True) -> list[dict]:
        """Les `k` éléments les plus pertinents : fusion (RRF) du classement par vecteurs et par mots-clés.

        `vecteur_question=None` = mots-clés seuls ; `mots_cles=False` = vecteurs seuls (pour comparer).
        """
        filtre = "WHERE verifie = 1" if verifies_seulement else ""
        lignes = self.base.execute(f"SELECT id, genre, doc, libelle, extrait, vecteur, origine FROM elements {filtre}").fetchall()
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
