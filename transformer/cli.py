import argparse
import json
import os
import sys

# Add directory to python path if not there
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from transformer.parse import parse_recruiter_csv, parse_ats_json, parse_recruiter_notes, parse_resume
from transformer.merge import merge_all_candidates
from transformer.project import project_candidate

def detect_and_parse(filepath):
    """
    Detects input file type and parses it accordingly.
    """
    if not os.path.exists(filepath):
        print(f"Warning: File not found: {filepath}", file=sys.stderr)
        return []
        
    filename = os.path.basename(filepath).lower()
    ext = os.path.splitext(filename)[1]
    
    print(f"Reading: {filename} ({ext})", file=sys.stderr)
    
    try:
        if ext == ".csv":
            return parse_recruiter_csv(filepath)
        elif ext == ".json":
            return parse_ats_json(filepath)
        elif ext == ".txt":
            if "notes" in filename or "recruiter" in filename:
                return parse_recruiter_notes(filepath)
            else:
                return parse_resume(filepath)
        elif ext == ".pdf":
            return parse_resume(filepath)
        else:
            print(f"Warning: Unknown file type for '{filename}'. Skipping.", file=sys.stderr)
            return []
    except Exception as e:
        print(f"Error parsing file '{filename}': {str(e)}. Gracefully degrading.", file=sys.stderr)
        return []

def main():
    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer")
    parser.add_argument("--inputs", nargs="+", help="Path to input files (CSV, JSON, TXT, PDF)")
    parser.add_argument("--config", help="Path to projection configuration JSON")
    parser.add_argument("--output", help="Path to save the output JSON file. If omitted, prints to stdout.")
    
    args = parser.parse_args()
    
    config = {}
    inputs = args.inputs or []
    output_path = args.output
    
    # Load config file if provided
    if args.config:
        try:
            with open(args.config, mode="r", encoding="utf-8") as f:
                config = json.load(f)
            # Fallback inputs if not provided on command line
            if not inputs and "inputs" in config:
                inputs = config["inputs"]
            # Fallback output path if not provided on command line
            if not output_path and "output" in config:
                output_path = config["output"]
        except Exception as e:
            print(f"Error loading configuration file: {str(e)}", file=sys.stderr)
            sys.exit(1)
            
    if not inputs:
        print("Error: No input files provided. Specify --inputs or configure them under 'inputs' in your config JSON.", file=sys.stderr)
        sys.exit(1)
        
    raw_lists = []
    for filepath in inputs:
        parsed = detect_and_parse(filepath)
        if parsed:
            raw_lists.append(parsed)
            print(f"Parsed {len(parsed)} raw records from {os.path.basename(filepath)}", file=sys.stderr)
            
    if not raw_lists:
        print("Error: No candidate records were successfully parsed. Exiting.", file=sys.stderr)
        sys.exit(1)
        
    # Merge candidates
    print("Merging and deduplicating candidate profiles...", file=sys.stderr)
    merged_profiles = merge_all_candidates(raw_lists)
    print(f"Deduplicated raw records into {len(merged_profiles)} canonical profiles.", file=sys.stderr)
    
    # Apply custom config projection
    final_output = []
    for profile in merged_profiles:
        projected = project_candidate(profile, config)
        final_output.append(projected)
            
    # Serialize output
    output_str = json.dumps(final_output, indent=2)
    
    if output_path:
        try:
            with open(output_path, mode="w", encoding="utf-8") as f:
                f.write(output_str)
            print(f"Success! Output written to {output_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output_str)

if __name__ == "__main__":
    main()
