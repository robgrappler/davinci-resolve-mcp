#!/bin/bash
# Delegates to the real quick-start script in scripts/.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/scripts/run-now.sh" "$@"
