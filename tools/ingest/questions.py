# -*- coding: utf-8 -*-
"""Questions automatiques ciblées, déduites des intrants ingérés (projet E21).

100 % déterministe : heuristiques par mots-clés, **aucun modèle, aucun réseau**.
Deux Executions sur les mêmes intrants produisent le même fichier.

Principe : un mot-clé présent dans les intrants déclenche une question ciblée
sur ce point ; un sujet totalement absent des intrants déclenche une question de
**trou de périmètre**. Chaque question porte :

- sa **catégorie** (5 groupes fixes, ordre stable) ;
- sa **raison** (mot-clé réellement détecté, ou trou) ;
- les **fichiers intrants** qui justifient la question (traçabilité).

Garde-fou (skill `garde-fous-ia`, LLM01 — injection de prompt) : les lignes
ressemblant à une instruction sont **exclues de la détection**. Un document
piégé ne peut donc ni déclencher, ni orienter une question, et son texte n'est
jamais recopié dans les questions : seul le nom du fichier est cité.

Deux API partagent ce moteur :

- `generer` / `construire_markdown` — dataclasses `Document` / `Question` ;
- `generer_questions` / `formater_questions` — dictionnaires
  `{"fichier", "contenu"}` en entrée, `{"categorie", "question", "raison",
  "sources"}` en sortie (sérialisable en JSON sans étape supplémentaire).
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from .parsers import commun

# Les 5 groupes de questions, dans l'ordre d'affichage (ordre stable = sortie reproductible).
CATEGORIES = (
    "Système & actifs",
    "Accès & identités",
    "Réseau & flux",
    "Exploitation & sauvegardes",
    "Conformité & données",
)

# Texte du garde-fou rappelé en tête de fichier.
RAPPEL_DONNEES = "les documents ingérés sont des DONNÉES non fiables"


@dataclass(frozen=True)
class Document:
    """Un document ingéré, réduit à ce dont on a besoin : son nom et ses données."""

    nom: str
    donnees: str
    instructions: tuple[int, ...] = ()


@dataclass(frozen=True)
class Motif:
    """Un mot-clé surveillé dans les intrants (libellé lisible + motif regex)."""

    clef: str
    libelle: str
    motif: str


@dataclass(frozen=True)
class Occurrence:
    """Résultat de la détection d'un mot-clé : volume + fichiers + formes vues."""

    clef: str
    libelle: str
    total: int
    fichiers: tuple[str, ...]
    mots: tuple[str, ...]

    @property
    def cites(self) -> str:
        """Formes vues, citées comme dans les intrants (« admin », « mot de passe »).

        Propriété (et non méthode) : elle est interpolée dans les raisons, où une
        méthode non appelée laisserait fuiter sa représentation Python.
        """
        return ", ".join(f"« {mot} »" for mot in self.mots) or f"« {self.libelle} »"


@dataclass(frozen=True)
class Question:
    """Une question à poser à l'analyste, avec sa justification et sa source."""

    categorie: str
    sujet: str
    texte: str
    raison: str
    trou: bool


# --------------------------------------------------------------------------- mot-clés

