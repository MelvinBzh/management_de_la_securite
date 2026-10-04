# -*- coding: utf-8 -*-
"""Détection amont E21 — évaluation d'événements du homelab contre des règles MITRE ATT&CK.

Le détecteur est **local et déterministe** : il lit un fichier d'événements déjà
anonymisé (JSON / JSON Lines / CSV), applique les règles déclarées dans
`regles/regles-detection.json` et produit un rapport Markdown. Aucun accès
réseau, aucune résolution DNS, aucun enrichissement : le rapport reprend les
événements **verbatim**.
"""