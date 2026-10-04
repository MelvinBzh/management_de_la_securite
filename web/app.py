# -*- coding: utf-8 -*-
"""Interface web locale E21 — wrapper de présentation du POC piloté par consignes.

Lancement :
    make web
    # ou : python3 -m streamlit run web/app.py

L'application n'exécute **jamais** la chaîne d'agents : elle ingère des documents
(données non fiables), prépare un brouillon de description, lit la bibliothèque
des analyses, exporte les rapports et affiche la commande opencode à lancer à la
main. Écriture bornée à `analyses/<cas>/` et `analyses/<cas>/intrants/`
(cf. `web/lib.py`) ; les exports partent dans un dossier temporaire.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

RACINE = Path(__file__).resolve().parents[1]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from web import lib  # noqa: E402  (chemin du dépôt garanti ci-dessus)
from tools.export import export as export_tool  # noqa: E402
from tools.ingest import preparer  # noqa: E402
from tools.ingest.ingest import parse_file  # noqa: E402
from tools.ingest.parsers import commun  # noqa: E402

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


# --------------------------------------------------------------------- sidebar
st.sidebar.title("E21")
st.sidebar.caption("Analyses de risques — prototype local")
PAGES = [
    "Ingérer des documents",
    "Préparer un cas",
    "Bibliothèque des analyses",
    "Lancer la chaîne",
    "À propos / Garde-fous",
]
page = st.sidebar.radio("Navigation", PAGES)
st.sidebar.divider()
st.sidebar.caption(
    "Données fictives uniquement · application locale sur `localhost` · "
    "écriture bornée à `analyses/**`."
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
    fichiers = st.file_uploader(
        "Déposez un ou plusieurs documents",
        type=lib.TYPES_UPLOAD,
        accept_multiple_files=True,
        help="PDF, images (PNG/JPG/WEBP), XLSX, CSV, DOCX, PPTX, ZIP, TXT, MD — analyse 100 % locale.",
    )
    st.subheader("Documents déposés")
    if not fichiers:
        st.info(
            "Aucun document pour l'instant. Les documents ingérés ici deviennent des "
            "« intrants » pour l'étape 1 (préparation d'un cas), onglet suivant."
        )
    else:
        documents = memoiser_documents(fichiers)
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
    st.caption(
        f"Dossier : `analyses/{dossier.name}` · "
        f"{len(lib.intrants_prepars(dossier))} intrant(s) · "
        f"exports : {', '.join(lib.FICHiers_CAS)}"
    )

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
        '<div class="e21-note">Cette application <b>n\'exécute rien</b> : la chaîne E21 est '
        "un POC piloté par consignes dans opencode. La commande ci-dessous est à copier puis "
        "à lancer dans opencode — l'humain reste décideur final.</div>",
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

# --------------------------------------------------------------- page 5 : garde-fous
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
  `analyses/<cas>/intrants/` ; les exports partent dans un dossier temporaire.
- **Chaîne non exécutée** — l'interface affiche la commande opencode, elle ne lance aucun agent.
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