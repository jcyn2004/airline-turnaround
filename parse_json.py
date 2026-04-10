import os
import json
import csv
import re
from pathlib import Path

aircraft_operations = {
    "aircraft_turnaround": '00',
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

agent_list = ["aircraft_acu_connect", "aircraft_baggage_unload", "aircraft_cabin_cleaning",
              "aircraft_catering_loading", "aircraft_chocks_install", "aircraft_crew_debrief",
              "aircraft_crew_exit", "aircraft_disembark", "aircraft_door_opening",
              "aircraft_engines_stop", "aircraft_inspection_maintenance", "aircraft_jetbridge_connect",
              "aircraft_fueling", "aircraft_gate_selection", "aircraft_ground_services",
              "aircraft_ground_traffic", "aircraft_gpu_connect", "aircraft_landing",
              "aircraft_lavatory_service", "aircraft_taxiing", "aircraft_traffic_controller",
              "aircraft_turnaround", "AirlineTurnaround"]

param_list = ["timestamp", "agent_name", "step_code", "tool_start", "tool_end", "tool_output", 
              "aircraft_direction", "aircraft_type",
              "flight_number", "flight_status", "assigned_runway_id", "assigned_runway_length",
              "deplaning_equipment_selection_execution_mode", "gate_id", "acu_readiness_status", "gpu_readiness_status",
              "wheels_chocks_readiness_status", "ground_clearance_type", "ground_clearance_status",
              "wheels_chocks_installation_status", "engines_stop_status", "acu_connection_status",
              "gpu_connection_status", "jetbridge_connection_status", "door_opening_status",
              "passenger_disembarkation_status", "baggage_unload_status", "crew_debrief_status",
              "crew_exit_status", "cabin_cleaning_status", "lavatory_service_status",
              "catering_loading_status", "inspection_maintenance_status", "fueling_status"]


def get_step_code(agent_name):
    """Get the step code from aircraft_operations dictionary based on agent_name"""
    return aircraft_operations.get(agent_name, "")


def extract_agent_name(content):
    """Extract agent name from the first line after 'Agent:' tag"""
    # 1. Extract the first line l1
    lines = content.split('\n', 1)  # Split only at first newline
    l1 = lines[0]
    
    # 2. Extract substring s1 after 'Agent' in l1
    if 'Agent' in l1:
        agent_name = l1.split('Agent', 1)[1]  # Get content after 'Agent'
    else:
        agent_name = ""  # Return empty string if 'Agent' not found

    # Reformat agent name path to extract the agent name    
    agent_name = agent_name.replace('__', '.')
    agent_name = agent_name.split('.')[-1]

    # 3. Remove l1 from s and save as s2
    if len(lines) > 1:
        log_body = lines[1]  # Remaining content after first line
    else:
        log_body = ""  # Empty string if only one line
    
    # 4. Return both s1 and s2
    return agent_name, log_body


def parse_json_blocks(content):
    """Extract all JSON blocks from the content with their timestamps"""
    blocks = []
    
    # Pattern to match timestamp and JSON block
    pattern = r'\[AGENT\] @ ([\d\-: ]+):\s*(?:Received arguments:|Got result:)\s*```json\s*(\{.*?\})\s*```'
    
    matches = re.finditer(pattern, content, re.DOTALL)
    
    for match in matches:
        timestamp = match.group(1).strip()
        json_str = match.group(2).strip()
        
        try:
            json_data = json.loads(json_str)
            blocks.append({
                'timestamp': timestamp,
                'json_data': json_data
            })
        except json.JSONDecodeError as e:
            # print(f"Error parsing JSON: {e}")
            continue
    
    return blocks


def extract_nested_json(text):
    """Extract JSON from tool_output if it contains embedded JSON"""
    if isinstance(text, str):
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    return {}


def flatten_data(json_data):
    """Flatten the JSON data, including nested tool_args and tool_output"""
    flat_data = {}
    tool_output_original = None
    extracted_values = {}
    
    for key, value in json_data.items():
        if key == 'tool_args' and isinstance(value, dict):
            # Merge tool_args into extracted_values
            extracted_values.update(value)
        elif key == 'tool_output':
            # Store the original tool_output (always preserve it)
            tool_output_original = value if isinstance(value, str) else json.dumps(value)
            
            # Try to extract JSON from tool_output if present
            if isinstance(value, str):
                nested_json = extract_nested_json(value)
                if nested_json:
                    # Extract only values that are in param_list
                    for nested_key, nested_value in nested_json.items():
                        if nested_key in param_list:
                            extracted_values[nested_key] = nested_value
            elif isinstance(value, dict):
                # If tool_output is already a dict, extract values in param_list
                for nested_key, nested_value in value.items():
                    if nested_key in param_list:
                        extracted_values[nested_key] = nested_value
        elif key in ['tool_start', 'tool_end']:
            flat_data[key] = value
        else:
            flat_data[key] = value
    
    # Merge extracted values into flat_data
    flat_data.update(extracted_values)
    
    # Always set tool_output to the original value
    if tool_output_original is not None:
        flat_data['tool_output'] = tool_output_original
    
    return flat_data


def parse_file(filepath, agent_name):
    """Parse a single file and return rows for CSV"""
    rows = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract agent name from file content and remove the top line from content
    extracted_agent_name, content = extract_agent_name(content)

    # print("-------------- AGENT NAME ------------- ")
    # print(extracted_agent_name)
    # print("--------------------------------------- ")
    
    # Parse JSON blocks
    blocks = parse_json_blocks(content)
    
    for block in blocks:

        # print("================ BLOCK ================ ")
        # print(block)
        # print("======================================= ")

        row = {param: "" for param in param_list}
        row['timestamp'] = block['timestamp']
        row['agent_name'] = extracted_agent_name

        # Remove extracted_agent_name append 
        extracted_agent_name_base = extracted_agent_name.split('-')[0]
        
        # Set step_code based on agent_name using the aircraft_operations dictionary
        # row['step_code'] = get_step_code(extracted_agent_name)
        row['step_code'] = get_step_code(extracted_agent_name_base)
        
        # Flatten and extract data
        flat_data = flatten_data(block['json_data'])
        
        # Fill in values for parameters in param_list
        for param in param_list:
            if param in flat_data:
                value = flat_data[param]
                # Convert None to empty string
                row[param] = "" if value is None else str(value)
        
        rows.append(row)
    
    return rows


def process_directory(directory_path, output_csv):
    """Process all files in directory that match agent_list"""
    all_rows = []
    
    directory = Path(directory_path)
    
    # Iterate through all files in directory
    for filepath in directory.iterdir():
        if filepath.is_file():
            filename = filepath.name
            
            # Check if any agent name is in the filename
            for agent in agent_list:
                if agent in filename:
                    # print(f"Processing file: {filename}")
                    rows = parse_file(filepath, agent)
                    all_rows.extend(rows)
                    break
    
    # Write to CSV
    if all_rows:
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=param_list)
            writer.writeheader()
            writer.writerows(all_rows)
        # print(f"CSV file created: {output_csv}")
        # print(f"Total rows written: {len(all_rows)}")
    else:
        # print("No data found to write to CSV")


