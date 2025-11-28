#!/bin/bash
# Wrapper for semi-automated local analysis
# Usage: ./analyze_local.sh [pcap_staging_dir]

STAGING_DIR=${1:-"$HOME/pcap_staging"}
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Ensure staging directory exists
if [ ! -d "$STAGING_DIR" ]; then
    echo "Creating staging directory: $STAGING_DIR"
    mkdir -p "$STAGING_DIR"
fi

echo "Analyzing PCAPs in: $STAGING_DIR"
python3 "$PROJECT_ROOT/scripts/watch_and_process_pcaps.py" --local-dir "$STAGING_DIR" --once
