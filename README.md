# Hadoop-based Network Analysis Pipeline

A scalable, offline processing solution for analyzing large volumes of network packet capture (.pcap) files using Apache Hadoop MapReduce framework.

## Overview

This system provides three distinct analysis modules:

1. **Pre-processing**: Converts binary .pcap files to structured JSON format
2. **Traffic Volume Analysis**: Identifies and ranks hosts by data transmitted
3. **Conversation & Latency Analysis**: Calculates performance metrics for TCP conversations

## Prerequisites

- **Hadoop**: Version 2.x or later (tested with Hadoop 3.x)
- **Python**: Version 3.x
- **Scapy**: Packet parsing library (`pip install scapy`)
- **Operating System**: Linux-based (tested on Ubuntu/CentOS)

## Installation

### 1. Install Hadoop (Pseudo-distributed Mode)

```bash
# Download Hadoop (example with Hadoop 3.3.4)
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.4/hadoop-3.3.4.tar.gz
tar -xzf hadoop-3.3.4.tar.gz
sudo mv hadoop-3.3.4 /opt/hadoop

# Set environment variables
export HADOOP_HOME=/opt/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
```

### 2. Configure Hadoop

Create configuration files in `$HADOOP_HOME/etc/hadoop/`:

**core-site.xml**:
```xml
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>
```

**hdfs-site.xml**:
```xml
<configuration>
    <property>
        <name>dfs.replication</name>
        <value>1</value>
    </property>
    <property>
        <name>dfs.namenode.name.dir</name>
        <value>/tmp/hadoop/namenode</value>
    </property>
    <property>
        <name>dfs.datanode.data.dir</name>
        <value>/tmp/hadoop/datanode</value>
    </property>
</configuration>
```

**mapred-site.xml**:
```xml
<configuration>
    <property>
        <name>mapreduce.framework.name</name>
        <value>yarn</value>
    </property>
</configuration>
```

**yarn-site.xml**:
```xml
<configuration>
    <property>
        <name>yarn.nodemanager.aux-services</name>
        <value>mapreduce_shuffle</value>
    </property>
</configuration>
```

### 3. Start Hadoop Services

```bash
# Format HDFS (only needed once)
hdfs namenode -format

# Start HDFS
start-dfs.sh

# Start YARN
start-yarn.sh

# Verify installation
hadoop version
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Step 1: Upload PCAP Files to HDFS

```bash
# Create input directory
hadoop fs -mkdir -p /input/pcap

# Upload your PCAP files
hadoop fs -put your_file.pcap /input/pcap/
```

### Step 2: Run Analysis Jobs

#### Pre-processing Job
Converts PCAP files to line-delimited JSON:

```bash
./scripts/run_preprocessing.sh /input/pcap /output/preprocessing
```

#### Traffic Volume Analysis
Analyzes traffic volume per IP address:

```bash
./scripts/run_traffic_volume.sh /output/preprocessing /output/traffic_volume
```

#### Conversation & Latency Analysis
Analyzes TCP conversations and calculates performance metrics:

```bash
./scripts/run_conversation_analysis.sh /output/preprocessing /output/conversation_analysis
```

### Step 3: View Results

```bash
# View traffic volume results
hadoop fs -cat /output/traffic_volume/part-*

# View conversation analysis results
hadoop fs -cat /output/conversation_analysis/part-*

# Download results to local filesystem
hadoop fs -get /output/traffic_volume ./results/
```

## Output Formats

### Pre-processing Output (JSON)
Each line contains a JSON object with packet information:
```json
{"timestamp": 1667851200.123456, "src_ip": "192.168.1.10", "dst_ip": "8.8.8.8", "src_port": 54321, "dst_port": 443, "proto": "TCP", "size": 1514, "tcp_flags": "SA"}
```

### Traffic Volume Analysis Output (TSV)
Tab-separated values with traffic statistics per IP:
```
IP_Address	Total_Bytes_Sent	Total_Bytes_Received
192.168.1.10	1048576	2097152
8.8.8.8	2097152	1048576
```

### Conversation Analysis Output (TSV)
Tab-separated values with TCP conversation metrics:
```
Conversation_Key	RTT_ms	Duration_sec	Total_Volume_bytes	Packet_Count
192.168.1.10:54321-8.8.8.8:443	15.234	45.678	1048576	1500
```

## Project Structure

```
dist-netanalysis/
├── preprocessing/
│   ├── mapper.py          # PCAP to JSON conversion
│   └── reducer.py         # JSON validation
├── traffic_volume/
│   ├── mapper.py          # IP traffic extraction
│   └── reducer.py         # Traffic aggregation
├── conversation_analysis/
│   ├── mapper.py          # Conversation grouping
│   └── reducer.py         # Metrics calculation
├── scripts/
│   ├── run_preprocessing.sh
│   ├── run_traffic_volume.sh
│   └── run_conversation_analysis.sh
├── test_data/             # Sample PCAP files for testing
├── docs/                  # Additional documentation
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Testing

### Local Testing (without Hadoop)
Test individual components locally:

```bash
# Test preprocessing mapper
cat test_data/sample.pcap | python3 preprocessing/mapper.py | head

# Test traffic volume mapper/reducer
cat test_data/sample.pcap | python3 preprocessing/mapper.py | python3 traffic_volume/mapper.py | sort | python3 traffic_volume/reducer.py
```

### Hadoop Testing
Run full pipeline on Hadoop:

```bash
# Upload test data
hadoop fs -put test_data/sample.pcap /input/pcap/

# Run all jobs
./scripts/run_preprocessing.sh
./scripts/run_traffic_volume.sh
./scripts/run_conversation_analysis.sh
```

## Troubleshooting

### Common Issues

1. **Hadoop command not found**
   - Ensure `$HADOOP_HOME/bin` is in your PATH
   - Source your environment variables: `source ~/.bashrc`

2. **Permission denied errors**
   - Check HDFS permissions: `hadoop fs -ls /`
   - Ensure user has write permissions to output directories

3. **Python/Scapy not found**
   - Verify Python 3.x is installed: `python3 --version`
   - Install Scapy: `pip3 install scapy`
   - Ensure Python is accessible on all Hadoop nodes

4. **PCAP parsing errors**
   - Verify PCAP files are not corrupted
   - Check that Scapy can read the files locally first
   - Review Hadoop logs for specific error messages

### Monitoring Jobs

- **Hadoop Web UI**: http://localhost:9870 (NameNode)
- **YARN Web UI**: http://localhost:8088 (ResourceManager)
- **Job logs**: `hadoop job -logs <job_id>`

### Performance Tips

- Use larger input files for better Hadoop efficiency
- Adjust MapReduce parameters for your cluster size
- Monitor resource usage during job execution
- Consider data compression for large datasets

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

