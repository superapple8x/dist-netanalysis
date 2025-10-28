# Quick Start Guide

This is an abbreviated version of the full [Testing Guide](TESTING_GUIDE.md) for experienced users who already have Hadoop installed.

## Prerequisites

- ✅ Hadoop 3.x installed and configured
- ✅ Java 11 installed
- ✅ Python 3.7+ with Scapy
- ✅ Passwordless SSH configured

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 2. Start Hadoop

```bash
start-dfs.sh
start-yarn.sh
jps  # Verify all services running
```

### 3. Prepare Test Data

```bash
# Generate sample PCAP (if not present)
cd test_data
python3 generate_test_pcap.py
cd ..

# Upload to HDFS
hadoop fs -mkdir -p /input/pcap
hadoop fs -put test_data/sample.pcap /input/pcap/
```

### 4. Run Pipeline

```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run all three jobs
./scripts/run_preprocessing.sh /input/pcap /output/preprocessing
./scripts/run_traffic_volume.sh /output/preprocessing /output/traffic_volume
./scripts/run_conversation_analysis.sh /output/preprocessing /output/conversation_analysis
```

### 5. View Results

```bash
# Traffic volume results
hadoop fs -cat /output/traffic_volume/part-* | column -t

# Conversation analysis results
hadoop fs -cat /output/conversation_analysis/part-* | column -t

# Download all results
hadoop fs -get /output ./results
```

## Quick Verification

```bash
# Check HDFS contents
hadoop fs -ls -R /output

# View job history
mapred job -list all

# Check YARN web UI
firefox http://localhost:8088
```

## Troubleshooting

| Issue | Quick Fix |
|-------|-----------|
| Hadoop not found | `source ~/.bashrc` or set HADOOP_HOME |
| SSH issues | `ssh localhost` should work without password |
| Port conflicts | Check if ports 9000, 9870, 8088 are free |
| Job fails | Check logs: `yarn logs -applicationId <app_id>` |

## Need More Help?

See the comprehensive [Testing Guide](TESTING_GUIDE.md) for:
- Complete Hadoop installation steps
- Detailed configuration
- Advanced troubleshooting
- Performance tuning

## Local Testing (No Hadoop)

Test mappers/reducers locally before Hadoop:

```bash
# Test preprocessing
cat test_data/sample.pcap | python3 preprocessing/mapper.py | head -10

# Test traffic volume pipeline
cat test_data/sample.pcap | \
  python3 preprocessing/mapper.py | \
  python3 traffic_volume/mapper.py | sort | \
  python3 traffic_volume/reducer.py

# Test conversation analysis pipeline
cat test_data/sample.pcap | \
  python3 preprocessing/mapper.py | \
  python3 conversation_analysis/mapper.py | sort | \
  python3 conversation_analysis/reducer.py
```

---

**Total Time**: ~5 minutes for setup + ~5 minutes for execution

