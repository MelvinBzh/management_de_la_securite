#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes : ce qui a changé dans la connaissance (`delta.py`) — aucun modèle, aucun réseau.

    python3 tools/connaissance/tests/test_delta.py
"""
from __future__ import annotations

import sys
import tempfile
import zlib
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.connaissance import couverture, delta, fiches, ingestion  # noqa: E402
from tools.connaissance.index import Index  # noqa: E402

RESULTATS: list[tuple[str, bool]] = []


def verifier(nom: str, condition: bool) -> None:
    RESULTATS.append((nom, bool(condition)))


def document(sujet: str, *lignes: str) -> str:
    return f"# {sujet}\n\n" + "\n".join(lignes) + "\n" + ("Texte de remplissage sans importance pour le test. " * 8) + "\n"


def vecteur_de(texte: str) -> list[float]:
    """Sac de mots hachés (déterministe) : deux phrases qui partagent presque tous leurs mots sont proches."""
    v = [0.0] * 64
    for mot in texte.lower().replace(":", " ").replace(".", " ").split():
        v[zlib.crc32(mot.encode()) % 64] += 1.0
    return v


def moteurs():
    def faits(nom, contenu):
        return [fiches.Fait(nom, l, l, True) for l in contenu.splitlines() if l.startswith("Fait")]
    return ingestion.Moteurs(faits, lambda n, c: ([], []), lambda t, **_: [vecteur_de(x) for x in t],
                             lambda index, **_: [], lambda index, besoin, vec=None, **_: couverture.Reponse(
                                 besoin, couverture.INCONNU, "", (), "", "sans_objet", True, ""))


M = moteurs()
D = Path(tempfile.mkdtemp(prefix="e21-delta-"))
idx = Index(":memory:")


def lire(nom, contenu):
    ingestion.traiter_document(idx, nom, contenu, M)


lire("a.md", document("A", "Fait : le serveur applicatif NordTMS est hébergé à Lesquin", "Fait : la sauvegarde Veeam est quotidienne"))
lire("b.md", document("B", "Fait : le pare-feu de bordure est un FortiGate", "Fait : le parc compte 126 portables Dell"))

# --- sans état appliqué, rien n'est inventé ---------------------------------------------------------------------------------------
verifier("sans baseline : delta vide", delta.calculer(idx, None).vide())
delta.ecrire_baseline(D, idx, signature="s1")
base = delta.lire_baseline(D)
verifier("baseline écrite puis relue (documents et éléments)", base and set(base["documents"]) == {"a.md", "b.md"} and len(base["elements"]) > 4)
verifier("rien n'a changé : delta vide", delta.calculer(idx, base).vide())

# --- ajout d'un document, modification d'un autre ----------------------------------------------------------------------------------
lire("b.md", document("B", "Fait : le pare-feu de bordure est un FortiGate", "Fait : le parc compte 132 portables Dell",
                      "Fait : un nouveau site est ouvert à Rungis avec une salle serveur"))
lire("c.md", document("C", "Fait : le serveur applicatif NordTMS est hébergé à Lesquin",
                      "Fait : le prestataire Opsitel assure la télémaintenance des pare-feu"))
d = delta.calculer(idx, base)
verifier("document ajouté et document modifié reconnus", d.documents_ajoutes == ["c.md"] and d.documents_modifies == ["b.md"])
verifier("« 126 portables » devenu « 132 portables » : fait MODIFIÉ (avant/après), pas perdu ni nouveau",
         any("126" in m["avant"]["extrait"] and "132" in m["apres"]["extrait"] for m in d.modifies))
verifier("un fait identique dans un autre document le CONFIRME (rien à changer)",
         any("Lesquin" in c["nouveau"]["extrait"] and c["existant"]["doc"] == "a.md" for c in d.confirmes))
verifier("un fait sans équivalent est NOUVEAU (Rungis, Opsitel)",
         any("Rungis" in n["extrait"] for n in d.nouveaux) and any("Opsitel" in n["extrait"] for n in d.nouveaux))
verifier("le fait inchangé du document modifié n'est ni nouveau ni modifié",
         not any("FortiGate" in n["extrait"] for n in d.nouveaux) and not any("FortiGate" in m["apres"]["extrait"] for m in d.modifies))
verifier("aucun fait perdu quand chacun a un équivalent", d.perdus == [])
verifier("le résumé compte tout", d.resume()["faits_modifies"] == 1 and d.resume()["documents_ajoutes"] == 1)

# --- retrait d'un document ---------------------------------------------------------------------------------------------------------
idx.supprimer_document("a.md")
d2 = delta.calculer(idx, base)
verifier("document retiré reconnu", "a.md" in d2.documents_retires)
verifier("faits du document retiré sans équivalent : PERDUS (avec leur texte)",
         any("Veeam" in p["extrait"] for p in d2.perdus))
verifier("le fait retiré qui existe encore ailleurs (c.md) est aussi perdu pour a.md, mais son identifiant n'est pas réutilisé",
         d2.retires_ids and all(i not in {x for (x,) in idx.base.execute("SELECT id FROM elements")} for i in d2.retires_ids))

# --- nouvelle baseline : de nouveau rien à signaler ----------------------------------------------------------------------------------
delta.ecrire_baseline(D, idx, signature="s2")
verifier("après application : delta vide", delta.calculer(idx, delta.lire_baseline(D)).vide())
base2 = delta.lire_baseline(D)
verifier("preuves « vues » : cumul jamais réduit (une preuve retirée reste connue des livrables qui la citent)",
         set(base["elements"]) <= {str(i) for i in base2["vus"]} and set(base["elements"]) - set(base2["elements"])
         and 999999 not in base2["vus"])

# --- l'état appliqué est amorcé AVANT de lire de nouveaux documents (projet analysé avant ce suivi) -----------------------------------
from tools.connaissance import travail  # noqa: E402

P = Path(tempfile.mkdtemp(prefix="e21-amorce-"))
(P / "intrants").mkdir()
(P / "intrants" / "a.md").write_text(document("A", "Fait : le serveur applicatif NordTMS est hébergé à Lesquin"), encoding="utf-8")
travail.executer(P, moteurs=moteurs())
verifier("première lecture, aucun livrable : pas d'état appliqué", delta.lire_baseline(P) is None)
(P / "01-actifs.md").write_text(chr(10).join(["# Actifs", "", "| ID | Actif |", "|---|---|", "| A01 | NordTMS |"]) + chr(10),
                                encoding="utf-8")   # l'analyse a eu lieu
(P / "intrants" / "b.md").write_text(document("B", "Fait : le pare-feu de bordure est un FortiGate"), encoding="utf-8")
travail.executer(P, moteurs=moteurs())
base_p = delta.lire_baseline(P)
verifier("document ajouté après l'analyse : l'état appliqué est celui d'AVANT (seul a.md)", base_p and set(base_p["documents"]) == {"a.md"})
idx_p = Index(travail.chemins(P)[1])
d_p = delta.calculer(idx_p, base_p)
verifier("le nouveau document est bien vu comme ajouté, ses faits comme nouveaux", d_p.documents_ajoutes == ["b.md"]
         and any("FortiGate" in n["extrait"] for n in d_p.nouveaux))
idx_p.fermer()

echecs = [n for n, ok in RESULTATS if not ok]
for n, ok in RESULTATS:
    print(("PASS " if ok else "FAIL ") + n)
print(f"DELTA: {len(RESULTATS) - len(echecs)} PASS, {len(echecs)} FAIL")
sys.exit(1 if echecs else 0)
