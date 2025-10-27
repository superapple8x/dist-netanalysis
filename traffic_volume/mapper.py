#!/usr/bin/env python3
"""
Traffic Volume Analysis Mapper for Hadoop Network Analysis Pipeline

This mapper reads line-delimited JSON data and emits key-value pairs for traffic
volume analysis. For each packet, it emits two records:
- src_ip as key with "sent" direction and packet size
- dst_ip as key with "received" direction and packet size
"""

import sys
import json

def main():
    """Main mapper function."""
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                packet = json.loads(line)
                
                # Extract packet information
                src_ip = packet.get('src_ip')
                dst_ip = packet.get('dst_ip')
                size = packet.get('size', 0)
                
                # Skip packets without IP information
                if not src_ip or not dst_ip:
                    continue
                
                # Emit source IP traffic (sent)
                print(f"{src_ip}\tsent\t{size}")
                
                # Emit destination IP traffic (received)
                print(f"{dst_ip}\treceived\t{size}")
                
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

