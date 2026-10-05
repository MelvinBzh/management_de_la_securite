#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests autonomes du socle Studio E21 (STUDIO-01 → STUDIO-08).

Exécution sans dépendance externe :
    python3 tools/studio/tests/test_db.py
    # ou : make test-studio
Compatible pytest (`pytest tools/studio/tests/test_db.py`) : les fonctions
`test_*` sont alors collectées.

Sortie attendue : STUDIO: N PASS, M FAIL, K SKIP (EXIT 0 seulement si 0 FAIL).

Isolation : tout se passe dans un `tempfile.TemporaryDirectory` — les tests
n'écrivent aucun fichier dans `.opencode/` (le déploiement de STUDIO-04 vise des
dossiers temporaires) et ne créent aucune base dans le dépôt. STUDIO-03 est la
seule exception : il LIT les vrais `.opencode/agents/*.md` et
`.opencode/skills/*/SKILL.md` du dépôt — le test vérifie donc l'inventaire réel
de la chaîne E21 — mais les écrit dans une base temporaire. Le seul fichier produit
hors dossier temporaire est l'export horodaté de STUDIO-05, dans `stockage_local/`
(dossier gitignoré), supprimé à la fin du test.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parents[3]
if str(RACINE) not in sys.path:
    sys.path.insert(0, str(RACINE))

from tools.studio import db  # noqa: E402  (import après ajustement de sys.path)
from tools.studio import entetes  # noqa: E402
from tools.studio import modeles_agents  # noqa: E402
from web import modeles_ollama  # noqa: E402

CONTENU = "# Studio — contenu de test\n\nEntité synthétique, sans valeur E21.\n"

try:
    import pytest

    _BaseSkip = pytest.skip.Exception
except ImportError:  # pragma: no cover
    pytest = None
    _BaseSkip = Exception


class SkipTest(_BaseSkip):
    """Test non exécutable dans cet environnement (motif documenté)."""


def sauter(message: str):
    """Interrompt le test en SKIP (motif : dépendance absente, fichier manquant…)."""
    raise SkipTest(message)


n_pass = 0
n_fail = 0
n_skip = 0


def passer(tid: str, detail: str = ""):
    """Enregistre et affiche un PASS."""
    global n_pass
    print(f"PASS {tid}{' — ' + detail if detail else ''}")
    n_pass += 1
    return True


def echouer(tid: str, detail: str):
    """Enregistre et affiche un FAIL."""
    global n_fail
    print(f"FAIL {tid} — {detail}")
    n_fail += 1
    return False


def sauter_test(tid: str, detail: str):
    """Enregistre et affiche un SKIP (environnement non conforme)."""
    global n_skip
    print(f"SKIP {tid} — {detail}")
    n_skip += 1
    return True


# --------------------------------------------------------------------------- outils
def base_temporaire(dossier: Path) -> Path:
    """Chemin d'une base jetable dans le dossier temporaire courant."""
    return dossier / "stockage_local" / "e21-test.sqlite3"


def tables(conn) -> set[str]:
    """Noms des tables présentes dans la base ouverte."""
    return {
        ligne[0]
        for ligne in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }


def lire_schema_version(conn) -> str | None:
    """Valeur de `meta.schema_version` (`None` si la clé est absente)."""
    ligne = conn.execute("SELECT valeur FROM meta WHERE cle = 'schema_version'").fetchone()
    return None if ligne is None else ligne[0]


def version_de(entites: list[dict], nom: str) -> int:
    """Version d'une entité dans une liste de dictionnaires."""
    versions = [entite["version"] for entite in entites if entite["nom"] == nom]
    assert len(versions) == 1, f"entité « {nom} » absente ou dupliquée : {versions}"
    return versions[0]


def leverer(action, type_cercle: type[Exception], fragment: str) -> str:
    """Vérifie qu'une exception de `type_cercle` contenant `fragment` est levée."""
    try:
        action()
    except type_cercle as exc:
        message = str(exc)
    else:
        raise AssertionError(f"{type_cercle.__name__} non levée")
    assert message.strip(), "exception levée sans message"
    assert fragment in message, f"message d'erreur inattendu : « {message} »"
    return message


