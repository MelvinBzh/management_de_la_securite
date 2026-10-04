# E21 « Des agents IA pour analyser les risques » — raccourcis de développement
#
#   make web          interface web locale (Streamlit, http://localhost:8501)
#   make suite        suite de référence T-01..T-13 (soutenance/tests/verification.py)
#   make test-*       runners autonomes par module (exit 0 si aucun FAIL)
#
# Aucune cible n'écrit dans `soutenance/` ni ne modifie `main`.

PYTHON ?= python3
PORT ?= 8501
# 0.0.0.0 = accessible depuis le réseau local (ex. http://192.168.x.x:8501)
# localhost = accessible uniquement depuis la machine (plus sûr si réseau non maîtrisé).
ADDRESS ?= 0.0.0.0

.PHONY: web suite test-ingest test-preparation test-export test-web test-reseau test-detection test-methodes \
	test-methodes-pasta test-methodes-linddun test-methodes-stride test-methodes-ebios \
	tests aide

## Interface web locale (streamlit) — s'arrête avec Ctrl+C.
## Lancement LAN : make web ADDRESS=0.0.0.0  (défaut) | machine seule : make web ADDRESS=localhost
web:
	$(PYTHON) -m streamlit run web/app.py \
		--server.headless true \
		--server.address $(ADDRESS) \
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

## Tests autonomes de la méthode EBIOS RM (ateliers générés).
test-methodes-ebios:
	PYTHONPATH=$(CURDIR) $(PYTHON) tools/methodes/ebios/tests/test_ebios.py

## Tests autonomes de la méthode PASTA (7 étapes générées).
test-methodes-pasta:
	$(PYTHON) tools/methodes/pasta/tests/test_pasta.py

## Tests autonomes de la méthode LINDDUN (7 fiches + DPF générés).
test-methodes-linddun:
	$(PYTHON) tools/methodes/linddun/tests/test_linddun.py

## Tests autonomes du validateur de DFD STRIDE.
test-methodes-stride:
	$(PYTHON) tools/methodes/stride/tests/test_check_dfd.py

## Les quatre runners de méthodes (chantier #28).
test-methodes: test-methodes-ebios test-methodes-pasta test-methodes-linddun test-methodes-stride

## Tous les runners autonomes, puis la suite de référence.
tests: test-ingest test-preparation test-export test-web test-reseau test-detection test-methodes suite

## Rappel des cibles disponibles.
aide:
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/^## //'
## Tests autonomes de l'inventaire réseau local-only (chantier #29).
test-reseau:
	$(PYTHON) tools/reseau/tests/test_inventaire.py

## Tests autonomes du détecteur de menaces (règles DET-01 → DET-12).
test-detection:
	$(PYTHON) tools/reseau/tests/test_detection.py
