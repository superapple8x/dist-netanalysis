# Test Data

This directory contains sample PCAP files for testing the Hadoop Network Analysis Pipeline.

## Files

- `sample.pcap`: Synthetic PCAP file with ~2400 packets containing TCP, UDP, and ICMP traffic
- `generate_test_pcap.py`: Script to generate additional test PCAP files

## Generated Test Data

The `sample.pcap` file contains:
- **TCP conversations**: Multiple 3-way handshakes, data exchange, and graceful connection termination
- **UDP traffic**: DNS-like query/response patterns
- **ICMP traffic**: Ping echo request/reply pairs

### Traffic Characteristics:
- Multiple client IPs: 192.168.1.10, 192.168.1.20, 192.168.1.30, 192.168.1.40
- Multiple server IPs: 10.0.0.100, 10.0.0.101, 8.8.8.8, 1.1.1.1
- Common ports: 80 (HTTP), 443 (HTTPS), 8080, 22 (SSH), 3306 (MySQL), 5432 (PostgreSQL), 53 (DNS)
- Realistic RTT values: 10-50ms for TCP handshakes

## Generating Custom Test Data

To generate your own test PCAP file:

```bash
# Generate 1000 packets (default)
python3 generate_test_pcap.py

# Generate 5000 packets with custom filename
python3 generate_test_pcap.py -o large_sample.pcap -n 5000

# View help
python3 generate_test_pcap.py --help
```

## Using Your Own PCAP Files

You can also test with your own network captures:

```bash
# Capture live traffic (requires root/sudo)
sudo tcpdump -i eth0 -w my_capture.pcap -c 1000

# Or use existing PCAP files from:
# - Wireshark sample captures: https://wiki.wireshark.org/SampleCaptures
# - PCAP repository: https://www.netresec.com/?page=PcapFiles
```

## Quick Local Test

Test the mappers/reducers locally before running on Hadoop:

```bash
# Test preprocessing
cat sample.pcap | python3 ../preprocessing/mapper.py | head -10

# Test full pipeline locally (no Hadoop required)
cat sample.pcap | python3 ../preprocessing/mapper.py | \
  python3 ../traffic_volume/mapper.py | sort | \
  python3 ../traffic_volume/reducer.py
```

