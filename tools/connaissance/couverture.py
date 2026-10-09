"""Couverture : ce que le dossier SAIT, ne sait QUE PARTIELLEMENT, ou IGNORE encore.

Une analyse de risques a des BESOINS D'INFORMATION (« qui est le RSSI ? », « quand a eu lieu la dernière
restauration réussie ? »). Pour chacun, l'index cherche des preuves, un juge dit si elles RÉPONDENT vraiment
(un passage voisin du sujet ne suffit pas), puis la réponse est vérifiée contre les preuves citées.

Trois issues, jamais une invention :
  - CONNU    : la réponse est tirée de preuves citées et vérifiées ;
  - PARTIEL  : une partie seulement est documentée → il manque quelque chose, dit explicitement ;
  - INCONNU  : aucune preuve → une QUESTION OUVERTE pour l'analyste (« à demander »), pas « n'existe pas ».
Absence d'information ≠ absence de mesure : le dossier ne conclut jamais « il n'y a pas de X », seulement « X n'est
pas documenté ». Même règle plus tard pour une recherche hors des documents (origine « externe ») : sans preuve → inconnu.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from . import contradictions, ollama, verification

MODELE_JUGE = "gemma4:12b"
CONNU, PARTIEL, INCONNU = "connu", "partiel", "inconnu"


@dataclass(frozen=True)
class Besoin:
    """Une information dont l'analyse a besoin."""

    id: str
    theme: str
    question: str


# Liste de départ pour une analyse de système d'information ; chaque projet peut fournir la sienne.
BESOINS: tuple[Besoin, ...] = (
    Besoin("gouv-rssi", "Gouvernance", "Qui est le RSSI et est-il indépendant du DSI ?"),
    Besoin("gouv-pssi", "Gouvernance", "Existe-t-il une politique de sécurité (PSSI) et de quelle version ?"),
    Besoin("gouv-comite", "Gouvernance", "À quelle fréquence se réunit le comité de sécurité ?"),
    Besoin("gouv-normes", "Gouvernance", "Quelles normes ou certifications (ISO 27001, etc.) sont obtenues ou visées ?"),
    Besoin("act-appli", "Actifs", "Quelles sont les applications critiques et qui en est propriétaire ?"),
    Besoin("act-sites", "Actifs", "Quels sont les sites de l'entreprise et leur rôle ?"),
    Besoin("act-postes", "Actifs", "Combien de postes de travail existent et sont-ils chiffrés ?"),
    Besoin("act-cloud", "Actifs", "Quels services sont hébergés en SaaS ou dans le cloud, chez quels fournisseurs ?"),
    Besoin("cont-sauv", "Continuité", "Comment sont réalisées les sauvegardes et où sont-elles stockées ?"),
    Besoin("cont-restau", "Continuité", "Quand a eu lieu la dernière restauration de sauvegarde réussie ?"),
    Besoin("cont-pra", "Continuité", "Existe-t-il un plan de reprise d'activité, quand a-t-il été testé, quel est le site de repli ?"),
    Besoin("acc-mfa", "Accès", "L'authentification multifacteur (MFA) est-elle en place, pour quels comptes ?"),
    Besoin("acc-admin", "Accès", "Les comptes d'administration sont-ils nominatifs ou partagés ?"),
    Besoin("acc-departs", "Accès", "Comment et sous quel délai les comptes des personnes parties sont-ils désactivés ?"),
    Besoin("acc-distant", "Accès", "Qui dispose d'un accès à distance (VPN, télémaintenance, prestataires) ?"),
    Besoin("res-segm", "Réseau", "Le réseau est-il segmenté et quels pare-feu protègent les sites ?"),
    Besoin("res-secours", "Réseau", "Quels sont les liens Internet et existe-t-il un lien de secours ?"),
    Besoin("res-obsol", "Réseau", "Quels équipements sont obsolètes ou hors support constructeur ?"),
    Besoin("exp-journal", "Exploitation", "Les journaux (logs) sont-ils centralisés et analysés, qui reçoit les alertes ?"),
    Besoin("exp-correctifs", "Exploitation", "Comment sont gérés les correctifs de sécurité et les vulnérabilités ?"),
    Besoin("exp-incidents", "Exploitation", "Quels incidents de sécurité ont eu lieu récemment ?"),
    Besoin("exp-intrusion", "Exploitation", "Un test d'intrusion ou un audit technique externe a-t-il été réalisé ?"),
    Besoin("don-registre", "Données", "Existe-t-il un registre des traitements RGPD et est-il complet ?"),
    Besoin("don-dpo", "Données", "Qui est le délégué à la protection des données (DPO) ?"),
    Besoin("don-perso", "Données", "Quelles données personnelles sont traitées (clients, salariés, géolocalisation) ?"),
    Besoin("don-cnil", "Données", "Comment une violation de données est-elle notifiée à la CNIL ?"),
    Besoin("fou-acces", "Fournisseurs", "Quels prestataires ont accès au système d'information et avec quelles clauses de sécurité ?"),
    Besoin("fou-assur", "Fournisseurs", "L'entreprise dispose-t-elle d'une assurance cyber ?"),
    Besoin("hum-sensib", "Humain", "Quelle sensibilisation à la sécurité a été faite et quand ?"),
    Besoin("hum-arrivee", "Humain", "Quel est le processus d'arrivée et de départ des collaborateurs ?"),
    Besoin("phy-salles", "Sécurité physique", "Comment sont protégées les salles serveurs (accès, incendie, énergie) ?"),
)

