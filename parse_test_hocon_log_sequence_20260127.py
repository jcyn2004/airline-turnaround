# import csv

# # Input and output file paths
# # log_file = 'your_log_file.txt'
# log_file = "test_hocon_log.txt"
# # output_csv = 'output.csv'
# output_csv = "test_hocon_log_sequence.csv"

# # Set to store unique rows (to avoid duplicates)
# unique_rows = set()

# # Read the log file and extract the first 2 elements
# with open(log_file, 'r', encoding='utf-8') as f:
#     for line in f:
#         line = line.strip()
#         if line:  # Skip empty lines
#             # Split by ' - ' and keep only first 2 elements
#             parts = line.split(' - ')
#             if len(parts) >= 2:
#                 first_two = (parts[0], parts[1])
#                 unique_rows.add(first_two)

# # Write to CSV file
# with open(output_csv, 'w', newline='', encoding='utf-8') as f:
#     writer = csv.writer(f)
    
#     # Optional: Add header row
#     writer.writerow(['Column1', 'Column2'])
    
#     # Write unique rows (sorted for consistency)
#     for row in sorted(unique_rows):
#         writer.writerow(row)

# print(f"CSV file created successfully with {len(unique_rows)} unique rows!")

####################################################################
####################################################################

# import csv

# def process_log_file(input_file, output_file):
#     """
#     Process log file and extract lines containing 'coded_tools.AirlineTurnaround.'
    
#     Args:
#         input_file: Path to input log file (txt)
#         output_file: Path to output CSV file
#     """
#     # Use a set to store unique rows (tuples are hashable)
#     unique_rows = set()
    
#     # Read and process the log file
#     with open(input_file, 'r', encoding='utf-8') as f:
#         for line in f:
#             # Remove leading/trailing whitespace and skip empty lines
#             line = line.strip()
#             if not line:
#                 continue
            
#             # Split by ' - '
#             parts = line.split(' - ')
            
#             # Check if we have at least 2 elements
#             if len(parts) >= 2:
#                 # Check if second element contains 'coded_tools.AirlineTurnaround.'
#                 if 'coded_tools.AirlineTurnaround.' in parts[1]:
#                     # Keep only first 2 elements
#                     row = (parts[0], parts[1])
#                     unique_rows.add(row)
    
#     # Write to CSV file
#     with open(output_file, 'w', newline='', encoding='utf-8') as f:
#         writer = csv.writer(f)
        
#         # Write header
#         writer.writerow(['Timestamp', 'Module'])
        
#         # Write unique rows (sorted for consistency)
#         for row in sorted(unique_rows):
#             writer.writerow(row)
    
#     print(f"Processed {len(unique_rows)} unique rows")
#     print(f"Results saved to {output_file}")

# # Example usage
# if __name__ == "__main__":
#     # input_log_file = "logfile.txt"  # Change this to your log file path
#     input_log_file = "test_hocon_log.txt"  # Change this to your log file path
#     # output_csv_file = "output.csv"   # Change this to your desired output path
#     output_csv_file = "test_hocon_log_sequence.csv"   # Change this to your desired output path
    
#     process_log_file(input_log_file, output_csv_file)

####################################################################
####################################################################

# import csv
# import re

# def extract_data_summary_blocks(log_file_path):
#     """
#     Extract DATA SUMMARY blocks from a log file.
    
#     Args:
#         log_file_path: Path to the log file
        
#     Returns:
#         List of DATA SUMMARY blocks (each block is a list of lines)
#     """
#     blocks = []
#     current_block = []
#     in_block = False
    
#     with open(log_file_path, 'r', encoding='utf-8') as f:
#         for line in f:
#             line = line.strip()
            
#             # Check if we're entering a DATA SUMMARY block
#             if 'DATA SUMMARY' in line:
#                 in_block = True
#                 current_block = []
#                 continue
            
#             # Check if we're exiting the block (empty line or another section marker)
#             if in_block and (not line or line.startswith('---') or line.startswith('===')):
#                 if current_block:
#                     blocks.append(current_block)
#                     current_block = []
#                 in_block = False
#                 continue
            
#             # Add line to current block if we're inside one
#             if in_block and line:
#                 current_block.append(line)
        
#         # Don't forget the last block if file ends while in a block
#         if current_block:
#             blocks.append(current_block)
    
#     return blocks

# def parse_line(line):
#     """
#     Parse a line by splitting on ' - ' and '|'.
    
#     Args:
#         line: String line to parse
        
#     Returns:
#         List of parsed elements
#     """
#     elements = []
    
#     # First split by ' - '
#     parts = line.split(' - ')
    
