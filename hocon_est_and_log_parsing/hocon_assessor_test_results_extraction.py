import re
import csv
from datetime import datetime

def extract_data_summaries(log_file_path, output_csv_path):
    """
    Extract DATA SUMMARY blocks from log file and save to CSV.
    
    Args:
        log_file_path: Path to the input log file
        output_csv_path: Path to the output CSV file
    """
    
    # Read the log file
    with open(log_file_path, 'r') as f:
        log_content = f.read()
    
    # Pattern to match DATA SUMMARY blocks
    # Matches from "DATA SUMMARY" to the ending "===" line
    summary_pattern = r'DATA SUMMARY.*?(?====+)'
    
    # Pattern to extract individual data lines
    # Captures: field_name | status | value
    data_line_pattern = r'INFO - ([a-z_]+)\s+\|\s+(\w+)\s+\|\s+(.+?)(?:\n|$)'
    
    summaries = re.findall(summary_pattern, log_content, re.DOTALL)
    
    all_records = []
    field_names = set()
    
    # Process each summary block
    for summary in summaries:
        record = {}
        
        # Extract timestamp from the first line of the block
        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', summary)
        if timestamp_match:
            record['timestamp'] = timestamp_match.group(1)
        
        # Extract all data lines
        data_lines = re.findall(data_line_pattern, summary)
        
        for field_name, status, value in data_lines:
            field_name = field_name.strip()
            status = status.strip()
            value = value.strip()
            
            # Store both status and value
            record[f'{field_name}_status'] = status
            record[f'{field_name}_value'] = value
            
            # Track all field names for CSV headers
            field_names.add(f'{field_name}_status') ## The comment makes sure that onlt "..._value" columns are kept.
            field_names.add(f'{field_name}_value')
        
        if record:
            all_records.append(record)
    
    # Prepare CSV headers
    if all_records:
        # Sort field names alphabetically, but keep timestamp first
        sorted_fields = ['timestamp'] + sorted([f for f in field_names])
        
        # Write to CSV
        with open(output_csv_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=sorted_fields)
            writer.writeheader()
            writer.writerows(all_records)
        
        print(f"Successfully extracted {len(all_records)} data summary blocks")
        print(f"CSV file saved to: {output_csv_path}")
    else:
        print("No data summary blocks found in the log file")

# Usage
if __name__ == "__main__":
    # log_file_path = "your_log_file.log"  # Change this to your log file path
    # output_csv_path = "data_summary.csv"  # Change this to your desired output path

    log_file_path = "/Users/971244/workspace/airline-turnaround/test_hocon_log.txt"  # Change this to your log file path
    output_csv_path = "/Users/971244/workspace/airline-turnaround/test_hocon_log_data_summary.csv"  # Change this to your desired output path

    extract_data_summaries(log_file_path, output_csv_path)