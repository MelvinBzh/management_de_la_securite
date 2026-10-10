"""Recherche HORS des documents du client : une information « externe » n'est jamais confondue avec une information fournie.

Règles (les mêmes que pour les documents, en plus strict) :
- ce qui vient d'une page web est rangé avec `origine = 'externe'` et son `url` ; l'analyse de base (dossier de preuves,
  couverture) n'utilise JAMAIS les éléments externes sauf demande explicite (`Index.rechercher(origines=...)`) ;
- une information externe n'est retenue que si (1) l'extrait cité existe MOT POUR MOT dans la page lue (le code le vérifie)
  et (2) les deux vérificateurs indépendants jugent la réponse soutenue par cet extrait ; sinon elle est jetée :
  « sans preuve → inconnu » ;
- elle reste « à valider » : une source générale (norme, guide, avis d'éditeur) ne dit pas ce qui est vrai CHEZ ce client ;
- les requêtes envoyées au moteur sont les questions GÉNÉRIQUES des besoins d'information, jamais un extrait des documents ;
- les adresses lues viennent d'un moteur de recherche : on refuse tout ce qui n'est pas du http(s) public (pas de réseau interne).

Moteur de recherche : une instance SearXNG (`E21_RECHERCHE_URL`, ex. http://192.168.2.10:8080) — non configuré, la
recherche externe est simplement indisponible, rien d'autre ne change. `recherche` et `lire` sont injectables (tests).
"""
from __future__ import annotations

import html
import ipaddress
import json
import os
import re
import socket
import urllib.parse
import urllib.request

from . import couverture, ollama, texte, verification

MODELE = "qwen3.5:9b"
MAX_RESULTATS = 3
LIMITE_PAGE = 120_000
LIMITE_CONSIGNE = 12_000

SCHEMA = {"type": "object", "properties": {"reponse": {"type": "string"}, "extrait": {"type": "string"}},
          "required": ["reponse", "extrait"]}
CONSIGNE = (
    "QUESTION : {question}\n\nPAGE WEB ({url}) :\n{page}\n\nSi la page répond à la question, donne reponse (30 mots maximum, tirée "
    "UNIQUEMENT de la page) et extrait = la PHRASE de la page qui la prouve, copiée MOT POUR MOT (40 mots maximum). Si la page "
    "ne répond pas, laisse les deux champs vides. N'ajoute aucune connaissance extérieure à la page."
)


def serveur_recherche() -> str:
    """Adresse du moteur de recherche (SearXNG), ou « » s'il n'est pas configuré."""
    return os.environ.get("E21_RECHERCHE_URL", "").strip().rstrip("/")


