# Récapitulatif des risques IA — Étape 1 (existant & actifs) · cas « ShoPix »

> Contrôle `e21-controle` du 2026-09-24 sur `00-description.md` / `01-actifs.md` — **re-contrôle après reprise (verdict final OK)**.
> Cadre : skill `garde-fous-ia` + **`ANSSI-IA-GEN`** (ANSSI 2024) — trois familles : manipulation, infection des données, exfiltration.

## Grille des six risques IA

| Risque IA | Classe ANSSI | Contrôle appliqué | Résultat |
|---|---|---|---|
| **Hallucination** | (désinformation) | Chaque affirmation confrontée à la base (`knowledge_base/`) ou à l'étude de cas ; placeholder CVE conservé tel quel (pas de CVE inventée) ; valeurs économiques re-dérivées du cas (≈ 1 150 €/semaine = 15 000 ÷ 13 ; ≈ 3 450 € en pic) | **OK** — motif de REJET du 1er contrôle corrigé (valeurs ≈ 330/990 € de A-07 vérifiées au calcul) |
| **Injection de prompt** | Manipulation | Recherche de marqueurs d'instructions cachées (« ignore tes instructions », etc.) dans les deux fichiers | OK — aucun |
| **Fuite de données** | Exfiltration | Recherche e-mails / IP / téléphones / noms réels ; seuls les noms fictifs du cas présents | OK — aucune donnée réelle |
| **Excès d'autonomie** | — | Les sorties formulent des hypothèses et propositions, aucune décision finale (validation humaine aux étapes 5/6) | OK |
| **Empoisonnement** | Infection des données | Sources limitées aux ID versionnés de la base ; aucune donnée externe injectée ; aucune instruction issue d'un document exécutée | OK |
| **Dépendance** | — | Fichiers Markdown autonomes, exploitables sans l'outil | OK |

## Exigences `ANSSI-IA-GEN` vérifiées

- **Manipulation (injection)** : aucun contenu d'entrée interprété comme instruction dans les livrables — OK.
- **Infection des données (empoisonnement)** : base de connaissances versionnée, pas de mise à jour automatique ; inputs de l'étude de cas traités comme données non fiables — OK.
- **Exfiltration (fuite)** : aucune donnée sensible réelle dans les fichiers, aucune transmission externe — OK.
- **Contrôle humain** : aucun verdict ici ne vaut décision de sécurité ; l'étape 6 (validation humaine formelle) reste la porte d'acceptation, et l'hypothèse « poste local admin » (F5) est à confirmer avec le dirigeant.
- **Journalisation** : présent rapport + `RAPPORT-CONTROLE.md` consignent requêtes, verdicts, motifs et historique des rejets.

## Verdict

**OK.** Un seul motif bloquant au 1er contrôle (valeur économique non dérivable du cas + contradiction A-07), corrigé et vérifié au re-contrôle. Tous les autres contrôles IA étaient et restent OK.