SCHEMA_BESOIN = {
    "type": "object",
    "properties": {"statut": {"type": "string", "enum": [CONNU, PARTIEL, INCONNU]},
                   "passages": {"type": "array", "items": {"type": "integer"}},
                   "reponse": {"type": "string"}, "manque": {"type": "string"}},
    "required": ["statut", "passages", "reponse", "manque"],
}

CONSIGNE = (
    "QUESTION : {question}\n\nPASSAGES (extraits de documents de l'entreprise) :\n{passages}\n\n"
    "Les passages permettent-ils de répondre à la question ? Réponds en JSON : statut = « connu » si les passages "
    "répondent complètement, « partiel » s'ils répondent en partie, « inconnu » si AUCUN passage ne répond (même si "
    "certains parlent d'un sujet voisin). passages = numéros des passages utilisés. reponse = la réponse en 30 mots "
    "maximum, tirée UNIQUEMENT des passages (vide si inconnu). manque = ce qu'il faudrait obtenir pour répondre "
    "complètement (document, personne à interroger) ; vide si connu. Ne complète jamais avec tes connaissances générales."
)


@dataclass(frozen=True)
class Reponse:
    besoin: Besoin
    statut: str
    reponse: str
    preuves: tuple[dict, ...]
    manque: str
    verification: str  # soutenu | non_soutenu | doute | sans_objet
    a_valider: bool    # nécessite une validation humaine
    pourquoi: str      # pourquoi, et quoi vérifier
    contestations: tuple = ()  # signalements : un AUTRE document contredit les preuves citées


def _juger(besoin: Besoin, candidats: list[dict], modele: str) -> dict:
    passages = "\n".join(
        f"[{i + 1}] (document {c['doc'][:40]}{' · ' + c['libelle'] if c['genre'] == 'passage' and c['libelle'] else ''}) {c['extrait']}"
        for i, c in enumerate(candidats))
    return ollama.discuter_json(modele, CONSIGNE.format(question=besoin.question, passages=passages),
                                SCHEMA_BESOIN, contexte=4096, max_sortie=260)


def evaluer(index, besoin: Besoin, vecteur_question: list[float] | None = None, *, k: int = 6,
            modele: str = MODELE_JUGE, juge=None, verificateurs=None, contre=None) -> Reponse:
    """Statut d'UN besoin. `juge(besoin, candidats, modele)`, `verificateurs` et `contre(index, preuves)` sont
    injectables pour les tests. `contre` cherche un autre document qui CONTREDIT les preuves citées."""
    juge = juge or _juger
    candidats = index.rechercher(besoin.question, vecteur_question, k=k)
    if not candidats:
        return Reponse(besoin, INCONNU, "", (), "Aucun document indexé n'aborde ce sujet.", "sans_objet", True,
                       "Aucune preuve : à demander à l'entreprise. Ne pas en conclure que la mesure n'existe pas.")
    verdict = juge(besoin, candidats, modele)
    statut = verdict.get("statut", INCONNU)
    cites = [p for p in verdict.get("passages", []) if isinstance(p, int) and 1 <= p <= len(candidats)]
    manque = str(verdict.get("manque", "")).strip()
    if statut not in (CONNU, PARTIEL) or not cites:
        # un « connu » sans preuve citée est une affirmation en l'air : il devient inconnu
        motif = "" if statut == INCONNU else "Le juge a répondu sans citer de preuve valide : réponse écartée."
        return Reponse(besoin, INCONNU, "", (), manque or "Information à obtenir.", "sans_objet", True,
                       (motif + " Aucune preuve ne répond : à demander. Ne pas en conclure que la mesure n'existe pas.").strip())
    preuves = tuple({"id": candidats[p - 1]["id"], "doc": candidats[p - 1]["doc"], "extrait": candidats[p - 1]["extrait"]} for p in cites)
    reponse = str(verdict.get("reponse", "")).strip()
    controle = verification.verifier("\n".join(p["extrait"] for p in preuves), reponse, verificateurs=verificateurs) if reponse else verification.DOUTE
    a_valider, pourquoi = False, ""
    if statut == PARTIEL:
        a_valider, pourquoi = True, f"Information partielle. Il manque : {manque or 'à préciser'}."
    if controle == verification.NON_SOUTENU:
        statut, a_valider = PARTIEL, True
        pourquoi = "La réponse proposée n'est pas soutenue par les preuves citées : relire les extraits avant de s'y fier."
    elif controle == verification.DOUTE:
        a_valider = True
        pourquoi = (pourquoi + " " if pourquoi else "") + "Les deux vérificateurs divergent : relire les extraits cités."
    contestations = tuple((contre or (lambda i, p: contradictions.contredit(i, p, modele=modele)))(index, preuves))
    if contestations:
        a_valider = True
        autres = " ; ".join(f"{s.doc_b[:30]} : « {s.extrait_b[:120]} »" for s in contestations[:2])
        pourquoi = (pourquoi + " " if pourquoi else "") + f"CONTESTÉ par un autre document — {autres}. Décider quelle source fait foi."
    return Reponse(besoin, statut, reponse, preuves, manque, controle, a_valider, pourquoi.strip(), contestations)


