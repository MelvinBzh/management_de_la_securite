# -*- coding: utf-8 -*-
"""Interface web locale E21 — wrapper de présentation du POC piloté par consignes.

Lancement :
    make web
    # ou : python3 -m streamlit run web/app.py

L'application ingère des documents (données non fiables), prépare un brouillon de
description, lit la bibliothèque des analyses et exporte les rapports. Elle peut
aussi lancer LOCALEMENT la chaîne d'agents via opencode, avec la commande fixe de
`web/lib.construire_commande` (démarrage et arrêt : `web/run_agent.py`) : aucun
contenu d'intrant ne passe sur la ligne de commande, les intrants restent des
données jamais exécutées. Écriture bornée à `analyses/**`, journaux de chaîne
compris dans `analyses/**/intrants/` (dossier gitignoré) ; les exports partent dans
un dossier temporaire.

L'onglet « Studio E21 » édite la **source de vérité** des agents et des skills : la
base locale `stockage_local/e21.sqlite3` (hors git), alimentée par `tools/studio/db.py`.
Chaque modification est écrite en base PUIS déployée vers `.opencode/` (copie que lit
opencode) ; son versionnement git passe par une branche (`studio-<HHMMSS>`) et une
pull request — jamais de push direct sur `main`. Le bloc d'état Ollama est une sonde
locale, courte et non bloquante ; le versionnement n'exécute que des commandes FIXES,
en liste d'arguments et sans shell.
"""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from web import lib  # noqa: E402  (chemin du dépôt garanti ci-dessus)
from web import modeles_ollama as conseils_ollama  # alias : app.py a déjà une fonction modeles_ollama()
from web import reglages  # noqa: E402  (réglages modèles, stockage local hors git)
from web import run_agent  # noqa: E402  (lancement réel de la chaîne, hors UI)
from tools.export import export as export_tool  # noqa: E402
from tools.ingest import preparer  # noqa: E402
from tools.ingest.ingest import nom_sur, parse_file  # noqa: E402
from tools.ingest.parsers import commun  # noqa: E402
from tools.studio import db  # noqa: E402  (base locale, source de vérité du studio)

TITRE_PAGE = "E21 — Analyses de risques"

st.set_page_config(page_title=TITRE_PAGE, layout="wide")

