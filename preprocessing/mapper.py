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
from scapy.all import *
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.layers.l2 import Ether

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
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
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
    try:
        # Read PCAP data from stdin
        # Note: Hadoop Streaming will handle file splitting
        packets = rdpcap(sys.stdin.buffer)
        
        for packet in packets:
            packet_record = process_packet(packet)
            if packet_record:
                # Output JSON line to stdout
                print(json.dumps(packet_record))
                
    except Exception as e:
        print(f"Fatal error in mapper: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

