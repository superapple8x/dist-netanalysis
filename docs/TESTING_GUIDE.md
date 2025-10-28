# Testing Guide - Hadoop Network Analysis Pipeline

**Version:** 1.0  
**Last Updated:** October 2025  
**Audience:** QA Engineers, DevOps, System Administrators

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [System Requirements](#system-requirements)
4. [Environment Setup](#environment-setup)
5. [Hadoop Installation](#hadoop-installation)
6. [Project Setup](#project-setup)
7. [Testing Procedure](#testing-procedure)
8. [Validation & Verification](#validation--verification)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Testing](#advanced-testing)

---

## Overview

This guide provides step-by-step instructions for testing the Hadoop Network Analysis Pipeline from scratch. You will:

- Set up a Hadoop cluster (pseudo-distributed mode on a single machine)
- Install and configure the network analysis pipeline
- Run all three analysis modules
- Validate the results

**Estimated Time:** 2-3 hours for first-time setup

---

## Prerequisites

### Required Software

- **Operating System**: Linux (Ubuntu 20.04+, CentOS 7+, or Fedora 36+)
- **User privileges**: `sudo` access for installation
- **Network**: Internet connection for downloading packages
- **Storage**: At least 10 GB free disk space
- **Memory**: Minimum 4 GB RAM (8 GB recommended)

### Required Knowledge

- Basic Linux command line
- Understanding of SSH and environment variables
- Familiarity with network concepts (TCP/IP, packets, ports)

---

## System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8 GB |
| Disk | 10 GB free | 20 GB+ free |
| OS | Ubuntu 20.04+ | Ubuntu 22.04+ |

---

## Environment Setup

### Step 1: Update System Packages

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL/Fedora
sudo dnf update -y
```

### Step 2: Install Java (Required for Hadoop)

Hadoop requires Java 8 or Java 11:

```bash
# Ubuntu/Debian
sudo apt install -y openjdk-11-jdk

# CentOS/RHEL/Fedora
sudo dnf install -y java-11-openjdk-devel

# Verify installation
java -version
```

**Expected output:**
```
openjdk version "11.0.x" ...
```

### Step 3: Install Python 3 and Dependencies

```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip

# CentOS/RHEL/Fedora
sudo dnf install -y python3 python3-pip

# Verify
python3 --version  # Should be 3.7 or higher
```

### Step 4: Set Up Passwordless SSH (Required for Hadoop)

Hadoop uses SSH to manage nodes (even in single-node mode):

```bash
# Install SSH server
sudo apt install -y openssh-server  # Ubuntu
# OR
sudo dnf install -y openssh-server  # Fedora/CentOS

# Start SSH service
sudo systemctl start sshd
sudo systemctl enable sshd

# Generate SSH key (press Enter for all prompts)
ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa

# Add key to authorized_keys
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 0600 ~/.ssh/authorized_keys

# Test passwordless SSH
ssh localhost
# Type 'exit' to logout

# If prompted for password, troubleshoot SSH configuration
```

---

## Hadoop Installation

### Step 1: Download Hadoop

```bash
# Create installation directory
sudo mkdir -p /opt
cd /opt

# Download Hadoop 3.3.6 (latest stable as of 2025)
sudo wget https://downloads.apache.org/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz

# Extract
sudo tar -xzf hadoop-3.3.6.tar.gz
sudo mv hadoop-3.3.6 hadoop

# Set ownership
sudo chown -R $USER:$USER /opt/hadoop
```

### Step 2: Configure Environment Variables

Add to `~/.bashrc`:

```bash
# Edit bashrc
nano ~/.bashrc

# Add these lines at the end:
export HADOOP_HOME=/opt/hadoop
export HADOOP_INSTALL=$HADOOP_HOME
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
export HADOOP_COMMON_LIB_NATIVE_DIR=$HADOOP_HOME/lib/native
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export HADOOP_OPTS="-Djava.library.path=$HADOOP_HOME/lib/native"

# Find Java home path
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))

# Save and exit (Ctrl+X, then Y, then Enter)

# Apply changes
source ~/.bashrc

# Verify
echo $HADOOP_HOME
hadoop version
```

**Expected output:**
```
Hadoop 3.3.6
```

### Step 3: Configure Hadoop

#### 3.1 Edit `hadoop-env.sh`

```bash
nano $HADOOP_HOME/etc/hadoop/hadoop-env.sh
```

Add or modify:
```bash
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
```

#### 3.2 Configure `core-site.xml`

```bash
nano $HADOOP_HOME/etc/hadoop/core-site.xml
```

Replace contents with:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
    <property>
        <name>hadoop.tmp.dir</name>
        <value>/home/${user.name}/hadoop/tmp</value>
    </property>
</configuration>
```

#### 3.3 Configure `hdfs-site.xml`

```bash
nano $HADOOP_HOME/etc/hadoop/hdfs-site.xml
```

Replace contents with:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>file:///home/${user.name}/hadoop/hdfs/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>file:///home/${user.name}/hadoop/hdfs/datanode</value>
    </property>
</configuration>
```

#### 3.4 Configure `mapred-site.xml`

```bash
nano $HADOOP_HOME/etc/hadoop/mapred-site.xml
```

Replace contents with:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
    <property>
        <name>mapreduce.application.classpath</name>
        <value>$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*:$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*</value>
    </property>
</configuration>
```

#### 3.5 Configure `yarn-site.xml`

```bash
nano $HADOOP_HOME/etc/hadoop/yarn-site.xml
```

Replace contents with:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
    <property>
        <name>yarn.nodemanager.env-whitelist</name>
        <value>JAVA_HOME,HADOOP_COMMON_HOME,HADOOP_HDFS_HOME,HADOOP_CONF_DIR,CLASSPATH_PREPEND_DISTCACHE,HADOOP_YARN_HOME,HADOOP_MAPRED_HOME</value>
    </property>
</configuration>
```

### Step 4: Format HDFS (First Time Only)

```bash
# Create directories
mkdir -p ~/hadoop/hdfs/namenode
mkdir -p ~/hadoop/hdfs/datanode
mkdir -p ~/hadoop/tmp

# Format the NameNode
hdfs namenode -format

# You should see: "Storage directory ... has been successfully formatted."
```

**⚠️ WARNING**: Only format HDFS once. Re-formatting will erase all data!

### Step 5: Start Hadoop Services

```bash
# Start HDFS
start-dfs.sh

# Start YARN
start-yarn.sh

# Verify all services are running
jps
```

**Expected output** (process IDs will differ):
```
12345 NameNode
12346 DataNode
12347 SecondaryNameNode
12348 ResourceManager
12349 NodeManager
12350 Jps
```

### Step 6: Verify Hadoop Web UIs

Open in browser:
- **HDFS NameNode**: http://localhost:9870
- **YARN ResourceManager**: http://localhost:8088
- **MapReduce JobHistory**: http://localhost:19888

---

## Project Setup

### Step 1: Clone or Navigate to Project

```bash
cd ~
# If cloning from GitHub:
git clone https://github.com/superapple8x/dist-netanalysis.git
cd dist-netanalysis

# Or navigate to existing project:
cd /path/to/dist-netanalysis
```

### Step 2: Install Python Dependencies

```bash
# Install required packages
pip3 install -r requirements.txt

# Verify Scapy installation
python3 -c "from scapy.all import *; print('Scapy installed successfully')"
```

### Step 3: Make Scripts Executable

```bash
chmod +x scripts/*.sh
chmod +x preprocessing/*.py
chmod +x traffic_volume/*.py
chmod +x conversation_analysis/*.py
chmod +x test_data/generate_test_pcap.py
```

### Step 4: Verify Test Data

```bash
ls -lh test_data/sample.pcap

# Should show a file around 1.5-2 MB
# If missing, generate it:
cd test_data
python3 generate_test_pcap.py
cd ..
```

---

## Testing Procedure

### Phase 1: Local Testing (No Hadoop)

Test individual components before running on Hadoop:

#### Test 1: Preprocessing Mapper

```bash
cd /path/to/dist-netanalysis

cat test_data/sample.pcap | python3 preprocessing/mapper.py | head -5
```

**Expected output**: JSON lines with packet data
```json
{"timestamp": 1730000000.123, "src_ip": "192.168.1.10", "dst_ip": "10.0.0.100", ...}
```

#### Test 2: Traffic Volume Pipeline

```bash
cat test_data/sample.pcap | python3 preprocessing/mapper.py | \
  python3 traffic_volume/mapper.py | sort | \
  python3 traffic_volume/reducer.py | head -10
```

**Expected output**: TSV with IP addresses and traffic stats
```
192.168.1.10    1234567    2345678
```

#### Test 3: Conversation Analysis Pipeline

```bash
cat test_data/sample.pcap | python3 preprocessing/mapper.py | \
  python3 conversation_analysis/mapper.py | sort | \
  python3 conversation_analysis/reducer.py | head -5
```

**Expected output**: Conversation metrics
```
192.168.1.10:54321-10.0.0.100:443    15.234    45.678    1048576    1500
```

### Phase 2: Hadoop Testing

#### Test 1: Upload Test Data to HDFS

```bash
# Create input directory
hadoop fs -mkdir -p /input/pcap

# Upload test PCAP file
hadoop fs -put test_data/sample.pcap /input/pcap/

# Verify upload
hadoop fs -ls /input/pcap
hadoop fs -du -h /input/pcap
```

**Expected output**: File listed with size ~1.5 MB

#### Test 2: Run Preprocessing Job

```bash
# Run the preprocessing job
./scripts/run_preprocessing.sh /input/pcap /output/preprocessing

# This should take 1-3 minutes
# Watch progress at: http://localhost:8088
```

**Expected output**:
```
Starting preprocessing job...
Input: /input/pcap
Output: /output/preprocessing
...
INFO mapreduce.Job: Job job_xxxxx completed successfully
Preprocessing job completed successfully!
```

**Verify results**:
```bash
# Check output directory
hadoop fs -ls /output/preprocessing

# View first 10 lines
hadoop fs -cat /output/preprocessing/part-* | head -10

# Count total output lines
hadoop fs -cat /output/preprocessing/part-* | wc -l
# Should show ~2400 lines (number of packets)
```

#### Test 3: Run Traffic Volume Analysis

```bash
./scripts/run_traffic_volume.sh /output/preprocessing /output/traffic_volume
```

**Verify results**:
```bash
# View all results
hadoop fs -cat /output/traffic_volume/part-*

# Expected format:
# IP_Address    Bytes_Sent    Bytes_Received
```

#### Test 4: Run Conversation Analysis

```bash
./scripts/run_conversation_analysis.sh /output/preprocessing /output/conversation_analysis
```

**Verify results**:
```bash
# View all results
hadoop fs -cat /output/conversation_analysis/part-*

# Expected format:
# Conversation_Key    RTT_ms    Duration_sec    Volume_bytes    Packet_Count
```

#### Test 5: Download Results

```bash
# Create local results directory
mkdir -p results

# Download all outputs
hadoop fs -get /output/preprocessing ./results/
hadoop fs -get /output/traffic_volume ./results/
hadoop fs -get /output/conversation_analysis ./results/

# View locally
cat results/traffic_volume/part-* | column -t
```

---

## Validation & Verification

### Success Criteria

✅ **All jobs should complete without errors**

Check each job status:
```bash
# View recent job history
mapred job -list all

# Check specific job details
mapred job -status <job_id>
```

✅ **Output verification**

| Analysis Type | Expected Output Files | Expected Content |
|---------------|----------------------|------------------|
| Preprocessing | part-00000, part-00001, ... | JSON lines (~2400) |
| Traffic Volume | part-00000 | TSV with 8 unique IPs |
| Conversation | part-00000 | TSV with ~100 conversations |

✅ **Data integrity checks**

```bash
# Check for empty files
hadoop fs -count /output/preprocessing
# Should show non-zero file count and size

# Check for errors in logs
yarn logs -applicationId <application_id> | grep -i error
```

### Expected Performance Metrics

| Metric | Single-Node Cluster | Expected Range |
|--------|-------------------|----------------|
| Preprocessing job time | ~1-3 minutes | Normal |
| Traffic volume job time | ~30-60 seconds | Normal |
| Conversation job time | ~30-60 seconds | Normal |
| HDFS utilization | ~5-10 MB | Normal |

---

## Troubleshooting

### Issue 1: Hadoop Command Not Found

**Symptom**: `bash: hadoop: command not found`

**Solution**:
```bash
# Verify HADOOP_HOME
echo $HADOOP_HOME

# If empty, re-apply environment variables
source ~/.bashrc

# Or manually set:
export HADOOP_HOME=/opt/hadoop
export PATH=$PATH:$HADOOP_HOME/bin
```

### Issue 2: SSH Connection Refused

**Symptom**: `ssh: connect to host localhost port 22: Connection refused`

**Solution**:
```bash
# Start SSH service
sudo systemctl start sshd

# Verify passwordless access
ssh localhost
```

### Issue 3: NameNode Not Starting

**Symptom**: `jps` doesn't show NameNode

**Solution**:
```bash
# Check logs
cat $HADOOP_HOME/logs/hadoop-*-namenode-*.log

# Common fix: Re-format (⚠️ erases data)
stop-dfs.sh
rm -rf ~/hadoop/hdfs/*
hdfs namenode -format
start-dfs.sh
```

### Issue 4: Python/Scapy Not Found

**Symptom**: `ModuleNotFoundError: No module named 'scapy'`

**Solution**:
```bash
# Install for all users
sudo pip3 install scapy

# Or install user-specific
pip3 install --user scapy
```

### Issue 5: Job Fails with "Permission Denied"

**Symptom**: Job fails with HDFS permission errors

**Solution**:
```bash
# Check HDFS permissions
hadoop fs -ls /

# Fix permissions
hadoop fs -chmod -R 777 /input
hadoop fs -chmod -R 777 /output
```

### Issue 6: Job Hangs or Times Out

**Symptom**: Job stuck at 0% or takes extremely long

**Solution**:
```bash
# Check YARN logs
yarn logs -applicationId <application_id>

# Verify resources available
yarn node -list

# Increase YARN memory (edit yarn-site.xml)
# Add:
# <property>
#   <name>yarn.nodemanager.resource.memory-mb</name>
#   <value>4096</value>
# </property>

# Restart YARN
stop-yarn.sh
start-yarn.sh
```

### Issue 7: Invalid JSON in Preprocessing Output

**Symptom**: Traffic volume job fails with "Invalid JSON"

**Solution**:
```bash
# Check preprocessing output for errors
hadoop fs -cat /output/preprocessing/part-* | python3 -m json.tool

# Re-run preprocessing with verbose logging
# Check mapper/reducer stderr logs
```

### Getting Help

1. **Check Hadoop logs**: `$HADOOP_HOME/logs/`
2. **Check YARN logs**: `yarn logs -applicationId <app_id>`
3. **Enable debug mode**: Add `-D mapreduce.map.log.level=DEBUG` to hadoop jar command
4. **HDFS Safe Mode**: If HDFS is in safe mode, wait or run: `hadoop dfsadmin -safemode leave`

---

## Advanced Testing

### Testing with Larger Datasets

```bash
# Generate larger PCAP file
cd test_data
python3 generate_test_pcap.py -o large_sample.pcap -n 10000

# Upload to HDFS
hadoop fs -put large_sample.pcap /input/pcap/

# Run full pipeline
./scripts/run_preprocessing.sh
./scripts/run_traffic_volume.sh
./scripts/run_conversation_analysis.sh
```

### Testing with Real Network Captures

```bash
# Capture live traffic (requires sudo)
sudo tcpdump -i eth0 -w real_capture.pcap -c 5000

# Or download sample captures
wget https://wiki.wireshark.org/SampleCaptures?action=AttachFile&do=get&target=http.cap

# Upload and test
hadoop fs -put real_capture.pcap /input/pcap/
./scripts/run_preprocessing.sh
```

### Performance Benchmarking

```bash
# Record job execution times
time ./scripts/run_preprocessing.sh

# Monitor resource usage
# In separate terminal:
watch -n 1 'jps && free -h && df -h'

# View job metrics in YARN UI
firefox http://localhost:8088
```

### Multi-Node Cluster Testing

If you have multiple machines, configure a true distributed cluster:

1. Install Hadoop on all nodes
2. Configure workers file: `$HADOOP_HOME/etc/hadoop/workers`
3. Update core-site.xml with master node hostname
4. Synchronize configurations across all nodes
5. Start cluster from master node

---

## Test Completion Checklist

Use this checklist to verify successful testing:

- [ ] Java 11 installed and `java -version` works
- [ ] Hadoop installed and `hadoop version` shows 3.3.6
- [ ] Passwordless SSH configured (`ssh localhost` works without password)
- [ ] HDFS formatted and NameNode started
- [ ] `jps` shows all 6 processes (NameNode, DataNode, etc.)
- [ ] Web UIs accessible (port 9870 and 8088)
- [ ] Python 3 and Scapy installed
- [ ] Test data present in `test_data/sample.pcap`
- [ ] Local pipeline tests pass (preprocessing mapper works)
- [ ] HDFS upload successful (`hadoop fs -ls /input/pcap` shows file)
- [ ] Preprocessing job completes successfully
- [ ] Traffic volume job completes successfully
- [ ] Conversation analysis job completes successfully
- [ ] Output files contain valid data
- [ ] Results downloaded to local filesystem

---

## Next Steps After Testing

Once testing is complete and successful:

1. **Document Results**: Record any issues, performance metrics, or observations
2. **Report Findings**: Share test report with development team
3. **Cluster Optimization**: Tune Hadoop parameters based on workload
4. **Production Deployment**: Plan multi-node cluster setup for production
5. **Monitoring Setup**: Implement logging and alerting for production use

---

## Appendix: Quick Reference Commands

### Hadoop Cluster Management
```bash
# Start all services
start-dfs.sh && start-yarn.sh

# Stop all services
stop-yarn.sh && stop-dfs.sh

# Check service status
jps

# HDFS health check
hdfs dfsadmin -report
```

### HDFS Operations
```bash
# List files
hadoop fs -ls /path

# Create directory
hadoop fs -mkdir -p /path/to/dir

# Upload file
hadoop fs -put local_file /hdfs/path

# Download file
hadoop fs -get /hdfs/path local_path

# Delete file/directory
hadoop fs -rm -r /path

# View file content
hadoop fs -cat /path/file

# Check disk usage
hadoop fs -du -h /path
```

### Job Management
```bash
# List running jobs
mapred job -list

# Kill a job
mapred job -kill <job_id>

# View job logs
yarn logs -applicationId <application_id>

# View application list
yarn application -list
```

---

## Contact & Support

For issues or questions:
- GitHub Issues: https://github.com/superapple8x/dist-netanalysis/issues
- Project Wiki: https://github.com/superapple8x/dist-netanalysis/wiki

---

**Document Version**: 1.0  
**Last Updated**: October 2025  
**Tested On**: Ubuntu 22.04, Hadoop 3.3.6, Python 3.10

