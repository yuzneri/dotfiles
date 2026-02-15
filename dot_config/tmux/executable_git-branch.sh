#!/bin/sh
cd "$1" 2>/dev/null || exit
b=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit
if ! git diff --quiet 2>/dev/null; then
  printf '#[fg=colour167]%s' "$b"
elif ! git diff --cached --quiet 2>/dev/null; then
  printf '#[fg=colour179]%s' "$b"
else
  printf '#[fg=colour114]%s' "$b"
fi
