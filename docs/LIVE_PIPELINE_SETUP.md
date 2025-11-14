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

2. **Identify your network interface** (required for tshark capture):

   ```bash
   # List all network interfaces
   ip link show
   # or
   ifconfig -a
   ```

   Look for the active interface (usually `eth0`, `enp0s31f6`, `ens33`, etc.). The interface should show `state UP`. Note the exact name as it's case-sensitive.

3. **Copy and edit the environment templates**:

   ```bash
   sudo install -m 640 config/tshark_capture.env.example /etc/tshark_capture.env
   sudo install -m 640 config/pcap_watcher.env.example /etc/pcap_watcher.env
   sudo chown root:root /etc/tshark_capture.env /etc/pcap_watcher.env
   ```

   **Edit `/etc/tshark_capture.env`** and set at minimum:
   - `TSHARK_CAPTURE_INTERFACE` to the exact interface name from step 2 (e.g., `enp0s31f6`, not `eth0`).
   - `TSHARK_CAPTURE_OUTPUT_DIR` to your desired capture directory (default: `/var/lib/pcap-stream`).

   **Edit `/etc/pcap_watcher.env`** and ensure:
   - `WATCH_LOCAL_DIR` matches `TSHARK_CAPTURE_OUTPUT_DIR` exactly (same path).
   - HDFS base paths match your cluster configuration.

4. **Create required directories** and set ownership:

   **If running services as root** (default):
   ```bash
   sudo mkdir -p /var/lib/pcap-stream
   sudo mkdir -p /var/log/tshark
   sudo chown root:root /var/lib/pcap-stream /var/log/tshark
   ```

   **If running tshark-capture as non-root user** (e.g., `pepper`):
   ```bash
   sudo mkdir -p /var/lib/pcap-stream
   sudo mkdir -p /var/log/tshark
   sudo chown pepper:pepper /var/lib/pcap-stream /var/log/tshark
   # Also ensure the user can read the config file
   sudo chown root:pepper /etc/tshark_capture.env
   sudo chmod 640 /etc/tshark_capture.env
   ```

   **If running pcap-watcher as non-root Hadoop user** (e.g., `hadoop`):
   ```bash
   # Ensure the Hadoop user can read from the capture directory
   sudo chmod 755 /var/lib/pcap-stream
   # Or add the Hadoop user to the same group and use group permissions
   sudo chgrp hadoop /var/lib/pcap-stream
   sudo chmod 750 /var/lib/pcap-stream
   ```

5. **Propagate master hostname aliases** so Hadoop tasks can reach the control node by either `master-node` or `octavius`:

   ```bash
   # Run on each node with sudo privileges
   sudo /home/pepper/dist-netanalysis/scripts/apply_master_alias.sh
   ```

   Override `MASTER_IP`/`MASTER_HOST`/`MASTER_ALIAS` when deploying to different environments. Confirm with `getent hosts master-node` and `getent hosts octavius` on every worker.

6. **Review systemd unit files** in `deploy/systemd/` and update paths or service users if your install location differs from `/home/pepper/dist-netanalysis`. Pay attention to:
   - `WorkingDirectory`
   - `ExecStart`
   - The service account (`User=`/`Group=` lines)
   - `Environment="HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop"` for Hadoop CLI access (change the path if Hadoop lives elsewhere)

## Pre-Flight Checks

Before starting the services, verify these prerequisites:

1. **Hadoop cluster is running**:
   ```bash
   # Check if Hadoop commands work
   hadoop version
   
   # Verify HDFS is accessible
   hadoop fs -ls /
   
   # If you get "Connection refused", start Hadoop:
   start-dfs.sh
   start-yarn.sh
   
   # Verify all services are running
   jps
   # Should show: NameNode, DataNode, ResourceManager, NodeManager, etc.
   ```

2. **HDFS is not in safe mode**:
   ```bash
   # Check safe mode status
   hdfs dfsadmin -safemode get
   
   # If in safe mode, leave it (only do this if you understand the implications)
   hdfs dfsadmin -safemode leave
   ```

3. **Network interface exists and is up**:
   ```bash
   # Verify the interface specified in TSHARK_CAPTURE_INTERFACE exists
   ip link show <your-interface-name>
   # Should show "state UP"
   ```

