#!/usr/bin/env bash
#
# Fix the pcap-watcher.service to use the correct user
#

set -e

echo "Fixing pcap-watcher.service to use 'pepper' user instead of 'hadoop'..."
sudo sed -i 's/^User=hadoop$/User=pepper/' /etc/systemd/system/pcap-watcher.service
sudo sed -i 's/^Group=hadoop$/Group=pepper/' /etc/systemd/system/pcap-watcher.service

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Restarting pcap-watcher.service..."
sudo systemctl restart pcap-watcher.service

echo ""
echo "Checking service status..."
systemctl status pcap-watcher.service --no-pager || true

echo ""
echo "Done! The service should now run as user 'pepper'."
echo "If you prefer to create a 'hadoop' user instead, run:"
echo "  sudo useradd -r -s /bin/bash hadoop"

