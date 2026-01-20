import re
import csv
from collections import defaultdict

def extract_data_summaries(log_file_path, output_csv_path):
    """
    Extract data summary blocks from log file and save as CSV.
    Each block becomes a row in the CSV file.
    """
    
    # Store all data blocks
    data_blocks = []
    current_block = {}
    in_data_summary = False
    
    # Read the log file
    with open(log_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Check if we're entering a DATA SUMMARY section
            if 'DATA SUMMARY' in line:
                in_data_summary = True
                current_block = {}
                continue
            
            # Check if we're exiting a DATA SUMMARY section
            if in_data_summary and '====' in line:
                if current_block:  # Only add if block has data
                    data_blocks.append(current_block)
                in_data_summary = False
                continue
            
            # Extract data lines within DATA SUMMARY section
            if in_data_summary and '|' in line:
                # Skip separator lines with only dashes
                if '----' in line:
                    continue
                
                # Parse the data line
                # Pattern: column_name | STATUS | value
                match = re.search(r'(\w+)\s*\|\s*(\w+)\s*\|\s*(.+)$', line)
                if match:
                    column_name = match.group(1).strip()
                    status = match.group(2).strip()
                    value = match.group(3).strip()
                    
                    # Remove columns ending with "_status"
                    if not column_name.endswith('_status'):
                        # Clean up the value (remove [RETURN] and 'None')
                        if value == 'None':
                            value = ''
                        else:
                            value = re.sub(r'\s*\[RETURN\].*$', '', value)
                        
                        current_block[column_name] = value
    
    # If no data blocks found, return
    if not data_blocks:
        print("No data summary blocks found in the log file.")
        return
    
    # Collect all unique column names (excluding those ending with _status)
    all_columns = set()
    for block in data_blocks:
        all_columns.update(block.keys())
    
    # Sort columns alphabetically for consistency
    all_columns = sorted(all_columns)
    
    # Write to CSV
    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_columns)
        writer.writeheader()
        
        for block in data_blocks:
            writer.writerow(block)
    
    print(f"Successfully extracted {len(data_blocks)} data summary block(s)")
    print(f"CSV file saved to: {output_csv_path}")
    print(f"Columns (excluding *_status): {len(all_columns)}")

# Usage
if __name__ == "__main__":
    # log_file_path = "your_log_file.log"  # Replace with your log file path
    # output_csv_path = "data_summary.csv"  # Replace with desired output path

    log_file_path = "/Users/971244/workspace/airline-turnaround/test_hocon_log.txt"  # Change this to your log file path
    output_csv_path = "/Users/971244/workspace/airline-turnaround/test_hocon_log_data_summary.csv"  # Change this to your desired output path
    
    extract_data_summaries(log_file_path, output_csv_path)