# Projet E21 — Ce que la V2 apporte

**Bilan des améliorations faites après la soutenance école (24 septembre → 12 octobre 2026)**

> **En une phrase.** Depuis l'audit du 24/09, **9 des 13 limites et promesses de la V1 sont levées (69 %)**, 1 est partielle et 3 sont
> laissées hors périmètre volontairement. Le code passe de **640 à ≈ 22 500 lignes**, et ajouter un document ne demande plus
> **≈ 3 h** de recalcul mais **13 minutes**.

| | V1 école (24/09) | V2 (12/10) |
|---|---|---|
| Nature | Consignes pour des agents, sans code applicatif | Application : ingestion, site, pilote, connaissance, validation, exports |
| Documents lus | Saisie à la main | 7 formats (PDF, OCR, Word, Excel, PowerPoint, images, ZIP) |
| Modèle d'IA | Service cloud | **Local** (Ollama, carte de 12 Go), un modèle par rôle |
| Preuve d'une affirmation | Source de référentiel | Extrait exact du document, vérifié : **97 %** (435 sur 447) |
| Niveau, identifiants, registre | Écrits par le modèle | Calculés par le programme ; registre en 2 min au lieu de 30 |
| Après un nouveau document | Refaire l'analyse | Mise à jour en **13 min**, lignes inchangées identiques |
| Cas traités | 1 (ShoPix, 14 risques) | 3 (+ Nordval 151 risques, SanteTech 135 risques) |
| Tests | 11 contrôles (T-01 à T-11) | 20 contrôles de référence + 35 fichiers de tests |

**Les 5 points restés ouverts à l'audit du 24/09**

| Point ouvert | État |
|---|---|
| Analyse manuelle de référence (#17) | **Fait** (15/10, SanteTech) : 30 risques de référence, 16 couverts par les agents, 7 partiels, 7 non couverts ; à relire et valider par l'analyste |
| Test d'injection réel (T-11) | **Fait** (04/10) : 11 contrôles, aucune consigne exécutée ; **rejoué le 15/10 avec le modèle en direct** sur la chaîne complète : 116 risques, aucune consigne exécutée |
| Tests pérennes (P2) | **Fait** : 35 fichiers de tests |
| Arbitrage budgétaire (#20) | Documenté (04/10) ; décision de l'analyste à confirmer |
| Base de connaissances par thématique | Non fait |

**Ce qui reste à faire, dit sans détour** : sécuriser le site (authentification, SSH, Ollama, conteneur) · trop de risques « Critique »
(48 à 56 %) · doublons d'actifs et citations inexistantes · valider les risques (SanteTech 0 sur 135, Nordval 10 sur 151) ·
relire et valider l'analyse de référence SanteTech (30 risques) · répéter le test d'injection en direct sur d'autres cas.

**Pour le prouver** : `03-DOSSIER-ECRIT-V2.pdf` (explications) · `06-PREUVES-TESTS-IA-LOCALE/` (livrables réels, journal, décisions,
exports) · `07-CONTROLE-DES-CHIFFRES.pdf` (chaque chiffre avec sa source et sa commande) · tag `ecole-2026-09-24` sur GitHub.