# --------------------------------------------------------------------------- STUDIO-01
def test_studio_01():
    """STUDIO-01 : `init()` crée base + schéma (entites, meta) et schema_version."""
    with tempfile.TemporaryDirectory() as tmp:
        chemin = base_temporaire(Path(tmp))
        assert not chemin.exists(), "la base ne doit pas exister avant init()"
        conn = db.init(chemin)
        try:
            assert chemin.is_file(), f"base non créée : {chemin}"
            noms = tables(conn)
            assert "entites" in noms, f"table « entites » absente (tables : {sorted(noms)})"
            assert "meta" in noms, f"table « meta » absente (tables : {sorted(noms)})"
            assert lire_schema_version(conn) == db.VERSION_SCHEMA, \
                f"schema_version absent ou incorrect : {lire_schema_version(conn)!r}"
            # Contrainte de type portée par le schéma : « agent » ou « skill » seulement.
            conn.execute(
                "INSERT INTO entites(type, nom, contenu, modifie_le) "
                "VALUES ('agent', 'controle-type', 'x', '2026-01-01T00:00:00+00:00')"
            )
            leverer(
                lambda: conn.execute(
                    "INSERT INTO entites(type, nom, contenu, modifie_le) "
                    "VALUES ('plugin', 'controle-type', 'x', '2026-01-01T00:00:00+00:00')"
                ),
                sqlite3.Error,
                "CHECK",
            )
            conn.rollback()  # annule la ligne de contrôle : base vide après fermeture
        finally:
            conn.close()
        db.sauvegarder("agent", "e21-init", CONTENU, chemin_db=chemin)
        # Idempotence : un second init() ne perd rien et ne réécrit pas le schéma.
        conn = db.init(chemin)
        try:
            assert lire_schema_version(conn) == db.VERSION_SCHEMA, "schema_version altéré"
        finally:
            conn.close()
        restants = db.lister("agent", chemin)
        assert [e["nom"] for e in restants] == ["e21-init"], \
            f"donnée perdue au second init() : {restants}"
    passer("STUDIO-01", "schéma entites + meta · schema_version · init() idempotent")


# --------------------------------------------------------------------------- STUDIO-02
def test_studio_02():
    """STUDIO-02 : `sauvegarder` crée en version 1 puis incrémente en version 2."""
    with tempfile.TemporaryDirectory() as tmp:
        chemin = base_temporaire(Path(tmp))
        db.init(chemin).close()
        premier = db.sauvegarder("agent", "e21-test-studio", CONTENU, chemin_db=chemin)
        assert premier["version"] == 1, f"création en version 1 attendue : {premier}"
        assert premier["source"] == "studio", f"source « studio » attendue : {premier}"
        assert premier["modifie_le"], "modifie_le vide à la création"
        assert premier["modifie_le"].startswith("20"), \
            f"modifie_le attendu en ISO UTC : {premier['modifie_le']!r}"

        modifie = CONTENU + "\nAjout.\n"
        deuxieme = db.sauvegarder("agent", "e21-test-studio", modifie, chemin_db=chemin)
        assert deuxieme["version"] == 2, f"mise à jour en version 2 attendue : {deuxieme}"
        assert deuxieme["source"] == "studio", f"source « studio » attendue : {deuxieme}"
        assert deuxieme["modifie_le"] >= premier["modifie_le"], "horodatage non monotone"

        lu = db.lire("agent", "e21-test-studio", chemin_db=chemin)
        assert lu == deuxieme, f"contenu relu différent de celui écrit : {lu}"
        assert lu["contenu"] == modifie, "contenu altéré à la relecture"
        assert db.lire("skill", "e21-test-studio", chemin_db=chemin) is None, \
            "la clé primaire (type, nom) doit isoler agent et skill"

        # Un skill du même nom vit dans la même table, sans collision.
        skill = db.sauvegarder("skill", "e21-test-studio", "# Skill\n", chemin_db=chemin)
        assert skill["version"] == 1, f"création skill en version 1 attendue : {skill}"
        assert len(db.lister("agent", chemin)) == 1, "l'agent a disparu de lister('agent')"
        assert len(db.lister("skill", chemin)) == 1, "le skill a disparu de lister('skill')"
    passer("STUDIO-02", "version 1 puis 2 · source studio · contenu relu identique")


