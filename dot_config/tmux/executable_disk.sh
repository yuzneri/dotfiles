#!/bin/sh
color() {
  if [ "$1" -ge 80 ] 2>/dev/null; then printf '#[fg=#d75f5f]'
  elif [ "$1" -ge 50 ] 2>/dev/null; then printf '#[fg=#d7af5f]'
  else printf '#[fg=#87d787]'
  fi
}
disk=$(df -h / | awk 'NR==2{gsub(/%/,"",$5); printf "%.0f", $5}')
printf '#[fg=#585858]D:%s%3d%%' "$(color "$disk")" "$disk"
