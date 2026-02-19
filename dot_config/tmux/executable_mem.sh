#!/bin/sh
pct=$(awk '/^MemTotal:/{t=$2} /^MemAvailable:/{a=$2} END{printf "%.0f",(t-a)/t*100}' /proc/meminfo)
tmux set -gq @mem_pct "$pct"
printf '%2d' "$pct"