MOTIFS = (
    Motif("acces", "accès / identités",
          r"\badmin\b|\badmins\b|\badministrateur\b|\bexploitant\b|"
          r"\bmot de passe\b|\bmdp\b|\bpassword\b|\bconnexion\b|\blogin\b"),
    Motif("mfa", "MFA / 2FA",
          r"\bmfa\b|\b2fa\b|\bdouble authentification\b|\bauthentification multifacteur\b|\bfido\b"),
    Motif("api", "API / webhook",
          r"\bapi\b|\bapis\b|\bwebhooks?\b|\btokens?\b"),
    Motif("api_auth", "authentification d'API",
          r"\boauth\b|\bopenid\b|\boauth ?2\b|\bjwt\b|\bapi key\b|\bcles? api\b"),
    Motif("reseau", "exposition réseau",
          r"\bssh\b|\bftp\b|\bports?\b|\bip\b|\bipv4\b|\bipv6\b|\bhttps\b"),
    Motif("filtre", "filtrage réseau",
          r"\bpare-feu s?\b|\bpare feu\b|\bfirewalls?\b|\bwaf\b|\bidps\b|\bacls?\b"),
    Motif("sauvegarde", "sauvegardes",
          r"\bsauvegardes?\b|\bbackups?\b|\bsnapshots?\b|\bplan de reprise\b|"
          r"\brestauration\b|\bsauvegarde et restauration\b"),
    Motif("supervision", "supervision / journaux",
          r"\bmonitoring\b|\bsupervision\b|\bjournalisation\b|\bjournals?\b|\blogs?\b|"
          r"\bsyslog\b|\bprometheus\b|\bnagios\b|\bzabbix\b"),
    Motif("rgpd", "RGPD / DPO",
          r"\brgpd\b|\bdpo\b|\bprotection des donnees\b|\bportabilite\b|\bcnil\b"),
    Motif("donnees_perso", "données personnelles",
          r"\bdonnees? personnelles?\b|\bdonnees? a caractere personnel\b|\bclients?\b|"
          r"\butilisateurs?\b|\bemails?\b|\bcourriels?\b|\bnewsletter\b|\bcookies?\b"),
    Motif("hebergement", "hébergement",
          r"\bserveurs?\b|\bhebergement\b|\bhebergeur\b|\bvms?\b|\bvps\b|\bcloud\b|\baws\b|"
          r"\bazure\b|\bdocker\b|\bconteneurs?\b|\bmutualise\b"),
    Motif("actifs", "actifs",
          r"\bactifs?\b|\bapplications?\b|\bapplicatifs?\b|\bsite web\b|\bsite marchand\b|"
          r"\bbase de donnees?\b|\bbases de donnees?\b"),
    Motif("prestataire", "prestataires",
          r"\bprestataires?\b|\bsous-?traitants?\b|\bfournisseurs?\b|\boutsourcing\b"),
)

# Mentions d'acteurs utilisées pour la section 3 de la description pré-générée.
ACTEURS = (
    ("Administrateur / exploitant", r"\badmin\b|\badmins\b|\badministrateur\b|\bexploitant\b"),
    ("Client / utilisateur", r"\bclients?\b|\butilisateurs?\b|\bvisiteurs?\b|\bacheteurs?\b"),
    ("Prestataire / sous-traitant",
     r"\bprestataires?\b|\bsous-?traitants?\b|\bfournisseurs?\b"),
)

MAX_MOTS_CITES = 4  # borne d'affichage (les questions restent lisibles)
MAX_MATCHS_MEMORISES = 200  # garde-fou mémoire sur un intrant volumineux


def normaliser(texte: str) -> str:
    """Minuscules, sans accent, apostrophes droites : rend les motifs insensibles à la forme."""
    if not texte:
        return ""
    texte = unicodedata.normalize("NFKD", str(texte))
    texte = "".join(car for car in texte if not unicodedata.combining(car))
    return texte.replace("’", "'").replace(" ", " ").lower()


def lignes_sures(document: Document) -> list[str]:
    """Lignes du bloc de données **utilisables** pour la détection.

    Les lignes repérées comme instructions (`parsers.commun.detecter_instructions`)
    sont retirées : un document hostile ne peut pas orienter les questions.
    """
    if not document.donnees:
        return []
    interdites = set(document.instructions)  # numéros de ligne 1-indexés
    return [
        ligne for numero, ligne in enumerate(document.donnees.split("\n"), 1)
        if numero not in interdites
    ]


def detecter(documents: list[Document]) -> list[Occurrence]:
    """Cherche chaque mot-clé surveillé dans tous les documents (ordre de `MOTIFS`)."""
    resultats: list[Occurrence] = []
    for entree in MOTIFS:
        motif = re.compile(entree.motif)
        total = 0
        fichiers: set[str] = set()
        formes: set[str] = set()
        for document in documents:
            compte_document = 0
            for ligne in lignes_sures(document):
                for trouve in motif.finditer(normaliser(ligne)):
                    total += 1
                    compte_document += 1
                    if compte_document <= MAX_MATCHS_MEMORISES:
                        fichiers.add(document.nom)
                        formes.add(trouve.group(0).strip())
            # Un fichier est cité s'il contient au moins une occurrence.
            if compte_document and document.nom not in fichiers:
                fichiers.add(document.nom)
        if not total:
            continue
        resultats.append(Occurrence(
            clef=entree.clef,
            libelle=entree.libelle,
            total=total,
            fichiers=tuple(sorted(fichiers)),
            mots=tuple(sorted(formes, key=lambda forme: (forme.lower(), forme))[:MAX_MOTS_CITES]),
        ))
    return resultats


