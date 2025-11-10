#!/usr/bin/env python3
"""
Continuous PCAP ingestion helper for the Hadoop network analysis pipeline.

This script watches a local directory for new *.pcap files (e.g., generated
continually by Wireshark), uploads each completed capture to HDFS, and runs the
existing preprocessing, traffic volume, and conversation analysis jobs for
every new file. Results are written to per-capture subdirectories in HDFS so
previous outputs are preserved.

Example usage:

    python3 scripts/watch_and_process_pcaps.py \
        --local-dir /var/log/pcap_outbox \
        --hdfs-input-base /input/pcap/live \
        --interval 30

Optional flags let you archive processed PCAPs locally and customise the HDFS
output locations. Run with --help for the full list of options.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATE_FILE = PROJECT_ROOT / "state" / "pcap_watch_state.json"


class CommandError(RuntimeError):
    """Raised when a subprocess command exits unsuccessfully."""


def log(message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}", flush=True)


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> None:
    """Run a shell command and raise CommandError on failure."""
    pretty_cmd = " ".join(str(part) for part in cmd)
    log(f"Running: {pretty_cmd}")
    try:
        subprocess.run(cmd, check=True, cwd=str(cwd or PROJECT_ROOT))
    except subprocess.CalledProcessError as exc:
        raise CommandError(f"Command failed ({exc.returncode}): {pretty_cmd}") from exc


def ensure_hdfs_directory(path: str) -> None:
    run_command(["hadoop", "fs", "-mkdir", "-p", path])


def upload_pcap_to_hdfs(local_path: Path, hdfs_dir: str) -> str:
    """Upload the PCAP file to the specified HDFS directory."""
    ensure_hdfs_directory(hdfs_dir)
    run_command(["hadoop", "fs", "-put", "-f", str(local_path), hdfs_dir])
    return f"{hdfs_dir.rstrip('/')}/{local_path.name}"


def slugify(name: str) -> str:
    safe_chars = []
    for char in name:
        if char.isalnum() or char in ("-", "_"):
            safe_chars.append(char)
        else:
            safe_chars.append("-")
    return "".join(safe_chars).strip("-") or "capture"


def file_is_stable(path: Path, checks: int, interval: float) -> bool:
    """Return True when the file size stops changing for the specified checks."""
    if checks <= 1:
        return True

    last_size = None
    stable_count = 0

    for _ in range(checks):
        try:
            current_size = path.stat().st_size
        except FileNotFoundError:
            return False

        if current_size == last_size:
            stable_count += 1
        else:
            stable_count = 1
        last_size = current_size

        if stable_count >= checks:
            return True
        time.sleep(interval)

    return False


def load_state(state_file: Path) -> Dict[str, Dict[str, float]]:
    if not state_file.exists():
        return {}
    try:
        with state_file.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, OSError):
        log(f"Warning: could not read state file {state_file}, starting fresh.")
    return {}


def save_state(state_file: Path, state: Dict[str, Dict[str, float]]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    tmp_file = state_file.with_suffix(".tmp")
    with tmp_file.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    tmp_file.replace(state_file)


def move_to_archive(src: Path, archive_dir: Path) -> Path:
    archive_dir.mkdir(parents=True, exist_ok=True)
    destination = archive_dir / src.name
    counter = 1
    while destination.exists():
        destination = archive_dir / f"{src.stem}_{counter}{src.suffix}"
        counter += 1
    shutil.move(str(src), destination)
    return destination


def process_capture(
    local_path: Path,
    args: argparse.Namespace,
    state: Dict[str, Dict[str, float]],
) -> None:
    """Upload the capture to HDFS and run the full Hadoop pipeline."""
    run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = slugify(local_path.stem)
    run_id = f"{slug}_{run_timestamp}"

    hdfs_input_dir = f"{args.hdfs_input_base.rstrip('/')}/{run_id}"
    hdfs_pre_output = f"{args.hdfs_preprocessing_base.rstrip('/')}/{run_id}"
    hdfs_traffic_output = f"{args.hdfs_traffic_base.rstrip('/')}/{run_id}"
    hdfs_conversation_output = f"{args.hdfs_conversation_base.rstrip('/')}/{run_id}"

    log(f"Uploading {local_path} to HDFS directory {hdfs_input_dir}")
    upload_pcap_to_hdfs(local_path, hdfs_input_dir)

    preprocessing_script = PROJECT_ROOT / "scripts" / "run_preprocessing.sh"
    traffic_script = PROJECT_ROOT / "scripts" / "run_traffic_volume.sh"
    conversation_script = PROJECT_ROOT / "scripts" / "run_conversation_analysis.sh"

    run_command(
        [str(preprocessing_script), hdfs_input_dir, hdfs_pre_output]
    )
    run_command(
        [str(traffic_script), hdfs_pre_output, hdfs_traffic_output]
    )
    run_command(
        [str(conversation_script), hdfs_pre_output, hdfs_conversation_output]
    )

    if args.archive_dir:
        archived_path = move_to_archive(local_path, args.archive_dir)
        log(f"Archived local PCAP to {archived_path}")

    file_stat = local_path.stat()
    state[str(local_path.resolve())] = {
        "size": file_stat.st_size,
        "mtime": file_stat.st_mtime,
        "processed_at": time.time(),
        "run_id": run_id,
        "hdfs_input": hdfs_input_dir,
        "hdfs_preprocessing": hdfs_pre_output,
        "hdfs_traffic": hdfs_traffic_output,
        "hdfs_conversation": hdfs_conversation_output,
    }
    log(f"Processing for {local_path.name} complete (run id: {run_id}).")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Watch a directory for new PCAP files and run the Hadoop analysis pipeline."
    )
    parser.add_argument(
        "--local-dir",
        required=True,
        type=Path,
        help="Directory where Wireshark writes PCAP files.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=30.0,
        help="Polling interval (seconds) between directory scans.",
    )
    parser.add_argument(
        "--stability-checks",
        type=int,
        default=2,
        help="Number of consecutive size checks required before a file is considered complete.",
    )
    parser.add_argument(
        "--stability-interval",
        type=float,
        default=3.0,
        help="Seconds to wait between stability checks.",
    )
    parser.add_argument(
        "--hdfs-input-base",
        default="/input/pcap/live",
        help="Base HDFS directory for raw PCAP uploads.",
    )
    parser.add_argument(
        "--hdfs-preprocessing-base",
        default="/output/preprocessing/live",
        help="Base HDFS directory for preprocessing job outputs.",
    )
    parser.add_argument(
        "--hdfs-traffic-base",
        default="/output/traffic_volume/live",
        help="Base HDFS directory for traffic volume job outputs.",
    )
    parser.add_argument(
        "--hdfs-conversation-base",
        default="/output/conversation_analysis/live",
        help="Base HDFS directory for conversation analysis outputs.",
    )
    parser.add_argument(
        "--archive-dir",
        type=Path,
        help="Optional local directory where processed PCAPs will be moved.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=DEFAULT_STATE_FILE,
        help=f"Path to the JSON file storing processed-file metadata (default: {DEFAULT_STATE_FILE}).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process any currently unhandled PCAPs and exit (no continuous watching).",
    )

    args = parser.parse_args(argv)
    local_dir: Path = args.local_dir.expanduser().resolve()
    if not local_dir.exists():
        parser.error(f"Local directory does not exist: {local_dir}")

    if args.archive_dir:
        args.archive_dir = args.archive_dir.expanduser().resolve()

    args.state_file = args.state_file.expanduser().resolve()
    state = load_state(args.state_file)

    log(f"Starting PCAP watcher in {local_dir}")
    log(f"Polling interval: {args.interval}s, stability checks: {args.stability_checks}")

    try:
        while True:
            processed_any = False
            for pcap_path in sorted(local_dir.glob("*.pcap")):
                if not pcap_path.is_file():
                    continue
                resolved = str(pcap_path.resolve())
                stat_result = pcap_path.stat()
                prev = state.get(resolved)
                already_processed = (
                    prev
                    and prev.get("size") == stat_result.st_size
                    and prev.get("mtime") == stat_result.st_mtime
                )
                if already_processed:
                    continue

                log(f"Detected new or updated PCAP: {pcap_path.name}")
                if not file_is_stable(
                    pcap_path, args.stability_checks, args.stability_interval
                ):
                    log(f"Skipping {pcap_path.name} (file still growing).")
                    continue

                try:
                    process_capture(pcap_path, args, state)
                    save_state(args.state_file, state)
                    processed_any = True
                except CommandError as exc:
                    log(f"ERROR: {exc}")
                except Exception as exc:
                    log(f"ERROR processing {pcap_path.name}: {exc}")

            if args.once:
                if not processed_any:
                    log("No new PCAP files detected.")
                break

            time.sleep(args.interval)

    except KeyboardInterrupt:
        log("Stopping watcher (Ctrl+C).")
        return 0

    log("Watcher finished.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