# Usage
if __name__ == "__main__":
    directory_path = "logs/thinking_dir" # os.getcwd() #"."  # Change this to your directory path
    output_csv = "json_output.csv"
    
    process_directory(directory_path, output_csv)

# code version 0.3

# import os
# import json
# import csv
# import re
# from pathlib import Path

# aircraft_operations = {
#     "aircraft_turnaround": '00',
#     "aircraft_traffic_controller": '01',
#     "aircraft_landing": '02',
#     "aircraft_gate_selection": '03',
#     "aircraft_ground_services": '04',
#     "aircraft_ground_traffic": '05',
#     "aircraft_taxiing": '06',
#     "aircraft_chocks_install": '07',
#     "aircraft_engines_stop": '08',
#     "aircraft_acu_connect": '09',
#     "aircraft_gpu_connect": '10',
#     "aircraft_jetbridge_connect": '11',
#     "aircraft_door_opening": '12',
#     "aircraft_disembark": '13',
#     "aircraft_baggage_unload": '14',
#     "aircraft_crew_debrief": '15',
#     "aircraft_crew_exit": '16',
#     "aircraft_cabin_cleaning": '17',
#     "aircraft_lavatory_service": '18',
#     "aircraft_catering_loading": '19',
#     "aircraft_inspection_maintenance": '20',
#     "aircraft_fueling": '21'
# }

