# 📋 Instructions for QA Team

Welcome! This document provides everything you need to test the Hadoop Network Analysis Pipeline.

---

## 🎯 What You Need to Do

Your task is to:
1. **Set up a Hadoop cluster** (can be single-node pseudo-distributed mode)
2. **Test the network analysis pipeline** with the provided test data
3. **Verify all three analysis modules** work correctly
4. **Document any issues** you encounter

---

## 📚 Documentation Available

We've prepared comprehensive documentation to guide you through the entire process:

### 1. **[TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** ⭐ START HERE
   - **Complete step-by-step instructions** from zero to working system
   - Hadoop installation guide (from scratch)
   - Environment configuration
   - Testing procedures
   - Troubleshooting common issues
   - **Estimated time**: 2-3 hours for first-time setup

### 2. **[QUICK_START.md](docs/QUICK_START.md)** ⚡ For Experienced Users
   - Abbreviated guide for those who already have Hadoop
   - Quick commands to get running
   - **Estimated time**: 10 minutes

### 3. **[TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** ✅ Track Your Progress
   - Comprehensive checklist for all testing steps
   - Issue tracking template
   - Sign-off form
   - Use this to ensure nothing is missed

---

## 🚀 Quick Overview

### What This Project Does
Analyzes network packet capture (PCAP) files using Hadoop MapReduce:
- **Module 1**: Converts PCAP to JSON format
- **Module 2**: Analyzes traffic volume per IP address
- **Module 3**: Analyzes TCP conversations and latency

### What's Included
```
dist-netanalysis/
├── preprocessing/          # PCAP to JSON conversion
├── traffic_volume/         # Traffic analysis
├── conversation_analysis/  # Conversation metrics
├── scripts/               # Hadoop job execution scripts
├── test_data/             # Sample PCAP file (ready to use!)
│   ├── sample.pcap       # ~2400 packets, ~1.5 MB
│   └── generate_test_pcap.py  # Generate more test data
├── docs/                  # Complete documentation
│   ├── TESTING_GUIDE.md   # Full testing guide
│   └── QUICK_START.md     # Quick reference
└── TESTING_CHECKLIST.md   # Your checklist
```

---

## 🛠️ Prerequisites (What You Need)

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+, CentOS 7+, or Fedora 36+)
- **CPU**: 2+ cores
- **RAM**: 4 GB minimum (8 GB recommended)
- **Disk**: 10 GB free space
- **Access**: Sudo/root privileges

### Software You'll Install (covered in guides)
- Java 11
- Hadoop 3.3.6
- Python 3.7+
- Scapy library

**Don't worry if you don't have these yet** - the [Testing Guide](docs/TESTING_GUIDE.md) walks you through installing everything!

---

## 📋 Recommended Testing Flow

```
1. Read TESTING_GUIDE.md (docs/TESTING_GUIDE.md)
   ↓
2. Install Java, Hadoop, Python (following guide)
   ↓
3. Configure Hadoop cluster (step-by-step in guide)
   ↓
4. Clone/download this project
   ↓
5. Follow testing procedures (Phase 1: Local, Phase 2: Hadoop)
   ↓
6. Use TESTING_CHECKLIST.md to track progress
   ↓
7. Document any issues encountered
   ↓
8. Submit test report with findings
```

---

## ✅ Success Criteria

Your testing is successful when:

- [ ] All Hadoop services start correctly
- [ ] Test data uploads to HDFS successfully
- [ ] All 3 MapReduce jobs complete without errors
- [ ] Output data is valid and makes sense
- [ ] You can view results in HDFS and download locally

**Expected job completion times** (single-node cluster):
- Preprocessing: 1-3 minutes
- Traffic Volume: 30-60 seconds
- Conversation Analysis: 30-60 seconds

---

## 🔧 What's Been Fixed

Before you start, we've already fixed several issues:
- ✅ Fixed script execution paths for Hadoop Streaming
- ✅ Removed incorrect input format configuration
- ✅ Created sample test data (~2400 packets)
- ✅ Added comprehensive documentation

---

## 📊 Expected Results

After running all three jobs, you should see:

### Preprocessing Output
```json
{"timestamp": 1730000000.123, "src_ip": "192.168.1.10", "dst_ip": "10.0.0.100", "proto": "TCP", ...}
```
- **~2400 JSON lines** (one per packet)

### Traffic Volume Output
```
192.168.1.10    567890    1234567
192.168.1.20    445678    987654
...
```
- **8 unique IP addresses** with sent/received byte counts

### Conversation Analysis Output
```
192.168.1.10:54321-10.0.0.100:443    15.234    45.678    1048576    1500
```
- **~100 TCP conversations** with RTT, duration, volume, packet count

---

## 🆘 Getting Help

### Documentation
1. Start with [TESTING_GUIDE.md](docs/TESTING_GUIDE.md) - it has detailed troubleshooting
2. Check the [Troubleshooting section](docs/TESTING_GUIDE.md#troubleshooting) for common issues
3. Review [README.md](README.md) for project overview

### Common Issues (Quick Fixes)

| Problem | Quick Fix |
|---------|-----------|
| `hadoop: command not found` | Run: `source ~/.bashrc` |
| SSH password prompts | Set up passwordless SSH (see guide) |
| NameNode won't start | Check logs: `$HADOOP_HOME/logs/` |
| Job fails with permissions | Fix HDFS permissions: `hadoop fs -chmod -R 777 /input /output` |
| Python/Scapy not found | Install: `pip3 install scapy` |

### Reporting Issues

When you encounter issues, please document:
1. **Error message** (exact text)
2. **Command that failed** (copy full command)
3. **System information** (OS, Hadoop version)
4. **Logs** (relevant excerpts from Hadoop logs)

Use the **Issue Tracking section** in [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md).

---

## 🎓 Learning Resources

If you're new to Hadoop:
- [Hadoop Documentation](https://hadoop.apache.org/docs/stable/)
- [Hadoop MapReduce Tutorial](https://hadoop.apache.org/docs/stable/hadoop-mapreduce-client/hadoop-mapreduce-client-core/MapReduceTutorial.html)
- [HDFS Commands Guide](https://hadoop.apache.org/docs/stable/hadoop-project-dist/hadoop-common/FileSystemShell.html)

---

## 📞 Contact

- **GitHub Repository**: https://github.com/superapple8x/dist-netanalysis
- **Issues**: https://github.com/superapple8x/dist-netanalysis/issues

---

## ⏱️ Time Estimates

| Task | First Time | Subsequent Times |
|------|------------|------------------|
| Hadoop setup | 1-2 hours | N/A |
| Project setup | 15 minutes | 5 minutes |
| Running tests | 30 minutes | 10 minutes |
| **Total** | **~3 hours** | **~15 minutes** |

---

## 🎬 Next Steps

1. **Start here**: Open [docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)
2. **Follow step-by-step** through all sections
3. **Use [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)** to track progress
4. **Document everything** as you go
5. **Report findings** when complete

---

## 📝 Final Notes

- **Take your time** - Hadoop setup can be tricky the first time
- **Don't skip steps** - especially SSH configuration
- **Document issues** - even minor ones help improve the project
- **Test thoroughly** - run all three analysis modules
- **Ask questions** - if something is unclear, report it

**Good luck with testing!** 🚀

---

**Document Version**: 1.0  
**Last Updated**: October 2025  
**Prepared By**: Development Team