CSS = """
<style>
  .block-container { padding-top: 2.2rem; max-width: 1400px; }
  h1, h2, h3 { letter-spacing: -0.01em; }
  .e21-note {
      border-left: 3px solid #d97706; background-color: #fffbeb;
      padding: 0.6rem 0.9rem; border-radius: 0.3rem; font-size: 0.92rem;
      color: #78350f;
  }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def analyser_document(octets: bytes, nom: str) -> dict:
    """Analyse un document téléversé (résultat mis en cache par contenu + nom)."""
    suffixe = Path(nom).suffix or ".bin"
    with tempfile.TemporaryDirectory() as tmp:
        chemin = Path(tmp) / f"{Path(nom).stem}{suffixe}"
        chemin.write_bytes(octets)
        return parse_file(chemin)


def memoiser_documents(fichiers) -> list[dict]:
    """Analyse les fichiers téléversés et les garde en session (« intrants »)."""
    documents = []
    for fichier in fichiers:
        resultat = analyser_document(fichier.getvalue(), fichier.name)
        documents.append({
            "nom": fichier.name,
            "markdown": resultat["markdown"],
            "meta": resultat["meta"],
        })
    valides = [doc for doc in documents if doc["meta"].get("ok")]
    st.session_state["documents"] = valides
    return documents


def chemins_de_televersement(elements, dossier_tmp: Path) -> list[Path]:
    """Transforme la valeur d'un `st.file_uploader` en chemins RÉELS sur disque.

    Streamlit renvoie des `UploadedFile` **en mémoire**, sans chemin : leurs
    octets sont donc écrits dans `dossier_tmp` — un dossier temporaire — sous un
    nom assaini par `nom_sur` (aucun séparateur de chemin, aucun `..` possible,
    donc rien ne peut être écrit hors du dossier temporaire). Un élément déjà un
    chemin (`str` ou `Path`, dossier récursif compris) est conservé tel quel.

    Deux fichiers homonymes ne s'écrasent pas : le second gagne un suffixe `-2`,
    `-3`… Un élément sans octets (objet inconnu) est ignoré silencieusement —
    garde-fou : l'interface ne doit pas planter sur une entrée parasite.
    """
    chemins: list[Path] = []
    utilises: set[str] = set()
    for element in elements or []:
        # Test de type AVANT tout `getattr` : un `Path` possède lui aussi un
        # attribut `name`, qui ne donnerait que son nom de fichier (le dossier
        # parent serait perdu et le parcours récursif deviendrait impossible).
        if isinstance(element, (str, Path)):
            chemins.append(Path(element))
            continue
        nom = nom_sur(Path(getattr(element, "name", "") or "").name or "document")
        base, index = nom, 2
        while base in utilises:
            base, index = f"{nom}-{index}", index + 1
        utilises.add(base)
        if not hasattr(element, "getvalue"):
            continue
        chemin = dossier_tmp / base
        chemin.write_bytes(element.getvalue())
        chemins.append(chemin)
    return chemins


# --------------------------------------------- page 5 : studio E21 (constantes, outils)
# Bloc Ollama : sonde STRICTEMENT locale (`localhost`) et courte — aucune donnée ne sort
# de la machine, le délai d'une seconde et l'absorption de toute erreur garantissent un
# bloc purement informatif qui ne doit ni ralentir ni faire échouer la page.
URL_OLLAMA = "http://localhost:11434/api/tags"
DELAI_OLLAMA = 1
MAX_MODELES_AFFICHES = 6

# Versionnement git du studio : uniquement des commandes FIXES, en liste d'arguments.
PREFIXE_BRANCHE_STUDIO = "studio-"
CHEMINS_VERSIONNES = (".opencode", "tools/studio")
MSG_COMMIT_STUDIO = "studio: mise à jour agents et skills depuis l'interface"
TITRE_PR_STUDIO = "studio: mise à jour agents et skills"
DELAI_GIT = 120


def modeles_ollama() -> list[str]:
    """Noms des modèles Ollama locaux, ou [] si le service ne répond pas.

    Sonde `/api/tags` avec un délai d'une seconde. Toute erreur (réseau, HTTP, JSON)
    est avalée : ce bloc est informatif, jamais bloquant pour la page.
    """
    try:
        with urllib.request.urlopen(URL_OLLAMA, timeout=DELAI_OLLAMA) as reponse:
            document = json.loads(reponse.read().decode("utf-8", "replace"))
    except Exception:  # garde-fou : un bloc informatif ne doit jamais casser la page
        return []
    modeles = document.get("models") if isinstance(document, dict) else None
    if not isinstance(modeles, list):
        return []
    return [
        nom for nom in
        (str(modele.get("name", "")) for modele in modeles if isinstance(modele, dict))
        if nom
    ]


def modele_de_agent(contenu: str) -> str:
    """Modèle déclaré par un agent dans son frontmatter, ou « (modèle par défaut) ».

    Lecture seule : le champ `model:` des **10 premières lignes** du contenu (le
    frontmatter est en tête de fichier). Aucune valeur n'est exécutée ni interprétée,
    c'est un simple relevé pour affichage. La signature du modèle est validée par
    `reglages.modele_valide` : un contenu piégé ne peut pas être présenté comme un
    modèle configured.
    """
    for ligne in (contenu or "").splitlines()[:10]:
        if not ligne.lower().startswith("model:"):
            continue
        valeur = ligne.split(":", 1)[1].strip().strip("\"'")
        return valeur if reglages.modele_valide(valeur) else "(modèle par défaut)"
    return "(modèle par défaut)"


def executer_commande(argv: list[str]) -> tuple[int, str]:
    """Exécute une commande par LISTE d'arguments, jamais via un shell (`shell=False`).

    Renvoie `(code_retour, sortie)`. Exécutable absent (`gh` non installé), refus ou
    délai dépassé sont convertis en code 1 et un message lisible : l'appelant décide
    de l'affichage, la page ne casse jamais.
    """
    try:
        fini = subprocess.run(
            argv,
            cwd=str(RACINE),
            capture_output=True,
            text=True,
            timeout=DELAI_GIT,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 1, f"exécution impossible — {exc}"
    return fini.returncode, ((fini.stdout or "") + (fini.stderr or "")).strip()


def url_pull_request(sortie: str) -> str:
    """URL de pull request annoncée par `gh pr create` ("" si elle n'y figure pas)."""
    for ligne in sortie.splitlines():
        propre = ligne.strip()
        if propre.startswith("https://"):
            return propre
    return ""


def versionner_sur_git() -> dict:
    """Branche + commit + push + pull request pour les écritures du studio.

    Ordre fixe : `git checkout -b studio-<HHMMSS>`, `git add .opencode tools/studio`,
    `git diff --cached --quiet`, `git commit`, `git push -u origin <branche>` puis
    `gh pr create`. Toutes les commandes passent par `executer_commande` (liste
    d'arguments, **jamais** de shell) et les chemins comme les messages sont FIXES :
    aucun contenu d'agent ou de skill — donc aucune consigne malveillante — n'entre
    dans une ligne de commande ; seul le nom de branche horodaté est calculé ici.

    S'arrête au premier échec (une étape non franchie ne déclare pas la page « verte »)
    et renvoie toujours toutes les clés : `branche`, `etapes`, `rien_a_committer`,
    `pr_url`, `pr_sortie` et `echec` (message d'erreur, vide si tout a réussi).
    """
    branche = PREFIXE_BRANCHE_STUDIO + time.strftime("%H%M%S")
    etapes: list[dict] = []
    bilan: dict = {
        "branche": branche,
        "etapes": etapes,
        "rien_a_committer": False,
        "pr_url": "",
        "pr_sortie": "",
        "echec": "",
    }

    code, sortie = executer_commande(["git", "checkout", "-b", branche])
    if code == 0:
        etapes.append({"etape": f"branche {branche} créée", "code": 0, "sortie": ""})
    else:
        # La branche peut déjà exister (opération relancée) : on vérifie qu'on est dessus
        # avant d'écrire, plutôt que de supposer le succès.
        code_courant, sortie_courante = executer_commande(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        )
        if code_courant != 0 or branche not in sortie_courante:
            bilan["echec"] = f"branche {branche} indisponible — {sortie}"
            return bilan
        etapes.append({"etape": f"branche {branche} déjà active", "code": 0, "sortie": ""})

    code, sortie = executer_commande(["git", "add", *CHEMINS_VERSIONNES])
    if code != 0:
        bilan["echec"] = f"git add {' '.join(CHEMINS_VERSIONNES)} a échoué — {sortie}"
        return bilan
    etapes.append({
        "etape": f"index : {' '.join(CHEMINS_VERSIONNES)}",
        "code": 0,
        "sortie": "",
    })

    # `--quiet` : code 0 = rien d'indexé, 1 = différences indexées. Un autre code
    # (dépôt absent…) est traité comme « à committer » : le commit échouera et le
    # message du commit sera alors affiché tel quel.
    code, _ = executer_commande(["git", "diff", "--cached", "--quiet"])
    if code == 0:
        bilan["rien_a_committer"] = True
        etapes.append({"etape": "aucune modification indexée", "code": 0, "sortie": ""})
        return bilan

    code, sortie = executer_commande(["git", "commit", "-m", MSG_COMMIT_STUDIO])
    if code != 0:
        bilan["echec"] = f"commit refusé — {sortie}"
        return bilan
    etapes.append({"etape": f"commit « {MSG_COMMIT_STUDIO} »", "code": 0, "sortie": sortie})

    code, sortie = executer_commande(["git", "push", "-u", "origin", branche])
    if code != 0:
        bilan["echec"] = f"push de {branche} refusé — {sortie}"
        return bilan
    etapes.append({"etape": f"branche {branche} poussée sur origin", "code": 0, "sortie": ""})

    corps = (
        "Modifié depuis l'interface Studio (source de vérité : base locale). "
        f"Branche : {branche}."
    )
    code, sortie = executer_commande(
        ["gh", "pr", "create", "--title", TITRE_PR_STUDIO, "--body", corps]
    )
    etapes.append({
        "etape": "ouverture de la pull request (gh pr create)",
        "code": code,
        "sortie": sortie,
    })
    bilan["pr_sortie"] = sortie
    if code != 0:
        bilan["echec"] = f"gh pr create a échoué — {sortie}"
        return bilan
    bilan["pr_url"] = url_pull_request(sortie)
    return bilan


def enregistrer_entite(type_: str, nom: str, contenu: str) -> bool:
    """Enregistre l'entité en base (source de vérité) puis la déploie dans `.opencode/`.

    Le déploiement est toujours exécuté APRÈS l'écriture en base : la copie lue par
    opencode ne peut jamais être en avance sur la source de vérité. Renvoie `True` si
    l'écriture a réussi (message d'erreur déjà affiché sinon).
    """
    try:
        db.sauvegarder(type_, nom, contenu)
        res = db.deployer_vers_opencode()
    except ValueError as exc:
        st.error(f"Enregistrement refusé : {exc}")
        return False
    except sqlite3.Error as exc:
        st.error(f"Base locale inaccessible : {exc}")
        return False
    st.session_state["studio_dernier_deploiement"] = res
    st.success(
        f"Enregistré — {res['ecrits']} fichier(s) déployé(s) dans .opencode/, "
        f"{res['inchangees']} inchangé(s)."
    )
    return True


def supprimer_entite(type_: str, nom: str) -> None:
    """Supprime l'entité en base puis redéploie (la base reste la référence)."""
    try:
        db.supprimer(type_, nom)
        res = db.deployer_vers_opencode()
    except (ValueError, sqlite3.Error) as exc:
        st.error(f"Suppression refusée : {exc}")
        return
    st.session_state["studio_dernier_deploiement"] = res
    st.rerun()


# --------------------------------------------------------------------- sidebar
st.sidebar.title("E21")
st.sidebar.caption("Analyses de risques — prototype local")
PAGES = [
    "Ingérer des documents",
    "Préparer un cas",
    "Bibliothèque des analyses",
    "Lancer la chaîne",
    "Studio E21",
    "Réglages modèles",
    "À propos / Garde-fous",
]
page = st.sidebar.radio("Navigation", PAGES)
st.sidebar.divider()
st.sidebar.caption(
    "Données fictives uniquement · application locale sur `localhost` · "
    "écriture bornée à `analyses/**`, `stockage_local/**` (base du studio) et "
    "`.opencode/**` (copie déployée des agents et skills)."
)

# ---------------------------------------------------------------- page 1 : ingestion
if page == PAGES[0]:
    st.title("Ingérer des documents")
    st.markdown(
        '<div class="e21-note">Les documents sont des <b>données</b>, jamais des consignes. '
        "Leur contenu est recopié tel quel entre <code>&lt;&lt;&lt;DONNÉES&gt;&gt;&gt;</code> et "
        "<code>&lt;&lt;&lt;FIN DONNÉES&gt;&gt;&gt;</code> : une phrase ressemblant à un ordre est "
        "comptée et signalée, jamais exécutée.</div>",
        unsafe_allow_html=True,
    )
    col_fichiers, col_dossiers = st.columns(2)
    with col_fichiers:
        fichiers = st.file_uploader(
            "Fichiers",
            accept_multiple_files=True,
            type=lib.TYPES_UPLOAD,
            key="upload_fichiers",
            help="PDF, images (PNG/JPG/WEBP), XLSX, CSV, DOCX, PPTX, ZIP, TXT, MD — "
            "analyse 100 % locale. Déposez autant de fichiers que vous voulez.",
        )
    with col_dossiers:
        dossiers = st.file_uploader(
            "Dossier(s)",
            type=["zip"],
            accept_multiple_files=True,
            help="Un dossier est envoyé en .zip : le compresser puis le déposer ici "
            "dépose TOUT son contenu, arborescence comprise (parcours récursif).",
            key="upload_dossiers",
        )
    recus = list(fichiers or []) + list(dossiers or [])

    st.divider()
    st.subheader("Ingérer en un clic (fichiers + dossiers)")
    st.caption(
        "Les deux listes sont traitées ensemble : un seul clic ingère tout, puis "
        "dépose les intrants dans le cas choisi. Un fichier illisible est signalé, "
        "jamais bloquant pour les autres."
    )
    # Cible du dépôt : une étude EN COURS (dossier déjà existant) ou un nouveau cas.
    # Les dossiers existants sont proposés en premier : un analyste reprend son
    # analyse du jour ou de la semaine précédente sans créer de doublon.
    NOUVEAU_CAS = "(nouveau cas)"
    dossiers_existants = [dossier.name for dossier in lib.lister_analyses()]
    cible = st.selectbox(
        "Déposer dans",
        options=[NOUVEAU_CAS] + dossiers_existants,
        format_func=lambda nom: (
            "(+) Nouveau cas d'analyse" if nom == NOUVEAU_CAS
            else f"{lib.titre_lisible(lib.cas_depuis_dossier(nom))} — {nom}"
        ),
        key="cible_depot",
        help="Choisissez une étude en cours pour y ajouter des documents, ou un nouveau cas.",
    )
    jour_lot: date | None = None  # None = cas créé aujourd'hui ; sinon, date d'origine
    if cible == NOUVEAU_CAS:
        nom_cas_lot = st.text_input(
            "Nom du cas",
            placeholder="ex. boutique-en-ligne",
            key="nom_cas_lot",
            help="Minuscules, chiffres et tirets — le nom est assaini puis refusé (fail "
            "closed) s'il contient un séparateur de chemin ou un marqueur d'instruction.",
        )
        dossier_cible = lib.dossier_cas(nom_cas_lot).name if nom_cas_lot.strip() else ""
    else:
        nom_cas_lot = lib.cas_depuis_dossier(cible)
        dossier_cible = cible
        st.caption(f"Documents ajoutés à l'étude en cours : `analyses/{cible}/intrants/`")
    if st.button(
        "Ingérer en un clic (fichiers + dossiers)",
        type="primary",
        key="ingerer_lot",
        disabled=not recus,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            chemins = chemins_de_televersement(recus, Path(tmp))
            with st.spinner("Ingestion du lot en cours…"):
                try:
                    if cible != NOUVEAU_CAS:
                        jour_lot = lib.jour_depuis_dossier(cible)
                    copies, messages = lib.ingérer_en_lot(chemins, nom_cas_lot, jour_lot)
                except ValueError as exc:
                    copies, messages = [], []
                    st.error(f"Dépôt refusé : {exc}")
        if not messages and not copies:
            st.warning("Rien à ingérer : déposez au moins un fichier ou un dossier.")
        for ligne in messages:
            if " : ignoré (" in ligne:
                st.warning(ligne)
            else:
                st.success(ligne)
        if copies:
            st.success(
                f"{len(copies)} fichier(s) copié(s) dans "
                f"`analyses/{dossier_cible}/intrants/` "
                "(un `.md` + un `.meta.json` par intrant)."
            )

    st.subheader("Documents déposés")
    if not recus:
        # Source de vérité = le téléverseur : plus aucun fichier déposé => plus
        # aucun document en session (sinon un document retiré de l'uploader
        # continuerait d'apparaître dans « Préparer un cas »).
        st.session_state["documents"] = []
        st.info(
            "Aucun document pour l'instant. Les documents ingérés ici deviennent des "
            "« intrants » pour l'étape 1 (préparation d'un cas), onglet suivant."
        )
    else:
        documents = memoiser_documents(recus)
        st.caption(f"{len(documents)} document(s) reçu(s), analyse locale et immédiate.")
        for document in documents:
            meta = document["meta"]
            st.markdown(f"#### {document['nom']}")
            if meta.get("ok"):
                details = f"type {meta.get('type') or 'inconnu'}"
                if "pages" in meta:
                    details += f" · {meta['pages']} page(s)"
                if meta.get("tableaux"):
                    details += f" · {meta['tableaux']} tableau(x)"
                if "ocr" in meta:
                    details += f" · OCR {meta['ocr']}"
                details += f" · {meta.get('taille_octets')} octets"
                st.caption(details)
            else:
                st.error(meta.get("message", "Extraction impossible."))
            if meta.get("instructions_detectees"):
                st.warning(
                    f"{meta['instructions_detectees']} passage(s) ressemblant à une instruction "
                    "détecté(s) : reproduits verbatim comme donnée, jamais exécutés."
                )
            for avertissement in meta.get("avertissements", []):
                st.warning(avertissement)
            with st.container(height=420, border=True):
                st.markdown(document["markdown"])
            base = Path(document["nom"]).stem
            col_md, col_meta = st.columns(2)
            col_md.download_button(
                "Télécharger le .md", document["markdown"].encode("utf-8"),
                file_name=f"{base}.md", mime="text/markdown", key=f"dl_{base}_md",
            )
            col_meta.download_button(
                "Télécharger le .meta.json",
                lib.meta_en_json(meta).encode("utf-8"),
                file_name=f"{base}.meta.json", mime="application/json",
                key=f"dl_{base}_meta",
            )

# ------------------------------------------------------------- page 2 : préparation
elif page == PAGES[1]:
    st.title("Préparer un cas")
    st.markdown(
        "Étape 1 de la chaîne : les intrants ingérés sont copiés dans "
        "`analyses/<AAAA-MM-JJ>_<cas>/intrants/`, puis l'outil en tire un "
        "**brouillon** de description et une liste de questions à l'analyste."
    )
    documents = st.session_state.get("documents") or []
    with st.form("form_preparation"):
        nom_saisi = st.text_input(
            "Nom du cas",
            placeholder="ex. boutique-en-ligne",
            help="Minuscules, chiffres et tirets — le dossier sera analyses/<date>_<nom>.",
        )
        selection = []
        if documents:
            tailles = {doc["nom"]: len(doc["markdown"]) for doc in documents}
            selection = st.multiselect(
                "Documents ingérés à utiliser comme intrants",
                options=[doc["nom"] for doc in documents],
                default=[doc["nom"] for doc in documents],
                format_func=lambda nom: f"{nom} ({tailles[nom]} car.)",
            )
        lancer = st.form_submit_button("Préparer le cas", type="primary")
    if not lancer:
        if not documents:
            st.info(
                "Aucun document ingéré dans cette session : ingérez d'abord des documents "
                "(onglet « Ingérer des documents »). Un nom de cas reste saisissable pour "
                "préparer un cas sans nouvel upload."
            )
        st.stop()
    try:
        cas = lib.nom_cas_sur(nom_saisi)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()
    if not selection:
        st.error("Aucun document sélectionné : cochez au moins un intrant, ou ingérez des documents.")
        st.stop()

    dossier = lib.dossier_cas(cas)
    titre = lib.titre_lisible(cas)
    try:
        with st.spinner("Copie des intrants et rédaction du brouillon…"):
            with tempfile.TemporaryDirectory() as tmp:
                for nom in selection:
                    document = next(d for d in documents if d["nom"] == nom)
                    base = Path(nom).stem
                    (Path(tmp) / f"{base}.md").write_text(document["markdown"], encoding="utf-8")
                    (Path(tmp) / f"{base}.meta.json").write_text(
                        lib.meta_en_json(document["meta"]), encoding="utf-8"
                    )
                copies = lib.copier_intrants(sorted(Path(tmp).iterdir()), cas)
            # Réutilisation des fonctions internes de `tools/ingest/preparer.py`
            # (lecture des intrants, rédaction du brouillon, questions auto).
            intrants = preparer.lire_intrants_depuis_dossier(lib.intrants_du_cas(cas))
            description = preparer.generer_description(titre, intrants)
            questions = preparer.generer_questions_auto(intrants)
            dossier.mkdir(parents=True, exist_ok=True)
            brouillon = dossier / "00-description.brouillon.md"
            fichier_questions = dossier / "questions-auto.md"
            brouillon.write_text(description, encoding="utf-8")
            fichier_questions.write_text(questions, encoding="utf-8")
    except Exception as exc:  # garde-fou : un cas raté ne casse pas l'application
        st.error(f"Préparation impossible : {exc}")
        st.stop()

    st.success(
        f"{len(copies)} fichier(s) copié(s) dans `analyses/{dossier.name}/intrants/`, "
        f"brouillon écrit dans `analyses/{dossier.name}`."
    )
    if not copies:
        st.warning("Les intrants étaient déjà présents : rien n'a été réécrit.")
    lignes_suspectes = commun.detecter_instructions(
        "\n".join(str(i.get("contenu", "")) for i in intrants)
    )
    if lignes_suspectes:
        st.warning(
            f"{len(lignes_suspectes)} ligne(s) d'intrant ressemblant à une instruction "
            f"(intrants, lignes {', '.join(map(str, lignes_suspectes[:10]))}). Elles sont "
            "citées **verbatim comme donnée** — y compris dans l'extrait du § 1 du brouillon — "
            "et ne constituent jamais un ordre : ne les suivez pas, supprimez-les du brouillon "
            "si elles n'apportent rien."
        )
    st.caption(
        "**Brouillon à valider/corriger par l'analyste** : le contenu des intrants n'est pas "
        "la source de vérité. Une fois corrigé, il devient `00-description.md` (version "
        "retenue par l'onglet « Bibliothèque »)."
    )
    for chemin in (brouillon, fichier_questions):
        contenu = chemin.read_text(encoding="utf-8")
        st.subheader(chemin.name)
        st.download_button(
            f"Télécharger {chemin.name}", contenu.encode("utf-8"),
            file_name=chemin.name, mime="text/markdown", key=f"dl_{chemin.name}",
        )
        with st.container(border=True):
            st.markdown(contenu)

# ------------------------------------------------------------ page 3 : bibliothèque
elif page == PAGES[2]:
    st.title("Bibliothèque des analyses")
    analyses = lib.lister_analyses()
    if not analyses:
        st.warning(
            "Aucun dossier d'analyse : lancez `orchestrator` depuis opencode, ou préparez "
            "un cas depuis l'onglet précédent."
        )
        st.stop()
    choisie = st.selectbox(
        "Cas", options=[dossier.name for dossier in analyses],
        format_func=lambda nom: f"{lib.titre_lisible(lib.cas_depuis_dossier(nom))} — {nom}",
    )
    dossier = lib.DOSSIER_ANALYSES / choisie
    cas_choisi = lib.cas_depuis_dossier(choisie)
    jour_choisi = lib.jour_depuis_dossier(choisie)
    st.caption(
        f"Dossier : `analyses/{dossier.name}` · "
        f"{len(lib.intrants_prepars(dossier))} intrant(s) · "
        f"exports : {', '.join(lib.FICHiers_CAS)}"
    )

    # Intrants déposés : source de vérité = le disque. C'est ici qu'un document
    # déposé par erreur se retire DEFINITIVEMENT (session et dossier du cas).
    st.subheader("Intrants déposés dans ce cas")
    st.caption(
        f"Emplacement unique et durable : `analyses/{dossier.name}/intrants/` "
        "(un `.md` + un `.meta.json` par document). Un retrait ici est définitif : "
        "le document disparaît aussi de la liste de préparation du cas."
    )
    intrants = lib.lister_intrants(cas_choisi, jour_choisi)
    if not intrants:
        st.info("Aucun intrant déposé dans ce cas.")
    for intrant in intrants:
        colonne_nom, colonne_action = st.columns([5, 2])
        with colonne_nom:
            details = f"{intrant['taille']} car."
            if not intrant["meta_ok"]:
                details += " · métadonnées (.meta.json) absentes"
            st.markdown(f"**{intrant['base']}** — {details}")
        with colonne_action:
            if st.button("Supprimer", key=f"suppr_{intrant['base']}", type="secondary"):
                st.session_state[f"conf_suppr_{intrant['base']}"] = intrant["base"]
        if st.session_state.get(f"conf_suppr_{intrant['base']}") == intrant["base"]:
            st.warning(
                f"Supprimer définitivement `{intrant['base']}` de ce cas ? "
                "Le document ne sera plus disponible pour la chaîne."
            )
            col_oui, col_non = st.columns(2)
            if col_oui.button("Oui, supprimer", key=f"oui_{intrant['base']}", type="primary"):
                # Les fichiers DÉJÀ générés qui citent ce document sont relevés AVANT
                # la suppression : ils sont signalés, jamais effacés (du travail
                # humain), et la préparation peut être relancée pour les régénérer.
                try:
                    residus = lib.artefacts_citant(cas_choisi, intrant["base"], jour_choisi)
                except ValueError as exc:
                    residus = []
                    st.error(str(exc))
                supprimes = lib.supprimer_intrant(cas_choisi, intrant["base"], jour_choisi)
                st.session_state.pop(f"conf_suppr_{intrant['base']}", None)
                if supprimes:
                    st.success(f"Supprimé : {', '.join(Path(p).name for p in supprimes)}")
                    if residus:
                        st.warning(
                            f"**{len(residus)} fichier(s) déjà produit(s) citent encore "
                            f"« {intrant['base']} »** — ils sont **conservés** (ils "
                            "représentent du travail humain) mais ne sont plus à jour :"
                        )
                        for nom_fichier in residus:
                            st.markdown(f"- `{nom_fichier}`")
                        st.info(
                            "Pour les remettre à jour : relancez la préparation du cas "
                            "(« Préparer un cas »), puis relancez l'étape concernée de la "
                            "chaîne. Aucun fichier n'a été effacé automatiquement."
                        )
                else:
                    st.error("Aucun fichier supprimé (intrant déjà absent).")
                st.rerun()
            if col_non.button("Annuler", key=f"non_{intrant['base']}"):
                st.session_state.pop(f"conf_suppr_{intrant['base']}", None)
                st.rerun()


    # Avancement de la chaîne E21 dans ce dossier : compte global + livrables
    # manquants de la première étape non terminée (source de vérité = dossiers).
    etapes = lib.avancement_chaine(dossier)
    if not etapes:
        st.caption("Étapes E21 : aucune étape réalisée pour ce dossier.")
    else:
        terminees = sum(1 for entree in etapes if entree["terminee"])
        reste = next((entree for entree in etapes if not entree["terminee"]), None)
        if reste is None:
            etat = (
                f"Étapes E21 : ✓ {terminees}/{len(etapes)} · chaîne complète — "
                "il reste à faire valider chaque risque par l'analyste (`valide_par`)."
            )
        else:
            manquants = [
                nom for nom in reste["fichiers"] if not (dossier / nom).is_file()
            ] or list(reste["fichiers"])
            etat = (
                f"Étapes E21 : ✓ {terminees}/{len(etapes)} · Où vous en êtes : restent "
                f"les livrables de l'étape « {reste['etape']} » ({', '.join(manquants)}) "
                "— lancez ou relancez la chaîne depuis l'onglet « Lancer la chaîne »."
            )
        st.caption(etat)

    for onglet, libelle in zip(st.tabs(list(lib.FICHiers_CAS)), lib.FICHiers_CAS):
        nom_fichier = lib.FICHiers_CAS[libelle]
        chemin = dossier / nom_fichier
        with onglet:
            if not chemin.exists():
                st.info(f"`{nom_fichier}` absent de ce cas.")
                continue
            with st.container(border=True):
                st.markdown(chemin.read_text(encoding="utf-8"))
            st.download_button(
                f"Télécharger {chemin.name}", chemin.read_bytes(),
                file_name=chemin.name, mime="text/markdown",
                key=f"dl_cas_{libelle}",
            )

    st.divider()
    st.subheader("Exporter le rapport")
    st.caption(
        "L'export est produit dans un dossier temporaire puis proposé au téléchargement : "
        "rien n'est écrit dans `analyses/`."
    )
    formats = {"PDF": "pdf", "Markdown": "md", "HTML": "html", "JSON": "json"}
    for colonne, (etiquette, fmt) in zip(st.columns(4), formats.items()):
        with colonne:
            if st.button(f"Exporter {etiquette}", key=f"export_{fmt}", use_container_width=True):
                exports = dict(st.session_state.get("exports", {}))
                try:
                    with st.spinner(f"Export {fmt.upper()}…"):
                        with tempfile.TemporaryDirectory() as tmp:
                            sortie = export_tool.exporter(str(dossier), fmt, out=tmp)
                            exports[fmt] = (sortie.read_bytes(), sortie.name)
                    st.session_state["exports"] = exports
                except Exception as exc:
                    exports.pop(fmt, None)
                    st.session_state["exports"] = exports
                    st.error(f"Export {fmt.upper()} impossible : {exc}")
    exports = st.session_state.get("exports", {})
    for colonne, (etiquette, fmt) in zip(st.columns(4), formats.items()):
        with colonne:
            if fmt in exports:
                contenu, nom_fichier = exports[fmt]
                st.download_button(
                    f"Télécharger {etiquette}", contenu, file_name=nom_fichier,
                    mime="application/pdf" if fmt == "pdf" else "text/plain",
                    key=f"dl_export_{fmt}", use_container_width=True,
                )

# ------------------------------------------------------------- page 4 : chaîne E21
elif page == PAGES[3]:
    st.title("Lancer la chaîne d'agents")
    st.markdown(
        '<div class="e21-note">Cette application peut <b>lancer la chaîne en local</b> '
        "via opencode, avec la commande fixe affichée ci-dessous. Les intrants restent "
        "des <b>données</b> jamais exécutées et l'<b>humain reste décideur final</b> : "
        "chaque risque est validé par l'analyste.</div>",
        unsafe_allow_html=True,
    )
    analyses = lib.lister_analyses()
    cible = st.selectbox(
        "Cas ciblé", options=["(nouveau cas)"] + [dossier.name for dossier in analyses],
        index=1 if analyses else 0,
        format_func=lambda nom: (
            nom if nom.startswith("(") else lib.titre_lisible(lib.cas_depuis_dossier(nom))
        ),
    )
    cas = "" if cible.startswith("(") else lib.cas_depuis_dossier(cible)
    commande = lib.construire_commande(cas or "mon-cas")
    st.code(commande, language="bash")
    if st.button("Copier la commande", key="copier_cmd"):
        st.session_state["commande_copiee"] = commande
        st.toast("Commande copiée : sélectionnez le champ ci-dessous et faites Ctrl+C.")
    if st.session_state.get("commande_copiee"):
        st.text_input(
            "Commande (copie manuelle : Ctrl+A puis Ctrl+C)",
            value=st.session_state["commande_copiee"], key="champ_commande",
        )
    st.caption(
        "Le texte affiché est fixe : seul le nom du cas y figure (assaini en "
        "`[a-z0-9-]`). Aucun contenu d'intrant — donc aucune instruction malveillante — "
        "ne peut y être injecté."
    )

    st.subheader("Lancement depuis l'application")
    st.caption(
        "Rien à saisir ici. Le modèle vient du profil actif de « Réglages modèles » : "
        "s'il s'agit d'Ollama, le serveur est sondé au lancement et, s'il ne répond pas, "
        f"toute la chaîne part automatiquement sur **{reglages.MODELE_SECOURS}** "
        "(vous êtes prévenu juste après le clic). Pour rester sur opencode en permanence, "
        "choisissez le profil « opencode » dans les réglages."
    )
    if not cas:
        st.info(
            "Préparez d'abord un cas (onglet « Préparer un cas ») pour pouvoir lancer la chaîne."
        )
        st.stop()
    run = st.session_state.get("run_chaine")
    if not run:
        if st.button("▶ Lancer la chaîne maintenant", type="primary", key="lancer_chaine"):
            # Réglages modèles : la décision de lancement est prise ici, pas par
            # l'analyste. `decider_lancement` sonde le serveur Ollama, réaligne les
            # en-têtes `model:` des agents (les deux magasins) et renvoie le modèle à
            # imposer ainsi que le endpoint à fournir à opencode.
            reglages_courants = reglages.charger()
            try:
                decision = reglages.decider_lancement(reglages_courants)
            except Exception as exc:  # noqa: BLE001 — on n'empêche pas de lancer
                st.warning(
                    f"Réglages des agents illisibles ({exc}) — la chaîne part sur "
                    f"{reglages.MODELE_SECOURS}."
                )
                decision = {
                    "profil": reglages.PROFIL_OPENCODE,
                    "modele": reglages.MODELE_SECOURS,
                    "endpoint": "",
                    "repli": True,
                    "raison": str(exc),
                    "alignes": 0,
                }
            st.session_state["decision_lancement"] = decision
            # Aucun `OPENCODE_CONFIG` n'est transmis : mesuré, opencode 1.18.32 ne le
            # lit pas, et la chaîne échoue alors sur une erreur serveur sans nom.
            # C'est `opencode.jsonc`, écrit par la décision, qui porte l'endpoint.
            env = None
            if not decision["config"].get("ecrit") and decision["config"].get("raison"):
                st.warning(f"Endpoint opencode : {decision['config']['raison']}")
            try:
                st.session_state["run_chaine"] = run_agent.lancer(
                    cas,
                    dossier=lib.DOSSIER_ANALYSES / cible,
                    modele=decision["modele"] or None,
                    env=env,
                )
            except run_agent.ChaineError as exc:
                st.error(str(exc))
            except ValueError as exc:
                st.error(str(exc))
            else:
                st.rerun()
    else:
        # Le processus est réutilisé tel quel : il vit en mémoire (jamais re-sérialisé).
        proc = run["proc"]
        etapes = lib.avancement_chaine(Path(run["dossier"]))
        terminees = sum(1 for entree in etapes if entree["terminee"])
        st.progress(terminees / max(1, len(etapes)))
        for entree in etapes:
            # Livrables listés une fois l'étape terminée ; « ○ » signale ce qui reste.
            marque = "✓" if entree["terminee"] else "○"
            livrables = f" ({', '.join(entree['fichiers'])})" if entree["terminee"] else ""
            st.caption(f"{marque} {entree['etape']}{livrables}")
        # La décision de lancement est rappelée tant que la session existe : c'est
        # elle qui dit si la chaîne a démarré sur Ollama ou sur le modèle de secours.
        decision = st.session_state.get("decision_lancement")
        if decision:
            if decision.get("repli"):
                st.warning(
                    f"⚠️ Repli automatique sur **{reglages.MODELE_SECOURS}** — "
                    f"{decision['raison']} La chaîne n'est pas plantée : elle part sans GPU. "
                    "Vérifiez l'endpoint dans « Réglages modèles », ou choisissez le profil "
                    "« opencode » pour rester sur big-pickle en permanence."
                )
            else:
                st.caption(
                    f"Modèle de la chaîne : **{decision['modele'] or 'modèle de chaque agent'}** "
                    f"(profil « {decision['profil']} »)"
                    + (f" — {decision['raison']}" if decision.get("raison") else "")
                    + (f" · {decision['alignes']} agent(s) aligné(s)"
                       if decision.get("alignes") else "")
                    + (f" · {decision['config']['raison']}"
                       if decision.get("config", {}).get("ecrit") else "")
                )
        if run_agent.est_vivant(proc):
            st.info(f"Analyse en cours… PID {run['pid']}")
        else:
            st.success(
                "Chaîne terminée — ouvrez les livrables dans « Bibliothèque des analyses »."
            )
            fin = run_agent.lire_log(run["fichier_log"], n=5)
            if fin:
                st.caption("Toute fin du journal :")
                st.code(fin, language="text")
        st.text_area(
            "Sortie de la chaîne",
            value=run_agent.lire_log(run["fichier_log"], n=40),
            height=200, disabled=True, key="zone_log_chaine",
        )
        st.caption(
            f"Journal : `{Path(run['fichier_log']).name}` · dernier rafraîchissement à "
            f"{time.strftime('%H:%M:%S')}."
        )
        col_actualiser, col_arreter = st.columns(2)
        if col_actualiser.button("Actualiser", key="maj_chaine", use_container_width=True):
            st.rerun()
        if col_arreter.button("Arrêter", key="arret_chaine", use_container_width=True):
            run_agent.terminer(proc)
            del st.session_state["run_chaine"]
            st.rerun()
        # Rafraîchissement automatique : exécuté en dernier pour que le journal et les
        # boutons (Arrêter/Actualiser) restent affichés pendant l'analyse.
        if run_agent.est_vivant(proc):
            time.sleep(1.2)
            st.rerun()

# --------------------------------------------------------------- page 5 : studio E21
elif page == PAGES[4]:
    st.title("Studio E21")
    st.markdown(
        '<div class="e21-note">La base locale <code>stockage_local/e21.sqlite3</code> est la '
        "<b>source de vérité</b> des agents et des skills. Les fichiers "
        "<code>.opencode/agents/</code> et <code>.opencode/skills/</code> sont la "
        "<b>copie déployée</b> (celle que lit opencode) : toute modification est appliquée "
        "à la base PUIS déployée, et peut être versionnée sur git en branche + PR "
        "(jamais de push direct sur main).</div>",
        unsafe_allow_html=True,
    )

    # (c) État Ollama : informatif, non bloquant (sonde locale d'une seconde).
    modeles = modeles_ollama()
    if modeles:
        st.success(
            f"Ollama détecté sur localhost:11434 — {len(modeles)} modèle(s) local(aux)"
        )
        affiches = modeles[:MAX_MODELES_AFFICHES]
        reste = len(modeles) - len(affiches)
        st.caption(
            "Modèles : " + ", ".join(f"`{nom}`" for nom in affiches)
            + (f" (+{reste} autre(s))." if reste else ".")
        )
    else:
        st.info(
            "Ollama non détecté sur localhost:11434 (démarrez-le pour un fonctionnement "
            "100 % local)."
        )

    # (b) Bootstrap : base vide -> amorçage depuis les fichiers `.opencode/` présents.
    try:
        par_type = {type_: db.lister(type_) for type_ in db.TYPES_VALIDES}
    except sqlite3.Error as exc:
        st.error(f"Base locale inaccessible : {exc}")
        st.stop()
    base_vide = not par_type["agent"] and not par_type["skill"]
    if base_vide:
        st.warning(
            "Base locale vide : aucun agent ni skill en base. Importez les fichiers "
            "`.opencode/` existants pour les garder comme source de vérité."
        )
        if st.button(
            "Importer agents et skills depuis .opencode",
            key="studio_bootstrap",
            type="primary",
        ):
            try:
                bilan = db.importer_depuis_opencode()
            except (ValueError, sqlite3.Error) as exc:
                st.error(f"Import impossible : {exc}")
            else:
                st.session_state["studio_bilan_import"] = bilan
                st.rerun()
    bilan_import = st.session_state.get("studio_bilan_import")
    if bilan_import:
        st.success(
            f"Import terminé — {bilan_import['importes']} entité(s) importée(s), "
            f"{bilan_import['mis_a_jour']} mise(s) à jour, "
            f"{bilan_import['inchangees']} inchangée(s) — {bilan_import['total']} en base."
        )

    # (d) Édition des agents et des skills (ordre des onglets = ordre de db.TYPES_VALIDES).
    st.subheader("Agents et skills")
    for onglet, type_ in zip(st.tabs(["Agents", "Skills"]), db.TYPES_VALIDES):
        with onglet:
            entites = par_type.get(type_, [])
            if not entites:
                st.info("Aucune entité — ajoutez-en une ci-dessous.")
            else:
                nom = st.selectbox(
                    "Entité", [entite["nom"] for entite in entites], key=f"sel_{type_}"
                )
                entite = next(e for e in entites if e["nom"] == nom)
                st.caption(
                    f"version {entite['version']} · source {entite['source']} · "
                    f"modifié le {entite['modifie_le']}"
                )
                contenu = st.text_area(
                    "Contenu (Markdown)",
                    value=entite["contenu"],
                    height=300,
                    key=f"ed_{type_}_{nom}",
                )
                col_enregistrer, col_supprimer = st.columns(2)
                if col_enregistrer.button(
                    "Enregistrer dans la base (source de vérité)",
                    key=f"save_{type_}",
                    use_container_width=True,
                ):
                    enregistrer_entite(type_, nom, contenu)
                # La confirmation est liée au NOM de l'entité : changer d'entité dans la
                # liste désarme le bouton (sinon un simple changement de sélection
                # laisserait une suppression validée pour une autre entité).
                if col_supprimer.button(
                    "Supprimer", key=f"del_{type_}", use_container_width=True
                ):
                    st.session_state[f"suppression_{type_}_{nom}"] = True
                if st.session_state.get(f"suppression_{type_}_{nom}"):
                    st.warning(
                        f"Suppression de « {nom} » : l'entrée disparaît de la base "
                        "(source de vérité). Le fichier déjà déployé dans `.opencode/` "
                        "reste sur le disque — supprimez-le (ou restaurez la version "
                        "précédente via git) pour que la chaîne lise la suppression."
                    )
                    if st.checkbox("Confirmer la suppression", key=f"conf_del_{type_}_{nom}"):
                        if st.button(
                            "Supprimer définitivement",
                            key=f"del_ok_{type_}_{nom}",
                            type="primary",
                        ):
                            supprimer_entite(type_, nom)

            # Ajout : nom validé par la base (fail closed), puis déploiement.
            st.divider()
            with st.form(f"form_ajout_{type_}"):
                st.caption("Ajouter un agent ou un skill — puis le déployer dans `.opencode/`.")
                nouveau_nom = st.text_input(
                    "Nom (slug)",
                    placeholder="ex. e21-nouvel-agent",
                    key=f"ajout_nom_{type_}",
                    help="Lettres, chiffres, point, tiret et tiret bas : le nom valide une "
                         "partie de chemin (aucun « / », aucun « .. »).",
                )
                nouveau_contenu = st.text_area(
                    "Contenu (Markdown)", height=200, key=f"ajout_contenu_{type_}"
                )
                ajouter = st.form_submit_button("Ajouter + déployer", key=f"ajout_ok_{type_}")
            if ajouter:
                if not (nouveau_nom or "").strip():
                    st.error("Donnez un nom (slug) à l'entité à ajouter.")
                elif not (nouveau_contenu or "").strip():
                    st.error("Donnez un contenu (Markdown) à l'entité à ajouter.")
                elif enregistrer_entite(type_, nouveau_nom, nouveau_contenu):
                    st.rerun()

    dernier = st.session_state.get("studio_dernier_deploiement")
    if dernier:
        st.caption(
            f"Dernier déploiement : {dernier['ecrits']} fichier(s) écrit(s) — cible "
            "`.opencode/agents` et `.opencode/skills/<nom>/SKILL.md`. opencode relit la "
            "copie déployée APRÈS l'écriture en base : utilisez « Actualiser » ou "
            "relancez la chaîne (« Lancer la chaîne ») pour que le changement soit pris."
        )

    # (e) Versionnement git : branche + PR, jamais de push direct sur main.
    st.divider()
    with st.expander("Versionner les agents/skills sur git"):
        st.warning(
            "Le studio écrit dans .opencode/ : les modifications sont suivies par git. "
            "Aucun push direct sur main (convention du dépôt)."
        )
        st.caption(
            "Commandes fixes, passées en liste d'arguments (jamais de shell) : seuls le "
            "nom de branche horodaté et les chemins fixes `.opencode` / `tools/studio` "
            "figurent dans la ligne de commande — aucun contenu d'agent n'y entre."
        )
        if st.button("Créer une branche + PR", key="studio_pr", type="primary"):
            with st.spinner("Branche, commit, push et ouverture de la pull request…"):
                st.session_state["studio_git"] = versionner_sur_git()
        bilan_git = st.session_state.get("studio_git")
        if bilan_git:
            for etape in bilan_git["etapes"]:
                marque = "✓" if etape["code"] == 0 else "○"
                detail = etape["sortie"] if etape["code"] == 0 else (etape["sortie"] or "échec")
                st.caption(f"{marque} {etape['etape']} — {detail or 'ok'}")
            if bilan_git["rien_a_committer"]:
                st.info("Rien de nouveau à versionner (aucune modification).")
            elif bilan_git["echec"]:
                st.error(f"Versionnement interrompu : {bilan_git['echec']}")
            else:
                st.success(
                    f"Branche {bilan_git['branche']} commitée et poussée — "
                    "la pull request attend une relecture humaine."
                )
            if bilan_git["pr_sortie"]:
                st.caption("Sortie de `gh pr create` :")
                st.code(bilan_git["pr_sortie"], language="text")
            if bilan_git["pr_url"]:
                st.link_button("Ouvrir la pull request", bilan_git["pr_url"])

    # (f) Export / import : sauvegarde portable de la base, hors git et hors .opencode/.
    with st.expander("Exporter / importer la base (JSON)"):
        st.caption(
            "L'export est écrit dans `stockage_local/` (dossier local, hors git) puis "
            "proposé au téléchargement. L'import restaure les entités d'un export, avec "
            "leur version exacte — relancez ensuite un déploiement vers `.opencode/`."
        )
        # La clé de session est distincte de celle du bouton : Streamlit range la valeur
        # de retour d'un widget sous SA clé, un nom partagé écraserait le chemin exporté.
        if st.button("Exporter la base (JSON)", key="studio_export"):
            try:
                st.session_state["studio_export_chemin"] = db.exporter_json()
            except (ValueError, sqlite3.Error) as exc:
                st.error(f"Export impossible : {exc}")
        chemin_export = st.session_state.get("studio_export_chemin")
        if chemin_export is not None and Path(chemin_export).is_file():
            st.download_button(
                "Télécharger le JSON",
                Path(chemin_export).read_bytes(),
                file_name=Path(chemin_export).name,
                mime="application/json",
                key="studio_dl_json",
            )
        televersement = st.file_uploader(
            "Importer un JSON", type=["json"], key="studio_import_json"
        )
        if televersement is not None:
            # Le fichier reçu est une DONNÉE non fiable : il est recopié tel quel dans un
            # dossier temporaire puis relu par `importer_json`, qui refuse tout contenu
            # non conforme (aucune entrée n'est exécutée, seulement stockée).
            with tempfile.TemporaryDirectory() as tmp:
                copie = Path(tmp) / "import-studio.json"
                copie.write_bytes(televersement.getvalue())
                try:
                    bilan_import = db.importer_json(copie)
                except (ValueError, sqlite3.Error) as exc:
                    st.error(str(exc))
                else:
                    st.session_state["studio_restaures"] = bilan_import["restaures"]
                    st.rerun()
        restaures = st.session_state.get("studio_restaures")
        if restaures is not None:
            st.success(
                f"{restaures} entité(s) restaurée(s) en base — pensez à les déployer "
                "dans `.opencode/`."
            )
            st.session_state.pop("studio_restaures", None)


# ------------------------------------------------------- page 6 : réglages modèles
elif page == PAGES[5]:
    st.title("Réglages modèles")
    st.markdown(
        '<div class="e21-note">Ces réglages sont <b>locaux et jamais versionnés</b> '
        f"(écrits dans <code>{reglages.DOSSIER_LOCAL.name}/{reglages.NOM_FICHIER}</code>, "
        "dossier gitignoré). Aucune clé d'API n'est stockée ailleurs ni réaffichée en "
        "clair. L'<b>humain reste décideur</b> : un modèle choisi ici ne remplace pas "
        "le modèle défini agent par agent.</div>",
        unsafe_allow_html=True,
    )
    courants = reglages.charger()

    # ---------------------------------------------------------- profils de réglages
    st.subheader("Profil de connexion")
    st.caption(
        "Deux configurations sont proposées côte à côte, chacune avec son endpoint, "
        "sa clé et son modèle : **opencode** (la configuration déjà présente dans le "
        "conteneur Docker, aucune surcharge) et **ollama** (un serveur Ollama, local ou "
        "sur une autre machine). Le profil actif est celui utilisé au prochain "
        "lancement de la chaîne."
    )
    noms = reglages.nom_profils(courants)
    libelles = {nom: f"{nom} — {reglages.libelle_profil(nom, courants)}" for nom in noms}
    col_profil, col_action = st.columns([3, 2])
    with col_profil:
        profil_choisi = st.selectbox(
            "Profil actif",
            options=noms,
            index=0,
            format_func=lambda n: libelles.get(n, n),
            key="regl_profil_actif",
        )
    # la liste place le profil actif en premier : ouvrir la page n'écrit donc rien ;
    # seul un changement explicite de la part de l'analyste bascule le profil.
    if profil_choisi != courants["profil_actif"]:
        try:
            with st.spinner("Bascule du profil…"):
                reglages.activer_profil(profil_choisi)
        except ValueError as exc:
            st.error(f"Profil non activable : {exc}")
        else:
            st.rerun()
    with col_action:
        st.caption(
            f"Actif : **{reglages.libelle_profil(profil_choisi, courants)}** — "
            f"modèle « {courants['modele_chaine'] or 'non imposé'} »."
        )
        if profil_choisi == reglages.PROFIL_OLLAMA:
            st.caption(
                f"Secours automatique : si le serveur ne répond pas au lancement, toute la "
                f"chaîne part sur **{reglages.MODELE_SECOURS}** (et vous êtes prévenu). "
                "Choisissez le profil « opencode » pour ne jamais dépendre du GPU."
            )
    with st.expander("Créer ou supprimer un profil"):
        nouveau_nom = st.text_input(
            "Nom du nouveau profil",
            value="",
            placeholder="ex. gpu-nuit",
            key="regl_nouveau_profil",
            help="Minuscules, chiffres, tiret et souligné uniquement (ex. « gpu-nuit »).",
        )
        if st.button("Créer ce profil", key="regl_creer_profil"):
            try:
                with st.spinner("Création…"):
                    etat = reglages.creer_profil(nouveau_nom)
            except ValueError as exc:
                st.error(f"Profil non créé : {exc}")
            else:
                st.success(f"Profil « {nouveau_nom} » créé : complétez son endpoint.")
                st.rerun()
        if noms and st.button("Supprimer le profil actif", key="regl_suppr_profil"):
            if profil_choisi == reglages.PROFIL_OPENCODE:
                st.error(
                    "Le profil « opencode » est le secours du système (il garantit une "
                    "chaîne sans GPU) : il ne peut pas être supprimé."
                )
            elif len(noms) <= 1:
                st.error("Impossible de supprimer le dernier profil.")
            else:
                try:
                    with st.spinner("Suppression…"):
                        etat = reglages.supprimer_profil(profil_choisi)
                except ValueError as exc:
                    st.error(f"Profil non supprimé : {exc}")
                else:
                    st.success(f"Profil « {profil_choisi} » supprimé.")
                    st.rerun()

    st.divider()
    st.subheader("Connexion à l'API des modèles")
    st.caption(
        "Ollama peut tourner sur une autre machine du réseau : indiquez son adresse, "
        "par exemple `http://192.168.1.50:11434`. Rien n'est envoyé en dehors de "
        "cette adresse, et aucune donnée d'analyse n'y transite. **Laissez l'adresse "
        "vide** dans le profil « opencode » : opencode lira alors sa propre "
        "configuration, aucune surcharge ne sera envoyée."
    )
    with st.form("form_reglages"):
        endpoint_saisi = st.text_input(
            "Adresse de l'API (endpoint)",
            value=courants["endpoint"],
            key="regl_endpoint",
            help="Format attendu : http://hôte:port ou https://hôte "
                 "(ex. http://192.168.1.50:11434). Ni espace, ni « ; », ni « & », "
                 "ni chevron : ces caractères sont refusés.",
        )
        cle_saisie = st.text_input(
            "Clé d'API (facultative)",
            value=reglages.masquer(courants["cle"]),
            type="password",
            placeholder=reglages.MASQUE_CLE,
            key="regl_cle",
            help="Jamais réaffichée en clair. Laissez vide pour un fournisseur local "
                 "sans authentification ; une clé cloud se renseigne plutôt dans le "
                 "`.env` au déploiement Docker.",
        )
        enregistrer_reglages = st.form_submit_button(
            "Enregistrer les réglages", type="primary"
        )
    if enregistrer_reglages:
        # Une clé masquée renvoyée telle quelle (« •••• ») ne doit pas écraser la
        # clé réellement enregistrée : on ne l'envoie que si elle a été retapée.
        charge = cle_saisie.strip()
        if not charge or charge == reglages.MASQUE_CLE:
            charge = courants["cle"]
        try:
            with st.spinner("Écriture des réglages…"):
                enregistres = reglages.enregistrer({
                    "endpoint": endpoint_saisi,
                    "cle": charge,
                })
        except ValueError as exc:
            st.error(f"Réglages refusés : {exc}")
        else:
            st.success(
                f"Réglages du profil « {enregistres['profil_actif']} » enregistrés dans "
                f"`{reglages.NOM_FICHIER}` — endpoint "
                f"{enregistres['endpoint'] or 'aucun (config opencode du conteneur)'} · clé "
                + (f"{reglages.masquer(enregistres['cle'])}" if enregistres["cle"]
                   else "aucune")
                + f" · modèle de chaîne : {enregistres['modele_chaine'] or 'aucun'}."
            )
            st.rerun()

    st.divider()
    st.subheader("Tester la connexion")
    st.caption(
        f"Sonde bornée (délai {int(reglages.DELAI_SONDE)} s) sur "
        "`<endpoint>/api/tags` : aucune redirection suivie, aucun secret affiché."
    )
    if not courants["endpoint"]:
        st.info(
            "Profil « opencode » : aucune adresse à tester — opencode lira sa propre "
            "configuration au lancement. Passez au profil « ollama » pour vérifier un "
            "serveur Ollama distant."
        )
    elif st.button("Tester la connexion", key="regl_tester"):
        with st.spinner("Sonde de l'endpoint…"):
            resultat = reglages.sonder(endpoint_saisi or courants["endpoint"])
        if resultat["joignable"]:
            st.success(f"{resultat['endpoint']} — {resultat['message']}")
            if resultat["modeles"]:
                st.dataframe(
                    {"Modèle": resultat["modeles"]},
                    use_container_width=True, hide_index=True,
                )
            else:
                st.warning(
                    "Le service répond mais n'annonce aucun modèle : lancez "
                    "`ollama pull <modèle>` sur cette machine."
                )
        else:
            st.error(resultat["message"] or "Endpoint injoignable.")
        st.session_state["regl_sonde"] = resultat

    st.divider()
    st.subheader("Modèle utilisé pour lancer la chaîne")
    sonde = st.session_state.get("regl_sonde") or {}
    detectes = list(sonde.get("modeles") or [])
    enregistres_chaine = courants["modele_chaine"]
    options = sorted({nom for nom in detectes + [enregistres_chaine] if nom})
    if not options:
        options = [enregistres_chaine] if enregistres_chaine else []
    PERSONNALISE = "— Autre identifiant (saisie manuelle) —"
    choix = [PERSONNALISE] + options
    index = options.index(enregistres_chaine) + 1 if enregistres_chaine in options else 0
    if not options and enregistres_chaine:
        choix = [PERSONNALISE, enregistres_chaine]
        index = 1
    modele_choisi = st.selectbox(
        "Modèle utilisé pour lancer la chaîne",
        options=choix,
        index=index,
        key="regl_modele_chaine",
        help="Passé à opencode en `--model` au prochain lancement de la chaîne.",
    )
    if options:
        st.caption(
            "Modèles détectés par le test de connexion (serveur Ollama). Tout autre "
            "fournisseur accessible à opencode — **par exemple `big-pickle` (OpenCode Zen)** "
            "— se saisit dans « Autre identifiant » : ce modèle n'est pas servi par Ollama, "
            "donc jamais listé automatiquement."
        )
    if modele_choisi == PERSONNALISE or not modele_choisi:
        modele_choisi = st.text_input(
            "Identifiant du modèle de la chaîne",
            value=enregistres_chaine,
            key="regl_modele_saisi",
            help="Exemples : `big-pickle`, `opencode/big-pickle`, `ollama/qwen2.5:7b`, "
                 "`anthropic/claude-sonnet-4-5`.",
        ).strip()
    if not options:
        st.info(
            "Aucun modèle détecté : testez la connexion ci-dessus pour découvrir les "
            "modèles du serveur Ollama, ou saisissez directement un identifiant "
            "(ex. `big-pickle`)."
        )
    st.caption(
        "Ce modèle s'applique au **lancement de la chaîne** (option `--model`) ; "
        "il **n'écrase pas** le modèle défini agent par agent dans le Studio : un "
        "agent dont le frontmatter fixe `model:` garde le sien."
    )
    if st.button("Enregistrer le modèle de la chaîne", key="regl_save_modele"):
        try:
            with st.spinner("Écriture du modèle…"):
                reglages.enregistrer({"modele_chaine": modele_choisi})
        except ValueError as exc:
            st.error(f"Modèle refusé : {exc}")
        else:
            st.success(
                f"Modèle de chaîne enregistré : `{modele_choisi}` — il sera utilisé "
                "au prochain lancement depuis « Lancer la chaîne »."
            )
            st.rerun()

    st.caption(
        "**Images et PDF** : leur texte est extrait **localement** (OCR Tesseract, "
        "installé dans l'image Docker) ; aucune image n'est envoyée à un modèle externe "
        "et aucun modèle vision payant n'est nécessaire. Si la qualité de l'OCR est "
        "insuffisante pour un document, il vaut mieux le scanner de nouveau ou saisir "
        "le texte à la main plutôt que brancher un modèle payant."
    )

    st.divider()
    st.subheader("Modèle configuré par agent (lecture seule)")
    st.caption(
        "Ces valeurs viennent des agents du Studio (`stockage_local/e21.sqlite3` puis "
        "`.opencode/agents/`). **Rien à éditer ici, et rien à éditer dans les agents** : "
        "c'est le bouton « ▶ Lancer la chaîne » qui réécrit la ligne `model:` de tous les "
        "agents selon le profil actif et la réponse du serveur — dans les deux endroits "
        "où elle existe (base Studio **et** `.opencode/agents/`), donc un Studio E21 "
        "dépliqué ensuite n'annule rien."
    )
    st.caption(
        "Le tableau ci-dessous montre donc l'état **avant** lancement : soit la valeur "
        "de secours livrée avec le dépôt, soit le résultat du dernier lancement. "
        "C'est aussi le modèle qui compte pour un agent lancé seul, et non par la chaîne."
    )
    try:
        agents_lus = db.lister("agent")
    except sqlite3.Error as exc:
        agents_lus = []
        st.error(f"Base locale inaccessible : {exc}")
    if agents_lus:
        st.dataframe(
            {
                "Agent": [entite["nom"] for entite in agents_lus],
                "Modèle": [
                    modele_de_agent(entite.get("contenu", "")) for entite in agents_lus
                ],
            },
            use_container_width=True, hide_index=True,
        )
    else:
        st.info("Aucun agent en base : importez-les depuis `.opencode/` (Studio E21).")

    st.divider()
    st.subheader("Modèles Ollama recommandés par agent (carte 12 Go)")
    st.caption(
        "Sélection faite pour une **RTX 5070 (12 Go)** : un seul modèle chargé à la "
        f"fois, {conseils_ollama.VRAM_UTILE_GO} Go utiles maximum (le tag `:8b` est déjà "
        "quantifié Q4). « installé » = le modèle est détecté sur ton serveur ; sinon la "
        "commande `ollama pull` est donnée. **Aucun modèle d'agent de plus de 12 Go n'est "
        "proposé** : il ne tiendrait pas."
    )
    modeles_vus = list((st.session_state.get("regl_sonde") or {}).get("modeles") or [])
    st.dataframe(
        pd.DataFrame(conseils_ollama.table_recommandations(modeles_vus)),
        use_container_width=True, hide_index=True,
    )
    st.caption(
        "**Une commande suffit, aucun agent à ouvrir.** Depuis le dépôt (ou le serveur) :"
    )
    st.code("make agents-modele PROFIL=ollama      # cette table, appliquée à tous les agents\n"
            "make agents-modele                     # retour à opencode/big-pickle (défaut)", language="bash")
    st.caption(
        "L'outil écrit la ligne `model:` de chaque agent **dans les deux endroits où elle "
        "existe** (base Studio et `.opencode/agents/`), donc un `make studio-deploy` "
        "n'annule pas le choix. **Depuis l'interface, vous n'avez pas besoin de cette "
        "commande** : le lancement fait exactement la même chose, avec en plus la liste "
        "des modèles réellement installés sur ton serveur (elle est récupérée au moment "
        "du test de connexion). Elle reste utile pour un lancement hors interface, ou "
        "pour forcer un état sur la machine."
    )
    st.caption(
        "Deux équivalents à connaître : sur l'agent **direct**, tu peux laisser le champ "
        "vide (opencode lit alors le modèle global) ; sur l'agent de **lecture d'image**, "
        "seul `qwen3-vl:8b` est utile — et l'OCR local fait déjà le travail dans la "
        "plupart des cas."
    )

    st.divider()
    st.markdown(
        '<div class="e21-note">Où sont stockés ces réglages ? Dans '
        f"<code>{reglages.DOSSIER_LOCAL.name}/{reglages.NOM_FICHIER}</code> et "
        f"<code>{reglages.DOSSIER_LOCAL.name}/{run_agent.NOM_CONFIG_RUNTIME}</code>, "
        "deux dossiers <b>gitignorés</b> : rien n'est versionné ni poussé sur GitHub. "
        "Pour les clés de modèles <b>cloud</b> en déploiement Docker, utilisez plutôt "
        "le fichier <code>.env</code> (jamais commité) — ces réglages ne servent qu'à "
        "l'application web locale.</div>",
        unsafe_allow_html=True,
    )

# --------------------------------------------------------------- page 7 : garde-fous
else:
    st.title("À propos / Garde-fous")
    st.markdown(
        "Ce prototype est un **wrapper de présentation** : l'analyse de risques reste "
        "une chaîne d'agents opencode pilotée par des consignes versionnées dans "
        "`.opencode/` (agents `e21-*`, skills par méthode)."
    )
    st.markdown(
        """
### Garde-fous appliqués

- **Données fictives** — le cas ShoPix et ses 14 risques sont entièrement fictifs.
- **Humain décideur** — chaque risque est validé par l'analyste (`valide_par`) ; l'interface
  ne valide rien à sa place.
- **Intrants non fiables** — les documents sont encadrés `<<<DONNÉES>>>` et reproduits
  verbatim ; une « instruction » contenue dans un document est signalée comme
  avertissement, jamais exécutée.
- **Écriture bornée** — l'application écrit uniquement dans `analyses/<cas>/` et
  `analyses/<cas>/intrants/` ; les exports partent dans un dossier temporaire. Le studio
  écrit en plus dans `stockage_local/` (base locale, gitignorée) et `.opencode/`
  (copie déployée des agents et skills).
- **Une seule commande exécutable** — la chaîne ne part que par la commande fixe opencode
  (bouton « Lancer la chaîne ») ; aucun contenu utilisateur n'est jamais interpolé sur la
  ligne de commande, les intrants restent des données.
- **Studio = édition de la source de vérité** — la base locale `stockage_local/e21.sqlite3`
  (gitignorée) est la source de vérité des agents/skills ; `.opencode/` est la copie
  déployée, versionnée en git via branche + PR (jamais de push direct).
- **Aucune donnée vers un service externe** — tout est local (`localhost`), pas d'authentification.
"""
    )
    st.caption(
        "Contexte technique : `documentation/technique/07-ameliorations-semaine.md` "
        "(chantiers #25 ingestion, #26 interface web, #27 rapports exportables)."
    )
    st.markdown(
        "[Dépôt GitHub](https://github.com/MelvinBzh/management_de_la_securite) · "
        "[Board projet](https://github.com/users/MelvinBzh/projects/6)"
    )