#     for part in parts:
#         # Then split each part by '|'
#         sub_parts = part.split('|')
#         for sub_part in sub_parts:
#             # Clean up whitespace and add non-empty elements
#             cleaned = sub_part.strip()
#             if cleaned:
#                 elements.append(cleaned)
    
#     return elements

# def process_log_to_csv(log_file_path, csv_file_path):
#     """
#     Extract DATA SUMMARY blocks from log file and write to CSV without duplicates.
    
#     Args:
#         log_file_path: Path to the input log file
#         csv_file_path: Path to the output CSV file
#     """
#     # Extract all DATA SUMMARY blocks
#     blocks = extract_data_summary_blocks(log_file_path)
    
#     # Parse all lines and collect unique rows
#     all_rows = []
#     max_columns = 0
    
#     for block in blocks:
#         for line in block:
#             parsed_elements = parse_line(line)
#             if parsed_elements:
#                 all_rows.append(parsed_elements)
#                 max_columns = max(max_columns, len(parsed_elements))
    
#     # Remove duplicates while preserving order
#     unique_rows = []
#     seen = set()
    
#     for row in all_rows:
#         # Convert list to tuple for hashing
#         row_tuple = tuple(row)
#         if row_tuple not in seen:
#             seen.add(row_tuple)
#             unique_rows.append(row)
    
#     # Write to CSV
#     with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
        
#         # Write all unique rows
#         for row in unique_rows:
#             writer.writerow(row)
    
#     print(f"Processed {len(blocks)} DATA SUMMARY blocks")
#     print(f"Found {len(all_rows)} total rows")
#     print(f"Wrote {len(unique_rows)} unique rows to {csv_file_path}")

# # Main execution
# if __name__ == "__main__":
#     # Specify your file paths
#     log_file = "test_hocon_log.txt"  # Change this to your log file path
#     csv_file = "test_hocon_log_sequence_complete.csv"          # Change this to your desired output path
    
#     # Process the log file
#     process_log_to_csv(log_file, csv_file)

####################################################################
####################################################################

# import pandas as pd
# import csv

# # Initialize column names
# column_names = ['timestamp', 'agent_name']

# # Step 1: Initialize empty list to store all rows
# all_rows = []

# # Step 2 & 3 & 4: Read and process the log file
# with open('test_hocon_log.txt', 'r') as file:
#     for line in file:
#         # Step 2: Filter lines with required criteria
#         if line.count(' - ') == 3 and ' - INFO - ' in line and line.count('|') == 2:
#             line_item = line.strip()
            
#             # Step 3: Split by ' - ' and extract components
#             parts = line_item.split(' - ')
#             time = parts[0]
#             agent = parts[1]
#             data_set = parts[-1]  # Last element
            
#             # Step 4: Create row_data
#             row_data = {}
            
#             # Step 4a & 4b: Add timestamp and agent
#             row_data['timestamp'] = time
#             row_data['agent_name'] = agent
            
#             # Step 4c: Process data_set
#             data_entries = data_set.split('|')
#             for entry in data_entries:
#                 if entry.strip():  # Skip empty entries
#                     # Step 4c.i: Split by '|' - entry is already split
#                     entry_parts = entry.split('|')
#                     if len(entry_parts) >= 1:
#                         # For entries already split, we need to split each by another delimiter
#                         # Assuming format is "parameter|value" in the data_set
#                         pass
            
#             # Reprocess data_set correctly (splitting pairs)
#             # Split data_set into parameter-value pairs
#             pairs = [pair.strip() for pair in data_set.split('|') if pair.strip()]
            
#             for i in range(0, len(pairs), 2):
#                 if i + 1 < len(pairs):
#                     parameter = pairs[i]
#                     value = pairs[i + 2]
                    
#                     # Step 4c.ii: Add parameter to column_names if not present
#                     if parameter not in column_names:
#                         column_names.append(parameter)
                    
#                     # Step 4c.iii: Add value to row_data
#                     row_data[parameter] = value
            
#             # Step 5: Add row to all_rows
#             all_rows.append(row_data)

# # Create DataFrame with all columns
# df = pd.DataFrame(all_rows, columns=column_names)

# # Fill NaN values with empty strings if needed
# df = df.fillna('')

# # Step 6: Save to CSV
# df.to_csv('test_hocon_log_sequence_complete.csv', index=False)

# print(f"Processing complete. {len(df)} rows written to output.csv")
# print(f"Columns: {column_names}")

####################################################################
####################################################################

import pandas as pd
import re
import time