# --------------------------------------------------------------------------- STUDIO-03
def test_studio_03():
    """STUDIO-03 : import du `.opencode/` réel, puis ré-import idempotent."""
    assert db.DOSSIER_AGENTS.is_dir(), f"dossier agents absent : {db.DOSSIER_AGENTS}"
    assert db.DOSSIER_SKILLS.is_dir(), f"dossier skills absent : {db.DOSSIER_SKILLS}"
    agents_disques = sorted(chemin.stem for chemin in db.DOSSIER_AGENTS.glob(f"*{db.SUFFIXE_MD}"))
    skills_disques = sorted(
        dossier.name
        for dossier in db.DOSSIER_SKILLS.iterdir()
        if dossier.is_dir() and (dossier / db.NOM_SKILL).is_file()
    )
    if not agents_disques or not skills_disques:
        sauter(
            f"inventaire `.opencode/` vide (agents : {len(agents_disques)}, "
            f"skills : {len(skills_disques)})"
        )

    with tempfile.TemporaryDirectory() as tmp:
        chemin = base_temporaire(Path(tmp))
        db.init(chemin).close()
        attendu = len(agents_disques) + len(skills_disques)

        premier = db.importer_depuis_opencode(chemin)
        assert premier["importes"] == attendu, \
            f"imports inattendus : {premier} ({attendu} fichiers sur disque)"
        assert premier["mis_a_jour"] == 0, f"première importation déjà mise à jour : {premier}"
        assert premier["total"] == attendu, f"total incohérent : {premier}"

        base_agents = db.lister("agent", chemin)
        base_skills = db.lister("skill", chemin)
        assert [e["nom"] for e in base_agents] == agents_disques, \
            f"agents importés différents des fichiers : {[e['nom'] for e in base_agents]}"
        assert [e["nom"] for e in base_skills] == skills_disques, \
            f"skills importés différents des fichiers : {[e['nom'] for e in base_skills]}"
        for entite in base_agents + base_skills:
            assert entite["source"] == "opencode", f"source « opencode » attendue : {entite}"
            assert entite["version"] == 1, f"version 1 attendue à l'import : {entite}"
            assert entite["contenu"].strip(), f"contenu vide pour {entite['nom']}"
        # Le contenu importé est bien celui du fichier opencode correspondant.
        for entite in base_agents:
            fichier = db.DOSSIER_AGENTS / f"{entite['nom']}{db.SUFFIXE_MD}"
            assert entite["contenu"] == fichier.read_text(encoding="utf-8"), \
                f"contenu altéré pour {entite['nom']}"
        for entite in base_skills:
            fichier = db.DOSSIER_SKILLS / entite["nom"] / db.NOM_SKILL
            assert entite["contenu"] == fichier.read_text(encoding="utf-8"), \
                f"contenu altéré pour {entite['nom']}"

        # Deuxième appel : rien ne change, aucune version n'est incrémentée.
        second = db.importer_depuis_opencode(chemin)
        assert second["importes"] == 0, f"ré-import : création inattendue {second}"
        assert second["mis_a_jour"] == 0, f"ré-import non idempotent : {second}"
        assert second["inchangees"] == attendu, f"inchangees inattendu au ré-import : {second}"
        apres = db.lister("agent", chemin)
        assert [e["version"] for e in apres] == [1] * len(base_agents), \
            "version incrémentée à tort lors d'un ré-import"
    detail = f"{len(agents_disques)} agents + {len(skills_disques)} skills importés"
    passer("STUDIO-03", f"{detail} · ré-import sans changement")


# --------------------------------------------------------------------------- STUDIO-04
def test_studio_04():
    """STUDIO-04 : déploiement vers des dossiers temporaires, puis idempotence."""
    with tempfile.TemporaryDirectory() as tmp:
        racine = Path(tmp)
        chemin = base_temporaire(racine)
        agents = racine / "opencode" / "agents"
        skills = racine / "opencode" / "skills"
        db.init(chemin).close()
        db.sauvegarder("agent", "e21-test-studio", CONTENU, chemin_db=chemin)
        db.sauvegarder("skill", "test-skill", CONTENU, chemin_db=chemin)

        premier = db.deployer_vers_opencode(agents, skills, chemin)
        fichier_agent = agents / "e21-test-studio.md"
        fichier_skill = skills / "test-skill" / db.NOM_SKILL
        assert premier["ecrits"] == 2, f"deux écritures attendues : {premier}"
        assert premier["inchangees"] == 0, f"rien n'était déjà à jour : {premier}"
        assert set(premier["chemins"]) == {fichier_agent, fichier_skill}, \
            f"chemins inattendus : {premier['chemins']}"
        for fichier in (fichier_agent, fichier_skill):
            assert fichier.is_file(), f"fichier non créé : {fichier}"
            assert fichier.read_text(encoding="utf-8") == CONTENU, \
                f"contenu déployé différent : {fichier}"

        # Relance sans changement : aucune écriture.
        second = db.deployer_vers_opencode(agents, skills, chemin)
        assert second["ecrits"] == 0, f"déploiement non idempotent : {second}"
        assert second["inchangees"] == 2, f"deux entités à jour attendues : {second}"
        assert second["chemins"] == [], f"aucun chemin attendu : {second}"

        # Modification en base : le fichier concerné est réécrit, l'autre non.
        db.sauvegarder("skill", "test-skill", CONTENU + "Version 2.\n", chemin_db=chemin)
        troisieme = db.deployer_vers_opencode(agents, skills, chemin)
        assert troisieme["ecrits"] == 1, f"une écriture attendue : {troisieme}"
        assert troisieme["chemins"] == [fichier_skill], f"chemin inattendu : {troisieme}"
        assert "Version 2." in fichier_skill.read_text(encoding="utf-8"), \
            "le nouveau contenu n'a pas été déployé"

        # Fichier déployé altéré hors Studio : la base le rétablit.
        fichier_agent.write_text("corruption locale\n", encoding="utf-8")
        quatrieme = db.deployer_vers_opencode(agents, skills, chemin)
        assert quatrieme["ecrits"] == 1, f"réécriture attendue : {quatrieme}"
        assert fichier_agent.read_text(encoding="utf-8") == CONTENU, \
            "le contenu de la base n'a pas rétabli le fichier"

        # Les vrais dossiers `.opencode/` n'ont pas été touchés par ce test.
        assert not (db.DOSSIER_AGENTS / "e21-test-studio.md").exists(), \
            "le test a écrit dans le vrai .opencode/agents (contamination du dépôt)"
    passer("STUDIO-04", "2 fichiers écrits · 2e relance 0 écriture · réécriture si écart")


