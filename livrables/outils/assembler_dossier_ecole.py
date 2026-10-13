"""Assemble le dossier écrit ÉCOLE (V1) en un seul Markdown, contenu inchangé, dans l'ordre demandé par le sujet.
Les schémas Mermaid sont extraits (diag/v1-*.mmd) pour être dessinés ; le reste est recopié tel quel."""
import re
import sys
from pathlib import Path

V1 = Path(sys.argv[1])            # .../V1-ecole
SORTIE = Path(sys.argv[2])        # fichier .md de sortie
DIAG = Path(sys.argv[3])          # dossier diag/ (sources .mmd)
D = V1 / "1-dossier-ecrit"
P = V1 / "2-prototype"

PARTIES = [
    ("1. Description du cas étudié", [
        ("Étude de cas pilote : boutique en ligne ShoPix", D / "01-description-du-cas/etude-de-cas.md"),
        ("Description du système (étape 1 de l'analyse)", D / "01-description-du-cas/00-description.md")]),
    ("2. Architecture et fiche de chaque agent", [
        ("Architecture", D / "02-architecture-et-fiches-agents/01-architecture.md"),
        ("Fiche de chaque agent", D / "02-architecture-et-fiches-agents/02-agents.md"),
        ("Format des échanges", D / "02-architecture-et-fiches-agents/03-format-echanges.md"),
        ("Garde-fous de sécurité", D / "02-architecture-et-fiches-agents/04-garde-fous.md")]),
    ("3. Choix du modèle et plan de test", [
        ("Choix du cas et du modèle de menaces", D / "03-choix-du-modele-et-plan-de-test/05-cas-et-modele.md"),
        ("Plan de test", D / "03-choix-du-modele-et-plan-de-test/06-plan-de-test.md"),
        ("Choix des modèles d'IA", D / "03-choix-du-modele-et-plan-de-test/CHOIX-MODELES-IA.md"),
        ("Campagne de tests (état au 24/09)", P / "tests/TESTS.md")]),
    ("4. Registre des risques obtenu", [
        ("Registre des risques validé", D / "04-registre-des-risques/registre-risques.md"),
        ("Synthèse", D / "04-registre-des-risques/SYNTHESE.md")]),
    ("5. Analyse critique des résultats (état au 24/09)", [
        ("Audit du système", D / "05-analyse-critique-etat-au-24-09/AUDIT-SYSTEME.md"),
        ("Benchmark face aux alternatives", D / "05-analyse-critique-etat-au-24-09/BENCHMARK.md"),
        ("Remédiation de l'audit", D / "05-analyse-critique-etat-au-24-09/MODIFICATIONS.md")]),
    ("6. Présentation générale et feuille de route", [
        ("Présentation du dépôt", D / "06-presentation-generale/README.md"),
        ("Feuille de route", D / "06-presentation-generale/ROADMAP.md")]),
]
AGENTS = ["orchestrator", "e21-analyse-existant", "e21-choix-methode", "e21-menaces", "e21-evaluation", "e21-traitement",
          "e21-validation-suivi", "e21-synthese", "e21-controle"]

compteur = [0]


def decaler(texte: str, n: int = 1) -> str:
    """Décale les titres de n niveaux (les blocs de code ne sont pas touchés)."""
    sortie, en_code = [], False
    for l in texte.split("\n"):
        if l.strip().startswith("```"):
            en_code = not en_code
        if not en_code:
            m = re.match(r"^(#{1,5})(\s.*)$", l)
            if m:
                l = "#" * min(len(m.group(1)) + n, 6) + m.group(2)
        sortie.append(l)
    return "\n".join(sortie)


def schemas(texte: str, prefixe: str) -> str:
    """Remplace chaque bloc ```mermaid par une image ; le code est écrit dans diag/ pour être dessiné."""
    def sub(m):
        compteur[0] += 1
        nom = f"v1-{prefixe}-{compteur[0]}"
        (DIAG / f"{nom}.mmd").write_text(m.group(1), encoding="utf-8")
        return f"![Schéma]({'diagrammes-v1/' + nom + '.png'})"
    return re.sub(r"```[ \t]*mermaid[ \t]*\r?\n(.*?)```", sub, texte, flags=re.S)


