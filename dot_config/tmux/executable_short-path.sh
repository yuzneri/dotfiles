#!/bin/sh
p="${1:-$PWD}"
p="${p#"$HOME"}"
[ "$p" != "$1" ] && p="~$p"
if [ "${#p}" -gt 30 ]; then
  echo "${p##*/}"
else
  echo "$p"
fi