# agent_list = ["aircraft_acu_connect", "aircraft_baggage_unload", "aircraft_cabin_cleaning",
#               "aircraft_catering_loading", "aircraft_chocks_install", "aircraft_crew_debrief",
#               "aircraft_crew_exit", "aircraft_disembark", "aircraft_door_opening",
#               "aircraft_engines_stop", "aircraft_inspection_maintenance", "aircraft_jetbridge_connect",
#               "aircraft_fueling", "aircraft_gate_selection", "aircraft_ground_services",
#               "aircraft_ground_traffic", "aircraft_gpu_connect", "aircraft_landing",
#               "aircraft_lavatory_service", "aircraft_taxiing", "aircraft_traffic_controller",
#               "aircraft_turnaround", "AirlineTurnaround"]

# param_list = ["timestamp", "agent_name", "step_code", "tool_start", "tool_end", "tool_output", 
#               "aircraft_direction", "aircraft_type",
#               "flight_number", "flight_status", "assigned_runway_id", "assigned_runway_length",
#               "gate_id", "acu_readiness_status", "gpu_readiness_status",
#               "wheels_chocks_readiness_status", "ground_clearance_type", "ground_clearance_status",
#               "wheels_chocks_installation_status", "engines_stop_status", "acu_connection_status",
#               "gpu_connection_status", "jetbridge_connection_status", "door_opening_status",
#               "passenger_disembarkation_status", "baggage_unload_status", "crew_debrief_status",
#               "crew_exit_status", "cabin_cleaning_status", "lavatory_service_status",
#               "catering_loading_status", "inspection_maintenance_status", "fueling_status"]


# def get_step_code(agent_name):
#     """Get the step code from aircraft_operations dictionary based on agent_name"""
#     return aircraft_operations.get(agent_name, "")


# def extract_agent_name(content):
#     """Extract agent name from the first line after 'Agent:' tag"""
#     # 1. Extract the first line l1
#     lines = content.split('\n', 1)  # Split only at first newline
#     l1 = lines[0]
    
#     # 2. Extract substring s1 after 'Agent' in l1
#     if 'Agent' in l1:
#         agent_name = l1.split('Agent', 1)[1]  # Get content after 'Agent'
#     else:
#         agent_name = ""  # Return empty string if 'Agent' not found

#     # Reformat agent name path to extract the agent name    
#     agent_name = agent_name.replace('__', '.')
#     agent_name = agent_name.split('.')[-1]

#     # 3. Remove l1 from s and save as s2
#     if len(lines) > 1:
#         log_body = lines[1]  # Remaining content after first line
#     else:
#         log_body = ""  # Empty string if only one line
    
#     # 4. Return both s1 and s2
#     return agent_name, log_body


# def parse_json_blocks(content):
#     """Extract all JSON blocks from the content with their timestamps"""
#     blocks = []
    
#     # Pattern to match timestamp and JSON block
#     pattern = r'\[AGENT\] @ ([\d\-: ]+):\s*(?:Received arguments:|Got result:)\s*```json\s*(\{.*?\})\s*```'
    
#     matches = re.finditer(pattern, content, re.DOTALL)
    
#     for match in matches:
#         timestamp = match.group(1).strip()
#         json_str = match.group(2).strip()
        