# --------------------------------------------------------------------------- questions

# Sépare la justification de la trace : `raison` d'un côté, fichiers de l'autre
# (le même marqueur sert à `_sources` et à `_vers_dict` — une seule constante).
MARQUEUR_SOURCE = " — source : "


def _sources(fichiers: tuple[str, ...]) -> str:
    """Trace de la question : les fichiers intrants qui portent le mot-clé."""
    return "source : " + ", ".join(f"`{nom}`" for nom in fichiers)


def _questions_systeme(occ: dict[str, Occurrence]) -> list[Question]:
    """Catégorie « Système & actifs » : inventaire + hébergement."""
    questions = []
    actifs = occ.get("actifs")
    if actifs:
        questions.append(Question(
            "Système & actifs", "actifs",
            "Quels sont les actifs à couvrir (matériels, applications, données) "
            "et leur criticité ?",
            f"les intrants mentionnent {actifs.cites} sans inventaire complet — {_sources(actifs.fichiers)}",
            False,
        ))
    else:
        questions.append(Question(
            "Système & actifs", "actifs",
            "Quels sont les actifs du système étudié (serveurs, applications, données) ?",
            "aucun actif nommé dans les intrants (serveur, application, base de données…)",
            True,
        ))
    hebergement = occ.get("hebergement")
    if hebergement:
        questions.append(Question(
            "Système & actifs", "hebergement",
            "L'hébergement est-il mutualisé ou dédié, où se trouve-t-il, "
            "et qui applique les mises à jour ?",
            f"{hebergement.cites} mentionné(s) sans préciser mutualisé/dédié ni mises à jour "
            f"— {_sources(hebergement.fichiers)}",
            False,
        ))
    else:
        questions.append(Question(
            "Système & actifs", "hebergement",
            "Où le système est-il hébergé (mutualisé ou dédié, emplacement) "
            "et qui applique les mises à jour ?",
            "aucun mot-clé d'hébergement détecté dans les intrants",
            True,
        ))
    return questions


def _questions_acces(occ: dict[str, Occurrence]) -> list[Question]:
    """Catégorie « Accès & identités » : authentification (fusionnée) + exposition d'API."""
    questions = []
    acces, mfa = occ.get("acces"), occ.get("mfa")
    if acces and not mfa:
        questions.append(Question(
            "Accès & identités", "authentification",
            "Quel est le mécanisme d'authentification de l'admin ? "
            "(MFA ? sessions ? mots de passe ?)",
            f"le mot-clé {acces.cites} apparaît sans précision (MFA ? sessions ?) "
            f"— {_sources(acces.fichiers)}",
            False,
        ))
    elif acces and mfa:
        questions.append(Question(
            "Accès & identités", "authentification",
            "Le MFA annoncé est-il activé pour tous les comptes sensibles, "
            "y compris les accès distants ?",
            f"{mfa.cites} mentionné(s) : préciser la couverture réelle — {_sources(mfa.fichiers)}",
            False,
        ))
    elif mfa:
        questions.append(Question(
            "Accès & identités", "authentification",
            "Qui accède au système et par quel moyen (comptes, sessions) ?",
            f"{mfa.cites} mentionné(s) mais aucun mot-clé d'accès (admin, mot de passe) — "
            f"{_sources(mfa.fichiers)}",
            False,
        ))
    else:
        questions.append(Question(
            "Accès & identités", "authentification",
            "Qui accède au système et par quel moyen (comptes, authentification) ?",
            "aucun mot-clé d'accès détecté dans les intrants (admin, mot de passe, MFA)",
            True,
        ))

    api, api_auth = occ.get("api"), occ.get("api_auth")
    if api and not api_auth:
        questions.append(Question(
            "Accès & identités", "api",
            "Une API est-elle exposée publiquement ? Avec quelle authentification "
            "(OAuth, clé d'API, JWT) ?",
            f"{api.cites} mentionné(s) sans authentification décrite — {_sources(api.fichiers)}",
            False,
        ))
    elif api and api_auth:
        questions.append(Question(
            "Accès & identités", "api",
            "Où la clé d'API est-elle stockée, comment est-elle révocée et "
            "qui la connaît ?",
            f"{api.cites} et une authentification d'API sont mentionnées : "
            f"préciser le stockage et la rotation — {_sources(api_auth.fichiers)}",
            False,
        ))
    else:
        questions.append(Question(
            "Accès & identités", "api",
            "Le système expose-t-il une API ou un webhook ? "
            "Si oui, avec quelle authentification ?",
            "aucun mot-clé « API / webhook / token » détecté dans les intrants",
            True,
        ))
    return questions