# 1. Create a dataframe with column names
column_names = ['timestamp', 'agent_name', 'step_code', 'aircraft_direction','aircraft_type', 'flight_number', 'flight_status','assigned_runway_id','assigned_runway_length', 
                'gate_id', 
                'ground_services_request_type', 'ground_services_inquiry_type', 'acu_readiness_status', 'gpu_readiness_status', 'wheels_chocks_readiness_status', 
                'ground_clearance_type', 'ground_clearance_status',                
                'wheels_chocks_installation_status',                 
                'engines_stop_status', 
                'acu_connection_status',
                'gpu_connection_status', 
                'jetbridge_connection_status',
                'door_opening_status', 
                'passenger_disembarkation_status', 
                'baggage_unload_status', 
                'crew_debrief_status',
                'crew_exit_status', 
                'cleaning_cabin_status', 
                'lavatory_service_status', 
                'catering_loading_status', 
                'inspection_maintenance_status', 
                'fueling_status'                
                ]

                # ['timestamp', 'agent_name', 'acu_connection_status', 'acu_readiness_status',
                # 'aircraft_direction', 'aircraft_landing_report', 'aircraft_type',
                # 'assigned_runway_id', 'assigned_runway_length', 'baggage_unload_status',
                # 'catering_loading_status', 'cleaning_cabin_status', 'clearance_landing_valid',
                # 'clearance_takeoff_valid', 'ground_clearance_type', 'crew_debrief_status',
                # 'crew_exit_status', 'door_opening_status', 'engines_stop_status',
                # 'flight_number', 'flight_status', 'fueling_status', 'gate_id',
                # 'gpu_connection_status', 'gpu_readiness_status', 'ground_clearance_status',
                # 'ground_clearance_type', 'ground_services_inquiry_type',
                # 'ground_services_request_type', 'inspection_maintenance_status',
                # 'jetbridge_connection_status', 'jetbridge_status', 'lavatory_service_status',
                # 'passenger_disembarkation_status', 'runway_length',
                # 'wheels_chocks_installation_status', 'wheels_chocks_readiness_status']

# Reference orfer or agent calls for the aircraf turnaround below drives the order parameters listed in column_names. 
                # ["aircraft_traffic_controller":'01', 
                # "aircraft_landing",
                # "aircraft_gate_selection",
                # "aircraft_ground_services",
                # "aircraft_ground_traffic",
                # "aircraft_taxiing",
                # "aircraft_chocks_install",
                # "aircraft_engines_stop",
                # "aircraft_acu_connect",
                # "aircraft_gpu_connect",
                # "aircraft_jetbridge_connect",
                # "aircraft_door_opening",
                # "aircraft_disembark",
                # "aircraft_baggage_unload",
                # "aircraft_crew_debrief",
                # "aircraft_crew_exit",
                # "aircraft_cabin_cleaning",
                # "aircraft_lavatory_service",
                # "aircraft_catering_loading",
                # "aircraft_inspection_maintenance",
                # "aircraft_fueling"]

# Create the dictionary
aircraft_operations = {
    "aircraft_traffic_controller": '01',
    "aircraft_landing": '02',
    "aircraft_gate_selection": '03',
    "aircraft_ground_services": '04',
    "aircraft_ground_traffic": '05',
    "aircraft_taxiing": '06',
    "aircraft_chocks_install": '07',
    "aircraft_engines_stop": '08',
    "aircraft_acu_connect": '09',
    "aircraft_gpu_connect": '10',
    "aircraft_jetbridge_connect": '11',
    "aircraft_door_opening": '12',
    "aircraft_disembark": '13',
    "aircraft_baggage_unload": '14',
    "aircraft_crew_debrief": '15',
    "aircraft_crew_exit": '16',
    "aircraft_cabin_cleaning": '17',
    "aircraft_lavatory_service": '18',
    "aircraft_catering_loading": '19',
    "aircraft_inspection_maintenance": '20',
    "aircraft_fueling": '21'
}

# # Method 1: Direct access
# value = aircraft_operations["aircraft_traffic_controller"]
# print(f"Value for 'aircraft_traffic_controller': {value}")

# # Method 2: Using get() method (safer - returns None if key doesn't exist)
# value = aircraft_operations.get("aircraft_traffic_controller")
# print(f"Value using get(): {value}")

# Method 3: Create a function to retrieve values
def get_operation_code(operation_name):
    """
    Returns the operation code for a given aircraft operation name.
    
    Args:
        operation_name (str): The name of the aircraft operation
    
    Returns:
        str: The operation code, or None if not found
    """
    return aircraft_operations.get(operation_name)

# Test the function
result = get_operation_code("aircraft_traffic_controller")
print(f"Function result: {result}")

df = pd.DataFrame(columns=column_names)

