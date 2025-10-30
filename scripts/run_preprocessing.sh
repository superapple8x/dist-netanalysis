#!/bin/bash
# Hadoop Job Execution Script for Preprocessing Job
# Converts PCAP files to line-delimited JSON format

# Configuration
HADOOP_HOME=${HADOOP_HOME:-/opt/hadoop}
HADOOP_STREAMING_JAR="$HADOOP_HOME/share/hadoop/tools/lib/hadoop-streaming-*.jar"
INPUT_DIR=${1:-"/input/pcap"}
OUTPUT_DIR=${2:-"/output/preprocessing"}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Check if Hadoop is available
if ! command -v hadoop &> /dev/null; then
    echo "Error: Hadoop command not found. Please ensure Hadoop is installed and in PATH."
    exit 1
fi

# Check if input directory exists in HDFS
if ! hadoop fs -test -d "$INPUT_DIR"; then
    echo "Error: Input directory $INPUT_DIR does not exist in HDFS."
    echo "Please upload your PCAP files to HDFS first:"
    echo "  hadoop fs -mkdir -p $INPUT_DIR"
    echo "  hadoop fs -put your_file.pcap $INPUT_DIR/"
    exit 1
fi

# Remove output directory if it exists
echo "Removing existing output directory: $OUTPUT_DIR"
hadoop fs -rm -r -f "$OUTPUT_DIR"

# Run the preprocessing job
echo "Starting preprocessing job..."
echo "Input: $INPUT_DIR"
echo "Output: $OUTPUT_DIR"

hadoop jar $HADOOP_STREAMING_JAR \
    -files "$PROJECT_DIR/preprocessing/mapper.py,$PROJECT_DIR/preprocessing/reducer.py" \
    -mapper "python3 mapper.py" \
    -reducer "python3 reducer.py" \
    -input "$INPUT_DIR" \
    -output "$OUTPUT_DIR"

if [ $? -eq 0 ]; then
    echo "Preprocessing job completed successfully!"
    echo "Output available at: $OUTPUT_DIR"
    echo "To view results: hadoop fs -cat $OUTPUT_DIR/part-*"
else
    echo "Preprocessing job failed!"
    exit 1
fi