#         try:
#             json_data = json.loads(json_str)
#             blocks.append({
#                 'timestamp': timestamp,
#                 'json_data': json_data
#             })
#         except json.JSONDecodeError as e:
#             # print(f"Error parsing JSON: {e}")
#             continue
    
#     return blocks


# def extract_nested_json(text):
#     """Extract JSON from tool_output if it contains embedded JSON"""
#     if isinstance(text, str):
#         match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
#         if match:
#             try:
#                 return json.loads(match.group(1))
#             except json.JSONDecodeError:
#                 pass
#     return {}


# def flatten_data(json_data):
#     """Flatten the JSON data, including nested tool_args and tool_output"""
#     flat_data = {}
    
#     for key, value in json_data.items():
#         if key == 'tool_args' and isinstance(value, dict):
#             # Merge tool_args into flat_data
#             flat_data.update(value)
#         elif key == 'tool_output':
#             # Store the original tool_output
#             flat_data['tool_output'] = value if isinstance(value, str) else json.dumps(value)
            
#             # Also extract JSON from tool_output if present
#             if isinstance(value, str):
#                 nested_json = extract_nested_json(value)
#                 flat_data.update(nested_json)
#             elif isinstance(value, dict):
#                 # If tool_output is already a dict, merge it
#                 flat_data.update(value)
#         elif key in ['tool_start', 'tool_end']:
#             flat_data[key] = value
#         else:
#             flat_data[key] = value
    
#     return flat_data


# def parse_file(filepath, agent_name):
#     """Parse a single file and return rows for CSV"""
#     rows = []
    
#     with open(filepath, 'r', encoding='utf-8') as f:
#         content = f.read()
    
#     # Extract agent name from file content and remove the top line from content
#     extracted_agent_name, content = extract_agent_name(content)

#     # print("-------------- AGENT NAME ------------- ")
#     # print(extracted_agent_name)
#     # print("--------------------------------------- ")
    
#     # Parse JSON blocks
#     blocks = parse_json_blocks(content)
    
#     for block in blocks:

#         # print("================ BLOCK ================ ")
#         # print(block)
#         # print("======================================= ")

#         row = {param: "" for param in param_list}
#         row['timestamp'] = block['timestamp']
#         row['agent_name'] = extracted_agent_name
        
#         # Set step_code based on agent_name using the aircraft_operations dictionary
#         row['step_code'] = get_step_code(extracted_agent_name)
        
#         # Flatten and extract data
#         flat_data = flatten_data(block['json_data'])
        
#         # Fill in values for parameters in param_list
#         for param in param_list:
#             if param in flat_data:
#                 value = flat_data[param]
#                 # Convert None to empty string
#                 row[param] = "" if value is None else str(value)
        
#         rows.append(row)
    
#     return rows


# def process_directory(directory_path, output_csv):
#     """Process all files in directory that match agent_list"""
#     all_rows = []
    
#     directory = Path(directory_path)
    
#     # Iterate through all files in directory
#     for filepath in directory.iterdir():
#         if filepath.is_file():
#             filename = filepath.name
            
#             # Check if any agent name is in the filename
#             for agent in agent_list:
#                 if agent in filename:
#                     # print(f"Processing file: {filename}")
#                     rows = parse_file(filepath, agent)
#                     all_rows.extend(rows)
#                     break
    
#     # Write to CSV
#     if all_rows:
#         with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=param_list)
#             writer.writeheader()
#             writer.writerows(all_rows)
#         # print(f"CSV file created: {output_csv}")
#         # print(f"Total rows written: {len(all_rows)}")
#     else:
#         # print("No data found to write to CSV")


# # Usage
# if __name__ == "__main__":
#     directory_path = "logs/thinking_dir" # os.getcwd() #"."  # Change this to your directory path
#     output_csv = "json_output.csv"
    
#     process_directory(directory_path, output_csv)

# Code version 0.2