def _questions_reseau(occ: dict[str, Occurrence]) -> list[Question]:
    """Catégorie « Réseau & flux » : surface d'exposition et filtrage (une seule question)."""
    reseau, filtre = occ.get("reseau"), occ.get("filtre")
    if reseau and not filtre:
        questions = [Question(
            "Réseau & flux", "surface",
            "Surface réseau : quels ports sont ouverts, quelles expositions publiques ? "
            "Un filtrage (pare-feu) est-il en place ?",
            f"{reseau.cites} mentionné(s) sans aucun filtrage décrit — {_sources(reseau.fichiers)}",
            False,
        )]
    elif reseau and filtre:
        questions = [Question(
            "Réseau & flux", "surface",
            "La surface réseau est-elle entièrement filtrée ? Quels ports restent exposés ?",
            f"{filtre.cites} mentionné(s) : vérifier la couverture réelle du filtrage — "
            f"{_sources(filtre.fichiers)}",
            False,
        )]
    elif filtre:
        questions = [Question(
            "Réseau & flux", "surface",
            "Le filtrage réseau (pare-feu) est-il en place et où est-il positionné ?",
            f"{filtre.cites} mentionné(s) sans description de la surface réseau — "
            f"{_sources(filtre.fichiers)}",
            False,
        )]
    else:
        questions = [Question(
            "Réseau & flux", "surface",
            "Comment le système est-il exposé sur le réseau (ports, adresses IP "
            "publiques) ? Un filtrage (pare-feu) est-il en place ?",
            "aucun mot-clé réseau ni pare-feu détecté dans les intrants",
            True,
        )]
    return questions


def _questions_exploitation(occ: dict[str, Occurrence]) -> list[Question]:
    """Catégorie « Exploitation & sauvegardes » : un sujet = une question (pas de doublon)."""
    questions = []
    sauvegarde = occ.get("sauvegarde")
    if sauvegarde:
        questions.append(Question(
            "Exploitation & sauvegardes", "sauvegarde",
            "Les sauvegardes sont-elles testées et hors-site ? "
            "Quelle est la fréquence et le délai de restauration ?",
            f"{sauvegarde.cites} mentionné(s) : préciser tests, hors-site et délais "
            f"— {_sources(sauvegarde.fichiers)}",
            False,
        ))
    else:
        questions.append(Question(
            "Exploitation & sauvegardes", "sauvegarde",
            "Existe-t-il une procédure de sauvegarde ?",
            "aucun mot-clé « sauvegarde / backup / plan de reprise » détecté dans les intrants",
            True,
        ))
    supervision = occ.get("supervision")
    if supervision:
        questions.append(Question(
            "Exploitation & sauvegardes", "supervision",
            "Les journaux sont-ils centralisés et conservés combien de temps ?",
            f"{supervision.cites} mentionné(s) : préciser la centralisation et la "
            f"conservation — {_sources(supervision.fichiers)}",
            False,
        ))
    else:
        questions.append(Question(
            "Exploitation & sauvegardes", "supervision",
            "Une supervision et des journaux centralisés sont-ils en place ?",
            "aucun mot-clé « monitoring / journal / logs » détecté dans les intrants",
            True,
        ))
    return questions


