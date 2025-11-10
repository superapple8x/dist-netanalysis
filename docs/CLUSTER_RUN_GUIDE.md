## Hadoop Cluster Run Guide

This guide documents the exact steps we used to bring the project’s Hadoop cluster online, load sample data, and execute the full analysis pipeline. Follow these instructions whenever you need to bring up (or verify) the cluster from a fresh shell.

---

### 1. Prerequisites

- Hadoop already installed under `/opt/hadoop` with configuration files in `/opt/hadoop/etc/hadoop`
- Passwordless SSH working between all nodes listed in `HADOOP_CONF_DIR/workers`
- Java 11+ available at `/usr/lib/jvm/java-11-openjdk`
- The repo checked out at `/home/pepper/dist-netanalysis`
- Optional: a second worker host named `worker-node` (as used in this repo); if you only run a single node, keep just `master-node` in the `workers` file

> **Tip:** Keep `/opt/hadoop/etc/hadoop/workers` in sync with the nodes you actually expect to run. Example for a single-node setup:
> ```
> master-node
> ```

---

### 2. Environment Variables (per shell)

Every new shell that runs Hadoop commands must export these variables (or source your shell profile if you added them there):

```bash
export HADOOP_HOME=/opt/hadoop
export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
```

If you forget this step, commands like `hadoop fs` or the job scripts will complain about missing `core-site.xml`.

---

### 3. Starting the Cluster

```bash
start-dfs.sh   # starts NameNode, DataNode(s), SecondaryNameNode
start-yarn.sh  # starts ResourceManager and NodeManager(s)
```

Verify everything is running:

```bash
jps                       # should list NameNode, DataNode, SecondaryNameNode, ResourceManager, NodeManager
hdfs dfsadmin -report     # confirms live datanodes (look for master-node and worker-node if applicable)
yarn node -list           # shows running NodeManagers
```

If the worker node does not appear, check connectivity (`ssh worker-node`) and validate the `workers` file.

---

### 4. Preparing Input Data

Generate or copy PCAP files locally:

```bash
cd /home/pepper/dist-netanalysis/test_data
python3 generate_test_pcap.py  # writes sample.pcap (~1.7 MB)
```

Upload (or refresh) the PCAP in HDFS:

```bash
hdfs dfsadmin -safemode leave                     # only needed if HDFS entered safe mode
hadoop fs -mkdir -p /input/pcap
hadoop fs -put -f /home/pepper/dist-netanalysis/test_data/sample.pcap /input/pcap/sample.pcap
hadoop fs -ls /input/pcap
```

---

### 5. Running the Pipeline Scripts

From `/home/pepper/dist-netanalysis` (with env vars exported):

```bash
./scripts/run_preprocessing.sh /input/pcap /output/preprocessing
./scripts/run_traffic_volume.sh /output/preprocessing /output/traffic_volume
./scripts/run_conversation_analysis.sh /output/preprocessing /output/conversation_analysis
```

Each script removes the target output directory before running. Monitor progress via:

- Console logs (shown by the script)
- YARN web UI: `http://master-node:8088`
- HDFS NameNode UI: `http://master-node:9870`

Check outputs:

```bash
hadoop fs -cat /output/preprocessing/part-* | head
hadoop fs -cat /output/traffic_volume/part-*
hadoop fs -cat /output/conversation_analysis/part-*
```

---

### 6. Continuous Processing (Optional)

If Wireshark (or another tool) continuously writes `.pcap` files to a directory, automate ingestion with the watcher script:

```bash
python3 scripts/watch_and_process_pcaps.py \
  --local-dir ~/pcap_outbox \
  --archive-dir ~/pcap_archive \
  --interval 30
```

Key behavior:

- Scans `--local-dir` for new `.pcap` files, waiting until they stop growing
- Uploads each capture to HDFS under `/input/pcap/live/<run-id>`
- Runs the three pipeline scripts and keeps outputs under `/output/{preprocessing,traffic_volume,conversation_analysis}/live/<run-id>`
- Optionally moves processed captures into the archive directory
- Tracks progress in `state/pcap_watch_state.json`, allowing safe restarts

Schedule the watcher (e.g., via `systemd`, `tmux`, or a screen session) alongside your capture workflow.

---

### 7. Stopping the Cluster

When finished:

```bash
stop-yarn.sh
stop-dfs.sh
```

HDFS data persists between runs. Do **not** re-run `hdfs namenode -format` unless you intend to erase everything.

---

### 8. Troubleshooting Checklist

- **Safe mode errors**: `hdfs dfsadmin -safemode leave`
- **Missing env vars (log4j/core-site error)**: If you run a job in a fresh shell and see

  ```
  WARNING: log4j.properties is not found. HADOOP_CONF_DIR may be incomplete.
  Exception in thread "main" java.lang.RuntimeException: core-site.xml not found
  ...
  Error: Input directory /input/pcap does not exist in HDFS.
  ```

  the shell is missing the Hadoop exports. Fix it by running:

  ```bash
  export HADOOP_HOME=/opt/hadoop
  export HADOOP_CONF_DIR=/opt/hadoop/etc/hadoop
  export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
  export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
  ```

  Then re-run the script. If the input check still fails, make sure `/input/pcap` exists in HDFS (`hadoop fs -mkdir -p /input/pcap`) and re-upload your capture (`hadoop fs -put -f <local>.pcap /input/pcap/`).
- **Mapper subprocess failed (code 1)**: If `run_conversation_analysis.sh` is pointed at raw PCAP input (for example `./run_conversation_analysis.sh /input/pcap /output/...`), the Python mapper exits with `PipeMapRed.waitOutputThreads(): subprocess failed with code 1`, causing repeated map retries until the job fails. This stage expects the JSON output directory from preprocessing. Run the commands in order:

  ```bash
  ./scripts/run_preprocessing.sh /input/pcap /output/preprocessing
  ./scripts/run_conversation_analysis.sh /output/preprocessing /output/conversation_analysis
  ```

  If you only need to rerun the final step, ensure `/output/preprocessing` still contains the JSON results. Re-run preprocessing if necessary.
- **Worker unreachable**: `ssh worker-node`, confirm network routing
- **Job retries reducers**: check YARN logs (`yarn logs -applicationId <id>`) but expect occasional retry; the framework automatically re-runs failed attempts
- **Watcher script logs**: watch stdout, or run with `--once` to process pending captures and exit

By repeating these steps you can reliably stand up the cluster, run the analytics, and wire in continuous PCAP processing.

