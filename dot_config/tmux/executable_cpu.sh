#!/bin/sh
# /proc/stat fields: user nice system idle iowait irq softirq steal
cache=/tmp/tmux_cpu_stat
set -- $(awk '/^cpu /{print $2,$3,$4,$5,$6,$7,$8,$9; exit}' /proc/stat)
t2=$(($1+$2+$3+$4+$5+$6+$7+$8)); i2=$(($4+$5+$8))
if [ -f "$cache" ]; then
  read t1 i1 pct < "$cache"
  dt=$((t2-t1))
  if [ "$dt" -ge 50 ]; then
    pct=$((100*(dt-(i2-i1))/dt))
  fi
else
  pct=0
fi
printf '%d %d %d' "$t2" "$i2" "$pct" > "$cache"
tmux set -gq @cpu_pct "$pct"
printf '%2d' "$pct"