# aircraft_operations = {
#     "aircraft_turnaround": '00',
#     "aircraft_traffic_controller": '01',
#     "aircraft_landing": '02',
#     "aircraft_gate_selection": '03',
#     "aircraft_ground_services": '04',
#     "aircraft_ground_traffic": '05',
#     "aircraft_taxiing": '06',
#     "aircraft_chocks_install": '07',
#     "aircraft_engines_stop": '08',
#     "aircraft_acu_connect": '09',
#     "aircraft_gpu_connect": '10',
#     "aircraft_jetbridge_connect": '11',
#     "aircraft_door_opening": '12',
#     "aircraft_disembark": '13',
#     "aircraft_baggage_unload": '14',
#     "aircraft_crew_debrief": '15',
#     "aircraft_crew_exit": '16',
#     "aircraft_cabin_cleaning": '17',
#     "aircraft_lavatory_service": '18',
#     "aircraft_catering_loading": '19',
#     "aircraft_inspection_maintenance": '20',
#     "aircraft_fueling": '21'
# }

# import os
# import json
# import csv
# import re
# from pathlib import Path

# agent_list = ["aircraft_acu_connect", "aircraft_baggage_unload", "aircraft_cabin_cleaning",
#               "aircraft_catering_loading", "aircraft_chocks_install", "aircraft_crew_debrief",
#               "aircraft_crew_exit", "aircraft_disembark", "aircraft_door_opening",
#               "aircraft_engines_stop", "aircraft_inspection_maintenance", "aircraft_jetbridge_connect",
#               "aircraft_fueling", "aircraft_gate_selection", "aircraft_ground_services",
#               "aircraft_ground_traffic", "aircraft_gpu_connect", "aircraft_landing",
#               "aircraft_lavatory_service", "aircraft_taxiing", "aircraft_traffic_controller",
#               "aircraft_turnaround", "AirlineTurnaround"]

# param_list = ["timestamp", "agent_name", "step_code", "tool_start", "tool_end", "tool_output", 
#               "aircraft_direction", "aircraft_type",
#               "flight_number", "flight_status", "assigned_runway_id", "assigned_runway_length",
#               "gate_id", "acu_readiness_status", "gpu_readiness_status",
#               "wheels_chocks_readiness_status", "ground_clearance_type", "ground_clearance_status",
#               "wheels_chocks_installation_status", "engines_stop_status", "acu_connection_status",
#               "gpu_connection_status", "jetbridge_connection_status", "door_opening_status",
#               "passenger_disembarkation_status", "baggage_unload_status", "crew_debrief_status",
#               "crew_exit_status", "cabin_cleaning_status", "lavatory_service_status",
#               "catering_loading_status", "inspection_maintenance_status", "fueling_status"]


# def get_step_code(agent_name):
#     """Get the step code from aircraft_operations dictionary based on agent_name"""
#     return aircraft_operations.get(agent_name, "")


# def extract_agent_name(content):
#     """Extract agent name from the first line after 'Agent:' tag"""
#     # 1. Extract the first line l1
#     lines = content.split('\n', 1)  # Split only at first newline
#     l1 = lines[0]
    
#     # 2. Extract substring s1 after 'Agent' in l1
#     if 'Agent' in l1:
#         agent_name = l1.split('Agent', 1)[1]  # Get content after 'Agent'
#     else:
#         agent_name = ""  # Return empty string if 'Agent' not found

#     # Reformat agent name path to extract the agent name    
#     agent_name = agent_name.replace('__', '.')
#     agent_name = agent_name.split('.')[-1]

#     # 3. Remove l1 from s and save as s2
#     if len(lines) > 1:
#         log_body = lines[1]  # Remaining content after first line
#     else:
#         log_body = ""  # Empty string if only one line
    
#     # 4. Return both s1 and s2
#     return agent_name, log_body


# def parse_json_blocks(content):
#     """Extract all JSON blocks from the content with their timestamps"""
#     blocks = []
    
