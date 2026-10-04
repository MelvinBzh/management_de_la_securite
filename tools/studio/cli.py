# -*- coding: utf-8 -*-
"""CLI du Studio E21 — portabilité machine de la source de vérité.

Usage (depuis la racine du dépôt, raccourcis Makefile) :
    make studio-init      # (nouvelle machine) base locale depuis .opencode/
    make studio-deploy    # écrit .opencode/ depuis la base (après édition)
    python3 -m tools.studio.cli export              # sauvegarde JSON portable
    python3 -m tools.studio.cli import <fichier.json>  # restaure la base

La base locale `stockage_local/e21.sqlite3` est gitignorée (jamais poussée).
Sur une nouvelle machine : git clone → make studio-init → make web.
"""
from __future__ import annotations

import json
import sys

from tools.studio import db

USAGE = """Commandes :
  import                         affiche le bilan d'import depuis .opencode/
  deploy                         affiche le bilan de déploiement vers .opencode/
  export [chemin.json]           sauvegarde JSON portable (défaut : stockage_local/)
  import-json <fichier.json>     restaure la base depuis le JSON
  liste [agent|skill]            liste les entités de la base
"""


def _bilan(titre: str, data: dict) -> int:
    print(f"{titre} :")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print(USAGE)
        return 0
    commande, args = argv[0], argv[1:]
    if commande == "import":
        return _bilan("Import depuis .opencode/", db.importer_depuis_opencode())
    if commande == "deploy":
        return _bilan("Deploiement vers .opencode/", db.deployer_vers_opencode())
    if commande == "export":
        chemin = args[0] if args else None
        return _bilan("Export JSON", {"fichier": str(db.exporter_json(chemin))})
    if commande == "import-json":
        if not args:
            print("Usage : import-json <fichier.json>", file=sys.stderr)
            return 1
        return _bilan("Import JSON", db.importer_json(args[0]))
    if commande == "liste":
        type_filtre = args[0] if args and args[0] in db.TYPES_VALIDES else None
        entites = db.lister(type_filtre) if type_filtre else (
            db.lister("agent") + db.lister("skill")
        )
        for e in entites:
            print(f"{e['type']:<6} {e['nom']:<40} v{e['version']}  {e['source']:<9} {e['modifie_le']}")
        print(f"{len(entites)} entite(s)")
        return 0
    print(USAGE, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())