#!/bin/sh
# Combined CPU/MEM/DISK stats — sets tmux options, outputs nothing
# Replaces separate cpu.sh, mem.sh, disk.sh (3 #() calls → 1)

os=$(uname -s 2>/dev/null)

format_pct() {
  value=$1
  case $value in
    ''|*[!0-9-]*)
      value=0
      ;;
  esac
  printf '%2d' "$value"
}

linux_cpu() {
  cache=/tmp/tmux_cpu_stat
  set -- $(awk '/^cpu /{print $2,$3,$4,$5,$6,$7,$8,$9; exit}' /proc/stat 2>/dev/null)
  if [ $# -lt 8 ]; then
    printf '0'
    return
  fi

  t2=$(($1 + $2 + $3 + $4 + $5 + $6 + $7 + $8))
  i2=$(($4 + $5 + $8))

  if [ -f "$cache" ]; then
    read t1 i1 cpu < "$cache"
    dt=$((t2 - t1))
    [ "$dt" -ge 50 ] && cpu=$((100 * (dt - (i2 - i1)) / dt))
  else
    cpu=0
  fi

  printf '%d %d %d\n' "$t2" "$i2" "$cpu" > "$cache"
  printf '%s' "${cpu:-0}"
}

linux_mem() {
  awk '
    /^MemTotal:/ { total=$2 }
    /^MemAvailable:/ { avail=$2 }
    END {
      if (total > 0) {
        printf "%.0f", (total - avail) / total * 100
      } else {
        print 0
      }
    }
  ' /proc/meminfo 2>/dev/null
}

darwin_cpu() {
  top -l 2 -n 0 2>/dev/null | awk '
    /^CPU usage:/ {
      for (i = 1; i <= NF; i++) {
        if ($i == "idle") {
          idle = $(i - 1)
          gsub(/%/, "", idle)
          cpu = 100 - idle
        }
      }
    }
    END {
      if (cpu == "") {
        print 0
      } else {
        printf "%.0f", cpu
      }
    }
  '
}

darwin_mem() {
  total=$(sysctl -n hw.memsize 2>/dev/null)
  pagesize=$(sysctl -n hw.pagesize 2>/dev/null)

  vm_stat 2>/dev/null | awk -v total="$total" -v pagesize="$pagesize" '
    /^Pages active:/ { active=$3 }
    /^Pages wired down:/ { wired=$4 }
    /^Pages occupied by compressor:/ { compressed=$5 }
    END {
      gsub(/\./, "", active)
      gsub(/\./, "", wired)
      gsub(/\./, "", compressed)

      if (total > 0 && pagesize > 0) {
        used = (active + wired + compressed) * pagesize
        printf "%.0f", used / total * 100
      } else {
        print 0
      }
    }
  '
}

disk_target=/
if [ "$os" = "Darwin" ] && [ -d /System/Volumes/Data ]; then
  disk_target=/System/Volumes/Data
fi

disk=$(df "$disk_target" 2>/dev/null | awk 'NR==2 { gsub(/%/, "", $5); printf "%.0f", $5 }')

case $os in
  Darwin)
    cpu=$(darwin_cpu)
    mem=$(darwin_mem)
    ;;
  *)
    cpu=$(linux_cpu)
    mem=$(linux_mem)
    ;;
esac

cpu=$(format_pct "$cpu")
mem=$(format_pct "$mem")
disk=$(format_pct "$disk")

cpu_fmt="${cpu}%"
mem_fmt="${mem}%"
disk_fmt="${disk}%"

tmux set -gq @cpu_pct "$cpu" \
  \; set -gq @mem_pct "$mem" \
  \; set -gq @disk_pct "$disk" \
  \; set -gq @cpu_fmt "$cpu_fmt" \
  \; set -gq @mem_fmt "$mem_fmt" \
  \; set -gq @disk_fmt "$disk_fmt"
