---
name: mac-test
description: Use when running iOS tests on the Mac mini via SSH. Triggered by "mac mini", "ssh mac-test", "xcodebuild", "lance les tests", "simulateur", "iOS simulator", or "test iOS".
---

# Skill — Tests Apple sur Mac mini

## Configuration SSH

La connexion SSH entre les VMs OpenCode et le Mac mini est configurée par Ansible via le playbook `deploy_mac_access.yml`.

**Paire de clés dédiée :**
- Clé privée : `~/.ssh/id_ed25519_mac` (déployée par Ansible)
- Clé publique dans `authorized_keys` du compte `opencode` sur le Mac mini
- Compte `opencode` (pas `melvin-macmini`)

**Config SSH (`~/.ssh/config`) :**
```
Host mac-test
  HostName 192.168.2.145
  User opencode
  IdentityFile ~/.ssh/id_ed25519_mac
  StrictHostKeyChecking no
```

---

## ⚠️ Règles critiques de connexion

### Pas de shell interactif
```bash
# ❌ INTERDIT — ne fonctionne pas, la connexion est coupée
ssh mac-test

# ✅ TOUJOURS passer une commande en argument
ssh mac-test "git status"
```

Le compte `opencode` utilise un shell restreint (`/usr/local/bin/opencode-restricted.sh`) qui :
- Change automatiquement vers le dossier de travail
- Whitelist les commandes autorisées
- Bloque tout le reste

### Pas de redirections `2>&1`
Le filtre de sécurité bloque `&` dans les commandes. Ne jamais utiliser `2>&1` :
```bash
# ❌ INTERDIT — "interdit" (le & est filtré)
ssh mac-test "xcodebuild test ... 2>&1"

# ✅ OK — la sortie va sur stdout/stderr par défaut
ssh mac-test "xcodebuild test ..."
```

