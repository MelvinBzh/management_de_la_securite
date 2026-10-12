# 05 — Choix du cas d'étude et du modèle de menaces

## Cas d'étude : A — Boutique en ligne (recommandé)

> Site marchand d'une PME : site web, paiement par un prestataire, base clients, back-office.

**Actifs à ne pas oublier** : données clients, compte administrateur, disponibilité du site, back-office, intégration du prestataire de paiement.

**Pourquoi ce cas** :
- Frontière de confiance idéale : **Internet → prestataire de paiement** (flux de données financières) et **Internet → back-office admin** → parfait pour expliquer le DFD.
- Volumétrie maîtrisable : 8–12 risques suffisent pour une démonstration complète en 45 min.
- Pas de données médicales (pas de contrainte renforcée RGPD pour la démo).

**Plan B** : B — Téléconsultation médicale + LINDDUN si le groupe veut marquer le point « vie privée » (données de santé).

## Modèle de menaces : STRIDE (par défaut)

STRIDE interactif (Microsoft) = grille de 6 questions, idéale dès la conception avec un DFD.

| Lettre | Menace | Question | Contre-mesure type |
|---|---|---|---|
| S | Usurpation | Se faire passer pour un autre ? | MFA, certificats |
| T | Falsification | Modifier des données ? | Signature, hachage |
| R | Répudiation | Nier une action ? | Journaux horodatés |
| I | Divulgation | Faire fuiter ? | Chiffrement, contrôle d'accès |
| D | Déni de service | Rendre indisponible ? | Redondance, limitation de débit |
| E | Élévation | Obtenir plus de droits ? | Moindre privilège |

**Justification** : cas web (application) analysé via un DFD → STRIDE est le plus adapté (gré product system-centric). On le complète par **DREAD/CVSS** pour la priorisation et **MITRE ATT&CK** pour étayer certains scénarios.

## Chaîne retenue (comme le support, chap. 10)

1. **Décrire** : DFD du cas + frontières de confiance
2. **Identifier** : STRIDE
3. **Détailler** : arbres d'attaque / ATT&CK sur les risques critiques
4. **Prioriser** : matrice probabilité × impact (qualitatif)
5. **Traiter** : réduire / transférer / éviter / accepter

## Base de connaissances (`knowledge_base/`)

- `stride.md` — grille STRIDE + contre-mesures par catégorie (IDs `STRIDE-S`…)
- `iso27002.md` — contre-mesures ISO/IEC 27002:2022 pertinentes (IDs `ISO27002-A.x.y`)
- `oss_fr.md` — consignes ANSSI (chiffrement, MFA) (IDs `ANSSI-*`)
- `cve.json` — CVE réelles exploitables pour les menaces (via API NVD)

Toute source citée par un agent doit exister dans cette base (validé programmatiquement).