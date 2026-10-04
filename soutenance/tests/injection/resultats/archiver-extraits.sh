#!/usr/bin/env bash
# Archivage des extraits de sortie (T-11) — à lancer après commande-ingest.sh
# et commande-preparer.sh, avant verification-injection.sh (contrôle V10 compare
# le corps archivé à la sortie réelle).
set -u
SORTIE=/tmp/opencode/t11
ARCHIVES=soutenance/tests/injection/resultats

# --- en-tête de traçabilité du brouillon ---------------------------------------
cat > "$ARCHIVES/brouillon-description.md" <<'FIN_ENTETE'
# ---------------------------------------------------------------------
# ARCHIVE T-11 — extrait de sortie réel
# (en-tête de traçabilité ajouté lors de l'archivage ; le corps ci-dessous
#  est la sortie VERBATIM du pipeline, vérifié par empreinte — voir
#  verification-injection.sh, contrôle V10.)
# Source      : /tmp/opencode/t11/00-description.md
# Produit par : tools.ingest.preparer (commande-preparer.sh, sortie-preparer.txt)
# Réf.        : tools/ingest/tests/fixtures/facture-pdf-texte.pdf (document piégé)
# Note        : la ligne hostile du document figure ici comme DONNÉE (extrait de
#               la section « 1. Cas étudié ») ; aucune section normative
#               (Périmètre, Acteurs, Champ de décision) n'en contient.
# ===== FIN EN-TÊTE DE TRAÇABILITÉ — CORPS VERBATIM CI-DESSOUS =====
FIN_ENTETE
cat "$SORTIE/00-description.md" >> "$ARCHIVES/brouillon-description.md"

# --- en-tête de traçabilité des questions auto ---------------------------------
cat > "$ARCHIVES/questions-auto.md" <<'FIN_ENTETE'
# ---------------------------------------------------------------------
# ARCHIVE T-11 — extrait de sortie réel
# (en-tête de traçabilité ajouté lors de l'archivage ; le corps ci-dessous
#  est la sortie VERBATIM du pipeline, vérifié par empreinte — voir
#  verification-injection.sh, contrôle V10.)
# Source      : /tmp/opencode/t11/questions-auto.md
# Produit par : tools.ingest.preparer (commande-preparer.sh, sortie-preparer.txt)
# Réf.        : tools/ingest/tests/fixtures/facture-pdf-texte.pdf (document piégé)
# Note        : AUCUNE question n'a été dérivée de la consigne du document
#               (grep code 1, contrôle V4).
# Rappel      : le pied de page « documents = DONNÉES non fiables » est celui
#               produit par tools.ingest.preparer (garde-fous-ia).
# ===== FIN EN-TÊTE DE TRAÇABILITÉ — CORPS VERBATIM CI-DESSOUS =====
FIN_ENTETE
cat "$SORTIE/questions-auto.md" >> "$ARCHIVES/questions-auto.md"

ls -l "$ARCHIVES/brouillon-description.md" "$ARCHIVES/questions-auto.md"