# --------------------------------------------------------------------------- STUDIO-05
def test_studio_05():
    """STUDIO-05 : export JSON puis restauration à l'identique (contenu + version)."""
    with tempfile.TemporaryDirectory() as tmp:
        racine = Path(tmp)
        chemin = base_temporaire(racine)
        db.init(chemin).close()
        db.sauvegarder("agent", "e21-export", CONTENU, chemin_db=chemin)
        db.sauvegarder("agent", "e21-export", CONTENU + "V2.\n", chemin_db=chemin)
        db.sauvegarder("skill", "skill-export", CONTENU, chemin_db=chemin)
        avant = db.lister("agent", chemin) + db.lister("skill", chemin)
        assert version_de(avant, "e21-export") == 2, "l'agent doit être en version 2 avant export"

        export = db.exporter_json(racine / "export.json", chemin_db=chemin)
        assert export.is_file(), f"export non écrit : {export}"
        document = json.loads(export.read_text(encoding="utf-8"))
        assert document["schema_version"] == db.VERSION_SCHEMA, \
            f"schema_version absent de l'export : {sorted(document)}"
        assert len(document["entites"]) == len(avant), \
            f"export incomplet : {len(document['entites'])} entités pour {len(avant)}"

        # Base réinitialisée : les entités sont restaurées à l'identique.
        for entite in avant:
            assert db.supprimer(entite["type"], entite["nom"], chemin_db=chemin), \
                f"suppression impossible : {entite['nom']}"
        assert db.lister("agent", chemin) == [] and db.lister("skill", chemin) == [], \
            "la base doit être vide avant restauration"

        retour = db.importer_json(export, chemin)
        assert retour["restaures"] == len(avant), f"restauration incomplète : {retour}"
        apres = db.lister("agent", chemin) + db.lister("skill", chemin)
        assert apres == avant, "contenu ou version altéré par la restauration"
        assert version_de(apres, "e21-export") == 2, \
            "la version exportée doit être restaurée sans incrément"

        # Export vers le dossier par défaut (nom horodaté) puis relecture.
        horodate = db.exporter_json(chemin_db=chemin)
        try:
            assert horodate.name.startswith(db.PREFIXE_EXPORT), \
                f"nom d'export inattendu : {horodate.name}"
            assert horodate.suffix == ".json", f"extension inattendue : {horodate.name}"
            assert horodate.is_file(), f"export par défaut non écrit : {horodate}"
        finally:
            horodate.unlink(missing_ok=True)
        # Fichier illisible ou mal formé : refus explicite, aucun import partiel.
        mauvais = racine / "mauvais.json"
        mauvais.write_text("{ pas du json", encoding="utf-8")
        leverer(lambda: db.importer_json(mauvais, chemin), ValueError, "invalide")
        leverer(lambda: db.importer_json(racine / "absent.json", chemin), ValueError, "illisible")
    passer("STUDIO-05", "export horodaté · restauration à l'identique · refus JSON invalide")


