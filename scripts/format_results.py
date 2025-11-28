#!/usr/bin/env python3
import sys

def format_size(size_bytes):
    """Format bytes into human readable string."""
    try:
        size = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    except ValueError:
        return str(size_bytes)

def main():
    lines = sys.stdin.readlines()
    if not lines:
        return

    # Detect format based on first line
    first_line_parts = lines[0].strip().split('\t')
    num_cols = len(first_line_parts)

    headers = []
    if num_cols == 3:
        headers = ["IP Address", "Bytes Sent", "Bytes Recv"]
        # Optional: Format byte columns
    elif num_cols == 5:
        headers = ["Conversation", "RTT (ms)", "Duration (s)", "Volume", "Packets"]
    else:
        # Fallback for unknown formats
        headers = [f"Col {i+1}" for i in range(num_cols)]

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    data = []
    
    for line in lines:
        parts = line.strip().split('\t')
        # Pad with empty strings if line is short
        parts += [''] * (len(headers) - len(parts))
        
        # Format specific columns if known type
        if num_cols == 3:
            parts[1] = format_size(parts[1])
            parts[2] = format_size(parts[2])
        elif num_cols == 5:
            parts[3] = format_size(parts[3])

        data.append(parts)
        for i, part in enumerate(parts):
            col_widths[i] = max(col_widths[i], len(str(part)))

    # Print Header
    header_row = " | ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print("-" * len(header_row))
    print(header_row)
    print("-" * len(header_row))

    # Print Data
    for parts in data:
        print(" | ".join(str(p).ljust(w) for p, w in zip(parts, col_widths)))

if __name__ == "__main__":
    main()
