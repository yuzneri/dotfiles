#!/bin/sh
# Combined CPU/MEM/DISK stats — sets tmux options, outputs nothing
# Replaces separate cpu.sh, mem.sh, disk.sh (3 #() calls → 1)

# CPU (differential from /proc/stat)
cache=/tmp/tmux_cpu_stat
set -- $(awk '/^cpu /{print $2,$3,$4,$5,$6,$7,$8,$9; exit}' /proc/stat)
t2=$(($1+$2+$3+$4+$5+$6+$7+$8)); i2=$(($4+$5+$8))
if [ -f "$cache" ]; then
  read t1 i1 cpu < "$cache"
  dt=$((t2-t1))
  [ "$dt" -ge 50 ] && cpu=$((100*(dt-(i2-i1))/dt))
else
  cpu=0
fi
printf '%d %d %d' "$t2" "$i2" "$cpu" > "$cache"

# Memory
mem=$(awk '/^MemTotal:/{t=$2} /^MemAvailable:/{a=$2} END{printf "%.0f",(t-a)/t*100}' /proc/meminfo)

# Disk
disk=$(df / | awk 'NR==2{gsub(/%/,"",$5); printf "%.0f",$5}')

# Format with right-aligned padding (match previous %2d behavior)
cpu=$(printf '%2d' "$cpu")
mem=$(printf '%2d' "$mem")
disk=$(printf '%2d' "$disk")

# Set all options in one tmux call (1 fork instead of 3)
tmux set -gq @cpu_pct "$cpu" \; set -gq @mem_pct "$mem" \; set -gq @disk_pct "$disk"