# --------------------------------------------------------------------------- STUDIO-06
def test_studio_06():
    """STUDIO-06 : suppression, tri par nom et refus des types invalides."""
    with tempfile.TemporaryDirectory() as tmp:
        chemin = base_temporaire(Path(tmp))
        db.init(chemin).close()
        for nom in ("zeta", "alpha", "mu"):
            db.sauvegarder("agent", nom, CONTENU, chemin_db=chemin)
        noms = [entite["nom"] for entite in db.lister("agent", chemin)]
        assert noms == ["alpha", "mu", "zeta"], f"lister doit trier par nom : {noms}"

        assert db.supprimer("agent", "mu", chemin_db=chemin) is True, "suppression non confirmée"
        assert db.supprimer("agent", "mu", chemin_db=chemin) is False, \
            "la seconde suppression doit renvoyer False"
        assert db.lire("agent", "mu", chemin_db=chemin) is None, "l'entité doit avoir disparu"
        assert [e["nom"] for e in db.lister("agent", chemin)] == ["alpha", "zeta"], \
            "liste après suppression inattendue"
        assert db.lire("agent", "absent", chemin_db=chemin) is None, \
            "lire une entité absente doit renvoyer None"

        # Type invalide : refus explicite (fail closed) sur toutes les entrées-sorties.
        for action in (
            lambda: db.lister("plugin", chemin),
            lambda: db.lire("plugin", "alpha", chemin),
            lambda: db.sauvegarder("plugin", "x", "y", chemin_db=chemin),
            lambda: db.supprimer("plugin", "alpha", chemin),
        ):
            leverer(action, ValueError, "Type d'entité refusé")

        # Nom piégé : un nom est une partie de chemin, il ne peut pas s'en évader.
        for nom_piege in ("../evasion", "a/b", "..", "", "  "):
            leverer(
                lambda nom_piege=nom_piege: db.sauvegarder(
                    "agent", nom_piege, "x", chemin_db=chemin
                ),
                ValueError,
                "Nom d'entité",
            )
        message = leverer(
            lambda: db.sauvegarder("agent", "../evasion", "x", chemin_db=chemin),
            ValueError,
            "séparateur de chemin",
        )
        assert ".." in message, f"le message doit citer « .. » : « {message} »"
    passer("STUDIO-06", "suppression · tri par nom · type et nom invalides refusés")


