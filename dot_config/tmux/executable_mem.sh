#!/bin/sh
color() {
  if [ "$1" -ge 80 ] 2>/dev/null; then printf '#[fg=#d75f5f]'
  elif [ "$1" -ge 50 ] 2>/dev/null; then printf '#[fg=#d7af5f]'
  else printf '#[fg=#87d787]'
  fi
}
mem=$(awk '/^MemTotal:/{t=$2} /^MemAvailable:/{a=$2} END{printf "%.0f", (t-a)/t*100}' /proc/meminfo)
printf '#[fg=#585858]M:%s%2d%%' "$(color "$mem")" "$mem"
