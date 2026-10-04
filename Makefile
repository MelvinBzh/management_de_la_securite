# E21 « Des agents IA pour analyser les risques » — raccourcis de développement
#
#   make web          interface web locale (Streamlit, http://localhost:8501)
#   make suite        suite de référence T-01..T-13 (soutenance/tests/verification.py)
#   make test-*       runners autonomes par module (exit 0 si aucun FAIL)
#
# Aucune cible n'écrit dans `soutenance/` ni ne modifie `main`.

PYTHON ?= python3
PORT ?= 8501

.PHONY: web suite test-ingest test-preparation test-export test-web tests aide

## Interface web locale (streamlit) — s'arrête avec Ctrl+C.
web:
	$(PYTHON) -m streamlit run web/app.py \
		--server.headless true \
		--server.address localhost \
		--server.port $(PORT)

## Suite de référence du projet (T-01..T-13).
suite:
	$(PYTHON) soutenance/tests/verification.py

## Tests autonomes de l'ingestion documentaire (chantier #25).
test-ingest:
	$(PYTHON) tools/ingest/tests/test_ingest.py

## Tests autonomes de la préparation (description + questions auto, chantier #31).
test-preparation:
	$(PYTHON) tools/ingest/tests/test_preparation.py

## Tests autonomes des exports de rapports (chantier #27).
test-export:
	$(PYTHON) tools/export/tests/test_export.py

## Tests autonomes de l'interface web (chantier #26).
test-web:
	$(PYTHON) web/tests/test_web.py

## Tous les runners autonomes, puis la suite de référence.
tests: test-ingest test-preparation test-export test-web suite

## Rappel des cibles disponibles.
aide:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## //'