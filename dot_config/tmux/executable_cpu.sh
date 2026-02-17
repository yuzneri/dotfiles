#!/bin/sh
color() {
  if [ "$1" -ge 80 ] 2>/dev/null; then printf '#[fg=#d75f5f]'
  elif [ "$1" -ge 50 ] 2>/dev/null; then printf '#[fg=#d7af5f]'
  else printf '#[fg=#87d787]'
  fi
}
cpu=$(top -bn2 -d0.5 | awk '/^%Cpu/{v=100-$8} END{printf "%.0f", v}')
printf '#[fg=#585858]C:%s%2d%%' "$(color "$cpu")" "$cpu"
