"""Citations des livrables : chaque fait sur le système renvoie à une preuve `[E12]` de l'index.

Trois contrôles, du plus solide au moins solide :
  1. le CODE vérifie que chaque identifiant cité existe dans l'index (une citation inventée est rejetée) ;
  2. le CODE vérifie qu'un livrable de faits cite ses lignes (au moins `PART_MIN` des lignes de tableau) ;
  3. DEUX vérificateurs indépendants (Gemma 4 + MiniCheck) jugent si la ligne est soutenue par SES extraits cités,
     sur des passages COURTS : accord = soutenu, accord négatif = non soutenu (à corriger), désaccord = doute
     (« nécessite une validation humaine », avec la ligne à relire).

Lecture confortable : à l'affichage, `[E12]` devient une note discrète ¹ dont l'infobulle montre l'extrait, et la
liste des preuves est repliée en bas de page. Le texte du livrable est échappé avant (aucun HTML venu d'un modèle).
"""
from __future__ import annotations

import html
import re

from . import verification

RE_CITATION = re.compile(r"`?\[E(\d+)\]`?")
PART_MIN = 0.7           # part minimale de lignes de tableau citées dans un livrable de faits
LIMITE_LIGNES = 40       # lignes soumises aux vérificateurs par livrable (le reste est compté « non vérifié »)
INDICATEURS_TABLEAU = ("|",)


def ids_cites(texte: str) -> list[int]:
    """Identifiants cités, dans l'ordre d'apparition, sans doublon."""
    vus: dict[int, None] = {}
    for m in RE_CITATION.finditer(texte):
        vus.setdefault(int(m.group(1)), None)
    return list(vus)


def extraits(index, ids: list[int]) -> dict[int, tuple[str, str]]:
    """`{id: (document, extrait)}` pour les identifiants qui existent dans l'index."""
    if not ids:
        return {}
    marques = ",".join("?" * len(ids))
    return {i: (doc, extrait) for i, doc, extrait in index.base.execute(
        f"SELECT id, doc, extrait FROM elements WHERE id IN ({marques})", ids)}


def lignes_de_donnees(texte: str) -> list[str]:
    """Lignes de données d'un tableau Markdown (hors en-tête et séparateur)."""
    lignes = [l for l in texte.splitlines() if l.lstrip().startswith("|")]
    donnees = [l for l in lignes if not set(l.replace("|", "").strip()) <= set("-: ")]
    return donnees[1:]


def affirmation(ligne: str) -> str:
    """Texte à vérifier d'une ligne : sans marqueurs de citation, cellules séparées par « ; »."""
    sans = RE_CITATION.sub("", ligne)
    cellules = [c.strip() for c in sans.strip().strip("|").split("|")] if sans.lstrip().startswith("|") else [sans.strip()]
    return " ; ".join(c for c in cellules if c)


def analyser(texte: str, index, *, exiger: bool = False, verificateurs=None, limite: int = LIMITE_LIGNES) -> dict:
    """Contrôle les citations d'un livrable. Renvoie :

    - `inexistantes` : identifiants cités qui ne sont pas dans l'index ;
    - `non_cite` : lignes de tableau sans citation (comptées seulement si `exiger`) ;
    - `non_soutenues` / `doutes` : lignes citantes que les vérificateurs rejettent / dont ils divergent ;
    - `verifiees`, `non_verifiees` : combien de lignes ont été soumises aux vérificateurs.
    """
    ids = ids_cites(texte)
    connus = extraits(index, ids)
    inexistantes = [i for i in ids if i not in connus]
    donnees = lignes_de_donnees(texte)
    non_cite = [l for l in donnees if not RE_CITATION.search(l)] if exiger else []
    candidates = [l for l in texte.splitlines() if RE_CITATION.search(l)]
    non_soutenues, doutes, verifiees = [], [], 0
    for ligne in candidates[:limite]:
        preuves = [connus[int(m.group(1))] for m in RE_CITATION.finditer(ligne) if int(m.group(1)) in connus]
        if not preuves:
            continue  # toutes les citations de la ligne sont inexistantes : déjà signalé plus haut
        document = "\n".join(f"({doc}) {extrait}" for doc, extrait in preuves)
        verdict = verification.verifier(document, affirmation(ligne), verificateurs=verificateurs)
        verifiees += 1
        if verdict == verification.NON_SOUTENU:
            non_soutenues.append(ligne.strip())
        elif verdict == verification.DOUTE:
            doutes.append(ligne.strip())
    return {"inexistantes": inexistantes, "non_cite": non_cite, "non_soutenues": non_soutenues, "doutes": doutes,
            "verifiees": verifiees, "non_verifiees": max(len(candidates) - verifiees, 0), "lignes_tableau": len(donnees),
            "part_citee": (1 - len(non_cite) / len(donnees)) if (exiger and donnees) else 1.0}


def corrections(nom: str, rapport: dict, exiger: bool = False) -> str:
    """Corrections (texte) à redonner à l'agent ; vide si les citations sont irréprochables.

    Les lignes en DOUTE ne sont pas corrigées d'autorité : elles vont à la validation humaine (`doutes`)."""
    morceaux = []
    if rapport["inexistantes"]:
        morceaux.append(f"{nom} : identifiants de preuve INEXISTANTS à retirer ou remplacer : "
                        + ", ".join(f"[E{i}]" for i in rapport["inexistantes"]) + ".")
    if exiger and rapport["part_citee"] < PART_MIN:
        morceaux.append(f"{nom} : trop de lignes sans preuve citée ({len(rapport['non_cite'])} sur {rapport['lignes_tableau']}) : "
                        "cite [E…] après chaque fait, ou retire la ligne si le dossier de preuves ne la soutient pas.")
    for ligne in rapport["non_soutenues"][:6]:
        morceaux.append(f"{nom} : la preuve citée ne soutient PAS cette ligne : « {affirmation(ligne)[:160]} ». "
                        "Corrige-la d'après la preuve, ou retire-la.")
    return " ".join(morceaux)


def pour_affichage(texte: str, details: dict[int, tuple[str, str]]) -> str:
    """Markdown/HTML de lecture : `[E12]` devient une note discrète ; les preuves sont repliées en bas.

    Le texte est échappé AVANT l'insertion des notes : aucun HTML produit par un modèle n'est rendu."""
    echappe = texte.replace("<", "&lt;")  # seul « < » ouvre une balise ; « > » reste utilisable (citations Markdown)
    numeros: dict[int, int] = {}

    def remplacer(m: re.Match) -> str:
        ident = int(m.group(1))
        if ident not in details:
            return f"<sup title=\"preuve introuvable\">[?]</sup>"
        numero = numeros.setdefault(ident, len(numeros) + 1)
        doc, extrait = details[ident]
        info = html.escape(f"{doc} — « {' '.join(extrait.split())[:300]} »", quote=True)
        return f"<sup title=\"{info}\">[{numero}]</sup>"

    corps = RE_CITATION.sub(remplacer, echappe)
    if not numeros:
        return corps
    notes = [f"<li value=\"{n}\"><b>{html.escape(details[i][0], quote=False)}</b> : « "
             f"{html.escape(' '.join(details[i][1].split())[:400], quote=False)} »</li>" for i, n in numeros.items()]
    return corps + ("\n\n<details><summary>Preuves citées (" + str(len(numeros)) + ")</summary><ol>" + "".join(notes) + "</ol></details>\n")