# 2. Create a list as raw_data with the size of column_names
raw_data = [None] * len(column_names)

# List to store all rows before creating dataframe
all_rows = []

# Filters for lines in the summary block
dataSummary_tag = ' - INFO - DATA SUMMARY'
data_summary_tag_start = ' - INFO - ------------------------------------------------------------'
data_summary_tag_end = ' - INFO - ============================================================'
data_summary_reached = 0 
data_summary_block = 0

# Determine when a list contains at least one non None element
def has_non_none_element_v4(lst):
    return len([x for x in lst if x is not None]) > 0

# Open and read the log file
with open('test_hocon_log.txt', 'r') as file:
    for line in file:
        if dataSummary_tag in line: 
            data_summary_reached = 1
        if ((data_summary_tag_start in line) & (data_summary_reached == 1)): 
            data_summary_block = 1
        if (data_summary_tag_end in line):
            data_summary_reached = 0
            data_summary_block = 0

        if (data_summary_block == 1): 
            # 3. Check if line contains required patterns
            dash_count = line.count(' - ')
            info_count = line.count(' - INFO - ')
            pipe_count = line.count('|')
            
            if dash_count == 3 and info_count == 1 and pipe_count == 2:
                line_item = line.strip()
                print("\n")
                print("\n")
                print("########## Line Item ##########\n")
                print(line_item)
                print("\n")
                print("\n")
                # 4. Split line_item by ' - '
                parts = line_item.split(' - ')
                
                if len(parts) >= 3:
                    agent = parts[1]
                    agent = agent.split('.')[3]
                    # coded_tools.AirlineTurnaround.aircraft_traffic_controller.aircraft_traffic_controller
                    data_set = parts[-1]

                    # Get the agent step operational code 
                    agent_code = get_operation_code(agent)

                    print("\n")
                    print("\n")
                    print("========== raw_data front end ==========\n")
                    print(time)
                    print(agent)
                    print(agent_code)
                    print(data_set)
                    # print(raw_data)
                    print("\n")
                    print("\n")

                    # 4a. Write time at first position if empty
                    if raw_data[0] is None:
                        time = parts[0]
                        raw_data[0] = time
                    
                    # 4b. Write agent at second position if empty
                    if raw_data[1] is None:
                        raw_data[1] = agent

                    # 4c. Write agent at second position if empty
                    if raw_data[2] is None:
                        raw_data[2] = agent_code
                        if agent_code is None: 
                            raw_data[2] = '00'

                    # 4d. Split data_set by '|'
                    data_parts = data_set.split('|')
                    
                    if len(data_parts) >= 3:
                        parameter = data_parts[0].strip()
                        value = data_parts[-1].strip()

                        print("\n")
                        print("\n")
                        print("---------- raw_data back end ----------\n")
                        print(parameter)
                        print(value)
                        # print(raw_data)
                        print("\n")
                        print("\n")
                        
                        # 4c.i. Determine the location of parameter in column_names
                        if parameter in column_names:
                            index = column_names.index(parameter)
                            
                            # 4c.ii. Write value at the index location in raw_data
                            raw_data[index] = value

                            print("\n")
                            print("\n")
                            print("---------- raw_data process. ----------\n")
                            # print(raw_data)
                            i = 0 
                            while i < len(raw_data):
                                element_value = raw_data[i]
                                element_key = column_names[i]
                                print(str(element_key) + ' : ' + str(element_value))
                                i = i + 1
                            # for element in raw_data:
                            #     print(element)
                            print("---------------------------------------\n")
                            print("\n")
                            print("\n")

        if (data_summary_block == 0): 

        # 5. Check if every position in raw_data has a non-empty entry
        # if all(item is not None for item in raw_data):
            # Add row_data as row to df
            # if all(element is not None for element in raw_data):
            if has_non_none_element_v4(raw_data):
                all_rows.append(raw_data.copy())

            # df.loc[len(df)] = raw_data

            # print("\n")
            # print("\n")
            # print("\n")
            # print("\n")
            # print("\n")
            # print("\n")
            # print("\n")
            # print("\n")
            # print("********** raw_data complete **********\n")
            # print(raw_data)
            # print("***************************************\n")
            # print("\n")
            # print("\n")

            # time.sleep(1)
            
            # Reset raw_data for next complete row
            raw_data = [None] * len(column_names)

            # if '' in line: 

    # Create dataframe from all collected rows
    # if all_rows:
df = pd.DataFrame(all_rows, columns=column_names)

# 6. Save df to a csv file
df.to_csv('test_hocon_log_sequence_complete.csv', index=False)

print(f"Processing complete. {len(df)} rows saved to output.csv")

####################################################################
####################################################################