def url_autorisee(url: str) -> bool:
    """http(s) vers une adresse PUBLIQUE uniquement (protège contre les adresses internes renvoyées par un moteur)."""
    analyse = urllib.parse.urlparse(url)
    if analyse.scheme not in ("http", "https") or not analyse.hostname:
        return False
    try:
        adresses = {info[4][0] for info in socket.getaddrinfo(analyse.hostname, None)}
    except OSError:
        return False
    for adresse in adresses:
        ip = ipaddress.ip_address(adresse.split("%")[0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            return False
    return bool(adresses)


def chercher_searxng(question: str, *, base: str | None = None, maximum: int = MAX_RESULTATS) -> list[tuple[str, str]]:
    """`[(url, titre)]` depuis l'API JSON de SearXNG."""
    base = base or serveur_recherche()
    if not base:
        raise RuntimeError("Recherche web non configurée (variable E21_RECHERCHE_URL).")
    adresse = base + "/search?" + urllib.parse.urlencode({"q": question, "format": "json", "language": "fr"})
    with urllib.request.urlopen(adresse, timeout=20) as reponse:
        donnees = json.load(reponse)
    return [(r["url"], r.get("title", "")) for r in donnees.get("results", [])[:maximum] if r.get("url")]


def texte_de_page(source: str) -> str:
    """Texte lisible d'une page HTML (scripts et styles retirés, entités décodées)."""
    sans = re.sub(r"(?is)<(script|style|noscript)[^>]*>.*?</\1>", " ", source)
    sans = re.sub(r"(?s)<[^>]+>", " ", sans)
    return " ".join(html.unescape(sans).split())


def lire_page(url: str) -> str:
    """Texte d'une page publique (refuse toute adresse non publique)."""
    if not url_autorisee(url):
        raise ValueError("adresse refusée (non publique ou schéma inattendu)")
    requete = urllib.request.Request(url, headers={"User-Agent": "E21-analyse-risques/1.0"})
    with urllib.request.urlopen(requete, timeout=20) as reponse:
        type_ = reponse.headers.get("Content-Type", "")
        if "html" not in type_ and "text" not in type_:
            raise ValueError("type de contenu non pris en charge : " + type_)
        brut = reponse.read(LIMITE_PAGE * 4).decode("utf-8", errors="replace")
    return texte_de_page(brut)[:LIMITE_PAGE]


def _extraire_ollama(question: str, url: str, page: str) -> dict:
    return ollama.discuter_json(MODELE, CONSIGNE.format(question=question, url=url, page=page[:LIMITE_CONSIGNE]), SCHEMA,
                                contexte=8192, max_sortie=300)


def retenir(question: str, url: str, page: str, *, extraire=_extraire_ollama, verificateurs=None) -> dict | None:
    """`{reponse, extrait}` si l'information externe passe les DEUX contrôles (extrait exact + deux vérificateurs), sinon None."""
    brut = extraire(question, url, page)
    reponse, extrait = str(brut.get("reponse", "")).strip(), str(brut.get("extrait", "")).strip()
    if not reponse or not extrait:
        return None
    if not texte.contient(extrait, texte.normaliser(page)):
        return None  # extrait inventé : jamais retenu
    if verification.verifier(extrait, reponse, verificateurs=verificateurs) != verification.SOUTENU:
        return None
    return {"reponse": reponse, "extrait": extrait}


def enrichir(index, besoin: couverture.Besoin, *, recherche=chercher_searxng, lire=lire_page, vecteurs=ollama.vecteurs,
             extraire=_extraire_ollama, verificateurs=None) -> list[dict]:
    """Cherche hors des documents la réponse à UN besoin ; range ce qui est retenu (origine « externe »). Renvoie les trouvailles."""
    trouvees = []
    deja = {l[0] for l in index.base.execute("SELECT url FROM elements WHERE origine = 'externe' AND libelle LIKE ?", (f"[{besoin.id}]%",))}
    for url, titre in recherche(besoin.question):
        if url in deja or not url_autorisee(url):
            continue
        try:
            page = lire(url)
            retenu = retenir(besoin.question, url, page, extraire=extraire, verificateurs=verificateurs)
        except Exception:  # noqa: BLE001 — une page illisible ne bloque pas les autres
            continue
        if not retenu:
            continue
        libelle = f"[{besoin.id}] {retenu['reponse']}"
        vec = vecteurs([f"{libelle}. {retenu['extrait']}"])[0]
        host = urllib.parse.urlparse(url).hostname or url
        index.ajouter_element("externe", host, libelle, retenu["extrait"], True, vec, origine="externe", url=url)
        trouvees.append({"besoin": besoin.id, "url": url, "titre": titre, "reponse": retenu["reponse"], "extrait": retenu["extrait"]})
    index.base.commit()
    return trouvees


def enrichir_inconnus(index, *, progression=None, **moteurs) -> list[dict]:
    """Recherche externe pour chaque besoin resté inconnu ou partiel dans la couverture déjà calculée."""
    ouverts = [d for d in index.couvertures() if d["statut"] in (couverture.INCONNU, couverture.PARTIEL)]
    tout = []
    for i, d in enumerate(ouverts, start=1):
        if progression:
            progression("externe", i, len(ouverts), d["question"])
        besoin = couverture.Besoin(d["besoin"], d.get("theme", ""), d["question"])
        tout += enrichir(index, besoin, **moteurs)
    return tout


def externes(index) -> list[dict]:
    """Éléments externes rangés dans l'index (pour l'affichage)."""
    cles = ("libelle", "extrait", "url", "doc")
    return [dict(zip(cles, l)) for l in index.base.execute(
        "SELECT libelle, extrait, url, doc FROM elements WHERE origine = 'externe' ORDER BY id")]


def rapport_markdown(lignes: list[dict]) -> str:
    """Section « Informations externes » du livrable : origine et source toujours visibles, toujours à valider."""
    if not lignes:
        return ""
    sortie = ["", "## Informations trouvées hors des documents (à valider)", "",
              "> Ces informations viennent du web, **pas des documents de l'entreprise**. Elles décrivent une règle ou une "
              "pratique générale ; elles ne disent pas ce qui est vrai chez ce client. Chacune cite une phrase exacte de sa source.", ""]
    for l in lignes:
        sortie.append(f"- {l['libelle']}  \n  source externe : {l['url']} — « {l['extrait'][:240]} »")
    return "\n".join(sortie) + "\n"