#     # Pattern to match timestamp and JSON block
#     pattern = r'\[AGENT\] @ ([\d\-: ]+):\s*(?:Received arguments:|Got result:)\s*```json\s*(\{.*?\})\s*```'
    
#     matches = re.finditer(pattern, content, re.DOTALL)
    
#     for match in matches:
#         timestamp = match.group(1).strip()
#         json_str = match.group(2).strip()
        
#         try:
#             json_data = json.loads(json_str)
#             blocks.append({
#                 'timestamp': timestamp,
#                 'json_data': json_data
#             })
#         except json.JSONDecodeError as e:
#             # print(f"Error parsing JSON: {e}")
#             continue
    
#     return blocks


# def extract_nested_json(text):
#     """Extract JSON from tool_output if it contains embedded JSON"""
#     if isinstance(text, str):
#         match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
#         if match:
#             try:
#                 return json.loads(match.group(1))
#             except json.JSONDecodeError:
#                 pass
#     return {}


# def flatten_data(json_data):
#     """Flatten the JSON data, including nested tool_args and tool_output"""
#     flat_data = {}
    
#     for key, value in json_data.items():
#         if key == 'tool_args' and isinstance(value, dict):
#             # Merge tool_args into flat_data
#             flat_data.update(value)
#         elif key == 'tool_output':
#             # Extract JSON from tool_output if present
#             nested_json = extract_nested_json(value)
#             flat_data.update(nested_json)
#         elif key in ['tool_start', 'tool_end']:
#             flat_data[key] = value
#         else:
#             flat_data[key] = value
    
#     return flat_data


# def parse_file(filepath, agent_name):
#     """Parse a single file and return rows for CSV"""
#     rows = []
    
#     with open(filepath, 'r', encoding='utf-8') as f:
#         content = f.read()
    
#     # Extract agent name from file content and remove the top line from content
#     extracted_agent_name, content = extract_agent_name(content)

#     # print("-------------- AGENT NAME ------------- ")
#     # print(extracted_agent_name)
#     # print("--------------------------------------- ")
    
#     # Parse JSON blocks
#     blocks = parse_json_blocks(content)
    
#     for block in blocks:

#         # print("================ BLOCK ================ ")
#         # print(block)
#         # print("======================================= ")

#         row = {param: "" for param in param_list}
#         row['timestamp'] = block['timestamp']
#         row['agent_name'] = extracted_agent_name
        
#         # Set step_code based on agent_name using the aircraft_operations dictionary
#         row['step_code'] = get_step_code(extracted_agent_name)
        
#         # Flatten and extract data
#         flat_data = flatten_data(block['json_data'])
        
#         # Fill in values for parameters in param_list
#         for param in param_list:
#             if param in flat_data:
#                 value = flat_data[param]
#                 # Convert None to empty string
#                 row[param] = "" if value is None else str(value)
        
#         rows.append(row)
    
#     return rows


# def process_directory(directory_path, output_csv):
#     """Process all files in directory that match agent_list"""
#     all_rows = []
    
#     directory = Path(directory_path)
    
#     # Iterate through all files in directory
#     for filepath in directory.iterdir():
#         if filepath.is_file():
#             filename = filepath.name
            
#             # Check if any agent name is in the filename
#             for agent in agent_list:
#                 if agent in filename:
#                     # print(f"Processing file: {filename}")
#                     rows = parse_file(filepath, agent)
#                     all_rows.extend(rows)
#                     break
    
#     # Write to CSV
#     if all_rows:
#         with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=param_list)
#             writer.writeheader()
#             writer.writerows(all_rows)
#         # print(f"CSV file created: {output_csv}")
#         # print(f"Total rows written: {len(all_rows)}")
#     else:
#         # print("No data found to write to CSV")


# # Usage
# if __name__ == "__main__":
#     directory_path = "logs/thinking_dir" # os.getcwd() #"."  # Change this to your directory path
#     output_csv = "json_output.csv"
    
#     process_directory(directory_path, output_csv)

