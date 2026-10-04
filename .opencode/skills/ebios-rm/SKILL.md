---
name: ebios-rm
description: Use when the risk analysis must follow the French EBIOS Risk Manager method (ANSSI). Best for administrations, critical operators and organization-level risk analysis. 5 ateliers from cadrage to traitement du risque.
---

# EBIOS Risk Manager (ANSSI, 2018)

Méthode française de gestion des risques en **5 ateliers**. Adaptée quand le système est relié à l'organisation / aux enjeux métier, ou exigence de l'ANSSI.

## Les 5 ateliers

1. **Cadrage et socle** — périmètre, valeurs métier, événements redoutés, socle de sécurité (existant à protéger).
2. **Sources de risque** — qui peut attaquer (accès de l'attaquant, objectifs), pour quelles motivations.
3. **Scénarios stratégiques** — chemins d'attaque via l'**écosystème** (fournisseurs, partenaires, prestataires).
4. **Scénarios opérationnels** — modes opératoires techniques de l'attaquant (techniques concrètes).
5. **Traitement du risque** — plan de sécurité, actions, suivi du **risque résiduel**.

## Mapping vers les 6 étapes du projet E21

| Projet E21 | EBIOS RM |
|---|---|
| 1 · Existant / actifs | Atelier 1 (cadrage, socle) |
| 2 · Choix méthode | EBIOS RM retenu comme méthode |
| 3 · Menaces | Ateliers 3–4 (scénarios stratégiques + opérationnels) |
| 4 · Évaluation | Risque = gravité × vraisemblance |
| 5 · Traitement | Atelier 5 (traitement + plan de sécurité) |
| 6 · Validation | Risque résiduel accepté + suivi |

## Livrables types d'un atelier EBIOS

- Atelier 1 → périmètre + socle + événements redoutés
- Atelier 2 → tableau des sources de risque (accès | cible | motivations)
- Ateliers 3–4 → scénarios d'attaque (straégiques/opérationnels) avec chemins
- Atelier 5 → plan de traitement + risque résiduel

Référence : ANSSI, *EBIOS Risk Manager* (2018) [source autorisée dans `knowledge_base`].

## Mise en œuvre opérationnelle

L'agent e21-ebios peut générer automatiquement un squelette opérationnel des 5 ateliers à partir des fichiers d'entrée d'une analyse.

### CLI

```bash
python3 -m tools.methodes.ebios <dossier_analyse> [--out DIR]
```

- Par défaut : `analyses/<cas>/ebios-ateliers/`
- `--out` : permet de rediriger la sortie vers un autre répertoire (explicite uniquement)

### Patron des livrables par atelier (sections obligatoires)

| Atelier | Fichier | Sections obligatoires |
|---|---|---|
| **A1** — Cadrage et socle | `A1-cadrage-socle.md` | Bandeau EBIOS RM, périmètre (reprise verbatim de 00-description.md), valeurs métier / biens essentiels (reprise verbatim de 01-actifs.md), **Événements redoutés**, socle de sécurité / mesures existantes, parties prenantes |
| **A2** — Sources de risque | `A2-sources-risque.md` | Bandeau EBIOS RM, **tableau des sources de risque** (accès \| cible \| motivations), suggestions selon type de système (web public / interne / données santé), champs à compléter |
| **A3** — Scénarios stratégiques | `A3-scenarios-strategiques.md` | Bandeau EBIOS RM, écosystème (fournisseurs, hébergeurs, prestataires), scénarios via l'écosystème (chemins), reprises verbatim des fichiers d'entrée |
| **A4** — Scénarios opérationnels | `A4-scenarios-operationnels.md` | Bandeau EBIOS RM, **gravité (1-4)**, **vraisemblance (1-4)**, **niveau (matrice EBIOS 4×4)** (laissés vides), tableaux par menaces principales (exploitation de vulnérabilité, déni de service, compromission de compte, fuite de données) |
| **A5** — Traitement du risque | `A5-traitement-risque.md` | Bandeau EBIOS RM, plan de traitement par risque identifié, colonnes : risque, niveau de risque, traitement (**réduire/transférer/éviter/accepter** selon skill analyse-risques), actions, responsable, échéance, **risque résiduel** |
| **README** | `README.md` | Rappel du déroulé des 5 ateliers, mode d'emploi, règles d'utilisation |

**Règle impérative :** Tout contenu emprunté aux fichiers d'entrée est recopié **verbatim** (jamais reformulé). Le reste est marqué `> _À compléter par l'analyste_`. Chaque fichier commence par `<!-- EBIOS RM — atelier généré — à valider par l'analyste -->`.

### Utilisation par les agents e21-*

Les agents e21-* doivent citer ce skill quand ils analysent un dossier où `ebios-ateliers/` existe. Ils s'appuient sur ces livrables pour :

- **Étape 3 (menaces)** : exploiter A3 (scénarios stratégiques) et A4 (scénarios opérationnels) pour formaliser les menaces/scénarios
- **Étape 4 (évaluation)** : s'appuyer sur A4 (gravité/vraisemblance) pour alimenter l'évaluation des risques
- **Étape 5 (traitement)** : s'appuyer sur A5 (plan de traitement + risque résiduel) pour proposer les contre-mesures et valider le risque résiduel

Les agents peuvent régénérer le squelette à l'identique (idempotent) si les fichiers d'entrée ont été mis à jour, sans jamais modifier les fichiers d'entrée.
