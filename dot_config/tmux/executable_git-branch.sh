#!/bin/sh
# Git branch with status color + ahead/behind + file counts (cached)
# Usage: git-branch.sh <path> [plain]
#   default: #[fg=colourXXX]<branch> ... (tmux-colored)
#   plain:   <branch> ... (no color codes, for zoom/copy mode)
#
# Two-level cache:
#   L1: event-based — .git/index or .git/HEAD newer than cache → invalidate
#   L2: time-based  — 5s TTL catches working-tree edits

dir="${1%/}"
cd "$dir" 2>/dev/null || exit

# Cache key from last two path components (no forks)
_p="${dir%/*}"
cache="/tmp/tmux_gb2_${_p##*/}_${dir##*/}"

# ---------- render helper ----------
# args: branch ahead behind staged modified untracked [plain]
render() {
  _b="$1" _a="${2:-0}" _bh="${3:-0}" _s="${4:-0}" _m="${5:-0}" _u="${6:-0}"
  if [ -n "$7" ]; then
    # plain mode
    printf '%s' "$_b"
    [ "$_a" -gt 0 ] && printf '↑%s' "$_a"
    [ "$_bh" -gt 0 ] && printf '↓%s' "$_bh"
    if [ "$_s" -gt 0 ] || [ "$_m" -gt 0 ] || [ "$_u" -gt 0 ]; then
      printf ' '
      [ "$_s" -gt 0 ] && printf '+%s' "$_s"
      [ "$_m" -gt 0 ] && printf '*%s' "$_m"
      [ "$_u" -gt 0 ] && printf '?%s' "$_u"
    fi
  else
    # colored mode — branch color by worst state
    if [ "$_m" -gt 0 ]; then
      printf '#[fg=colour167]%s' "$_b"
    elif [ "$_s" -gt 0 ]; then
      printf '#[fg=colour179]%s' "$_b"
    else
      printf '#[fg=colour114]%s' "$_b"
    fi
    [ "$_a" -gt 0 ] && printf '#[fg=colour114]↑%s' "$_a"
    [ "$_bh" -gt 0 ] && printf '#[fg=colour167]↓%s' "$_bh"
    if [ "$_s" -gt 0 ] || [ "$_m" -gt 0 ] || [ "$_u" -gt 0 ]; then
      printf ' '
      [ "$_s" -gt 0 ] && printf '#[fg=colour179]+%s' "$_s"
      [ "$_m" -gt 0 ] && printf '#[fg=colour167]*%s' "$_m"
      [ "$_u" -gt 0 ] && printf '#[fg=colour246]?%s' "$_u"
    fi
  fi
}

# ---------- find git dir (supports worktrees) ----------
if [ -d "$dir/.git" ]; then
  _gd="$dir/.git"
elif [ -f "$dir/.git" ]; then
  IFS= read -r _line < "$dir/.git"
  _gd="${_line#gitdir: }"
  case "$_gd" in /*) ;; *) _gd="$dir/$_gd" ;; esac
else
  _gd=""
fi

# ---------- cache check ----------
if [ -n "$_gd" ] && [ -f "$cache" ] \
   && [ ! "$_gd/index" -nt "$cache" ] \
   && [ ! "$_gd/HEAD" -nt "$cache" ]; then
  IFS='|' read -r _ts _br _a _bh _s _m _u < "$cache"
  if [ "$(( $(date +%s) - _ts ))" -lt 5 ] && [ -n "$_br" ]; then
    render "$_br" "$_a" "$_bh" "$_s" "$_m" "$_u" "$2"
    exit
  fi
fi

# ---------- background fetch (every 5 min) ----------
if [ -n "$_gd" ]; then
  _fetch_stamp="/tmp/tmux_gf_${_p##*/}_${dir##*/}"
  _now=$(date +%s)
  _do_fetch=0
  if [ -f "$_fetch_stamp" ]; then
    IFS= read -r _last_fetch < "$_fetch_stamp"
    [ "$(( _now - _last_fetch ))" -ge 300 ] && _do_fetch=1
  else
    _do_fetch=1
  fi
  if [ "$_do_fetch" -eq 1 ]; then
    printf '%s' "$_now" > "$_fetch_stamp"
    git fetch --quiet 2>/dev/null &
  fi
fi

# ---------- cache miss — git status ----------
status=$(git status --porcelain -b 2>/dev/null) || exit

# Parse branch from header: ## branch...upstream [ahead N, behind M]
_nl='
'
_head="${status%%${_nl}*}"
branch="${_head#\#\# }"
branch="${branch%%...*}"
branch="${branch%% \[*}"

case "$branch" in
  ""|"HEAD (no branch)"*)
    branch=$(git rev-parse --short HEAD 2>/dev/null || printf '???') ;;
  "Initial commit on "*)
    branch="${branch#Initial commit on }" ;;
  "No commits yet on "*)
    branch="${branch#No commits yet on }" ;;
esac

# Parse ahead/behind (shell builtins only)
ahead=0 behind=0
case "$_head" in
  *"ahead "*)
    _tmp="${_head#*ahead }"
    ahead="${_tmp%%[],]*}" ;;
esac
case "$_head" in
  *"behind "*)
    _tmp="${_head#*behind }"
    behind="${_tmp%%]*}" ;;
esac

# Count file statuses
staged=0 modified=0 untracked=0
_rest="${status#*${_nl}}"
[ "$_rest" = "$status" ] && _rest=""

if [ -n "$_rest" ]; then
  _oldifs="$IFS"
  IFS="$_nl"
  for _line in $_rest; do
    case "$_line" in
      '??'*) untracked=$((untracked + 1)) ;;
      '!!'*) ;;
      *)
        case "$_line" in [MADRC]*) staged=$((staged + 1)) ;; esac
        case "$_line" in ?[MD]*) modified=$((modified + 1)) ;; esac
        ;;
    esac
  done
  IFS="$_oldifs"
fi

# Write cache
printf '%s|%s|%s|%s|%s|%s|%s' \
  "$(date +%s)" "$branch" "$ahead" "$behind" "$staged" "$modified" "$untracked" \
  > "$cache"

render "$branch" "$ahead" "$behind" "$staged" "$modified" "$untracked" "$2"
