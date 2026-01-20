import re
import csv
from collections import defaultdict

def parse_log_file(log_file_path):
    """
    Parse log file and extract data summary blocks.
    Returns a list of dictionaries, each representing one data summary block.
    """
    summaries = []
    current_summary = {}
    in_summary_block = False
    
    with open(log_file_path, 'r') as f:
        for line in f:
            # Check if we're entering a DATA SUMMARY block
            if 'DATA SUMMARY' in line:
                in_summary_block = True
                current_summary = {}
                continue
            
            # Check if we're exiting a summary block (line with ====)
            if in_summary_block and '====' in line:
                if current_summary:  # Only add if we have data
                    summaries.append(current_summary)
                in_summary_block = False
                continue
            
            # Parse data lines within summary block
            if in_summary_block:
                # Match pattern: field_name | STATUS | value
                match = re.search(r'- INFO - (\S+)\s+\|\s+(\S+)\s+\|\s+(.+)$', line)
                if match:
                    field_name = match.group(1)
                    status = match.group(2)
                    value = match.group(3).strip()
                    
                    # Remove [RETURN] suffix if present
                    value = re.sub(r'\s+\[RETURN\]$', '', value)
                    
                    # Convert "None" string to empty string
                    if value == 'None':
                        value = ''
                    
                    # Store with _value suffix
                    current_summary[f'{field_name}_value'] = value
    
    return summaries

def save_to_csv(summaries, output_csv_path):
    """
    Save the parsed summaries to a CSV file.
    Only includes columns ending with '_value'.
    """
    if not summaries:
        print("No data summaries found in the log file.")
        return
    
    # Get all unique field names (already have _value suffix)
    all_fields = set()
    for summary in summaries:
        all_fields.update(summary.keys())
    
    # Sort fields alphabetically for consistent column order
    fieldnames = sorted(all_fields)
    
    # Write to CSV
    with open(output_csv_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)
    
    print(f"Successfully extracted {len(summaries)} data summary blocks.")
    print(f"CSV file saved to: {output_csv_path}")
    print(f"Number of columns: {len(fieldnames)}")

# Main execution
if __name__ == "__main__":
    # Specify your input and output file paths
    # log_file_path = "your_log_file.log"  # Change this to your log file path
    # output_csv_path = "data_summary.csv"  # Change this to your desired output path

    log_file_path = "/Users/971244/workspace/airline-turnaround/test_hocon_log.txt"  # Change this to your log file path
    output_csv_path = "/Users/971244/workspace/airline-turnaround/test_hocon_log_data_summary.csv"  # Change this to your desired output path
    
    # Parse and save
    summaries = parse_log_file(log_file_path)
    save_to_csv(summaries, output_csv_path)