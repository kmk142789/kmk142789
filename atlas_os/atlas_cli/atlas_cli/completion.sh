#!/usr/bin/env bash
# Bash completion script for atlas CLI.
_atlas_complete() {
  local cur prev opts
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  prev="${COMP_WORDS[COMP_CWORD-1]}"
  opts="status nodes storage logs"
  if [[ ${COMP_CWORD} -eq 1 ]]; then
    COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
    return 0
  fi
  if [[ ${COMP_WORDS[1]} == "storage" ]]; then
    COMPREPLY=( $(compgen -W "list" -- ${cur}) )
    return 0
  fi
}
complete -F _atlas_complete atlas
