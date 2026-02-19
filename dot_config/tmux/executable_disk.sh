#!/bin/sh
pct=$(df -h / | awk 'NR==2{gsub(/%/,"",$5); printf "%.0f",$5}')
tmux set -gq @disk_pct "$pct"
printf '%2d' "$pct"
