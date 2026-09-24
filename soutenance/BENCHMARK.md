# Benchmark du système E21 — alternatives étudiées

> Produit par l'agent `research` (benchmark comparatif, 2026-09-24), mis en forme par l'orchestrateur.
> Usage : section « Avantages & inconvénients » de la soutenance.

## 1. Alternatives comparées

| # | Approche | Principe |
|---|---|---|
| A1 | **Analyse manuelle** (papier / tableur) | L'analyste applique la méthode 6 étapes seul, documents natifs |
| A2 | **Microsoft Threat Modeling Tool (TMT)** | Outil desktop gratuit, DFD + génération de menaces STRIDE |
| A3 | **OWASP Threat Dragon** | Web/desktop open source, DFD + STRIDE par nœud |
| A4 | **IriusRisk** | Plateforme commerciale : DFD → risques → tests / CISO workflow |
| A5 | **pytm** | Génération de threat models en Python (code = modèle) |
| A6 | **Framework seul** (STRIDE/LINDDUN/EBIOS sur document) | Méthode papier + grille, sans outil ni IA |
| A7 | **LLM générique (chat)** : « analyse ces risques avec STRIDE » | Un modèle généraliste répond sans structure ni garde-fous |
| A8 | **Frameworks multi-agents** (AutoGen, CrewAI, LangGraph) | Ordonnancement d'agents génériques, sans méthode métier intégrée |

## 2. Grille de comparaison (notation 1–5, 5 = meilleur)

| Critère | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | **E21** |
|---|---|---|---|---|---|---|---|---|---|
| Effort (faible = bon) | 2 | 3 | 3 | 4 | 2 | 2 | 5 | 4 | **5** |
| Reproductibilité | 2 | 4 | 4 | 4 | 4 | 3 | 1 | 3 | **5** |
| Traçabilité des sources | 3 | 2 | 2 | 3 | 2 | 3 | 1 | 2 | **5** |
| Humain dans la boucle | 5 | 3 | 3 | 4 | 2 | 4 | 2 | 2 | **5** |
| Coût (faible = bon) | 4 | 5 | 5 | 1 | 5 | 5 | 4 | 3 | **4** |
| Adaptabilité de méthode | 4 | 2 | 2 | 3 | 3 | 5 | 3 | 4 | **5** |
| Qualité / endurance | 3 | 3 | 3 | 4 | 3 | 3 | 2 | 3 | **4** |
| Maîtrise des risques IA | — | — | — | — | — | — | 1 | 2 | **4** |