4. **Directories and permissions are correct**:
   ```bash
   # Check capture directory exists and is writable
   ls -ld /var/lib/pcap-stream
   touch /var/lib/pcap-stream/.test && rm /var/lib/pcap-stream/.test
   
   # Check config files are readable
   sudo -u <service-user> cat /etc/tshark_capture.env > /dev/null
   ```

5. **tshark is installed and accessible**:
   ```bash
   which tshark
   tshark --version
   ```

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

## Expected Outcomes & Validation

Follow the checklist below to confirm the live pipeline is operating correctly.  If any step fails, double-check the previous configuration sections before proceeding.

1. **Systemd reports healthy services**  
   Both services should be `active (running)`:

   ```bash
   systemctl is-active tshark-capture.service   # → active
   systemctl is-active pcap-watcher.service     # → active
   ```

2. **Rotating capture files appear locally**  
   Within one polling interval (`WATCH_INTERVAL`) you should see files like:

   ```bash
   ls -lh /var/lib/pcap-stream/
   # live_20251113-120501.pcap  live_20251113-120531.pcap  …
   ```
   Their sizes will stabilise once `dumpcap` finishes each rotation.

3. **Watcher log shows successful processing**  
   Tail the journal or the service output and look for messages similar to:

   ```text
   [2025-11-13 12:06:08] Detected new or updated PCAP: live_20251113-120501.pcap
   [2025-11-13 12:06:45] Processing for live_20251113-120501.pcap complete (run id: live_20251113-120501_20251113T120645Z).
   ```

4. **HDFS directories are populated**  
   After a capture is processed, the following directories (with matching *run-id*) should exist and contain `part-00000` files:

   ```bash
   hadoop fs -ls /input/pcap/live/
   hadoop fs -ls /output/preprocessing/live/
   hadoop fs -ls /output/traffic_volume/live/
   hadoop fs -ls /output/conversation_analysis/live/
   ```

5. **Job outputs are readable**  
   Example quick sanity-check:

   ```bash
   hadoop fs -cat /output/traffic_volume/live/*/part-00000 | head
   # 192.168.1.10  1048576  2097152
   ```

6. **Optional archive directory**  
   If you configured `--archive-dir`, the processed `.pcap` moves there instead of remaining in the capture directory.

When every item above passes, the tester can be confident the live pipeline is ingesting traffic, running all three Hadoop jobs, and persisting results without manual intervention.

## Troubleshooting

This section addresses common issues encountered during setup and operation.

### Issue 1: pcap-watcher Service Fails with "Connection refused"

**Symptoms:**
- Service status shows `failed` or `restarting`
- Logs show: `ERROR: Command failed (1)` when running `hadoop fs -mkdir`
- Error message: `Connection refused` from Hadoop

**Cause:** The Hadoop cluster (NameNode) is not running or not accessible.

**Solution:**
```bash
# 1. Check if Hadoop is running
jps
# If NameNode/DataNode are missing, start Hadoop:
start-dfs.sh
start-yarn.sh

# 2. Verify HDFS is accessible
hadoop fs -ls /

# 3. Check if HDFS is in safe mode (prevents writes)
hdfs dfsadmin -safemode get
# If in safe mode and you need to write:
hdfs dfsadmin -safemode leave

# 4. Restart the watcher service
sudo systemctl restart pcap-watcher.service
```

**Prevention:** Always verify Hadoop is running before starting the watcher service. Consider adding a systemd dependency (see Issue 6).

### Issue 2: HDFS Safe Mode Prevents Operations

**Symptoms:**
- Commands like `hadoop fs -rm` or `hadoop fs -mkdir` fail
- Error: `org.apache.hadoop.hdfs.server.namenode.SafeModeException`

**Cause:** HDFS enters safe mode after startup or when datanodes are missing.

**Solution:**
```bash
# Check safe mode status
hdfs dfsadmin -safemode get

# Leave safe mode (only if you understand the implications)
hdfs dfsadmin -safemode leave

# Verify you can now write
hadoop fs -mkdir -p /test && hadoop fs -rm -r /test
```

**Note:** Safe mode is a safety feature. Only leave it if you're certain your cluster is healthy.

### Issue 3: tshark-capture Service Fails with Permission Errors

**Symptoms:**
- Service in restart loop
- Logs show: `Operation not permitted` or `Permission denied`
- Multiple permission-related errors

**Common permission issues:**

