#!/bin/bash
# Relaunch exo uniquement (ne tue pas exoflash)
pkill -f "uv run exo.*--api-port 52415"
sleep 1
export EXO_PORT=52415
nohup uv run exo --api-port 52415 > ~/.exo/exo_log/exo.log 2>&1 &
sleep 1
tail -f ~/.exo/exo_log/exo.log
