#!/usr/bin/env python3
"""
Preprocessing Reducer for Hadoop Network Analysis Pipeline

This reducer validates JSON format and ensures proper line-delimited JSON output.
It acts as an identity reducer (pass-through) with validation.
"""

import sys
import json

def validate_json_line(line):
    """Validate that a line contains valid JSON."""
    try:
        json.loads(line.strip())
        return True
    except json.JSONDecodeError:
        return False

def main():
    """Main reducer function."""
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            # Validate JSON format
            if validate_json_line(line):
                # Output valid JSON line
                print(line)
            else:
                # Log invalid JSON to stderr
                print(f"Invalid JSON line: {line}", file=sys.stderr)
                
    except Exception as e:
        print(f"Fatal error in reducer: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

