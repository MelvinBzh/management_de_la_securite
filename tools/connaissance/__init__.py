"""Dossier de connaissance E21 : fiches de faits, relations, contradictions, index de recherche.

Rôle : séparer l'information de CHAQUE document (faits atomiques à extrait exact), la relier
(entités, relations typées, contradictions) et la rendre interrogeable, pour que les agents lisent
seulement ce dont ils ont besoin au lieu de recharger tous les documents.

Principe directeur : **un fait n'entre dans l'index que si son extrait existe mot pour mot dans le
document source** — cette vérification est faite par le code (`texte.contient`), jamais par un modèle.

Paquet autonome : bibliothèque standard uniquement, aucun branchement sur le site ni sur les agents
(à relier une fois l'architecture validée). Voir `README.md` pour le schéma d'ensemble.
"""
