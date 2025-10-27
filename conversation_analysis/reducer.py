#!/usr/bin/env python3
"""
Conversation & Latency Analysis Reducer for Hadoop Network Analysis Pipeline

This reducer calculates performance metrics for TCP conversations:
- Initial Connection RTT (time between first SYN and SYN-ACK)
- Total conversation duration
- Total data volume
- Total packet count

Output format: Conversation_Key\tRTT_ms\tDuration_sec\tTotal_Volume_bytes\tPacket_Count
"""

import sys
import json
from collections import defaultdict

def calculate_rtt(packets):
    """
    Calculate RTT as the time delta between the first SYN and the corresponding SYN-ACK packet.
    Returns RTT in milliseconds, or None if no valid SYN/SYN-ACK pair found.
    """
    syn_packets = []
    syn_ack_packets = []
    
    # Find SYN and SYN-ACK packets
    for packet in packets:
        tcp_flags = packet.get('tcp_flags', '')
        timestamp = packet.get('timestamp', 0)
        
        if 'S' in tcp_flags and 'A' not in tcp_flags:  # SYN only
            syn_packets.append(timestamp)
        elif 'S' in tcp_flags and 'A' in tcp_flags:  # SYN-ACK
            syn_ack_packets.append(timestamp)
    
    # Calculate RTT from first SYN to first SYN-ACK
    if syn_packets and syn_ack_packets:
        syn_time = min(syn_packets)
        syn_ack_time = min(syn_ack_packets)
        if syn_ack_time > syn_time:
            rtt_ms = (syn_ack_time - syn_time) * 1000  # Convert to milliseconds
            return rtt_ms
    
    return None

def calculate_conversation_metrics(packets):
    """Calculate all conversation metrics."""
    if not packets:
        return None
    
    # Sort packets by timestamp
    sorted_packets = sorted(packets, key=lambda p: p.get('timestamp', 0))
    
    # Calculate duration
    first_timestamp = sorted_packets[0].get('timestamp', 0)
    last_timestamp = sorted_packets[-1].get('timestamp', 0)
    duration_sec = last_timestamp - first_timestamp
    
    # Calculate total volume
    total_volume = sum(packet.get('size', 0) for packet in packets)
    
    # Calculate packet count
    packet_count = len(packets)
    
    # Calculate RTT
    rtt_ms = calculate_rtt(packets)
    
    return {
        'rtt_ms': rtt_ms,
        'duration_sec': duration_sec,
        'total_volume_bytes': total_volume,
        'packet_count': packet_count
    }

def main():
    """Main reducer function."""
    try:
        # Dictionary to store packets per conversation
        conversations = defaultdict(list)
        
        # Process input from mapper
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Parse mapper output: Conversation_Key\tJSON_Packet_Data
                parts = line.split('\t', 1)
                if len(parts) != 2:
                    print(f"Invalid mapper output: {line}", file=sys.stderr)
                    continue
                
                conversation_key = parts[0]
                packet_json = parts[1]
                
                # Parse packet data
                packet = json.loads(packet_json)
                conversations[conversation_key].append(packet)
                
            except json.JSONDecodeError:
                print(f"Invalid JSON packet data: {line}", file=sys.stderr)
                continue
            except Exception as e:
                print(f"Error processing line: {e}", file=sys.stderr)
                continue
        
        # Calculate and output metrics for each conversation
        for conversation_key, packets in conversations.items():
            metrics = calculate_conversation_metrics(packets)
            
            if metrics:
                rtt_ms = metrics['rtt_ms']
                duration_sec = metrics['duration_sec']
                total_volume_bytes = metrics['total_volume_bytes']
                packet_count = metrics['packet_count']
                
                # Handle None RTT (no valid SYN/SYN-ACK pair)
                rtt_str = f"{rtt_ms:.3f}" if rtt_ms is not None else "N/A"
                
                # Output in TSV format
                print(f"{conversation_key}\t{rtt_str}\t{duration_sec:.6f}\t{total_volume_bytes}\t{packet_count}")
            else:
                print(f"No valid metrics for conversation: {conversation_key}", file=sys.stderr)
            
    except Exception as e:
        print(f"Fatal error in reducer: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

