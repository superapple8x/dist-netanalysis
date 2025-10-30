#!/usr/bin/env python3
"""
Preprocessing Mapper for Hadoop Network Analysis Pipeline

This mapper reads binary PCAP data from stdin and converts it to line-delimited JSON.
Each line contains packet information: timestamp, src_ip, dst_ip, src_port, dst_port, 
proto, size, and tcp_flags.
"""

import sys
import json
import struct
import os
import tempfile
import re

# Configure Scapy to use a writable temp directory for cache/config
# This fixes permission issues in Hadoop YARN containers
os.environ['HOME'] = tempfile.gettempdir()

from scapy.all import PcapReader
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.l2 import Ether

# Configuration flags (can be controlled via environment variables)
INCLUDE_NON_IP = os.environ.get('INCLUDE_NON_IP', 'false').lower() in ('1', 'true', 'yes', 'y')

def extract_tcp_flags(packet):
    """Extract TCP flags as a string representation."""
    if packet.haslayer(TCP):
        flags = []
        tcp_layer = packet[TCP]
        if tcp_layer.flags & 0x02:  # SYN
            flags.append('S')
        if tcp_layer.flags & 0x10:  # ACK
            flags.append('A')
        if tcp_layer.flags & 0x01:  # FIN
            flags.append('F')
        if tcp_layer.flags & 0x04:  # RST
            flags.append('R')
        if tcp_layer.flags & 0x08:  # PSH
            flags.append('P')
        if tcp_layer.flags & 0x20:  # URG
            flags.append('U')
        return ''.join(flags)
    return None

def process_packet(packet):
    """Process a single packet and return JSON representation."""
    try:
        # Extract basic packet information
        timestamp = float(packet.time)
        size = len(packet)
        
        # Initialize fields with defaults
        src_ip = None
        dst_ip = None
        src_port = None
        dst_port = None
        proto = None
        tcp_flags = None
        
        # Extract IP layer information
        if packet.haslayer(IP):
            ip_layer = packet[IP]
            src_ip = str(ip_layer.src)  # Explicit string conversion
            dst_ip = str(ip_layer.dst)
            
            # Validate IP format
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not (re.match(ip_pattern, src_ip) and re.match(ip_pattern, dst_ip)):
                print(f"Warning: Invalid IP format: {src_ip} -> {dst_ip}", file=sys.stderr)
                return None
            
            proto = ip_layer.proto
            
            # Map protocol numbers to names
            proto_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
            proto = proto_map.get(proto, f'IP_{proto}')
            
            # Extract port information for TCP/UDP
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                tcp_flags = extract_tcp_flags(packet)
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
        else:
            # Handle non-IP packets if configured to include them
            if INCLUDE_NON_IP:
                return {
                    'timestamp': timestamp,
                    'src_ip': None,
                    'dst_ip': None,
                    'src_port': None,
                    'dst_port': None,
                    'proto': 'NON_IP',
                    'size': size,
                    'tcp_flags': None,
                }
            # If not including non-IP packets, skip this packet
            return None
        
        # Create packet record
        packet_record = {
            'timestamp': timestamp,
            'src_ip': src_ip,
            'dst_ip': dst_ip,
            'src_port': src_port,
            'dst_port': dst_port,
            'proto': proto,
            'size': size,
            'tcp_flags': tcp_flags
        }
        
        return packet_record
        
    except Exception as e:
        # Log error to stderr (captured by Hadoop logs)
        print(f"Error processing packet: {e}", file=sys.stderr)
        return None

def main():
    """Main mapper function."""
    packets_processed = 0
    packets_with_ip = 0
    packets_output = 0
    
    try:
        # Read PCAP data from stdin using streaming PcapReader
        # This enables packet-by-packet processing without loading entire file into memory
        reader = PcapReader(sys.stdin.buffer)
        
        for packet in reader:
            packets_processed += 1
            
            packet_record = process_packet(packet)
            if packet_record:
                if packet_record.get('src_ip') and packet_record.get('dst_ip'):
                    packets_with_ip += 1
                packets_output += 1
                # Output JSON line to stdout
                print(json.dumps(packet_record))
                sys.stdout.flush()  # Ensure immediate output
            
            # Log progress every 100 packets
            if packets_processed % 100 == 0:
                print(f"Progress: {packets_processed} processed, {packets_with_ip} with IP, {packets_output} output", file=sys.stderr)
        
        reader.close()
        
        # Final statistics
        print(f"Mapper completed: {packets_processed} processed, {packets_output} output ({100.0*packets_output/packets_processed:.1f}%)", file=sys.stderr)
        
    except Exception as e:
        # Log but don't fail - partial reads expected with PCAP splits
        print(f"Warning: PCAP read ended with: {e}", file=sys.stderr)
        # Drain remaining stdin to avoid Hadoop "Broken pipe" when mapper exits early
        try:
            while sys.stdin.buffer.read(65536):
                pass
        except Exception:
            pass
        print(f"Final stats: {packets_processed} processed, {packets_output} output", file=sys.stderr)

if __name__ == "__main__":
    main()

