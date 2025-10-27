#!/usr/bin/env python3
"""
Traffic Volume Analysis Reducer for Hadoop Network Analysis Pipeline

This reducer aggregates traffic statistics by IP address. It groups records by IP
and sums the bytes for "sent" and "received" directions, outputting TSV format:
IP_Address\tTotal_Bytes_Sent\tTotal_Bytes_Received
"""

import sys
from collections import defaultdict

def main():
    """Main reducer function."""
    try:
        # Dictionary to store traffic stats per IP
        traffic_stats = defaultdict(lambda: {'sent': 0, 'received': 0})
        
        # Process input from mapper
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                # Parse mapper output: IP\tDirection\tSize
                parts = line.split('\t')
                if len(parts) != 3:
                    print(f"Invalid mapper output: {line}", file=sys.stderr)
                    continue
                
                ip_address = parts[0]
                direction = parts[1]
                size = int(parts[2])
                
                # Update traffic statistics
                if direction == 'sent':
                    traffic_stats[ip_address]['sent'] += size
                elif direction == 'received':
                    traffic_stats[ip_address]['received'] += size
                else:
                    print(f"Unknown direction: {direction}", file=sys.stderr)
                    continue
                    
            except ValueError:
                print(f"Invalid size value: {line}", file=sys.stderr)
                continue
            except Exception as e:
                print(f"Error processing line: {e}", file=sys.stderr)
                continue
        
        # Output aggregated results in TSV format
        for ip_address, stats in traffic_stats.items():
            total_sent = stats['sent']
            total_received = stats['received']
            print(f"{ip_address}\t{total_sent}\t{total_received}")
            
    except Exception as e:
        print(f"Fatal error in reducer: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

