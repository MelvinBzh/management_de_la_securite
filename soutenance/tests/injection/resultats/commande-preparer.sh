#!/usr/bin/env bash
# Exécution réelle — préparation de l'étape 1 (00-description.md + questions-auto.md)
# à partir des intrants ingérés, dont le PDF PIÉGÉ.
# À lancer depuis la racine du dépôt, après commande-ingest.sh.
set -u
SORTIE=/tmp/opencode/t11

echo "== python3 -m tools.ingest.preparer --help =="
PYTHONPATH=. python3 -m tools.ingest.preparer --help

echo
echo "== python3 -m tools.ingest.preparer ${SORTIE} --titre Mini-Boutique --out ${SORTIE} =="
PYTHONPATH=. python3 -m tools.ingest.preparer \
    "${SORTIE}" \
    --titre "Mini-Boutique" \
    --out "${SORTIE}"
echo "code de sortie preparer : $?"

echo
echo "== fichiers produits =="
ls -la "${SORTIE}"
