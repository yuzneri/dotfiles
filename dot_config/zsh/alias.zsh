if builtin command -v mise > /dev/null; then
  mnpm()  { local s="$1"; shift; mise use -g "npm:${s}" "$@"; }
  mbun()  { local s="$1"; shift; mise use -g "bun:${s}" "$@"; }
  mpipx()  { local s="$1"; shift; mise use -g "pipx:${s}" "$@"; }
  mgh() { local s="$1"; shift; mise use -g "github:${s}" "$@"; }
  mgl() { local s="$1"; shift; mise use -g "gitlab:${s}" "$@"; }
fi

alias ls='ls --color=auto'
alias ll='ls -lh --color=auto'
