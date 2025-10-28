# Testing Checklist for QA Team

**Project**: Hadoop Network Analysis Pipeline  
**Repository**: https://github.com/superapple8x/dist-netanalysis

---

## Pre-Testing Setup

### System Preparation
- [ ] Linux system available (Ubuntu 20.04+, CentOS 7+, or Fedora 36+)
- [ ] Minimum 4 GB RAM (8 GB recommended)
- [ ] At least 10 GB free disk space
- [ ] Internet connection available
- [ ] Sudo/root access confirmed

### Required Software Installation
- [ ] Java 11 installed (`java -version`)
- [ ] Python 3.7+ installed (`python3 --version`)
- [ ] Pip3 installed (`pip3 --version`)
- [ ] SSH server installed and running (`systemctl status sshd`)
- [ ] Passwordless SSH configured (`ssh localhost` works without password)

### Hadoop Installation
- [ ] Hadoop 3.3.6 downloaded and extracted to `/opt/hadoop`
- [ ] Environment variables set in `~/.bashrc` (HADOOP_HOME, PATH)
- [ ] `hadoop version` command works
- [ ] Hadoop configuration files updated:
  - [ ] `core-site.xml`
  - [ ] `hdfs-site.xml`
  - [ ] `mapred-site.xml`
  - [ ] `yarn-site.xml`
- [ ] HDFS formatted (`hdfs namenode -format`)
- [ ] Hadoop services started (`start-dfs.sh && start-yarn.sh`)
- [ ] All 6 processes running (`jps` shows NameNode, DataNode, etc.)
- [ ] Web UIs accessible:
  - [ ] http://localhost:9870 (HDFS)
  - [ ] http://localhost:8088 (YARN)

---

## Project Setup

### Code Preparation
- [ ] Project cloned/downloaded from GitHub
- [ ] Navigate to project directory (`cd dist-netanalysis`)
- [ ] Python dependencies installed (`pip3 install -r requirements.txt`)
- [ ] Scapy verified (`python3 -c "from scapy.all import *"`)
- [ ] Scripts made executable (`chmod +x scripts/*.sh`)

### Test Data
- [ ] `test_data/sample.pcap` exists (should be ~1.5 MB)
- [ ] If missing, generated using: `python3 test_data/generate_test_pcap.py`
- [ ] Test PCAP file readable by Scapy

---

## Phase 1: Local Testing (No Hadoop)

### Preprocessing Test
- [ ] Run: `cat test_data/sample.pcap | python3 preprocessing/mapper.py | head -10`
- [ ] Output shows valid JSON lines with packet data
- [ ] No Python errors or exceptions
- [ ] Fields present: timestamp, src_ip, dst_ip, proto, size

### Traffic Volume Test
- [ ] Run full local pipeline for traffic volume
- [ ] Command executes without errors
- [ ] Output shows TSV format with IP addresses
- [ ] Output contains IP addresses from test data (192.168.1.x, 10.0.0.x)

### Conversation Analysis Test
- [ ] Run full local pipeline for conversation analysis
- [ ] Command executes without errors
- [ ] Output shows conversation metrics
- [ ] RTT values present (or "N/A" for some)

**Local Testing Result**: ✅ Pass / ❌ Fail

---

## Phase 2: Hadoop Testing

### HDFS Upload
- [ ] Create input directory: `hadoop fs -mkdir -p /input/pcap`
- [ ] Upload test PCAP: `hadoop fs -put test_data/sample.pcap /input/pcap/`
- [ ] Verify upload: `hadoop fs -ls /input/pcap` shows file
- [ ] Check file size: `hadoop fs -du -h /input/pcap` (~1.5 MB)

### Job 1: Preprocessing
- [ ] Run: `./scripts/run_preprocessing.sh /input/pcap /output/preprocessing`
- [ ] Job starts without errors
- [ ] Job completes successfully (check output message)
- [ ] Output directory created: `hadoop fs -ls /output/preprocessing`
- [ ] Output contains part files (part-00000, etc.)
- [ ] View output: `hadoop fs -cat /output/preprocessing/part-* | head -10`
- [ ] Output is valid JSON lines
- [ ] Total output lines ~2400: `hadoop fs -cat /output/preprocessing/part-* | wc -l`

**Job Duration**: _______ minutes  
**Result**: ✅ Pass / ❌ Fail

### Job 2: Traffic Volume Analysis
- [ ] Run: `./scripts/run_traffic_volume.sh /output/preprocessing /output/traffic_volume`
- [ ] Job starts without errors
- [ ] Job completes successfully
- [ ] Output directory created: `hadoop fs -ls /output/traffic_volume`
- [ ] View output: `hadoop fs -cat /output/traffic_volume/part-*`
- [ ] Output format is TSV (tab-separated)
- [ ] Output contains 8 unique IP addresses
- [ ] Byte counts are non-zero and reasonable

**Job Duration**: _______ seconds  
**Result**: ✅ Pass / ❌ Fail

