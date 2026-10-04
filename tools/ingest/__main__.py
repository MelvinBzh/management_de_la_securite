# -*- coding: utf-8 -*-
"""Exécution en module : `python3 -m tools.ingest ...` (depuis la racine du dépôt)."""
import sys

from .ingest import main

if __name__ == "__main__":
    sys.exit(main())