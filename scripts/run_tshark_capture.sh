#!/usr/bin/env bash
# shellcheck disable=SC2155
#
# Headless tshark capture wrapper with ring-buffer rotation.
# Reads configuration from environment variables (optionally loaded via --env-file).
# Intended to be managed via systemd. Supports log redirection and sanity checks.

set -euo pipefail

PROGRAM_NAME="$(basename "$0")"
DEFAULT_ENV_FILE="/etc/tshark_capture.env"

log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp="$(date '+%Y-%m-%d %H:%M:%S')"
    echo "[$timestamp] [$PROGRAM_NAME] [$level] $message" >&2
}

usage() {
    cat <<'USAGE'
Usage: run_tshark_capture.sh [--env-file /path/to/env]

Starts a continuous tshark capture using ring-buffer rotation. Configuration is
taken from environment variables. See config/tshark_capture.env.example for
available settings.

Environment variables (with defaults):
  TSHARK_CAPTURE_INTERFACE        (required)
  TSHARK_CAPTURE_OUTPUT_DIR       (required)
  TSHARK_CAPTURE_FILE_PREFIX      default: capture
  TSHARK_CAPTURE_RING_FILE_SIZE_MB default: 200
  TSHARK_CAPTURE_RING_FILE_COUNT  default: 20
  TSHARK_CAPTURE_BPF_FILTER       default: (empty)
  TSHARK_CAPTURE_EXTRA_OPTIONS    default: (empty)
  TSHARK_CAPTURE_LOG_DIR          default: logs/tshark
  TSHARK_CAPTURE_USER             default: current user

The script ensures output/log directories exist and then execs tshark.
USAGE
}

load_env_file() {
    local env_file="$1"
    if [[ -z "$env_file" ]]; then
        return
    fi

    if [[ ! -f "$env_file" ]]; then
        log "ERROR" "Environment file not found: $env_file"
        exit 1
    fi

    # shellcheck disable=SC1090
    source "$env_file"
    log "INFO" "Loaded environment from $env_file"
}

# Parse arguments
ENV_FILE_OVERRIDE=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --env-file)
            shift
            if [[ $# -eq 0 ]]; then
                log "ERROR" "--env-file requires a path argument"
                exit 1
            fi
            ENV_FILE_OVERRIDE="$1"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log "ERROR" "Unknown argument: $1"
            usage
            exit 1
            ;;
    esac
    shift
done

# Load env file if provided or default exists
if [[ -n "$ENV_FILE_OVERRIDE" ]]; then
    load_env_file "$ENV_FILE_OVERRIDE"
elif [[ -f "$DEFAULT_ENV_FILE" ]]; then
    load_env_file "$DEFAULT_ENV_FILE"
fi

if ! command -v tshark >/dev/null 2>&1; then
    log "ERROR" "tshark not found in PATH"
    exit 1
fi

: "${TSHARK_CAPTURE_INTERFACE:?TSHARK_CAPTURE_INTERFACE must be set}"
: "${TSHARK_CAPTURE_OUTPUT_DIR:?TSHARK_CAPTURE_OUTPUT_DIR must be set}"

TSHARK_CAPTURE_FILE_PREFIX="${TSHARK_CAPTURE_FILE_PREFIX:-capture}"
TSHARK_CAPTURE_RING_FILE_SIZE_MB="${TSHARK_CAPTURE_RING_FILE_SIZE_MB:-200}"
TSHARK_CAPTURE_RING_FILE_COUNT="${TSHARK_CAPTURE_RING_FILE_COUNT:-20}"
TSHARK_CAPTURE_BPF_FILTER="${TSHARK_CAPTURE_BPF_FILTER:-}"
TSHARK_CAPTURE_EXTRA_OPTIONS="${TSHARK_CAPTURE_EXTRA_OPTIONS:-}"
TSHARK_CAPTURE_LOG_DIR="${TSHARK_CAPTURE_LOG_DIR:-logs/tshark}"
TSHARK_CAPTURE_USER="${TSHARK_CAPTURE_USER:-$(id -un)}"

OUTPUT_DIR="${TSHARK_CAPTURE_OUTPUT_DIR%/}"
LOG_DIR="${TSHARK_CAPTURE_LOG_DIR%/}"

mkdir -p "$OUTPUT_DIR"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/${TSHARK_CAPTURE_FILE_PREFIX}.log"
touch "$LOG_FILE"
chown "$TSHARK_CAPTURE_USER" "$LOG_FILE" >/dev/null 2>&1 || true

log "INFO" "Starting tshark capture"
log "INFO" "Interface: $TSHARK_CAPTURE_INTERFACE"
log "INFO" "Output dir: $OUTPUT_DIR"
log "INFO" "File prefix: $TSHARK_CAPTURE_FILE_PREFIX"
if [[ -n "$TSHARK_CAPTURE_BPF_FILTER" ]]; then
    log "INFO" "BPF filter: $TSHARK_CAPTURE_BPF_FILTER"
fi
log "INFO" "Ring buffer: ${TSHARK_CAPTURE_RING_FILE_COUNT} files x ${TSHARK_CAPTURE_RING_FILE_SIZE_MB} MB"

PCAP_PATH_TEMPLATE="$OUTPUT_DIR/${TSHARK_CAPTURE_FILE_PREFIX}_%Y%m%d-%H%M%S.pcap"

EXTRA_ARGS=()
if [[ -n "$TSHARK_CAPTURE_EXTRA_OPTIONS" ]]; then
    # shellcheck disable=SC2206 # allow word splitting for additional options
    EXTRA_ARGS=($TSHARK_CAPTURE_EXTRA_OPTIONS)
fi

TSHARK_CMD=(tshark
    -i "$TSHARK_CAPTURE_INTERFACE"
    -b "files:${TSHARK_CAPTURE_RING_FILE_COUNT}"
    -b "filesize:$((TSHARK_CAPTURE_RING_FILE_SIZE_MB * 1024))"
    -w "$PCAP_PATH_TEMPLATE"
)

if [[ -n "$TSHARK_CAPTURE_BPF_FILTER" ]]; then
    TSHARK_CMD+=(-f "$TSHARK_CAPTURE_BPF_FILTER")
fi

if [[ ${#EXTRA_ARGS[@]} -gt 0 ]]; then
    TSHARK_CMD+=("${EXTRA_ARGS[@]}")
fi

exec "${TSHARK_CMD[@]}" >> "$LOG_FILE" 2>&1

