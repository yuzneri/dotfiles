for dir in /usr/share/zsh/vendor-completions /usr/share/zsh/site-functions /usr/local/share/zsh/site-functions; do
  if [ -d "$dir" ]; then
    FPATH="$dir:$FPATH"
  fi
done

# Autoloads
autoload -Uz compinit bashcompinit vcs_info add-zsh-hook
compinit
bashcompinit

# VCS
zstyle ':vcs_info:*' actionformats '(%b|%a)'
zstyle ':vcs_info:*' formats "%F{green}%c%u(%b)%f"
zstyle ':vcs_info:git:*' check-for-changes true
zstyle ':vcs_info:git:*' stagedstr "%F{yellow}"
zstyle ':vcs_info:git:*' unstagedstr "%F{red}"
precmd() { vcs_info }

# Completion
zstyle ':completion:*' completer _oldlist _complete _approximate _correct _match _prefix
zstyle ':completion:*' matcher-list '' 'm:{a-z}={A-Z}' '+m:{A-Z}={a-z}'
zstyle ':completion:*' list-colors ${(s.:.)LS_COLORS}
zstyle ':completion:*' menu select=1
zstyle ':completion:*' use-cache true
zstyle ':completion:*:*files' ignored-patterns '*?.o' '*?~' '*\#'
zstyle ':completion:*:sudo:*' command-path $path
zstyle ':completion:*:processes' command 'ps x -o pid,s,args'
zstyle ':completion:*:*:kill:*:processes' list-colors '=(#b) #([%0-9]#)*=0=01;31'
bindkey "^[[Z" reverse-menu-complete

if command -v fzf > /dev/null 2>&1; then
  function select-history() {
    BUFFER=$(history -n -r 1 | fzf --no-sort +m --query "$LBUFFER")
    CURSOR=$#BUFFER
    zle reset-prompt
  }
  zle -N select-history
  bindkey '^r' select-history
fi