def sans_front_matter(texte: str) -> tuple[str, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", texte, flags=re.S)
    return (m.group(1), m.group(2)) if m else ("", texte)


out = []
out.append("""# Dossier écrit — version école

**Projet E21 — Management de la sécurité — M2 Cybersécurité, Sup de Vinci Rennes**

**Des agents IA pour analyser les risques**

| | |
|---|---|
| Équipe | Melvin RAIMBAULT, Lucas HUARD, Jérémy LESSA, David AMARO MONTEIRO (groupe de 4) |
| Production | Travail de cours, 23 et 24 septembre 2026 |
| État du dépôt | Tag Git `ecole-2026-09-24` (commit `b7f3155`, 24/09/2026 à 13h34) |
| Cas d'étude | Boutique en ligne ShoPix (données fictives) : 14 risques validés |
| Document | Assemblage du 13 octobre 2026 |

> **À propos de ce document.** Il réunit, dans l'ordre demandé par le sujet, les documents produits pendant le travail de cours.
> **Leur contenu n'est pas modifié** : seuls les titres sont décalés, les schémas sont dessinés et les pictogrammes en couleur
> sont remplacés par des signes typographiques. Chaque partie
> indique le fichier d'origine. Les améliorations faites après la soutenance (V2) sont dans le dossier `2-AMELIORATIONS-V2`.

## Correspondance avec ce que demande le sujet

| Le sujet demande | Où le trouver dans ce document |
|---|---|
| Description du cas étudié | Partie 1 |
| Architecture et fiche de chaque agent | Partie 2 |
| Consignes (prompts) utilisées | Annexe A |
| Registre des risques obtenu | Partie 4 |
| Analyse critique des résultats | Partie 5 (audit, benchmark, remédiation) |
| Choix et justification du modèle | Partie 3 |
| Exemple d'exécution et traces des échanges | Dossier `03-PROTOTYPE` (étapes 00 à 06, `RAPPORT-CONTROLE.md`) |
| Soutenance | Dossier `02-SOUTENANCE-ECOLE` |

> **Note de lecture.** L'analyse manuelle de référence et l'exécution réelle du test d'injection figuraient encore dans la feuille
> de route à la date du 24/09 (voir la partie 5, « Ce qui est encore ouvert ») : elles ont été réalisées ensuite et sont
> présentées dans le dossier V2.
""")
for titre, docs in PARTIES:
    out.append(f"\n---\n\n# {titre}\n")
    for sous, chemin in docs:
        brut = chemin.read_text(encoding="utf-8")
        brut = schemas(brut, chemin.stem.lower().replace(" ", "-"))
        out.append(f"\n## {sous}\n\n*Fichier d'origine : `{chemin.relative_to(V1).as_posix()}`*\n")
        out.append(decaler(brut, 2))

out.append("\n---\n\n# Annexe A. Consignes (prompts) des agents\n")
out.append("Les consignes ci-dessous sont les fichiers d'agents `.opencode/agents/` tels qu'ils étaient au 24/09. L'en-tête de chaque "
           "fichier (modèle, permissions) est reproduit en bloc de code ; le texte qui suit est la consigne.\n")
for nom in AGENTS:
    chemin = D / "07-consignes-prompts-des-agents" / "agents" / f"{nom}.md"
    fm, corps = sans_front_matter(chemin.read_text(encoding="utf-8"))
    out.append(f"\n## {nom}\n\n*Fichier d'origine : `{chemin.relative_to(V1).as_posix()}`*\n")
    if fm:
        out.append("```\n" + fm.strip() + "\n```\n")
    out.append(decaler(schemas(corps, nom), 2))
out.append("\nLes quinze skills (grilles STRIDE, LINDDUN, EBIOS RM, PASTA, DREAD, CVSS, ATT&CK, format du registre, garde-fous IA…) "
           "sont fournis en fichiers dans `03-PROTOTYPE/skills/`.\n")
texte_final = "\n".join(out)
for ancien, nouveau in (("️", ""), ("✅", "✔"), ("❌", "✘"), ("\U0001f534 ", ""), ("\U0001f7e0 ", ""),
                        ("\U0001f7e1 ", ""), ("\U0001f7e6 ", ""), ("⏳", "(en attente)"), ("ℹ", "i")):
    texte_final = texte_final.replace(ancien, nouveau)
SORTIE.write_text(texte_final, encoding="utf-8")
print("blocs mermaid extraits :", compteur[0], "| taille :", SORTIE.stat().st_size // 1024, "Ko")
