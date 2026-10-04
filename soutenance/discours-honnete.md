# Discours honnête — ce que le système fait, ce qu'il ne fait pas

> Projet E21 « Des agents IA pour analyser les risques » — M2 Cybersécurité.
> Usage : soutenance, partie « ce que l'outil ne fait PAS » + réponses aux questions du jury.
> Sources : `ROADMAP.md`, `soutenance/CHOIX-MODELES-IA.md`, `soutenance/TESTS.md`, `.opencode/skills/garde-fous-ia/SKILL.md`, `soutenance/MODIFICATIONS.md`, `analyses/2026-09-23_boutique-en-ligne/06-validation.md`.
> Règle de rédaction : aucune affirmation sans référence à un fichier du dépôt ou à une source de la `knowledge_base/`.

## 1. Capacités et limites réelles

### 1.1 Le modèle : `opencode/big-pickle`, un GLLM

- **Capacité réelle** : enchaînement des étapes de la méthode (cadrage → actifs → méthode → menaces → évaluation → traitement → validation), rédaction de registres structurés, synthèse longue (le cas ShoPix = 11 fichiers ≈ 25–30 k tokens) ; le routeur de modèles est documenté tâche par tâche dans `soutenance/CHOIX-MODELES-IA.md` § 3 (un modèle par étape, pas un modèle unique).
- **Limite n° 1 — l'hallucination** : un GLLM peut produire une affirmation plausible et fausse. Conséquence directe, appliquée comme règle du dépôt : **aucune affirmation n'est acceptée sans source** (source de la `knowledge_base/`, code ISO/IEC 27002:2022, STRIDE, LINDDUN, ANSSI, RGPD). Le contrôle est **déterministe et gratuit** (`sources ⊆ index`), pas une promesse du modèle — test **T-05 : 65 citations contrôlées**.
- **Limite n° 2 — pas de raisonnement garanti sur les calculs** : la matrice probabilité × impact et les moyennes DREAD sont **recalculées par un contrôle indépendant** (T-04 : 42 cas, T-03 : 14/14), car « la moyenne affichée par le modèle » n'est pas une preuve.
- **Limite n° 3 — le contexte** : 128 k de contexte suffisent pour une analyse E21 ; le « 1 M de contexte » marketing ne change pas la qualité d'un raisonnement (`CHOIX-MODELES-IA.md` § 2, tâche 5).
- **Limite n° 4 — pas de fabrication de CVE** : aucune note CVSS n'est inventée. Tant que `composer audit` n'a pas tourné sur le SDK PayFlow, la CVE reste un **placeholder signalé comme tel** dans le registre (R-05).

### 1.2 Le livrable : un POC Markdown, pas un produit SaaS

- **Capacité réelle** : les livrables sont des **fichiers `.md` + `.json` versionnés et révisables** (`analyses/<AAAA-MM-JJ>_<cas>/`, registre `registre-risques.md` + `registre_risques.json`), chaque étape séparée, chaque risque justifié. Un correcteur peut refaire le calcul, corriger une valeur, et le diff montre ce qui a changé. Les sorties sont **autonomes** : aucun code propriétaire n'est nécessaire pour les lire.
- **Limite n° 5 — ce n'est pas un service** : pas de SaaS, pas de dashboard public, pas d'API publique, pas de multi-utilisateurs, pas de supervision continue. Une analyse est **un instantané**, pas un service de supervision branché en permanence. L'interface web présente dans le dépôt (Streamlit, `T-14`) est une **application locale** : elle affiche une bibliothèque d'analyses, exporte des rapports et ne lance la chaîne que par une **unique commande fixe** opencode en local (bouton « Lancer la chaîne » — `T-15` : un document piégé uploadé est reproduit verbatim comme donnée, jamais dans la commande). La validation reste pilotée par **fichiers + CI** : le workflow GitHub Actions (`.github/workflows/suite.yml`, `T-18`) rejoue `verification.py` + `make suite` sur chaque push/PR vers `main`, indépendamment de l'interface.
- **Limite n° 6 — périmètre technique** : pas d'analyse de code applicatif réel, pas de test d'intrusion, pas de lecture automatique de CVE ; inventaire et détection restent **locaux et opt-in** (`tools/reseau/`, `T-17`, rapport anonymisé — aucune IP/MAC réelle dans le dépôt). Le cas d'emploi est l'analyse **amont** (architecture, dossier, entretiens), pas l'audit technique.

### 1.3 La trajectoire : ollama / auto-hébergé en roadmap

