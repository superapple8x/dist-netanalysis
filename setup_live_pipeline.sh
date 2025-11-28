#!/usr/bin/env bash
#
# Setup script for Live Pipeline based on docs/LIVE_PIPELINE_SETUP.md
# Run with sudo privileges when password is required.
#

set -e

PROJECT_DIR="/home/pepper/dist-netanalysis"

echo "=== Step 1: Setting capabilities for dumpcap (optional) ==="
sudo setcap 'CAP_NET_ADMIN,CAP_NET_RAW+eip' "$(command -v dumpcap)"

echo ""
echo "=== Step 2: Copying and setting up environment configuration files ==="
sudo install -m 640 "${PROJECT_DIR}/config/tshark_capture.env.example" /etc/tshark_capture.env
sudo install -m 640 "${PROJECT_DIR}/config/pcap_watcher.env.example" /etc/pcap_watcher.env
sudo chown root:root /etc/tshark_capture.env /etc/pcap_watcher.env

echo ""
echo "=== Step 3: Creating required directories ==="
sudo mkdir -p /var/lib/pcap-stream
sudo mkdir -p /var/log/tshark
sudo chown root:root /var/lib/pcap-stream /var/log/tshark

echo ""
echo "=== Step 4: Propagating master hostname aliases ==="
sudo "${PROJECT_DIR}/scripts/apply_master_alias.sh"

echo ""
echo "=== Step 5: Installing systemd service files ==="
sudo cp "${PROJECT_DIR}/deploy/systemd/tshark-capture.service" /etc/systemd/system/
sudo cp "${PROJECT_DIR}/deploy/systemd/pcap-watcher.service" /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "=== Step 6: Enabling and starting services ==="
sudo systemctl enable --now tshark-capture.service
sudo systemctl enable --now pcap-watcher.service

echo ""
echo "=== Step 7: Health checks ==="
echo "Checking service status..."
systemctl status tshark-capture.service --no-pager || true
echo ""
systemctl status pcap-watcher.service --no-pager || true

echo ""
echo "=== Setup complete! ==="
echo ""
echo "To monitor logs, run:"
echo "  sudo journalctl -u tshark-capture.service -f"
echo "  sudo journalctl -u pcap-watcher.service -f"
echo ""
echo "To check captured files:"
echo "  ls -lh /var/lib/pcap-stream"
echo "  hadoop fs -ls /input/pcap/live"
echo ""
echo "Remember to edit /etc/tshark_capture.env and /etc/pcap_watcher.env"
echo "to configure capture interface, directories, and HDFS paths."