# --------------------------------------------------------------------------- STUDIO-07
def test_studio_07():
    """STUDIO-07 : `agents-modele` bascule tous les agents dans les DEUX magasins.

    Sans ce test, la question « où est le modèle de l'agent ? » n'a pas de réponse
    fiable : le modèle vit dans l'en-tête, présent à la fois dans la base Studio
    (source de vérité) et dans `.opencode/agents/*.md` (copie déployée). L'outil doit
    écrire les deux, sinon `make studio-deploy` annule le choix en silence.
    """
    with tempfile.TemporaryDirectory() as tmp:
        racine = Path(tmp)
        chemin = base_temporaire(racine)
        agents = racine / "agents"
        agents.mkdir()
        db.init(chemin).close()

        # deux agents : l'un vient de la base, l'autre n'existe que sur disque
        contenu = (
            "---\n"
            "description: agent de test\n"
            "model: opencode/big-pickle\n"
            "temperature: 0.1\n"
            "---\n\n"
            "Consignes.\n"
        )
        db.sauvegarder("agent", "e21-test", contenu, chemin_db=chemin)
        (agents / "e21-test.md").write_text(contenu, encoding="utf-8")
        seul_fichier = contenu.replace("opencode/big-pickle", "autre/modele")
        (agents / "e21-hors-base.md").write_text(seul_fichier, encoding="utf-8")

        # a) profil inconnu : refus explicite, rien n'est écrit
        leverer(
            lambda: modeles_agents.appliquer_profil(
                "inconnu", chemin_db=chemin, dossier_agents=agents
            ),
            ValueError,
            "Profil inconnu",
        )

        # b) bascule vers ollama : les deux magasins sont alignés
        bilan = modeles_agents.appliquer_profil(
            "ollama", chemin_db=chemin, dossier_agents=agents
        )
        assert bilan["modifies"], "aucun agent basculé"
        attendu = f"ollama/{modeles_ollama.RECOMMANDATION_DEFAUT}"
        contenu_fichier = (agents / "e21-test.md").read_text(encoding="utf-8")
        contenu_base = db.lire("agent", "e21-test", chemin_db=chemin)["contenu"]
        assert f"model: {attendu}" in contenu_fichier, \
            f"fichier non bascule : {contenu_fichier.splitlines()[:4]}"
        assert contenu_fichier == contenu_base, \
            "base et fichier divergent : un deploy annulerait la bascule"
        assert f"model: {attendu}" in (agents / "e21-hors-base.md").read_text(encoding="utf-8"), \
            "agent présent sur disque seul : il doit être bascule aussi"

        # c) le reste du contenu est préservé (consignes, temperature, description)
        assert "temperature: 0.1" in contenu_fichier and "Consignes." in contenu_fichier, \
            "le hors-modèle ne doit pas être touché"

        # d) idempotence : une seconde passe n'écrit rien
        avant = (agents / "e21-test.md").read_text(encoding="utf-8")
        bilan2 = modeles_agents.appliquer_profil(
            "ollama", chemin_db=chemin, dossier_agents=agents
        )
        assert bilan2["modifies"] == [], f"seconde passe non idempotente : {bilan2}"
        assert (agents / "e21-test.md").read_text(encoding="utf-8") == avant, \
            "fichier modifié alors que le modèle est deja conforme"

        # e) simulation : n'écrit rien du tout
        avant_sim = (agents / "e21-test.md").read_text(encoding="utf-8")
        bilan3 = modeles_agents.appliquer_profil(
            "opencode", chemin_db=chemin, dossier_agents=agents, dry_run=True
        )
        assert bilan3["modifies"], "la simulation doit annoncer les changements"
        assert bilan3["ecrits_base"] == 0 and bilan3["ecrits_fichiers"] == 0, \
            "la simulation a écrit"
        assert (agents / "e21-test.md").read_text(encoding="utf-8") == avant_sim, \
            "la simulation a modifié le fichier"

        # f) retour au profil opencode : big-pickle pour tout le monde
        modeles_agents.appliquer_profil(
            "opencode", chemin_db=chemin, dossier_agents=agents
        )
        for nom in ("e21-test", "e21-hors-base"):
            texte = (agents / f"{nom}.md").read_text(encoding="utf-8")
            assert f"model: {modeles_agents.MODELE_OPENCODE}" in texte, \
                f"retour opencode incomplet pour {nom}"

        # g) liste de modèles installés : on ne retient que ce qui existe, sinon
        #    l'agent pointerait un modèle absent (Ollama le téléchargerait d'abord)
        modeles_agents.appliquer_profil("ollama", chemin_db=chemin, dossier_agents=agents)
        avant_prefere = (agents / "e21-test.md").read_text(encoding="utf-8")
        assert f"model: {attendu}" in avant_prefere, \
            f"prérequis du test (g) non satisfait : {avant_prefere.splitlines()[:4]}"
        bilan_prefere = modeles_agents.appliquer_profil(
            "ollama", chemin_db=chemin, dossier_agents=agents,
            modeles_disponibles=("mistral:7b",),
        )
        contenu_prefere = (agents / "e21-test.md").read_text(encoding="utf-8")
        assert "model: ollama/mistral:7b" in contenu_prefere, \
            f"un modèle installé doit être préféré : {contenu_prefere.splitlines()[:4]}"
        changes = {e["agent"]: e["modele"] for e in bilan_prefere["modifies"]}
        assert changes == {"e21-test": "ollama/mistral:7b", "e21-hors-base": "ollama/mistral:7b"}, \
            f"les deux agents sans recommandation doivent suivre la liste : {changes}"
        assert "model: ollama/mistral:7b" in (agents / "e21-hors-base.md").read_text(
            encoding="utf-8"
        ), "l'agent présent sur disque seul doit suivre lui aussi"

        # h) un agent sans ligne `model:` n'est pas réécrit (on ne fabrique rien)
        sans_modele = racine / "agents2"
        sans_modele.mkdir()
        nu = "---\ndescription: pas de modele\n---\n\nTexte.\n"
        (sans_modele / "e21-nu.md").write_text(nu, encoding="utf-8")
        vide = base_temporaire(racine / "b2")
        db.init(vide).close()
        bilan4 = modeles_agents.appliquer_profil(
            "ollama", chemin_db=vide, dossier_agents=sans_modele
        )
        assert (sans_modele / "e21-nu.md").read_text(encoding="utf-8") == nu, \
            "un agent sans modele ne doit pas être réécrit"
        assert bilan4["modifies"] == [], "aucun changement ne devait être annonce"
    passer(
        "STUDIO-07",
        f"agents-modele : 2 magasins alignes · idempotent · simulation sans effet · "
        "retour opencode · modèles installés privilégiés · agent sans modele intact",
    )


