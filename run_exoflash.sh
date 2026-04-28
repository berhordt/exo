#!/bin/bash
# Wrapper pour lancer exoflash avec configuration isolée

cd ~/exoflash

# Répertoire de données isolé
export EXO_HOME=~/.exoflash

# Port API différent
export EXO_PORT=52416

# Namespace libp2p différent → isolation réseau complète
export EXO_LIBP2P_NAMESPACE=exoflash

# Créer les répertoires
mkdir -p ~/.exoflash/exo_log

# Lancer exo
exec .venv/bin/python3 .venv/bin/exo --api-port 52416
