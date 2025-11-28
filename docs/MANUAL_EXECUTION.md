# Manual Pipeline Execution Guide

This guide explains how to manually run the network analysis pipeline components without relying on systemd services or continuous automation. This is useful for debugging, ad-hoc analysis, or development.

## Part 1: Manual Packet Capture

Instead of the headless background service, you can run `tshark` directly in your terminal.

### 1. Identify your interface
```bash
ip link show
# Look for your active interface (e.g., eth0, enp0s3, wlan0)
```

### 2. Run a simple capture
Capture packets to a single file and stop after a specific count or duration.

```bash
# Capture 1000 packets to my_capture.pcap
sudo tshark -i <interface> -w my_capture.pcap -c 1000

# OR capture for 60 seconds
sudo tshark -i <interface> -w my_capture.pcap -a duration:60
```

### 3. Run a ring-buffer capture (mimics production)
If you want to test the rotation logic used in production:

```bash
# Rotate files every 10MB, keep 5 files max
sudo tshark -i <interface> -w live_capture.pcap -b filesize:10240 -b files:5
```

---

## Part 2: Manual Data Processing

Once you have a `.pcap` file (e.g., `my_capture.pcap`), you need to feed it into the Hadoop pipeline. You have two options.

### Option A: Semi-Automated (Recommended)

Use the existing watcher script in "one-shot" mode. This handles the HDFS upload, directory creation, and job chaining for you.

1.  **Create a staging directory** and move your pcap there:
    ```bash
    mkdir -p ~/pcap_staging
    cp my_capture.pcap ~/pcap_staging/
    ```

2.  **Run the processor**:
    ```bash
    # Process all files in staging and exit
    ./scripts/analyze_local.sh
    
    # OR specify a custom directory
    ./scripts/analyze_local.sh ~/my_custom_staging
    ```

3.  **Check results**:
    The script prints the output paths. You can view them with `hadoop fs -cat` and pipe to our formatter for a nice table:

    ```bash
    # Traffic Volume
    hadoop fs -cat "/output/traffic_volume/live/.../part-*" | python3 scripts/format_results.py

    # Conversation Analysis
    hadoop fs -cat "/output/conversation_analysis/live/.../part-*" | python3 scripts/format_results.py
    ```
fish: No matches for wildcard '/output/traffic_volume/live/my_capture_20251119T052344Z/part-*'. See `help wildcards-globbing`.
hadoop fs -cat /output/traffic_volume/live/my_capture_20251119T052344Z/part-*
               ^~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
    ```

### Option B: Fully Manual (Step-by-Step)

If you want to understand exactly what happens under the hood, run these commands one by one.

**Note:** We must convert the binary `.pcap` to JSON locally because Hadoop Streaming cannot read binary files directly.

#### 1. Define Variables
```bash
# Set a unique ID for this run
RUN_ID="manual_run_$(date +%Y%m%d_%H%M%S)"
PCAP_FILE="my_capture.pcap"
JSON_FILE="my_capture.json"

# HDFS Paths
HDFS_OUT_PRE="/output/preprocessing/manual/$RUN_ID"
HDFS_OUT_TRAFFIC="/output/traffic_volume/manual/$RUN_ID"
HDFS_OUT_CONV="/output/conversation_analysis/manual/$RUN_ID"
```

#### 2. Preprocess Locally (PCAP -> JSON)
Use the mapper script to convert the binary capture to line-delimited JSON.
```bash
cat "$PCAP_FILE" | python3 preprocessing/mapper.py > "$JSON_FILE"
```

#### 3. Upload JSON to HDFS
We upload the JSON directly to the "preprocessing output" directory, skipping the Hadoop preprocessing job.
```bash
hadoop fs -mkdir -p "$HDFS_OUT_PRE"
hadoop fs -put "$JSON_FILE" "$HDFS_OUT_PRE/"
```

#### 4. Run Analysis Jobs
These jobs now read the JSON data from HDFS.

**Traffic Volume Analysis:**
```bash
./scripts/run_traffic_volume.sh "$HDFS_OUT_PRE" "$HDFS_OUT_TRAFFIC"
```

**Conversation Analysis:**
```bash
./scripts/run_conversation_analysis.sh "$HDFS_OUT_PRE" "$HDFS_OUT_CONV"
```

#### 5. View Results
```bash
echo "Traffic Volume Results:"
hadoop fs -cat "$HDFS_OUT_TRAFFIC/part-*" | head

echo "Conversation Analysis Results:"
hadoop fs -cat "$HDFS_OUT_CONV/part-*" | head
```

## Troubleshooting

### "Name node is in safe mode"
If you see an error like `mkdir: Cannot create directory ... Name node is in safe mode`, it means HDFS is in a read-only state (common after startup).

**Fix:**
```bash
hdfs dfsadmin -safemode leave
```

### "No such file or directory"
If `hadoop fs -ls` fails, check if the previous step actually succeeded. The watcher script stops immediately if it hits an error (like Safe Mode), so the output directories won't be created.

### "No matches for wildcard" (fish/zsh)
If you see `No matches for wildcard` or `zsh: no matches found`, your shell is trying to expand the `*` locally instead of passing it to Hadoop.

**Fix:** Wrap the path in quotes.
```bash
hadoop fs -cat "/output/traffic_volume/live/.../part-*"
```

### "No new PCAP files detected"
The watcher script remembers files it has already processed (stored in `state/pcap_watch_state.json`). If you want to re-process the same file:
1.  **Touch the file** to update its timestamp: `touch ~/pcap_staging/my_capture.pcap`
2.  **Or delete the state file**: `rm state/pcap_watch_state.json`

