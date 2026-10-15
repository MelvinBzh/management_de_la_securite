# 02-methodes.md — Choix de la méthode

## Tableau comparatif

| Méthode | Point de départ | Effort | Idéal pour | Quand choisir |
|---|---|---|---|---|
| **STRIDE** | DFD | Moyen | Analyse générale | Web app, architecture [E48], [E49] |
| **LINDDUN** | Données personnelles | Haut | Vie privée/RGPD | Données sensibles [E64], [E65] |
| **EBIOS RM** | Organisation | Fort | Administrations, enjeux métier | Administrations, OIV, NIS2 [EBIOS-RM-2018] |
| **PASTA** | Objectif métier | Fort | Impact économique | Stratégie, décisions [E52], [E93] |

## Choix retenu

### STRIDE principal + LINDDUN complémentaire + EBIOS RM (A3/A4) extensif

**Justification** : Le cas présente une architecture mutualisée [E49] avec des données personnelles traitées [E17], et des fournisseurs externes (PayFlow, MailJet, hébergeur HostPlanet) [E48]. STRIDE identifie les menaces systématiques sur chaque actif du DFD [E49]. LINDDUN est **non applicable** car aucune donnée personnelle n'est documentée dans ce dossier — le système utilise des noms génériques (clients, commandes, produits). EBIOS RM A3/A4 étend l'analyse aux scénarios stratégiques (A3 : menaces organisationnelles) et opérationnels (A4 : menaces écosystème/fournisseurs) [E48].

**Outils associés** :
- `python3 -m tools.methodes.stride.check_dfd analyses/test-injection-ecole/` → `stride-validation/` (DFD + STRIDE)
- `python3 -m tools.methodes.linddun analyses/test-injection-ecole/` → `linddun-workbook/` (menaces RGPD — **à générer seulement si des données personnelles sont documentées**)
- `python3 -m tools.methodes.ebios analyses/test-injection-ecole/` → `ebios-ateliers/` (A3/A4 : scénarios stratégie/opérationnels)
- DREAD pour la priorisation des menances identifiées

## Pré-requisits

### Données personnelles

Le dossier ne documente **aucune donnée personnelle** dans le système : les clients sont nommés sans détails personnels, les comptes utilisateur utilisent des identifiants génériques. LINDDUN n'est pas applicable. RGPD est donc hors d'application pour ce cas précis [E17].

### Périmètre organisationnel

Le système est une entreprise privée (TPE), non administrative. EBIOS RM est applicable en approche volontaire avec ses ateliers A3/A4 pour couvrir les scénarios organisationnels et écosystème [E48].

## Chaîne retenue

1. **DFD** → Schéma Mermaid de l'architecture zones Internet/DMZ/Fournisseurs, identifiant actifs et flux critiques
2. **STRIDE** → Validation DFD : frontières de confiance entre zones, couverture des 6 catégories (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Environment Modification)
3. **EBIOS RM A3/A4** → Extension aux scénarios stratégiques (A3) et opérationnels (A4) pour les fournisseurs/hebergeurs
4. **DREAD** → Grille de priorisation rapide sur chaque menace STRIDE identifiée

## Justification détaillée par méthode

### STRIDE [E48], [E49]

- **Point fort** : Couverture systématique de tous les actifs (site, API, base, flux)
- **Limite ici** : N'identifie pas spécifiquement les menaces RGPD — mais elles ne sont pas en jeu (non documenté)
- **Adaptation** : S'applique directement au DFD fourni [E49], front ères Internet↔DMZ↔Interne↔Fournisseurs

### EBIOS RM A3/A4 [E48]

- **Atelier A3 (Scénarios stratégiques)** : Couvre menaces externes organisationnelles (cybercriminels, concurrents)
- **Atelier A4 (Scénarios opérationnels)** : Couvre les risques liés aux fournisseurs (HostPlanet, PayFlow, MailJet)
- **Justification** : L'architecture mutualisée [E49] place le système dans un écosystème où les actions des voisins peuvent impacter le site — besoin d'une vision organisationnelle

### DREAD pour priorisation [E48], [E82]

- Usage : Noter rapidement chaque menace STRIDE/EBIOS sur 5 critères (Destruction, Reproducibility, Exploitability, Affected users, Discoverability)
- Alternative CVSS v4.0 possible si données vulnérabilités concrètes disponibles

## Sources citées

- STRIDE : Microsoft Threat Analysis Model [E48]
- EBIOS RM : ANSSI Risk Manager 2018 (EBIOS-RM-2018)
- DREAD : Subject but widely used in agile contexts [E82]
- RGPD : Non applicable, aucune donnée personnelle documentée

---

### Citations validées dans ce fichier

| Identifiant | Usage |
|---|---|
| [E48] | Contexte boutique + périmètre + données personnelles non applicables |
| [E49] | Architecture DFD + contraintes hébergeur mutualisé |
| EBIOS-RM-2018 | Référence méthode EBIOS RM ANSSI |
| [E82] | Justification priorisation DREAD rapide |

---

> **Remarque sur le livrable** : Les dossiers `stride-validation/`, `ebios-ateliers/` et `dread-priorisation/` sont à générer par les outils CLI correspondants. Le dossier `linddun-workbook/` n'est **pas généré** car aucune donnée personnelle n'est documentée dans ce cas.