→ **Note globale** : les outils dédiés (A2–A5) excellent sur un périmètre (DFD, STRIDE) mais sont **fermés** (méthode imposée, pas d'EBIOS/LINDDUN, exports propriétaires), les LLM génériques (A7) sont **incohérents et non contrôlés**, les frameworks multi-agents (A8) apportent l'orchestration mais **pas la méthode métier ni les garde-fous**. E21 combine : orchestration (A8), méthode et grilles (A6), outils open source de contrôle, et l'humain décideur (A1).

## 3. Avantages du système E21 (faits vérifiables dans le dépôt)

1. **Méthode métier encodée dans des skills** (`analyse-risques`, `stride`, `linddun`, `dread`, `cvss`, `ebios-rm`, `pasta`, `mitre-attack`) : la grille n'est pas laissée à l'initiative du LLM → reproductibilité.
2. **Sources obligatoires à ID stable** (`knowledge_base/README.md`) et **rejet automatique des sources inconnues** : chaque risque du registre ShoPix est sourcé (13/13).
3. **Humain décideur réellement dans la boucle** : `valide_par` rempli par l'analyste ; décisions de rejet (R-13) et de modification (R-14) **traces réelles** dans `06-validation.md`.
4. **Coût quasi nul** : 0 € de licence, mode **mock déterministe** (démo garantie sans LLM externe), ou local via `ollama` — de 0 à ~1 $ pour une analyse complète en API (cf. `CHOIX-MODELES-IA.md`).
5. **Traçabilité complète** : branche dédiée, push à chaque étape, issue #9 suivie sur le board (Todo → In Progress → Review → Done), PR #10 fusionnée.
6. **Garde-fous explicites** (skill `garde-fous-ia`), 6 risques IA couverts : hallucination → rejet sans source ; injection → documents traités comme données non fiables ; fuite → anonymisation ; excès d'autonomie → lecture seule ; empoisonnement → index contrôlé ; dépendance → sorties `.md` autonomes.
7. **Adaptabilité** : bascule de méthode par skill (STRIDE défaut, LINDDUN pour RGPD, EBIOS RM pour OIV/administration, PASTA pour la vision métier) sans toucher aux agents.
8. **Méthode des 6 étapes alignée au sujet E21** (p. 28) et au support CISSP (threat modeling, chap. 10) — documentée dans `documentation/technique/`.

## 4. Inconvénients et parades

| Inconvénient | Parade |
|---|---|
| **Dépendance à l'environnement opencode** (pas un site web autonome) | Sorties 100 % `.md`/`.json` autonomes (test « dépendance » du plan de test) ; abstraction `LlmProvider` interchangeable |
| **Pas de parsing automatique des documents entrants** (PDF/.doc/.xlsx) — l'analyseur ou l'utilisateur résume | Feuille de route : intégration parseurs (PyMuPDF/Docling/OCR) — cf. `PERSPECTIVES` ; en attendant, collecte en une passe par questions |
| **Pas d'analyse technique automatique du système réel** (pas de scan réseau, pas de vuln scan) | Le cas d'emploi vise l'**analyse au sens EBIOS/architecture** (amont) ; les CVE doivent être confirmées (ex. `composer audit`) et sont explicitement non fabriquées |
| **Évaluation probabilité/impact qualitative** (subjectivité résiduelle) | Matrice normalisée + justification unique par risque + validation humaine obligatoire + sources réelles (incidents 2023–2025 du cas ShoPix) |
| **Coût cumulé si API** (7 étapes × reprises, taxe thinking) | Routeur de modèles (petit modèle pour contrôle, cache context) — cf. `CHOIX-MODELES-IA.md` ; local/mock pour la démo |
| **Risque résiduel d'hallucination sur les valeurs** (JSON « valide ≠ correct », plafond ≈ 83 % mesuré en 2026) | Contrôles déterministes (`valider_sources`, schéma, enums) + validation humaine — jamais de verdict automatique |
| **Index ISO 27002 imparfait** (audit : IDs non canoniques dans `knowledge_base/`) | Corrigé au plan P1 (ré-indexation mapping 2022 + re-validation des citations) |

## 5. Positionnement final

E21 n'est **ni un outil de threat modeling de plus, ni un prompt** : c'est un **système d'analyse de risques au sens E21/EBIOS**, qui emprunte aux outils dédiés leur **rigueur méthodologique** (grilles, matrice, sources) et aux systèmes multi-agents leur **automatisation**, tout en gardant l'**analyste comme décideur** de bout en bout. Les deux atouts démontrables : **reproductibilité** (skills) et **traçabilité** (sources + git + board).

## 6. Sources
- Microsoft TMT : learn.microsoft.com (Threat Modeling Tool) · OWASP Threat Dragon : owasp.org/www-project-threat-dragon · IriusRisk : iriusrisk.com · pytm : github.com/iacsec/pytm · AutoGen/CrewAI/LangGraph : docs respectives · STRIDE/LINDDUN : méthodes d'origine (Microsoft, KU Leuven) · EBIOS RM : ANSSI · `documentation/technique/01-architecture.md`, `06-plan-de-test.md` · `analyses/2026-09-23_boutique-en-ligne/` (registre & RAPPORT-CONTROLE).