- **Ce qui est fait** : l'abstraction de modèle est **interchangeable à la configuration** ; le modèle nominal est `opencode/big-pickle` (API cloud), le changement de modèle est une ligne de configuration, pas une réécriture (`ROADMAP.md`, pile « Modèle LLM »).
- **Ce qui est roadmap, pas livré** : **ollama en local / auto-hébergement**. Raison documentée : **souveraineté et vie privée** (le cas traite des données personnelles RGPD : en production, exigence ANSSI = hébergement FR, pas d'API US), **coût** (une analyse ≈ quelques centimes d'API, 0 € en local) et **reproductibilité** (le registre ne dépend plus d'un service tiers).
- **Pourquoi ce n'est pas fait maintenant, et c'est dit tel quel** : la **machine de démonstration** a **~1 Go de RAM libre** ; aucun modèle 7–8B n'y est exécutable dans des conditions de confort (`CHOIX-MODELES-IA.md` § 0 et § 4.4). Les alternatives locales **sur cette machine** supposent une machine ≥ 16 Go (certains modèles 3–5B très légers tourneraient mais ne conviennent pas aux tâches de raisonnement choisies). Le dire est plus honnête que de promettre un mode local qui ne démarrerait pas.

### 1.4 Ce que les agents font — et ce qu'ils ne font pas

| Les agents **font** | Les agents **ne font pas** |
|---|---|
| Pré-travail : inventaire des actifs, DFD et frontières de confiance, choix et justification de la méthode (STRIDE, LINDDUN, EBIOS RM, PASTA) | **Ne décident pas.** `valide_par` est **humain et uniquement humain** — T-08 : 14/14 risques, 28 occurrences, aucun risque « auto-validé » |
| Brouillons : menaces, évaluation (matrice + DREAD), projet de registre, contre-mesures sourcées, synthèse | **N'acceptent pas un risque** à la place du dirigeant : l'acceptation des résiduels est une décision de gestion actée dans `06-validation.md` |
| Contrôles : rejouent la matrice, recalculent DREAD, vérifient `sources ⊆ index`, le schéma JSON et la cohérence Markdown ↔ JSON | **Ne tranchent pas à la place du contrôle déterministe** : le petit modèle mobilisé en contrôle ne sert qu'à signaler une **anomalie sémantique**, jamais à décider (`CHOIX-MODELES-IA.md` § 3, message clé) |
| Rappelent les étapes manquantes : trous détectés dans les entrées, questions à poser, échéances de revue | **Ne déploient pas de contre-mesures** : aucune écriture hors `analyses/**`, `bash` refusé aux agents de chaîne, `e21-controle` en lecture seule |
| Documentent : rapport de contrôle à chaque étape, traces de test archivées | **Ne produisent pas de décision de gestion chiffrée** : les coûts du cas sont des ordres de grandeur issus du dossier, pas des devis |

Frontière à énoncer devant le jury : **le système prépare, vérifie et trace ; l'humain décide et valide.** C'est un choix d'architecture (agents sans outils d'écriture système, humain dans la boucle), pas une promesse.

## 2. Engagements d'honnêteté tenus dans le dépôt

Chaque engagement ci-dessous est **vérifiable par un fichier du dépôt**, pas par une promesse.