# --------------------------------------------------------------------------- STUDIO-08
def test_studio_08():
    """STUDIO-08 : le déploiement refuse d'écrire un en-tête qu'opencode refuserait.

    opencode ne signale pas un agent refusé : il bascule sur l'agent par défaut et
    la chaîne démarre sans ses consignes, en sortant en code 0. Le seul endroit où
    l'on peut encore dire « non » avant que le dépôt soit cassé, c'est ici.
    """
    with tempfile.TemporaryDirectory() as tmp:
        racine = Path(tmp)
        chemin = base_temporaire(racine)
        agents = racine / "agents"
        skills = racine / "skills"
        db.init(chemin).close()

        def entete(mode: str) -> str:
            return f"---\ndescription: agent de test\nmode: {mode}\n---\n\nCorps.\n"

        bon = entete("subagent")
        casse = entete("agent")
        db.sauvegarder("agent", "e21-bon", bon, chemin_db=chemin)
        db.sauvegarder("agent", "e21-casse", casse, chemin_db=chemin)

        leverer(
            lambda: db.deployer_vers_opencode(
                agents, skills, chemin_db=chemin
            ),
            ValueError,
            "e21-casse",
        )
        assert not (agents / "e21-casse.md").exists(), \
            "un en-tête refusé ne doit surtout pas atteindre le disque"
        assert not (agents / "e21-bon.md").exists(), \
            "le refus doit être global : un déploiement partiel est un dépôt incohérent"

        message = leverer(
            lambda: db.deployer_vers_opencode(agents, skills, chemin_db=chemin),
            ValueError,
            "opencode",
        )
        assert "n'est pas enregistré" in message and "défaut" in message, \
            f"le message doit rappeler la conséquence silencieuse : « {message} »"
        assert "Aucun fichier n'a été écrit" in message, \
            f"le message doit dire que le dépôt est intact : « {message} »"

        # réparé : le déploiement passe, et rien n'est réécrit une seconde fois
        db.sauvegarder("agent", "e21-casse", entete("primary"), chemin_db=chemin)
        bilan = db.deployer_vers_opencode(agents, skills, chemin_db=chemin)
        assert bilan["ecrits"] == 2, bilan
        assert (agents / "e21-casse.md").read_text(encoding="utf-8").find(
            "mode: primary"
        ) != -1, "le fichier doit porter le mode réparé"
        assert db.deployer_vers_opencode(agents, skills, chemin_db=chemin)["ecrits"] == 0, \
            "déploiement doit rester idempotent"

        # un agent sans en-tête reste déployable : c'est opencode qui est seul juge
        db.sauvegarder("agent", "e21-sans-entete", "Corps seul.\n", chemin_db=chemin)
        bilan = db.deployer_vers_opencode(agents, skills, chemin_db=chemin)
        assert bilan["ecrits"] == 1, bilan
    passer(
        "STUDIO-08",
        "en-tête mode invalide : déploiement refusé, rien sur disque, message nommant "
        "la conséquence silencieuse · réparé puis idempotent · agent sans en-tête accepté",
    )