### Job 3: Conversation Analysis
- [ ] Run: `./scripts/run_conversation_analysis.sh /output/preprocessing /output/conversation_analysis`
- [ ] Job starts without errors
- [ ] Job completes successfully
- [ ] Output directory created: `hadoop fs -ls /output/conversation_analysis`
- [ ] View output: `hadoop fs -cat /output/conversation_analysis/part-*`
- [ ] Output format is TSV with 5 columns
- [ ] RTT values present (some may be "N/A")
- [ ] Duration and packet counts are reasonable

**Job Duration**: _______ seconds  
**Result**: ✅ Pass / ❌ Fail

### Results Download
- [ ] Create local results directory: `mkdir -p results`
- [ ] Download preprocessing output: `hadoop fs -get /output/preprocessing ./results/`
- [ ] Download traffic volume output: `hadoop fs -get /output/traffic_volume ./results/`
- [ ] Download conversation analysis output: `hadoop fs -get /output/conversation_analysis ./results/`
- [ ] Verify local files exist in `results/` directory
- [ ] Files are readable and contain expected data

---

## Phase 3: Validation

### Data Integrity
- [ ] No empty output files
- [ ] No corrupted/malformed data
- [ ] JSON output from preprocessing is valid (test with `jq` or `python -m json.tool`)
- [ ] TSV output has consistent column counts
- [ ] No unexpected NULL or missing values

### Performance Metrics
- [ ] Preprocessing completed in < 5 minutes
- [ ] Traffic volume completed in < 2 minutes
- [ ] Conversation analysis completed in < 2 minutes
- [ ] No jobs failed or were killed
- [ ] Memory usage acceptable (check YARN UI)
- [ ] No excessive warnings in logs

### Output Verification
- [ ] **Preprocessing**: ~2400 JSON lines output
- [ ] **Traffic Volume**: 8 IP addresses with traffic stats
- [ ] **Conversation Analysis**: ~100 TCP conversations
- [ ] IP addresses match expected test data (192.168.1.x, 10.0.0.x, 8.8.8.8, 1.1.1.1)
- [ ] Packet sizes reasonable (not all zeros, not impossibly large)
- [ ] RTT values realistic (1-100ms range, or N/A)

---

## Phase 4: Advanced Testing (Optional)

### Larger Dataset
- [ ] Generate larger PCAP: `python3 test_data/generate_test_pcap.py -o large.pcap -n 10000`
- [ ] Upload and process larger file
- [ ] Jobs complete successfully with more data
- [ ] Performance scales reasonably

### Real Network Capture
- [ ] Obtain real PCAP file (capture or download sample)
- [ ] Process real network data
- [ ] Results make sense for real traffic patterns

### Error Handling
- [ ] Test with corrupted PCAP file (graceful failure)
- [ ] Test with empty input directory (appropriate error message)
- [ ] Test with insufficient HDFS space (graceful handling)

---

## Issue Tracking

### Issues Encountered

| # | Issue Description | Severity | Status | Resolution |
|---|------------------|----------|--------|------------|
| 1 |                  | High/Med/Low | Open/Fixed | |
| 2 |                  | High/Med/Low | Open/Fixed | |
| 3 |                  | High/Med/Low | Open/Fixed | |

### Severity Definitions
- **High**: Blocks testing, prevents system from working
- **Medium**: Workaround available, affects functionality
- **Low**: Minor issue, cosmetic, or documentation error

---

## Final Sign-Off

### Overall Test Result
- [ ] ✅ **PASS**: All critical tests passed, ready for production
- [ ] ⚠️ **PASS WITH ISSUES**: Tests passed with minor issues documented
- [ ] ❌ **FAIL**: Critical issues prevent deployment

### Test Summary

**Total Tests Run**: _______  
**Tests Passed**: _______  
**Tests Failed**: _______  
**Tests Skipped**: _______

**Testing Duration**: _______ hours

**Test Environment**:
- OS: _______________________
- Hadoop Version: ___________
- Python Version: ___________
- Test Date: ________________

### Recommendations

_[Provide recommendations for improvements, optimizations, or required fixes]_

---

### Tested By

**Name**: _______________________  
**Date**: _______________________  
**Signature**: __________________

---

## Additional Notes

_[Any additional observations, concerns, or suggestions]_

---

## Appendix: Quick Commands

```bash
# Check Hadoop status
jps

# Check HDFS contents
hadoop fs -ls -R /

# View job history
mapred job -list all

# Check YARN applications
yarn application -list

# Clean up HDFS for re-testing
hadoop fs -rm -r /output/*
hadoop fs -rm -r /input/pcap/*

# Restart Hadoop if needed
stop-yarn.sh && stop-dfs.sh
start-dfs.sh && start-yarn.sh

# Check logs for specific application
yarn logs -applicationId <application_id>
```

---

**Reference Documents**:
- [Full Testing Guide](docs/TESTING_GUIDE.md)
- [Quick Start Guide](docs/QUICK_START.md)
- [Main README](README.md)