def _questions_conformite(occ: dict[str, Occurrence]) -> list[Question]:
    """Catégorie « Conformité & données » : RGPD / données personnelles."""
    rgpd, perso = occ.get("rgpd"), occ.get("donnees_perso")
    if rgpd:
        return [Question(
            "Conformité & données", "rgpd",
            "Le registre des traitements, les durées de conservation et le rôle du DPO "
            "sont-ils documentés ?",
            f"{rgpd.cites} mentionné(s) : vérifier le registre et les durées — "
            f"{_sources(rgpd.fichiers)}",
            False,
        )]
    if perso:
        return [Question(
            "Conformité & données", "rgpd",
            "Des traitements de données personnelles sont-ils réalisés ? "
            "Le registre RGPD est-il à jour ?",
            f"{perso.cites} mentionné(s) sans mention RGPD ni DPO — {_sources(perso.fichiers)}",
            False,
        )]
    return [Question(
        "Conformité & données", "rgpd",
        "Le système traite-t-il des données personnelles (RGPD) ?",
        "aucun mot-clé « RGPD / données personnelles » détecté dans les intrants",
        True,
    )]


def generer(documents: list[Document]) -> tuple[Question, ...]:
    """Produit la liste ordonnée des questions automatiques (≤ 1 question par sujet)."""
    occ = {occurrence.clef: occurrence for occurrence in detecter(documents)}
    questions: list[Question] = []
    for fabrique in (_questions_systeme, _questions_acces, _questions_reseau,
                     _questions_exploitation, _questions_conformite):
        questions.extend(fabrique(occ))
    return tuple(questions)


def trou(questions: tuple[Question, ...]) -> tuple[Question, ...]:
    """Sous-ensemble des questions correspondant à un trou de périmètre."""
    return tuple(question for question in questions if question.trou)


# --------------------------------------------------------------------------- rendu

def _document_piege(documents: list[Document]) -> tuple[str, ...]:
    """Noms des documents contenant des passages ressemblant à une instruction."""
    return tuple(sorted(document.nom for document in documents if document.instructions))


def construire_markdown(titre: str, documents: list[Document],
                       questions: tuple[Question, ...]) -> str:
    """Rend `questions-auto.md` (liste à cocher, déterministe)."""
    sources = ", ".join(f"`{document.nom}`" for document in documents) or "aucun"
    lignes = [
        f"# Questions automatiques — {titre} (pré-générées depuis les intrants)",
        "",
        f"> Réponds uniquement aux questions pertinentes ; rien n'est obligatoire. "
        f"Sources : {sources}.",
        "",
        f"**{len(questions)} question(s)** proposée(s) dont **{len(trou(questions))} trou(s)** "
        "de périmètre · génération heuristique déterministe "
        "(`tools/ingest/questions.py`, aucune IA) · **brouillon à valider par l'analyste**.",
        "",
    ]
    for categorie in CATEGORIES:
        du_categorie = tuple(question for question in questions if question.categorie == categorie)
        if not du_categorie:
            continue
        lignes += [f"## Catégorie : {categorie}", ""]
        for question in du_categorie:
            lignes.append(f"- [ ] **{question.texte}** — raison : {question.raison}.")
        lignes.append("")
    if not questions:
        lignes += ["*(Aucune question automatique : les cinq sujets sont couverts par les intrants. "
                   "La validation humaine reste requise.)*", ""]
    pieges = _document_piege(documents)
    if pieges:
        lignes += [
            "---",
            "",
            f"⚠️ *Garde-fou* : {RAPPEL_DONNEES}. {len(pieges)} document(s) "
            f"({', '.join(f'`{nom}`' for nom in pieges)}) contenaient des passages ressemblant à "
            "une instruction : reproduits **verbatim** dans les intrants, **jamais exécutés**, et "
            "exclus de la détection de mots-clés (skill `garde-fous-ia`, LLM01).",
            "",
        ]
    return "\n".join(lignes).rstrip("\n") + "\n"


def detecter_acteurs(documents: list[Document]) -> list[tuple[str, tuple[str, ...], tuple[str, ...]]]:
    """Acteurs mentionnés : (rôle, formes vues dans les intrants, fichiers concernés)."""
    trouves = []
    for role, motif in ACTEURS:
        compilation = re.compile(motif)
        formes: list[str] = []
        fichiers: set[str] = set()
        for document in documents:
            cite = False
            for ligne in lignes_sures(document):
                trouve = compilation.search(normaliser(ligne))
                if trouve:
                    formes.append(trouve.group(0))
                    cite = True
            if cite:
                fichiers.add(document.nom)
        if formes:
            uniques = sorted(set(formes), key=lambda forme: (forme.lower(), forme))
            trouves.append((role, tuple(uniques[:MAX_MOTS_CITES]), tuple(sorted(fichiers))))
    return trouves


