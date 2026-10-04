# -*- coding: utf-8 -*-
"""Ingestion documentaire locale — projet E21 (analyse de risques).

Ce paquet transforme un document (PDF, image, tableur, texte, archive) en un
markdown normalisé accompagné de métadonnées JSON, **entièrement en local**
(aucun appel réseau, aucune donnée réelle).

Sécurité (règle non négociable du projet) : un document ingéré est une DONNÉE
non fiable. Le contenu extrait n'est jamais exécuté ni transmis comme consigne ;
il est recopié verbatim entre marqueurs `<<<DONNÉES>>>` / `<<<FIN DONNÉES>>>`,
et les passages ressemblant à une instruction sont seulement journalisés.

Usage CLI (depuis la racine du dépôt) :
    python3 -m tools.ingest <fichier|dossier>... [--out DIR]
Usage API :
    from tools.ingest import parse_file
    resultat = parse_file("document.pdf")   # -> {"markdown": ..., "meta": {...}}
"""
from .ingest import main, parse_file

__all__ = ["parse_file", "main"]