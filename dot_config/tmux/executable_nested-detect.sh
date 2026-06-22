#!/bin/bash
# Set tmux @nested and related styles based on the attaching client's env.
# A client is considered "nested" if it sets LC_TMUX_NESTED=1
# (typically forwarded via ssh SendEnv from an outer tmux).
set -u

client_pid="${1:-}"
nested=0

if [ -n "$client_pid" ] && [ -r "/proc/$client_pid/environ" ]; then
  if grep -qz '^LC_TMUX_NESTED=1' "/proc/$client_pid/environ" 2>/dev/null; then
    nested=1
  fi
fi

if [ "$nested" = 1 ]; then
  tmux set -g @nested "#[fg=#1c1c1c,bg=#ff8c3a,bold] SSH #[default]"
  tmux set -g pane-border-lines heavy
  tmux set -g pane-border-style "fg=#5f3a1a"
  tmux set -g pane-active-border-style "fg=#ff8c3a"
else
  tmux set -g @nested ""
  tmux set -g pane-border-lines single
  tmux set -g pane-border-style "fg=#303030"
  tmux set -g pane-active-border-style "fg=#af87ff"
fi

tmux refresh-client -S 2>/dev/null || true
