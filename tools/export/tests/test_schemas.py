#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes de la réparation des schémas Mermaid (`tools/export/schemas.py`) — aucun modèle, aucun réseau.

Les sorties attendues ont aussi été validées avec l'analyseur officiel de Mermaid (mermaid.parse, v11) : 30 schémas sur 30
(13 schémas réels de projets dont 3 en erreur, et 17 cas piégés).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.export import schemas  # noqa: E402

ECHECS: list[str] = []
NL = chr(10)


def verifier(nom: str, condition: bool) -> None:
    print(("PASS " if condition else "FAIL ") + nom)
    if not condition:
        ECHECS.append(nom)


def r(code: str) -> tuple[str, list[str]]:
    return schemas.reparer_mermaid(code)


# --- un schéma déjà correct n'est pas touché -----------------------------------------------------------------------------------
valide = "flowchart LR" + NL + "  A[Client] -->|HTTPS| B[(Base)]" + NL + "  B -.-> C((Sauvegarde))" + NL + "  A --> B & C" + NL
code, corr = r(valide)
verifier("schéma correct : rendu à l'identique, aucune correction", code == valide and corr == [])

# --- les défauts réels constatés ---------------------------------------------------------------------------------------------
code, _ = r("flowchart LR" + NL + "  Core_Net -.→ API_Gateway")
verifier("flèche Unicode « -.→ » : devient « -.-> »", "Core_Net -.-> API_Gateway" in code)
code, _ = r("flowchart LR" + NL + "  Utilisateur → Portail")
verifier("flèche « → » seule : devient « --> »", "Utilisateur --> Portail" in code)
code, _ = r("graph LR" + NL + "  D --> E[Prioriser (DREAD/CVSS)<br>04-evaluation.md]")
verifier("parenthèses dans un libellé : mis entre guillemets, <br> conservé", 'E["Prioriser (DREAD/CVSS)<br>04-evaluation.md"]' in code)
code, _ = r("flowchart TD" + NL + "  A[Base de données (SQL)] --> B{Choix ? (oui/non)}")
verifier("parenthèse finale du libellé conservée (A[Base (SQL)])", 'A["Base de données (SQL)"]' in code and 'B{"Choix ? (oui/non)"}' in code)
code, _ = r("flowchart LR" + NL + "  Internet -->|VPN| Réseau interne" + NL + "  Réseau interne -->|AD| Annuaire")
verifier("nom d'étape avec espaces et accents : identifiant sûr + libellé, réutilisé ensuite",
         'Reseau_interne[Réseau interne]' in code and code.count("Reseau_interne") == 2 and "Annuaire" in code)
code, _ = r("flowchart LR" + NL + '  subgraph "Zone DMZ (FortiGate)"' + NL + "    A[Web]" + NL + "  end")
verifier("zone sans identifiant : identifiant ajouté, titre guillemeté", 'subgraph sg1["Zone DMZ (FortiGate)"]' in code and "  end" in code)
code, _ = r("flowchart LR" + NL + "  [E12] -->|Audit| DSI")
verifier("citation [E12] utilisée comme nœud : le lien est gardé", 'E12["Preuve E12"] -->|Audit| DSI' in code)
code, _ = r("flowchart LR" + NL + "  DSI --> Actif [E34]")
verifier("citation collée dans un libellé : retirée", "[E34]" not in code and "DSI --> Actif" in code)
code, _ = r("flowchart TD" + NL + "  A[Début] -- oui --> B[Fin]")
verifier("« A -- texte --> B » : devient « A -->|texte| B »", "A[Début] -->|oui| B[Fin]" in code)
code, _ = r("flowchart LR" + NL + "  A[As" + chr(0x2011) + "Is] --> B")
verifier("tiret insécable remplacé", chr(0x2011) not in code and "As-Is" in code)

# --- ce qu'on ne sait pas réparer est mis en commentaire, jamais inventé ----------------------------------------------------
code, corr = r("flowchart LR" + NL + "  A --> B" + NL + "  SAN <----Core--- Citrix")
verifier("lien mal formé : mis en commentaire, le reste du schéma est sauf", "%% SAN <----Core--- Citrix" in code and "A --> B" in code
         and any("commentaire" in c for c in corr))
code, _ = r("flowchart LR" + NL + "  Légende : bleu = interne" + NL + "  A --> B")
verifier("texte libre dans le schéma : mis en commentaire", "%% Légende : bleu = interne" in code)

# --- autres types de schémas : seulement les caractères ------------------------------------------------------------------------
code, _ = r("sequenceDiagram" + NL + "  Alice->>Bob: Bonjour [E12]")
verifier("diagramme de séquence : structure inchangée, citation retirée", "Alice->>Bob: Bonjour" in code and "[E12]" not in code)

# --- Markdown complet -------------------------------------------------------------------------------------------------------------
md = "# Titre" + NL + NL + "```mermaid" + NL + "flowchart LR" + NL + "  A → B" + NL + "```" + NL + NL + "Texte." + NL
corrige, corr = schemas.reparer_markdown(md)
verifier("Markdown : le bloc mermaid est réparé, le reste intact", "A --> B" in corrige and corrige.startswith("# Titre") and corrige.endswith("Texte." + NL) and corr)

# --- fichier : écriture seulement s'il y a eu correction ---------------------------------------------------------------------------
d = Path(tempfile.mkdtemp(prefix="e21-schemas-"))
f = d / "00-description.md"
f.write_text(md, encoding="utf-8")
n = schemas.reparer_fichier(f)
verifier("fichier réparé sur place, copie d'avant conservée", n >= 1 and "A --> B" in f.read_text(encoding="utf-8")
         and (d / "00-description.avant-correction-schema.md").is_file())
n2 = schemas.reparer_fichier(f)
verifier("fichier déjà correct : aucune écriture", n2 == 0)

print("SCHEMAS:", "OK" if not ECHECS else f"{len(ECHECS)} ECHEC(S)")
sys.exit(1 if ECHECS else 0)