# Code version 0.1 

# import os
# import json
# import csv
# import re
# from pathlib import Path

# agent_list = ["aircraft_acu_connect", "aircraft_baggage_unload", "aircraft_cabin_cleaning",
#               "aircraft_catering_loading", "aircraft_chocks_install", "aircraft_crew_debrief",
#               "aircraft_crew_exit", "aircraft_disembark", "aircraft_door_opening",
#               "aircraft_engines_stop", "aircraft_inspection_maintenance", "aircraft_jetbridge_connect",
#               "aircraft_fueling", "aircraft_gate_selection", "aircraft_ground_services",
#               "aircraft_ground_traffic", "aircraft_gpu_connect", "aircraft_landing",
#               "aircraft_lavatory_service", "aircraft_taxiing", "aircraft_traffic_controller",
#               "aircraft_turnaround", "AirlineTurnaround"]

# param_list = ["timestamp", "agent_name", "step_code", "tool_start", "tool_end", "tool_output", 
#               "aircraft_direction", "aircraft_type",
#               "flight_number", "flight_status", "assigned_runway_id", "assigned_runway_length",
#               "gate_id", "acu_readiness_status", "gpu_readiness_status",
#               "wheels_chocks_readiness_status", "ground_clearance_type", "ground_clearance_status",
#               "wheels_chocks_installation_status", "engines_stop_status", "acu_connection_status",
#               "gpu_connection_status", "jetbridge_connection_status", "door_opening_status",
#               "passenger_disembarkation_status", "baggage_unload_status", "crew_debrief_status",
#               "crew_exit_status", "cabin_cleaning_status", "lavatory_service_status",
#               "catering_loading_status", "inspection_maintenance_status", "fueling_status"]



# def extract_agent_name(content):
#     """Extract agent name from the first line after 'Agent:' tag"""
#     # match = re.search(r'<<Agent:\s*(.+)', content)
#     # # print("\n")
#     # # print("---------- MATCH ---------- ")
#     # # print(match)
#     # # print("--------------------------------------- ")
#     # # print("\n")
#     # if match:
#     #     agent_full_name = match.group(1).strip()
#     #     # Extract the last part after the last dot or double underscore
#     #     parts = re.split(r'[._]+', agent_full_name)
#     #     return parts[-1] if parts else agent_full_name
#     # return ""

#     # agent_name = content.split('Agent: ') #= 'Agent: aircraft_turnaround_manager.aircraft_turnaround_operator.__AirlineTurnaround__aircraft_acu_connect'
#     # agent_name = content.split('Agent: ')[1]
#     # # print(agent_name)
#     # return agent_name,new_content

# # def process_string(s):
# #     """
# #     Extract first line, substring after 'Agent', and remaining content.
    
# #     Args:
# #         s: String content of a text file
        
# #     Returns:
# #         tuple: (s1, s2) where s1 is content after 'Agent' in first line,
# #                and s2 is the string without the first line
# #     """
#     # 1. Extract the first line l1
#     lines = content.split('\n', 1)  # Split only at first newline
#     l1 = lines[0]
    
#     # 2. Extract substring s1 after 'Agent' in l1
#     if 'Agent' in l1:
#         agent_name = l1.split('Agent', 1)[1]  # Get content after 'Agent'
#     else:
#         agent_name = ""  # Return empty string if 'Agent' not found

#     # Reformat agent name path to extract the agent name    
#     agent_name = agent_name.replace('__', '.')
#     agent_name = agent_name.split('.')[-1]

#     # # print("-------------- AGENT NAME ------------- ")
#     # # print(agent_name)
#     # # print("--------------------------------------- ")

#     # 3. Remove l1 from s and save as s2
#     if len(lines) > 1:
#         log_body = lines[1]  # Remaining content after first line
#     else:
#         log_body = ""  # Empty string if only one line
    
#     # 4. Return both s1 and s2
#     return agent_name, log_body

