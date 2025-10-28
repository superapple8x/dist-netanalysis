#!/usr/bin/env python3
"""
Generate sample PCAP file for testing the Hadoop Network Analysis Pipeline.
This script creates a synthetic PCAP file with various network traffic patterns.
"""

from scapy.all import *
from scapy.layers.inet import IP, TCP, UDP, ICMP
import random
import time

def generate_test_pcap(filename="sample.pcap", num_packets=1000):
    """
    Generate a test PCAP file with diverse network traffic.
    
    Args:
        filename: Output PCAP filename
        num_packets: Number of packets to generate
    """
    packets = []
    base_time = time.time()
    
    # Define some test IP addresses and ports
    client_ips = ["192.168.1.10", "192.168.1.20", "192.168.1.30", "192.168.1.40"]
    server_ips = ["10.0.0.100", "10.0.0.101", "8.8.8.8", "1.1.1.1"]
    server_ports = [80, 443, 8080, 22, 3306, 5432]
    
    print(f"Generating {num_packets} packets...")
    
    # Generate TCP conversations with 3-way handshake
    conversation_count = 0
    for i in range(num_packets // 10):  # Create multiple conversations
        client_ip = random.choice(client_ips)
        server_ip = random.choice(server_ips)
        client_port = random.randint(49152, 65535)
        server_port = random.choice(server_ports)
        
        timestamp = base_time + conversation_count * 0.1
        
        # SYN packet
        syn_packet = Ether()/IP(src=client_ip, dst=server_ip)/TCP(
            sport=client_port, 
            dport=server_port, 
            flags='S', 
            seq=1000
        )
        syn_packet.time = timestamp
        packets.append(syn_packet)
        
        # SYN-ACK packet (with realistic RTT)
        syn_ack_packet = Ether()/IP(src=server_ip, dst=client_ip)/TCP(
            sport=server_port, 
            dport=client_port, 
            flags='SA', 
            seq=2000, 
            ack=1001
        )
        syn_ack_packet.time = timestamp + random.uniform(0.010, 0.050)  # 10-50ms RTT
        packets.append(syn_ack_packet)
        
        # ACK packet
        ack_packet = Ether()/IP(src=client_ip, dst=server_ip)/TCP(
            sport=client_port, 
            dport=server_port, 
            flags='A', 
            seq=1001, 
            ack=2001
        )
        ack_packet.time = timestamp + random.uniform(0.011, 0.051)
        packets.append(ack_packet)
        
        # Data exchange (PSH-ACK packets)
        for j in range(random.randint(5, 15)):
            # Client sends data
            data_size = random.randint(100, 1500)
            push_packet = Ether()/IP(src=client_ip, dst=server_ip)/TCP(
                sport=client_port, 
                dport=server_port, 
                flags='PA', 
                seq=1001+j*100, 
                ack=2001+j*100
            )/Raw(load='X'*data_size)
            push_packet.time = timestamp + 0.1 + j * 0.02
            packets.append(push_packet)
            
            # Server responds
            response_size = random.randint(100, 1500)
            response_packet = Ether()/IP(src=server_ip, dst=client_ip)/TCP(
                sport=server_port, 
                dport=client_port, 
                flags='PA', 
                seq=2001+j*100, 
                ack=1001+(j+1)*100
            )/Raw(load='Y'*response_size)
            response_packet.time = timestamp + 0.1 + j * 0.02 + random.uniform(0.005, 0.015)
            packets.append(response_packet)
        
        # FIN packet (graceful close)
        fin_packet = Ether()/IP(src=client_ip, dst=server_ip)/TCP(
            sport=client_port, 
            dport=server_port, 
            flags='FA', 
            seq=2000, 
            ack=3000
        )
        fin_packet.time = timestamp + 1.0
        packets.append(fin_packet)
        
        conversation_count += 1
    
    # Add some UDP traffic
    print("Adding UDP traffic...")
    for i in range(num_packets // 20):
        timestamp = base_time + i * 0.05
        client_ip = random.choice(client_ips)
        server_ip = random.choice(server_ips)
        
        udp_packet = Ether()/IP(src=client_ip, dst=server_ip)/UDP(
            sport=random.randint(49152, 65535), 
            dport=53  # DNS
        )/Raw(load='DNS query data')
        udp_packet.time = timestamp
        packets.append(udp_packet)
        
        # UDP response
        udp_response = Ether()/IP(src=server_ip, dst=client_ip)/UDP(
            sport=53, 
            dport=random.randint(49152, 65535)
        )/Raw(load='DNS response data')
        udp_response.time = timestamp + random.uniform(0.001, 0.020)
        packets.append(udp_response)
    
    # Add some ICMP traffic (ping)
    print("Adding ICMP traffic...")
    for i in range(num_packets // 50):
        timestamp = base_time + i * 0.1
        client_ip = random.choice(client_ips)
        server_ip = random.choice(server_ips)
        
        # ICMP Echo Request
        icmp_request = Ether()/IP(src=client_ip, dst=server_ip)/ICMP(type=8, code=0)
        icmp_request.time = timestamp
        packets.append(icmp_request)
        
        # ICMP Echo Reply
        icmp_reply = Ether()/IP(src=server_ip, dst=client_ip)/ICMP(type=0, code=0)
        icmp_reply.time = timestamp + random.uniform(0.001, 0.050)
        packets.append(icmp_reply)
    
    # Sort packets by timestamp
    packets.sort(key=lambda p: p.time)
    
    # Write to PCAP file
    print(f"Writing {len(packets)} packets to {filename}...")
    wrpcap(filename, packets)
    
    print(f"✓ Successfully created {filename}")
    print(f"  Total packets: {len(packets)}")
    print(f"  File size: {os.path.getsize(filename)} bytes")
    
    # Print statistics
    tcp_count = sum(1 for p in packets if p.haslayer(TCP))
    udp_count = sum(1 for p in packets if p.haslayer(UDP))
    icmp_count = sum(1 for p in packets if p.haslayer(ICMP))
    
    print(f"\nPacket breakdown:")
    print(f"  TCP packets: {tcp_count}")
    print(f"  UDP packets: {udp_count}")
    print(f"  ICMP packets: {icmp_count}")

if __name__ == "__main__":
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description='Generate test PCAP file for Hadoop pipeline')
    parser.add_argument('-o', '--output', default='sample.pcap', help='Output PCAP filename')
    parser.add_argument('-n', '--num-packets', type=int, default=1000, help='Number of packets to generate')
    
    args = parser.parse_args()
    
    generate_test_pcap(args.output, args.num_packets)

