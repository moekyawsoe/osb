#!/usr/bin/env bash
set -e

# Run OSB with local python3
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):$PYTHONPATH"
python3 -m osb.main "$@"