# def parse_json_blocks(content):
#     """Extract all JSON blocks from the content with their timestamps"""
#     blocks = []
    
#     # Pattern to match timestamp and JSON block
#     pattern = r'\[AGENT\] @ ([\d\-: ]+):\s*(?:Received arguments:|Got result:)\s*```json\s*(\{.*?\})\s*```'
    
#     matches = re.finditer(pattern, content, re.DOTALL)
    
#     for match in matches:
#         timestamp = match.group(1).strip()
#         json_str = match.group(2).strip()
        
#         try:
#             json_data = json.loads(json_str)
#             blocks.append({
#                 'timestamp': timestamp,
#                 'json_data': json_data
#             })
#         except json.JSONDecodeError as e:
#             # print(f"Error parsing JSON: {e}")
#             continue
    
#     return blocks

# def extract_nested_json(text):
#     """Extract JSON from tool_output if it contains embedded JSON"""
#     if isinstance(text, str):
#         match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
#         if match:
#             try:
#                 return json.loads(match.group(1))
#             except json.JSONDecodeError:
#                 pass
#     return {}

# def flatten_data(json_data):
#     """Flatten the JSON data, including nested tool_args and tool_output"""
#     flat_data = {}
    
#     for key, value in json_data.items():
#         if key == 'tool_args' and isinstance(value, dict):
#             # Merge tool_args into flat_data
#             flat_data.update(value)
#         elif key == 'tool_output':
#             # Extract JSON from tool_output if present
#             nested_json = extract_nested_json(value)
#             flat_data.update(nested_json)
#         elif key in ['tool_start', 'tool_end']:
#             flat_data[key] = value
#         else:
#             flat_data[key] = value
    
#     return flat_data

# def parse_file(filepath, agent_name):
#     """Parse a single file and return rows for CSV"""
#     rows = []
    
#     with open(filepath, 'r', encoding='utf-8') as f:
#         content = f.read()
    
#     # Extract agent name from file content and remove the top line from content
#     extracted_agent_name, content = extract_agent_name(content)

#     # print("-------------- AGENT NAME ------------- ")
#     # print(extracted_agent_name)
#     # print("--------------------------------------- ")
    
#     # Parse JSON blocks
#     blocks = parse_json_blocks(content)
    
#     for block in blocks:

#         # print("================ BLOCK ================ ")
#         # print(block)
#         # print("======================================= ")

#         row = {param: "" for param in param_list}
#         row['timestamp'] = block['timestamp']
#         row['agent_name'] = extracted_agent_name
        
#         # Flatten and extract data
#         flat_data = flatten_data(block['json_data'])
        
#         # Fill in values for parameters in param_list
#         for param in param_list:
#             if param in flat_data:
#                 value = flat_data[param]
#                 # Convert None to empty string
#                 row[param] = "" if value is None else str(value)
        
#         rows.append(row)
    
#     return rows

# def process_directory(directory_path, output_csv):
#     """Process all files in directory that match agent_list"""
#     all_rows = []
    
#     directory = Path(directory_path)
    
#     # Iterate through all files in directory
#     for filepath in directory.iterdir():
#         if filepath.is_file():
#             filename = filepath.name
            
#             # Check if any agent name is in the filename
#             for agent in agent_list:
#                 if agent in filename:
#                     # print(f"Processing file: {filename}")
#                     rows = parse_file(filepath, agent)
#                     all_rows.extend(rows)
#                     break
    
#     # Write to CSV
#     if all_rows:
#         with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=param_list)
#             writer.writeheader()
#             writer.writerows(all_rows)
#         # print(f"CSV file created: {output_csv}")
#         # print(f"Total rows written: {len(all_rows)}")
#     else:
#         # print("No data found to write to CSV")

# # Usage
# if __name__ == "__main__":
#     directory_path = "logs/thinking_dir" # os.getcwd() #"."  # Change this to your directory path
#     output_csv = "json_output.csv"
    
#     process_directory(directory_path, output_csv)