def construire_document(nom: str, donnees: str) -> Document:
    """Fabrique un `Document` en repérant les passages ressemblant à une instruction."""
    return Document(
        nom=nom,
        donnees=donnees,
        instructions=tuple(commun.detecter_instructions(donnees)),
    )


# --------------------------------------------------------------------------- API `dict`

# Les deux API partagent le même moteur déterministe : `generer` / `construire_markdown`
# travaillent sur des dataclasses (précis, typé), `generer_questions` /
# `formater_questions` sur des dictionnaires (sérialisable en JSON sans étapeextraire).


def _document_de(intrant: dict) -> Document:
    """Transforme `{"fichier": str, "contenu": str}` en `Document`.

    Le contenu est déjà le texte entre `<<<DONNÉES>>>` et `<<<FIN DONNÉES>>>` : il est
    transmis tel quel, et `commun.detecter_instructions` repère les lignes piégées afin
    qu'elles ne puissent ni déclencher ni orienter une question (garde-fous-ia, LLM01).
    """
    return construire_document(
        nom=str(intrant.get("fichier", "") or "document"),
        donnees=str(intrant.get("contenu", "") or ""),
    )


def _vers_dict(question: Question) -> dict:
    """Transforme une `Question` en `{"categorie", "question", "raison", "sources"}`.

    La trace des fichiers, portée par la `raison` sous forme de citation, est extraite
    dans le champ `sources` (liste de noms de fichiers, triée et sans doublon).
    """
    raison, marqueur, cite = question.raison.partition(MARQUEUR_SOURCE)
    sources = re.findall(r"`([^`]+)`", cite) if marqueur else []
    return {
        "categorie": question.categorie,
        "question": question.texte,
        "raison": raison.strip(),
        "sources": sorted(dict.fromkeys(sources)),
    }


def generer_questions(intrants: list[dict]) -> list[dict]:
    """Questions automatiques déduites des intrants, en dictionnaires.

    `intrants` : liste de `{"fichier": str, "contenu": str}`, le `contenu` étant déjà
    le texte placé entre `<<<DONNÉES>>>` et `<<<FIN DONNÉES>>>` par l'ingestion.

    Renvoie au plus une question par sujet (pas de doublon), ordonnée par catégorie
    puis par ordre d'apparition dans `MOTIFS` : deux appels sur les mêmes intrants
    produisent la même liste. Le texte d'un document n'est jamais recopié dans une
    question — seule la forme du mot-clé et le nom du fichier sont cités.
    """
    documents = [_document_de(intrant) for intrant in intrants or []]
    return [_vers_dict(question) for question in generer(documents)]


def formater_questions(questions: list[dict]) -> str:
    """Rend la liste de questions en markdown à cocher, groupée par catégorie.

    Reprend les questions produites par `generer_questions` (champs `categorie`,
    `question`, `raison`, `sources`) sans les modifier. L'en-tête rappelle les
    fichiers d'origine : union triée des `sources` de toutes les questions.
    """
    questions = list(questions or [])
    sources = sorted({str(nom) for question in questions
                      for nom in question.get("sources") or [] if nom})
    lignes = [
        "# Questions automatiques (pré-générées depuis les intrants)",
        "",
        "> Réponds uniquement aux questions pertinentes. Sources : "
        + (", ".join(sources) if sources else "aucun")
        + ".",
        "",
    ]
    for categorie in CATEGORIES:
        du_categorie = [q for q in questions if q.get("categorie") == categorie]
        if not du_categorie:
            continue
        lignes += [f"## Catégorie : {categorie}", ""]
        for question in du_categorie:
            lignes.append(f"- [ ] **{question['question']}** — raison : {question['raison']}.")
        lignes.append("")
    return "\n".join(lignes).rstrip("\n") + "\n"