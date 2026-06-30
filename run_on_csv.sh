#!/bin/bash
# Reusable script to run the candidate transformer on any CSV file.

if [ -z "$1" ]; then
    echo "Error: Missing input CSV file path."
    echo "Usage: ./run_on_csv.sh <path_to_csv_file>"
    exit 1
fi

CSV_PATH="$1"

if [ ! -f "$CSV_PATH" ]; then
    echo "Error: File '$CSV_PATH' not found."
    exit 1
fi

echo "Running Candidate Data Transformer on '$CSV_PATH'..."
PYTHONPATH=. ./venv/bin/python3 transformer/cli.py --inputs "$CSV_PATH" --output output.json

if [ $? -eq 0 ]; then
    echo "Success! Standard canonical profile results saved to output.json"
else
    echo "Failed to process CSV file."
fi
