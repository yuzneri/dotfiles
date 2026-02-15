#!/bin/sh
cd "$1" 2>/dev/null || exit
b=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) || exit

# Branch colour based on working-tree / index state
if ! git diff --quiet 2>/dev/null; then
  printf '#[fg=colour167]%s' "$b"
elif ! git diff --cached --quiet 2>/dev/null; then
  printf '#[fg=colour179]%s' "$b"
else
  printf '#[fg=colour114]%s' "$b"
fi

# Ahead / behind upstream
counts=$(git rev-list --left-right --count HEAD...@{upstream} 2>/dev/null) || exit 0
ahead=$(printf '%s' "$counts" | cut -f1)
behind=$(printf '%s' "$counts" | cut -f2)

if [ "$ahead" -gt 0 ] 2>/dev/null && [ "$behind" -gt 0 ] 2>/dev/null; then
  printf ' #[fg=colour179]⇡%s⇣%s' "$ahead" "$behind"
elif [ "$ahead" -gt 0 ] 2>/dev/null; then
  printf ' #[fg=colour114]⇡%s' "$ahead"
elif [ "$behind" -gt 0 ] 2>/dev/null; then
  printf ' #[fg=colour167]⇣%s' "$behind"
fi