def test_studio_09():
    """STUDIO-09 : une clé de permission « * » nue est refusée au déploiement.

    Régression du 05/10/2026, celle qui a fait échouer toutes les chaînes :
    en YAML, une clé qui commence par `*` est un **alias**. Les douze agents
    écrivaient

        permission:
          bash:
            *: deny

    opencode 1.18.34 n'enregistre alors **aucun** de ces agents — sans message,
    sans code d'erreur. `opencode run --agent orchestrator` affiche seulement
    « agent not found. Falling back to default agent », la chaîne démarre sans les
    consignes de l'orchestrateur, sort en code 0, et l'agent générique improvise
    à la place (il a proposé un `e21.txt` et une session inexistante).

    La correction — écrire `'*': deny` — a été validée en isolement : à en-tête
    identique, le fichier avec `*` nu n'est pas enregistré et l'appel bascule sur
    l'agent par défaut ; le même fichier avec `'*'` est enregistré et répond.

    STUDIO-08 vérifiait le `mode`. Un `mode` correct ne sauvait rien : c'est la
    deuxième façon, indépendante, d'éteindre tout le dépôt en silence.
    """
    with tempfile.TemporaryDirectory() as tmp:
        racine = Path(tmp)
        chemin = base_temporaire(racine)
        agents = racine / "agents"
        skills = racine / "skills"
        db.init(chemin).close()

        def entete(cle: str) -> str:
            return (
                "---\ndescription: agent de test\nmode: primary\n"
                "permission:\n  read: allow\n  bash:\n"
                f"    {cle}: deny\n    gh *: allow\n---\n\nCorps.\n"
            )

        db.sauvegarder("agent", "e21-nu", entete("*"), chemin_db=chemin)
        message = leverer(
            lambda: db.deployer_vers_opencode(agents, skills, chemin_db=chemin),
            ValueError,
            "e21-nu",
        )
        assert not (agents / "e21-nu.md").exists(), \
            "un en-tête que opencode écarterait ne doit pas atteindre le disque"
        assert "entre guillemets" in message, \
            f"le message doit dire quoi corriger : « {message} »"

        # la même permission, protégée : elle est acceptée telle quelle
        assert entetes.verifier_permission(entete("'*'")) == [], \
            "une clé protégée est valide"
        assert entetes.verifier_permission(entete("*")), \
            "la clé nue doit être signalée"
        db.sauvegarder("agent", "e21-nu", entete("'*'"), chemin_db=chemin)
        bilan = db.deployer_vers_opencode(agents, skills, chemin_db=chemin)
        assert bilan["ecrits"] == 1 and (agents / "e21-nu.md").is_file(), bilan

        # et le dépôt livré lui-même ne contient plus aucune clé nue
        racine_repo = Path(__file__).resolve().parents[3]
        fautives = []
        for agent in sorted((racine_repo / ".opencode" / "agents").glob("*.md")):
            fautives += [
                f"{agent.name} ligne {n}"
                for n, ligne in enumerate(
                    agent.read_text(encoding="utf-8").splitlines(), 1
                )
                if re.match(r"^\s+\*:(?:\s|$)", ligne)
            ]
        assert not fautives, (
            "les agents du dépôt ne doivent contenir aucune clé YAML « * » nue — "
            f"opencode les écarterait tous : {fautives}"
        )

        # Même clé de lariat, second piège indépendant : opencode lit
        # `permission.edit` comme `{motif: décision}`. Le dépôt livrait l'inverse
        # (`deny: "**"`), ce qu'il refuse aussi — l'agent est alors écarté sans que
        # le fichier ait l'air faux.
        def entete_inversee() -> str:
            return (
                "---\ndescription: agent de test\nmode: primary\n"
                "permission:\n  read: allow\n  edit:\n"
                '    deny: "**"\n    allow: "analyses/**"\n---\n\nCorps.\n'
            )

        def entete_droite() -> str:
            return (
                "---\ndescription: agent de test\nmode: primary\n"
                "permission:\n  read: allow\n  edit:\n"
                '    "**": deny\n    "analyses/**": allow\n---\n\nCorps.\n'
            )

        rapports = entetes.verifier_permission(entete_inversee())
        assert len(rapports) == 2 and all("inversée" in r for r in rapports), \
            f"le bloc edit inversé doit être signalé ligne à ligne : {rapports}"
        assert entetes.verifier_permission(entete_droite()) == [], \
            "motif en clé et décision en valeur : la forme attendue"
        db.sauvegarder("agent", "e21-inv", entete_inversee(), chemin_db=chemin)
        message = leverer(
            lambda: db.deployer_vers_opencode(agents, skills, chemin_db=chemin),
            ValueError,
            "e21-inv",
        )
        assert "inversée" in message, \
            f"le message doit nommer l'inversion : « {message} »"
        db.supprimer("agent", "e21-inv", chemin_db=chemin)
    passer(
        "STUDIO-09",
        "permission opencode : « * » nue refusée (clé nue = alias YAML) · bloc "
        "« edit » motif/décision inversé refusé · formes correctes acceptées · "
        "dépôt livré conforme",
    )


# ------------------------------------------------------------------------ exécution
def executer_tests() -> int:
    """Exécute STUDIO-01 → STUDIO-09 ; renvoie 0 si aucun FAIL."""
    tests = [
        test_studio_01, test_studio_02, test_studio_03,
        test_studio_04, test_studio_05, test_studio_06, test_studio_07, test_studio_08,
        test_studio_09,
    ]
    for test in tests:
        tid = test.__name__.replace("test_studio_", "STUDIO-")
        try:
            test()
        except SkipTest as exc:
            sauter_test(tid, str(exc))
        except AssertionError as exc:
            echouer(tid, str(exc) or "assertion sans message")
        except Exception as exc:
            echouer(tid, f"{type(exc).__name__}: {exc}")
    print(f"STUDIO: {n_pass} PASS, {n_fail} FAIL, {n_skip} SKIP")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(executer_tests())