**3a. Cannot read config file:**
```bash
# Error: /etc/tshark_capture.env: Permission denied
# Solution: Fix ownership and permissions
sudo chown root:<service-user> /etc/tshark_capture.env
sudo chmod 640 /etc/tshark_capture.env
```

**3b. Cannot write to output directory:**
```bash
# Error: Cannot write to /var/lib/pcap-stream
# Solution: Fix directory ownership
sudo chown <service-user>:<service-user> /var/lib/pcap-stream
sudo chmod 755 /var/lib/pcap-stream
```

**3c. Cannot capture packets (dumpcap fails):**
```bash
# Error: Operation not permitted when launching dumpcap
# Solution A: Run as root (default in service file)
# Solution B: Grant capabilities to dumpcap
sudo setcap 'CAP_NET_ADMIN,CAP_NET_RAW+eip' "$(command -v dumpcap)"
# Then update service file to run as non-root user
```

**3d. Cannot write log file:**
```bash
# Error: Cannot write to log directory
# Solution: Fix log directory ownership
sudo chown <service-user>:<service-user> /var/log/tshark
sudo chmod 755 /var/log/tshark
```

### Issue 4: Wrong Network Interface Configured

**Symptoms:**
- Service starts but no packets are captured
- Logs show interface errors
- Files are created but remain empty (0 bytes)

**Cause:** The interface name in `/etc/tshark_capture.env` doesn't match the actual interface.

**Solution:**
```bash
# 1. List all interfaces
ip link show
# or
ifconfig -a

# 2. Identify the active interface (state UP)
# Common names: eth0, enp0s31f6, ens33, wlan0

# 3. Update the config file
sudo nano /etc/tshark_capture.env
# Change: TSHARK_CAPTURE_INTERFACE="eth0"
# To:     TSHARK_CAPTURE_INTERFACE="enp0s31f6"  # (your actual interface)

# 4. Restart the service
sudo systemctl restart tshark-capture.service
```

### Issue 5: Filename Template Confusion

**Symptoms:**
- Service runs but files have unexpected names
- Files named like `capture_00001_20251113-120501.pcap` instead of expected format

**Explanation:** This is **normal behavior**. When using tshark's ring buffer (`-b files:`), tshark automatically appends a sequence number to prevent overwrites. The format is: `<prefix>_<seq>_<timestamp>.pcap`.

**No action needed** - the watcher script handles these filenames correctly. The sequence numbers ensure files are unique even if rotation happens quickly.

### Issue 6: Services Start Before Hadoop is Ready

**Symptoms:**
- Services start on boot but fail immediately
- Hadoop cluster takes time to initialize

**Solution:** Add a systemd dependency (optional improvement):

Edit `/etc/systemd/system/pcap-watcher.service` and add:
```ini
[Unit]
After=hadoop-namenode.service network-online.target
Wants=hadoop-namenode.service
```

**Note:** This requires a hadoop-namenode.service unit. Alternatively, increase `RestartSec` to give Hadoop more time to start.

### Issue 7: Datanode Won't Stop During Cluster Restart

**Symptoms:**
- `stop-dfs.sh` hangs or datanode process remains
- Cannot cleanly restart Hadoop

**Solution:**
```bash
# 1. Force kill the datanode process
jps | grep DataNode
kill -9 <pid>

# 2. Or stop everything forcefully
stop-yarn.sh
stop-dfs.sh
# Wait a few seconds, then:
pkill -9 -f DataNode
pkill -9 -f NameNode

# 3. Clean restart
start-dfs.sh
start-yarn.sh
```

### General Debugging Tips

1. **Check service status:**
   ```bash
   systemctl status tshark-capture.service
   systemctl status pcap-watcher.service
   ```

2. **View recent logs:**
   ```bash
   sudo journalctl -u tshark-capture.service -n 50
   sudo journalctl -u pcap-watcher.service -n 50
   ```

3. **Follow logs in real-time:**
   ```bash
   sudo journalctl -u tshark-capture.service -f
   sudo journalctl -u pcap-watcher.service -f
   ```

4. **Test commands manually:**
   ```bash
   # Test tshark capture manually
   sudo tshark -i <interface> -w /tmp/test.pcap -c 10

   # Test Hadoop access
   hadoop fs -ls /
   hadoop fs -mkdir -p /test
   ```

5. **Verify file permissions:**
   ```bash
   ls -la /etc/tshark_capture.env
   ls -ld /var/lib/pcap-stream
   ls -ld /var/log/tshark
   ```

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