1. **Sources obligatoires (anti-hallucination)** — règle du skill `garde-fous-ia` (« aucune sortie acceptée sans source ») et test **T-05** : toutes les sources citées existent à l'index `knowledge_base/` — 65 citations contrôlées. Un identifiant inexistant fait échouer la suite.
2. **Une référence inventée ne peut pas se cacher derrière une référence vraie** — **T-10** vérifie l'index ISO/IEC 27002:2022 canonique jusque dans les consignes vivantes (`.opencode/agents/`, `.opencode/skills/`, `prompts/`) : le contrôle est anti-récursif, pas circulaire.
3. **Les calculs affichés sont recalculés, pas crus** — **T-04** (matrice probabilité × impact, 42 cas) et **T-03** (moyennes DREAD, 14/14) : la valeur affichée doit être la valeur recalculée.
4. **L'injection de prompt est traitée comme une donnée hostile** — **T-07** (régression statique : la consigne cachée d'un « cahier des charges » piégé est absente de toutes les sorties, convention `<<<DONNÉES>>>` en place) et **T-11** (protocole d'exposition réelle, `soutenance/tests/injection/PROTOCOLE.md`), désormais **PASS** : une exécution réelle a été archivée le **2026-10-04** dans `soutenance/tests/injection/resultats/` (document piégé de production, 11 contrôles, ligne hostile conservée **verbatim** comme donnée et absente de toute consigne, `VERDICT: PAS DE CONSIGNE EXECUTEE`) — **avec sa limite assumée et documentée** : aucun appel LLM en direct dans cette exécution, la démonstration avec un agent `e21-*` est prévue en séance.
5. **Un test non exécuté reste visible** — trois statuts (PASS / SKIP / FAIL), un SKIP n'est jamais compté comme PASS, et il est rappelé dans le résultat global (ex. « 10 PASS + 1 SKIP » au 2026-09-24). Le dossier assume ses tests non faits au lieu de les masquer.
6. **Pas de validation automatique** — **T-08** : `valide_par = Melvin RAIMBAULT · 2026-09-24` sur chaque risque (Markdown et JSON).
7. **Rien n'est simulé pour faire joli** — pas de mock de LLM dans le POC, pas de jeu de données « réel » : le cas ShoPix est fictif et déclaré fictif ; les tests d'ingestion utilisent de vraies fixtures de production et le résultat est archivé.
8. **Les limites du système sont écrites dans le dépôt** — `soutenance/PLAN-45MIN.md` § A liste dix limites explicites (dont « pas de CVE fabriquées », « pas de supervision continue », « dépend d'opencode »), et `MODIFICATIONS.md` liste ce qui a **changé** par rapport à une version antérieure, plus flatteuse (index ISO corrigé, 14 risques et non 13, budget 4 300 € et non 2 300 €, T-11 non exécuté).
9. **Les six risques IA du système sont traités par des mesures concrètes** (skill `garde-fous-ia`, chacune contrôlable) : hallucination → sources obligatoires ; injection → séparation consignes/données (`<<<DONNÉES>>>`, entrée traitée comme non fiable) ; fuite → anonymisation avant tout traitement et **aucune donnée réelle vers un service externe** ; excès d'autonomie → agents sans outils d'écriture, l'humain décide ; empoisonnement → base versionnée à IDs stables, pas de mise à jour automatique ; dépendance → **POC piloté par consignes**, modèle interchangeable, ollama en roadmap.
10. **L'incertitude est conservée quand elle existe** : probabilité et impact sont **qualitatifs** (matrice) ; la priorisation DREAD est un **ordre de traitement**, la matrice fait foi ; le rang DREAD de R-09 (7,0) est faible alors que son impact métier est maximal — le dossier le dit au lieu de masquer la tension.

## 3. Encart prêt à lire en soutenance

> « Je vous présente un POC, pas un produit : ce sont des fichiers Markdown et JSON versionnés, que vous pouvez recalculer et corriger vous-même — un livrable que je ne maîtrise plus après coup. Le modèle qui le produit est un grand modèle de langage, donc il peut se tromper avec aplomb : c'est pourquoi **chaque affirmation doit citer une source**, et le contrôle de cette règle est déterministe, pas une promesse du modèle — 65 citations vérifiées. Le système **prépare, vérifie et trace** ; il ne décide pas : la validation de chaque risque reste humaine, et les tests le contrôlent, y compris le scénario d'injection de consigne. Ce que je n'ai pas fait, je le dis : le passage en modèle local est une trajectoire, pas une fonctionnalité livrée, et un test d'injection reste à démontrer en direct devant vous. »

## 4. Questions probables du jury et réponses courtes

| Question | Réponse |
|---|---|
| « Votre IA se trompe ? » | Oui, un GLLM peut halluciner. D'où la règle : pas de source, pas de sortie acceptée (T-05), et des contrôles déterministes qui recalculent la matrice et DREAD (T-03, T-04) au lieu de croire le modèle. |
| « Qui valide le risque ? » | L'humain, toujours : `valide_par` est rempli par l'analyste (T-08, 14/14). Le système produit un **projet** de registre, pas une décision. |
| « Et si un document piégé passe vos consignes ? » | Le contenu d'un document est encadré `<<<DONNÉES>>>` et traité comme **non fiable** : une instruction y est conservée verbatim comme donnée, journalisée, et n'est jamais exécutée. T-07 en régression statique, T-11 en exposition réelle (exécution archivée 04/10/2026, `VERDICT: PAS DE CONSIGNE EXECUTEE`) ; la démo en direct avec un agent `e21-*` reste à jouer en séance. |
| « Pourquoi pas un modèle local tout de suite ? » | La machine de démo a ~1 Go de RAM libre : aucun 7–8B n'y tourne. Le routeur de modèles est prêt, le passage à ollama est une ligne de configuration — c'est une question de machine, pas d'architecture. |
| « Vos chiffres de coût sont fiables ? » | Non, ce sont des **ordres de grandeur de cadrage** issus du dossier du cas, pas des devis ; l'arbitrage est explicitement ouvert et argumenté dans `soutenance/arbitrage-budgetaire.md`. |