#!/usr/bin/env bash

set -eux

POSITIONAL_ARGS=()

while [[ $# -gt 0 ]]; do
  case $1 in
    -static)
      POSITIONAL_ARGS+=("-rc") 
      shift
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

set -- "${POSITIONAL_ARGS[@]}"

exec /usr/bin/ar "$@"