def evaluer_tous(index, besoins: tuple[Besoin, ...] = BESOINS, vecteurs_questions: list[list[float]] | None = None,
                 **options) -> list[Reponse]:
    """Statut de chaque besoin. Les vecteurs des questions sont calculés ici sauf s'ils sont fournis."""
    if vecteurs_questions is None:
        vecteurs_questions = ollama.vecteurs([b.question for b in besoins], prefixe="search_query: ")
    return [evaluer(index, b, v, **options) for b, v in zip(besoins, vecteurs_questions)]


def priorite(r: Reponse) -> int:
    """Urgence de traitement : 4 contesté ou non soutenu · 3 non documenté · 2 partiel · 1 vérificateurs en doute · 0 rien à faire."""
    if r.contestations or r.verification == verification.NON_SOUTENU:
        return 4
    if r.statut == INCONNU:
        return 3
    if r.statut == PARTIEL:
        return 2
    return 1 if r.a_valider else 0


def questions_ouvertes(reponses: list[Reponse]) -> list[str]:
    """Une ligne par besoin non pleinement établi, les plus importants d'abord : ce qu'il faut demander ou relire."""
    lignes = []
    for r in sorted(reponses, key=lambda r: -priorite(r)):
        if r.statut == INCONNU:
            lignes.append(f"[{r.besoin.theme}] {r.besoin.question} → NON DOCUMENTÉ. {r.manque}".strip())
        elif r.a_valider:
            lignes.append(f"[{r.besoin.theme}] {r.besoin.question} → {'CONTESTÉ' if r.contestations else 'À VALIDER'}. {r.pourquoi}".strip())
    return lignes


def rapport_markdown(reponses: list[Reponse], signaux: list | None = None) -> str:
    """Livrable « Recherches, relations, contradictions, questions » (Markdown, affichable dans le site)."""
    compte = {s: sum(1 for r in reponses if r.statut == s) for s in (CONNU, PARTIEL, INCONNU)}
    sortie = ["# Recherches, contradictions et questions ouvertes", "",
              f"{len(reponses)} besoins d'information examinés : **{compte[CONNU]} connus**, "
              f"**{compte[PARTIEL]} partiels**, **{compte[INCONNU]} non documentés**.", "",
              "> « Non documenté » signifie que **les documents fournis n'en parlent pas**. Cela ne prouve pas que la "
              "mesure n'existe pas : c'est une question à poser à l'entreprise.", ""]
    for titre, statut in (("Ce que nous savons", CONNU), ("Ce que nous savons en partie", PARTIEL)):
        sortie += [f"## {titre}", ""]
        retenus = [r for r in reponses if r.statut == statut]
        if not retenus:
            sortie += ["_Aucun._", ""]
        for r in retenus:
            sortie.append(f"- **{r.besoin.question}** {r.reponse}" + (f" _({'CONTESTÉ — ' if r.contestations else 'à valider : '}{r.pourquoi})_" if r.a_valider else ""))
            for p in r.preuves:
                sortie.append(f"  - preuve ({p['doc'][:40]}) : « {p['extrait'][:200]} »")
            if statut == PARTIEL and r.manque:
                sortie.append(f"  - **Manque** : {r.manque}")
        sortie.append("")
    sortie += ["## Ce que nous ignorons encore (questions à poser)", ""]
    inconnus = [r for r in reponses if r.statut == INCONNU]
    sortie += [f"- [{r.besoin.theme}] **{r.besoin.question}** {r.manque}".rstrip() for r in inconnus] or ["_Aucune._"]
    sortie += ["", "## Contradictions entre documents (à valider)", ""]
    ligne = lambda s: f"- {s.doc_a[:40]} : « {s.extrait_a[:160]} » **≠** {s.doc_b[:40]} : « {s.extrait_b[:160]} » — {s.explication[:200]}"  # noqa: E731
    hautes = [s for s in signaux or [] if getattr(s, "priorite", "haute") == "haute"]
    basses = [s for s in signaux or [] if getattr(s, "priorite", "haute") == "basse"]
    sortie += [ligne(s) for s in hautes] or ["_Aucune contradiction de priorité haute._"]
    if basses:
        sortie += ["", f"### À relire si le temps le permet ({len(basses)}) — non confirmées par un second avis", ""]
        sortie += [ligne(s) for s in basses]
    return "\n".join(sortie) + "\n"
