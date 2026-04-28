# EXO / EXOFLASH — Procédure de redémarrage

## Architecture

| Instance | Machines | Port API | Namespace libp2p | Rôle |
|----------|----------|----------|------------------|------|
| **exo** | ML1 + ML2 | 52415 | (défaut) | Cluster distribué (1 master + 1 worker) |
| **exoflash** | ML1 | 52416 | `exoflash` | Instance isolée (master seul) |

## Isolation réseau

L'isolation entre `exo` et `exoflash` repose sur deux mécanismes complémentaires :

1. **`EXO_HOME`** — Répertoire de données séparé (`~/.exo` vs `~/.exoflash`)
   - Identité du nœud (`node_id.keypair`)
   - Logs et caches
   - Modèles téléchargés

2. **`EXO_LIBP2P_NAMESPACE`** — Clé de réseau privé libp2p différente
   - `exo` : namespace par défaut (`v0.0.1` hardcodé)
   - `exoflash` : `EXO_LIBP2P_NAMESPACE=exoflash`
   - Les deux instances ne peuvent **pas** communiquer au niveau protocole

## Procédure de redémarrage

### Redémarrer exo (cluster ML1 + ML2)

**⚠️ IMPORTANT** : Toujours redémarrer **ML1 en premier**, puis ML2.

**Sur ML1** :
```bash
ssh cgeek@192.168.1.148
cd ~/exo
pkill -f "exo.*52415"
sleep 2
nohup .venv/bin/python3 .venv/bin/exo --api-port 52415 > ~/.exo/exo_log/exo.log 2>&1 &
```

**Sur ML2** :
```bash
ssh cgeek@192.168.1.20
cd ~/exo
pkill -f "exo.*52415"
sleep 2
nohup .venv/bin/python3 .venv/bin/exo --api-port 52415 > ~/.exo/exo_log/exo.log 2>&1 &
```

**Vérification** (attendre 5-10 secondes) :
```bash
# Sur ML1 ou ML2
curl -s http://localhost:52415/health 2>/dev/null | head -1
grep "elected master\|demoting self" ~/.exo/exo_log/exo.log | tail -5
```

### Redémarrer exoflash (instance isolée ML1)

```bash
ssh cgeek@192.168.1.148
cd ~/exoflash
pkill -f "exo.*52416"
sleep 2
nohup ./run_exoflash.sh > ~/.exoflash/exo_log/exo.log 2>&1 &
```

**Vérification** :
```bash
curl -s http://localhost:52416/ | head -1
grep "EXO_LIBP2P_NAMESPACE" ~/.exoflash/exo_log/exo.log | tail -1
# Doit afficher : EXO_LIBP2P_NAMESPACE: exoflash
```

## Erreur classique : les nœuds ne se voient plus

**Symptôme** : Après redémarrage de ML2, les deux nœuds restent en mode "master" séparés.

**Cause** : ML1 conserve un état obsolète de l'ancienne instance ML2.

**Solution** :
1. Arrêter les deux nœuds
2. **Redémarrer ML1 en premier** (il s'élit master avec une identité fraîche)
3. Redémarrer ML2 (il découvre ML1 et se dégrade en worker)

## Fichiers de configuration

### exo (~/exo/relaunch.sh)
```bash
#!/bin/bash
pkill -f "uv run exo.*--api-port 52415"
sleep 1
export EXO_PORT=52415
nohup uv run exo --api-port 52415 > ~/.exo/exo_log/exo.log 2>&1 &
sleep 1
tail -f ~/.exo/exo_log/exo.log
```

### exoflash (~/exoflash/run_exoflash.sh)
```bash
#!/bin/bash
cd ~/exoflash
export EXO_HOME=~/.exoflash
export EXO_PORT=52416
export EXO_LIBP2P_NAMESPACE=exoflash
mkdir -p ~/.exoflash/exo_log
exec .venv/bin/python3 .venv/bin/exo --api-port 52416
```

## Vérification de l'état

| Vérification | Commande | Résultat attendu |
|--------------|----------|------------------|
| exo répond | `curl http://localhost:52415/` | `<!doctype html>` |
| exoflash répond | `curl http://localhost:52416/` | `<!doctype html>` |
| exo élu master | `grep elected ~/.exo/exo_log/exo.log` | `Node ... elected master` |
| exoflash isolé | `grep NAMESPACE ~/.exoflash/exo_log/exo.log` | `EXO_LIBP2P_NAMESPACE: exoflash` |
| Pas de conflit | `grep "Cancelling other" ~/.exo/exo_log/exo.log` | Vide (après stabilisation) |

## Ports en écoute typiques

Chaque instance expose deux ports :
- **Port API** (fixe) : 52415 pour exo, 52416 pour exoflash
- **Port libp2p** (dynamique) : assigné par l'OS, visible avec `lsof -Pan -p <PID> -i`

## Dépôts Git

- **exo** : `https://lab.cgeek.fr/cgeek/exo.git` (branche `fix/prefill-step-size`)
- **dflash-testing** : `https://lab.cgeek.fr/clawrence/dflash-testing.git` (branche `main`)

---

*Dernière mise à jour : 2026-05-13*
