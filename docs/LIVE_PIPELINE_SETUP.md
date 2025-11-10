# Live Pipeline Setup

This guide explains how to run the network analysis pipeline continuously by combining:

1. A headless `tshark` capture that rotates `.pcap` files into a staging directory.
2. The Hadoop ingestion watcher that uploads each capture and executes the MapReduce jobs.
3. Systemd units to keep both components alive and automatically start them on boot.

## Prerequisites

- Wireshark CLI (`tshark`) installed (`sudo apt install tshark` or equivalent).
- Java and Hadoop already configured (see `docs/CLUSTER_RUN_GUIDE.md`).
- Python 3 with dependencies from `requirements.txt`.
- Sufficient disk space for rotating capture files and HDFS outputs.
- Root privileges (or delegated capabilities) to access the capture interface.

### Allowing non-root captures (optional)

To run the capture under a non-root account, grant `tshark` the required capabilities:

```bash
sudo setcap 'CAP_NET_ADMIN,CAP_NET_RAW+eip' "$(command -v dumpcap)"
```

Alternatively, keep the service running as `root` (the default in `tshark-capture.service`).

## Configuration

1. **Clone or deploy this repository** to a stable location accessible by both services (e.g., `/opt/dist-netanalysis`).

2. **Copy and edit the environment templates**:

   ```bash
   sudo install -m 640 config/tshark_capture.env.example /etc/tshark_capture.env
   sudo install -m 640 config/pcap_watcher.env.example /etc/pcap_watcher.env
   sudo chown root:root /etc/tshark_capture.env /etc/pcap_watcher.env
   ```

   Adjust at least:
   - `TSHARK_CAPTURE_INTERFACE` to the appropriate NIC (use `ip link` to list).
   - `TSHARK_CAPTURE_OUTPUT_DIR` and `WATCH_LOCAL_DIR` to the directory where captures are stored (must match).
   - HDFS base paths if your cluster uses different conventions.

3. **Create required directories** and set ownership:

   ```bash
   sudo mkdir -p /var/lib/pcap-stream
   sudo mkdir -p /var/log/tshark
   sudo chown root:root /var/lib/pcap-stream /var/log/tshark
   ```

   If you run the watcher as a non-root Hadoop user, ensure it has read access to `/var/lib/pcap-stream`.

4. **Propagate master hostname aliases** so Hadoop tasks can reach the control node by either `master-node` or `octavius`:

   ```bash
   # Run on each node with sudo privileges
   sudo /home/pepper/dist-netanalysis/scripts/apply_master_alias.sh
   ```

   Override `MASTER_IP`/`MASTER_HOST`/`MASTER_ALIAS` when deploying to different environments. Confirm with `getent hosts master-node` and `getent hosts octavius` on every worker.

5. **Review systemd unit files** in `deploy/systemd/` and update paths or service users if your install location differs from `/home/pepper/dist-netanalysis`. Pay attention to:
   - `WorkingDirectory`
   - `ExecStart`
   - The service account (`User=`/`Group=` lines)
   - `Environment="HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop"` for Hadoop CLI access (change the path if Hadoop lives elsewhere)

## Service Installation

Copy the units and reload systemd:

```bash
sudo cp deploy/systemd/tshark-capture.service /etc/systemd/system/
sudo cp deploy/systemd/pcap-watcher.service /etc/systemd/system/
sudo systemctl daemon-reload
```

Enable and start the capture first, then the watcher:

```bash
sudo systemctl enable --now tshark-capture.service
sudo systemctl enable --now pcap-watcher.service
```

## Health Checks

- Verify the services are active:

  ```bash
  systemctl status tshark-capture.service
  systemctl status pcap-watcher.service
  ```

- Inspect logs via `journalctl` (the capture script also appends to `/var/log/tshark/<prefix>.log`):

  ```bash
  sudo journalctl -u tshark-capture.service -f
  sudo journalctl -u pcap-watcher.service -f
  ```

- Confirm rotating files are appearing in `TSHARK_CAPTURE_OUTPUT_DIR` and uploaded to HDFS:

  ```bash
  ls -lh /var/lib/pcap-stream
  hadoop fs -ls /input/pcap/live
  ```

- Check watcher state and outputs:
  - `state/pcap_watch_state.json` records processed files.
  - Hadoop job logs remain available under the usual `hadoop fs -cat /output/...` paths.

## Operational Tips

- Rotate or ship `TSHARK_CAPTURE_LOG_DIR` and journal logs into central logging.
- Monitor disk usage on the capture directory; the ring buffer limits total size to `filesize * files`, but leave headroom.
- Use the `--archive-dir` watcher option by extending the systemd service if long-term local retention is required.
- Consider running a staging HDFS job (`hadoop fs -du -h`) to watch space consumption of live outputs.

## Recommended Next Improvements

- **Alerting**: Add systemd watchdogs, integrate with Prometheus/Alertmanager, or configure email alerts for service failures.
- **Metrics**: Expose capture statistics (packet counts, drop rates) via `tshark -z io,stat` or wrap with a metrics exporter for Grafana dashboards.
- **Security Hardening**: Restrict service accounts, enforce `ProtectSystem=full` and `ProtectHome=yes` in the unit files, and secure `/etc/*.env` with minimal permissions.
- **Automated Testing**: Build CI checks that run `watch_and_process_pcaps.py --once` against `test_data/sample.pcap`.
- **Scalability**: Evaluate Kafka/Flume ingestion if multiple capture nodes must feed a central Hadoop cluster.

Refer back to `README.md` for the MapReduce job details and to `docs/CLUSTER_RUN_GUIDE.md` for cluster-level deployment guidance.

