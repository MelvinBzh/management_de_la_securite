---
name: stride
description: Use to identify threats on an application/system described by a DFD (data-flow diagram). Default Microsoft grid of 6 threat categories. Best when analyzing a web application at design time. Combine with DREAD/CVSS for prioritization.
---

# STRIDE (Microsoft)

Grille de **6 catégories de menaces**, en partie le « miroir » des propriétés de sécurité (CIA + authentificité + non-répudiation + autorisation). On applique les 6 questions à **chaque élément du DFD** (acteurs, processus, stockages, flux).

## La grille

| Lettre | Menace | Question à poser | Contre-mesure type | Propriété violée |
|---|---|---|---|---|
| **S** | Usurpation (Spoofing) | Quelqu'un peut-il se faire passer pour un autre ? | Authentification forte (MFA), certificats | Authenticité |
| **T** | Falsification (Tampering) | Peut-on modifier les données ? | Signature numérique, contrôle d'intégrité | Intégrité |
| **R** | Répudiation (Repudiation) | Peut-on nier avoir fait une action ? | Journaux horodatés, signature | Non-répudiation |
| **I** | Divulgation (Information disclosure) | Des informations peuvent-elles fuiter ? | Chiffrement, contrôle d'accès | Confidentialité |
| **D** | Déni de service (DoS) | Peut-on rendre le service indisponible ? | Redondance, limitation de débit | Disponibilité |
| **E** | Élévation de privilèges (Elevation of privilege) | Peut-on obtenir plus de droits ? | Moindre privilège | Autorisation |

## Méthode d'application

1. Dessiner le **DFD** du système + frontières de confiance (passage des données entre zones : Internet → DMZ → réseau interne).
2. Les attaques se concentrent au **passage des frontières** : y chercher en priorité.
3. Appliquer STRIDE élément par élément ; noter `categorie = STRIDE-X`.
4. STRIDE dit **quoi chercher**, pas comment prioriser → compléter par DREAD ou CVSS.

Référence : Microsoft STRIDE ; A. Shostack, *Threat Modeling: Designing for Security* (2014) [source autorisée].