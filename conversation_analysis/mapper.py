#!/usr/bin/env python3
"""
Conversation & Latency Analysis Mapper for Hadoop Network Analysis Pipeline

This mapper reads line-delimited JSON data and groups packets into TCP conversations.
A conversation is defined by the 4-tuple: (Source IP, Source Port, Destination IP, Destination Port),
treated symmetrically. Only TCP packets are processed.
"""

import sys
import json

def normalize_conversation_key(src_ip, src_port, dst_ip, dst_port):
    """
    Create a normalized conversation key by sorting the 4-tuple.
    This ensures bidirectional conversations are treated as the same conversation.
    """
    # Create both possible orderings
    key1 = f"{src_ip}:{src_port}-{dst_ip}:{dst_port}"
    key2 = f"{dst_ip}:{dst_port}-{src_ip}:{src_port}"
    
    # Return the lexicographically smaller one for consistency
    return key1 if key1 < key2 else key2

def main():
    """Main mapper function."""
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                packet = json.loads(line)
                
                # Only process TCP packets
                if packet.get('proto') != 'TCP':
                    continue
                
                # Extract packet information
                src_ip = packet.get('src_ip')
                dst_ip = packet.get('dst_ip')
                src_port = packet.get('src_port')
                dst_port = packet.get('dst_port')
                
                # Skip packets without complete TCP information
                if not all([src_ip, dst_ip, src_port, dst_port]):
                    continue
                
                # Create normalized conversation key
                conversation_key = normalize_conversation_key(src_ip, src_port, dst_ip, dst_port)
                
                # Emit conversation key and packet data
                print(f"{conversation_key}\t{line}")
                
            except json.JSONDecodeError:
                print(f"Invalid JSON line: {line}", file=sys.stderr)
                continue
            except Exception as e:
                print(f"Error processing packet: {e}", file=sys.stderr)
                continue
                
    except Exception as e:
        print(f"Fatal error in mapper: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

