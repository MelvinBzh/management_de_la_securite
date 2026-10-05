#!/bin/sh
# ---------------------------------------------------------------------------
# Mise à jour de l'application E21 déployée en Docker (serveur).
#
# Usage :  ./scripts/update-docker.sh     (depuis le dépôt, root ou sudo)
#
# Ce script ne touche JAMAIS aux données :
#   - analyses/          (cas d'étude + intrants)  -> volume hôte
#   - stockage_local/    (base source de vérité)   -> volume hôte
# Il récupère le nouveau code, reconstruit l'image et relance le conteneur.
# ---------------------------------------------------------------------------
set -e
cd "$(dirname "$0")/.."

echo "==> git pull (nouveau code)"
git pull --ff-only

echo "==> rebuild + relance du conteneur"
docker compose up -d --build

echo "==> nettoyage des anciennes images (dangling uniquement)"
docker image prune -f

echo "==> OK. Application à jour : http://<ip-du-serveur>:8501"