### Sécurité du whitelist
Le script restreint bloque automatiquement :
- Chemins avec `..` (traversal)
- Caractères `| ; & $ `` (injection)
- Toute commande non whitelistée

---

## Chemins

### Dossier de travail
Le working directory SSH est :
```
/Volumes/SSD mac-mini/Users/opencode/projects/
```

### Repo Vel Manager
```
/Volumes/SSD mac-mini/Users/opencode/projects/velo-manager/
```

Utiliser `git -C` pour cibler le sous-dossier repo :
```bash
ssh mac-test "git -C velo-manager status"
ssh mac-test "git -C velo-manager log --oneline -5"
```

### Repo non cloné ?
Le clone est fait **manuellement** par Melvin (pas de `git clone` autorisé via SSH restricted). Demander à Melvin de cloner si le repo n'existe pas.

---

## Commandes autorisées (whitelist)

### Git (depuis le WORKDIR)
| Commande | Exemple |
|----------|---------|
| `git status` | `ssh mac-test "git -C velo-manager status"` |
| `git pull` | `ssh mac-test "git -C velo-manager pull"` |
| `git fetch` | `ssh mac-test "git -C velo-manager fetch"` |
| `git branch` | `ssh mac-test "git -C velo-manager branch"` |
| `git branch -a` | `ssh mac-test "git -C velo-manager branch -a"` |
| `git diff` | `ssh mac-test "git -C velo-manager diff"` |
| `git log` | `ssh mac-test "git -C velo-manager log --oneline -10"` |
| `git stash` | `ssh mac-test "git -C velo-manager stash"` |
| `git stash drop` | `ssh mac-test "git -C velo-manager stash drop"` |
| `git checkout` | `ssh mac-test "git -C velo-manager checkout branch-name"` |
| `git restore` | `ssh mac-test "git -C velo-manager restore file.swift"` |
| `git show` | `ssh mac-test "git -C velo-manager show HEAD"` |

### Lecture seule
| Commande | Exemple |
|----------|---------|
| `ls` | `ssh mac-test "ls velo-manager/"` |
| `cat` | `ssh mac-test "cat velo-manager/CLAUDE.md"` |
| `head` / `tail` | `ssh mac-test "head -20 velo-manager/file.swift"` |
| `grep` | `ssh mac-test "grep -r 'TODO' velo-manager/Velo/"` |
| `find` | `ssh mac-test "find velo-manager -name '*.swift'"` |
| `wc` | `ssh mac-test "wc -l velo-manager/Velo/*.swift"` |

### Écriture (si nécessaire)
| Commande | Exemple |
|----------|---------|
| `mkdir` | `ssh mac-test "mkdir -p velo-manager/new_dir"` |
| `touch` | `ssh mac-test "touch velo-manager/file.txt"` |
| `cp` / `mv` | `ssh mac-test "cp velo-manager/a.txt velo-manager/b.txt"` |

### Xcode / Swift
| Commande | Exemple |
|----------|---------|
| `xcodebuild` | `ssh mac-test "xcodebuild -project velo-manager/Velo.xcodeproj -list"` |
| `swift` | `ssh mac-test "swift --version"` |
| `swiftc` | `ssh mac-test "swiftc --version"` |

### Outils système
| Commande | Exemple |
|----------|---------|
| `python3` | `ssh mac-test "python3 --version"` |
| `node` / `npm` / `npx` | `ssh mac-test "node --version"` |

### Simulateur (whitelist étendu v2)
| Commande | Exemple |
|----------|---------|
| `killall Simulator` | `ssh mac-test "killall Simulator"` |
| `pkill Simulator` | `ssh mac-test "pkill Simulator"` |
| `xcrun simctl erase all` | `ssh mac-test "xcrun simctl erase all"` |
| `xcrun simctl boot` | `ssh mac-test "xcrun simctl boot 'iPhone 17'"` |
| `xcrun simctl list devices` | `ssh mac-test "xcrun simctl list devices"` |

### Nettoyage DerivedData
| Commande | Exemple |
|----------|---------|
| `rm *DerivedData/*` | `ssh mac-test "rm -rf /Volumes/SSD mac-mini/Users/opencode/Library/Developer/Xcode/DerivedData/Velo-*"` |

### Pipes autorisés (lecture seule depuis commandes whitelistées)
```
grep, head, tail, wc, sort, uniq, awk, cut, tr, tee
```
Exemple :
```bash
ssh mac-test "ls velo-manager/ | grep Swift"
ssh mac-test "xcodebuild test ... | tail -30"
```

---

## Lancer les tests

### Prérequis
1. Le repo doit être cloné dans `/Volumes/SSD mac-mini/Users/opencode/projects/velo-manager/`
2. Être sur la bonne branche
3. Faire un `git pull` avant de lancer les tests

### Vérifier les targets et schemes
```bash
ssh mac-test "xcodebuild -project velo-manager/Velo.xcodeproj -list"
```

### Lister les simulateurs disponibles
```bash
ssh mac-test "xcodebuild -project velo-manager/Velo.xcodeproj -scheme Velo -showdestinations | grep iOS"
```

### Build (vérifier que ça compile)
```bash
ssh mac-test "xcodebuild build -project velo-manager/Velo.xcodeproj -scheme Velo -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5'"
```

### Tests unitaires
```bash
ssh mac-test "xcodebuild test -project velo-manager/Velo.xcodeproj -scheme Velo -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -only-testing:VeloTests"
```

### Tests UI (tous)
```bash
ssh mac-test "xcodebuild test -project velo-manager/Velo.xcodeproj -scheme Velo -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -only-testing:VeloUITests"
```

### Tests UI (module spécifique)
```bash
# Smoke tests uniquement
ssh mac-test "xcodebuild test -project velo-manager/Velo.xcodeproj -scheme Velo -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -only-testing:VeloUITests/SmokeUITests"

# Un seul test
ssh mac-test "xcodebuild test -project velo-manager/Velo.xcodeproj -scheme Velo -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5' -only-testing:VeloUITests/SmokeUITests/test_01_appLaunches"
```

### Simulateur recommandé
- **iPhone 17 Pro** (iOS 26.5) — `platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5`
- Le CLAUDE.md local mentionne `iPhone 17` mais le Mac mini a `iPhone 17 Pro`

---

## Workflow agent

1. Modifier le code sur la VM OpenCode
2. `git push` vers GitHub (compte **Pulses-dev**, pas MelvinBzh)
3. `ssh mac-test "git -C velo-manager pull"` — récupérer les changements
4. Vérifier la branche : `ssh mac-test "git -C velo-manager branch"`
5. Si mauvaise branche : `ssh mac-test "git -C velo-manager checkout <branche>"`
6. `ssh mac-test "xcodebuild test ..."` — lancer les tests
7. Lire les logs dans stdout et analyser les erreurs
8. Corriger le code sur la VM et recommencer
9. `git push` final quand tous les tests passent

---

## Branches du projet

| Branche | Contenu |
|---------|---------|
| `main` | Code stable (pas de UI tests) |
| `feature/test-plan-global` | Tests UI complets |

---

## Règles importantes

- **Ne jamais** modifier les settings Xcode, certificats ou profils de provisioning
- **Ne jamais** toucher aux fichiers `.xcconfig`
- Les repos Apple sont sur le compte GitHub **Pulses-dev** (pas MelvinBzh)
- Travailler uniquement dans `/Volumes/SSD mac-mini/Users/opencode/projects/`
- **Toujours** faire `git pull` avant de lancer les tests
- Lire les logs **complets** — les erreurs sont souvent en fin de sortie
- En cas de conflit local : `git stash` → `git pull` → `git stash drop`
- `git clone` n'est pas autorisé via SSH restricted — clones faits manuellement par Melvin
- Ne jamais utiliser `2>&1` dans les commandes SSH (le `&` est filtré)
- Timeout : les UI tests prennent ~7 min, prévoir un timeout de 600s minimum

---

## Dépannage simulateur

### Erreur "Timed out waiting for AX loaded notification"
Le simulateur reste dans un état vérouillé après un run. Solutions :

```bash
# 1. Tuer le processus Simulator
ssh mac-test "killall Simulator"

# 2. Effacer tous les simulateurs
ssh mac-test "xcrun simctl erase all"

# 3. Si toujours bloqué, alterner le modèle de simulateur
#    (chaque modèle a son propre runtime)
ssh mac-test "xcodebuild test ... -destination 'platform=iOS Simulator,name=iPhone 17 Pro,OS=26.5'"
ssh mac-test "xcodebuild test ... -destination 'platform=iOS Simulator,name=iPhone 17,OS=26.5'"

# 4. En dernier recours, supprimer DerivedData et réessayer
ssh mac-test "rm -rf /Volumes/SSD mac-mini/Users/opencode/Library/Developer/Xcode/DerivedData/Velo-*"
```

**Astuce :** alterner entre `iPhone 17 Pro Max`, `iPhone 17 Pro`, `iPhone 17` d'un run à l'autre
permet d'éviter le lock car chaque modèle boote un nouveau processus simulateur.

---

## Diagnostic

### Si une commande échoue avec "non autorisee"
→ La commande n'est pas dans le whitelist. Vérifier `/usr/local/bin/opencode-restricted.sh` sur le Mac mini.

### Si git dit "not a git repository"
→ On n'est pas dans le bon dossier. Utiliser `git -C velo-manager` pour cibler le repo.

### Si xcodebuild ne trouve pas le scheme
→ Vérifier avec `xcodebuild -project velo-manager/Velo.xcodeproj -list`

### Si le simulateur n'est pas trouvé
→ Lister les destinations disponibles avec `-showdestinations`

### Si le repo n'est pas à jour
→ `ssh mac-test "git -C velo-manager pull"` puis relancer le test
