import csv
import re
from datetime import datetime

def parse_log_file(log_file_path, output_csv_path):
    """
    Parse log file and extract DATA SUMMARY blocks into CSV format.
    
    Args:
        log_file_path: Path to the input log file
        output_csv_path: Path to the output CSV file
    """
    
    # Store all data rows
    data_rows = []
    current_block = {}
    current_timestamp = None
    in_data_summary = False
    
    with open(log_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Check if we're entering a DATA SUMMARY block
            if 'DATA SUMMARY' in line:
                in_data_summary = True
                current_block = {}
                # Extract timestamp from the line
                timestamp_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})', line)
                if timestamp_match:
                    current_timestamp = timestamp_match.group(1)
                continue
            
            # Check if we've reached the end of a DATA SUMMARY block
            if in_data_summary and '========' in line:
                if current_block:
                    # Add timestamp as first column
                    current_block['timestamp'] = current_timestamp
                    data_rows.append(current_block)
                in_data_summary = False
                current_block = {}
                current_timestamp = None
                continue
            
            # Parse data lines within DATA SUMMARY block
            if in_data_summary and '|' in line:
                # Skip separator lines
                if '------------' in line:
                    continue
                
                # Extract the data after the last '|'
                parts = line.split('|')
                if len(parts) >= 2:
                    # Get the field name (first column before any |)
                    # Find the field name in the line
                    field_match = re.search(r'INFO - ([a-z_]+)\s+\|', line)
                    if field_match:
                        field_name = field_match.group(1).strip()
                        # Get value after the last '|'
                        value = parts[-1].strip()
                        # Remove [RETURN] occurrences
                        value = value.replace('[RETURN]', '').strip()
                        current_block[field_name] = value
    
    # Write to CSV
    if data_rows:
        # Get all unique column names, with timestamp first
        all_columns = ['timestamp']
        for row in data_rows:
            for key in row.keys():
                if key != 'timestamp' and key not in all_columns:
                    all_columns.append(key)
        
        # Write CSV file
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_columns)
            writer.writeheader()
            writer.writerows(data_rows)
        
        print(f"Successfully extracted {len(data_rows)} data blocks to {output_csv_path}")
        print(f"Columns: {len(all_columns)}")
    else:
        print("No data summary blocks found in the log file.")

# Example usage
if __name__ == "__main__":
    # Replace with your actual file paths
    # log_file_path = "your_log_file.log"
    # output_csv_path = "output_data.csv"
    
    log_file_path = "/Users/971244/workspace/airline-turnaround/test_hocon_log.txt"  # Change this to your log file path
    output_csv_path = "/Users/971244/workspace/airline-turnaround/test_hocon_log_data_summary.csv"  # Change this to your desired output path

    parse_log_file(log_file_path, output_csv_path)