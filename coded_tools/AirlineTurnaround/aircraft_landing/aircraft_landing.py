from typing import Any, Dict, Union
import logging
import pandas as pd
import json 
from neuro_san.interfaces.coded_tool import CodedTool
from datetime import datetime
import time
import random
import os
import platform
import fcntl
from typing import Dict, Any, Union
import asyncio
import re

def _from_args_or_sly(args: Dict[str, Any], sly: Dict[str, Any], key: str) -> Any:
    """Prefer args[key]; fallback to sly_data[key]."""
    v = args.get(key)
    return v if v is not None else sly.get(key)

def _from_sly_or_args(sly: Dict[str, Any], args: Dict[str, Any], key: str) -> Any:
    """Prefer args[key]; fallback to sly_data[key]."""
    v = sly.get(key)
    return v if v is not None else args.get(key)

class execute_clearance_validation(CodedTool):
    """
    CodedTool implementation that calls function for clearance validation.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"
        aircraft_base = "/Users/971244/workspace/airline-turnaround/coded_tools/aircraft_operation/aircraft_base.csv"
        runway_base = "/Users/971244/workspace/airline-turnaround/coded_tools/aircraft_operation/runways_base.csv"

        # Check aircraft type parameter passed by the agent
        aircraft_type: str = args.get("aircraft_type", None)   
        clearance_type: str = args.get("clearance_type", None)   
        assigned_runway_id: str = args.get("assigned_runway_id", None)  
        assigned_runway_length: str = args.get("assigned_runway_length", None)  

        clearance_landing_valid = 'No'
        clearance_takeoff_valid = 'No'

        if aircraft_type is None: 
            aircraft_type: str = sly_data.get(aircraft_type, None)

        if clearance_type is None: 
            clearance_type: str = sly_data.get(clearance_type, None)
 
        if assigned_runway_id is None: 
            assigned_runway_id: str = sly_data.get(assigned_runway_id, None)

        if assigned_runway_length is None: 
            assigned_runway_length: str = sly_data.get(assigned_runway_length, None)

        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ aircraft landing agent $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print("clearance_type: ", clearance_type)
        print("aircraft_type: ", aircraft_type)
        print("assigned_runway_id: ", assigned_runway_id)
        print("assigned_runway_length: ", assigned_runway_length)
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

        if ((clearance_type == 'cleared for landing') | ('landing' in clearance_type)):    

            df1 = pd.read_csv(aircraft_base)
            print("---------------------- raw aircraft data ------------------------")
            print(df1)

            min_runway_length_for_landing = df1[df1['Aircraft_Model'] == aircraft_type]                                                
            min_runway_length_for_landing = min_runway_length_for_landing['Landing(m)'].iloc[0]
            print("---------------------- min runway length(m) for landing airfraft_type ------------------------")
            print(min_runway_length_for_landing)        

            assigned_runway_length = float(str(assigned_runway_length).split(' ')[0])
            min_runway_length_for_landing = float(str(min_runway_length_for_landing).split(' ')[0]) 

            if (assigned_runway_length < min_runway_length_for_landing):
                return "Error: assigned runway length does not meet aircraft landing requirement."
            else: 
                clearance_landing_valid = 'Yes'

                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow} clearance to land {aircraft_type} to runway {assigned_runway_id} that has a length of [{min_runway_length_for_landing}] meters is valid. \n"
                print("----------------------------------------------")
                print(line)

                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")
        
        if ((clearance_type == 'cleared for takeoff') | ('takeoff' in clearance_type)):    

            df1 = pd.read_csv(aircraft_base)
            print("---------------------- raw aircraft data ------------------------")
            print(df1)

            min_runway_length_for_takeoff = df1[df1['Aircraft_Model'] == aircraft_type]                                                  
            min_runway_length_for_takeoff = min_runway_length_for_takeoff['Takeoff(m)'].iloc[0]
            print("---------------------- min runway length(m) for takeoff airfraft_type ------------------------")
            print(min_runway_length_for_takeoff)    

            assigned_runway_length = float(str(assigned_runway_length).split(' ')[0])
            min_runway_length_for_takeoff = float(str(min_runway_length_for_takeoff).split(' ')[0]) 

            if (assigned_runway_length < min_runway_length_for_takeoff):
                return "Error: assigned runway length does not meet aircraft takeoff requirement."
            else:     
                clearance_takeoff_valid = 'Yes'

                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow} clearance to takeoff {aircraft_type} to runway {assigned_runway_id} that has a length of [{min_runway_length_for_takeoff}] meters is valid. \n"
                print("----------------------------------------------")
                print(line)
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")

        sly_data["clearance_landing_valid"] = clearance_landing_valid 
        sly_data["clearance_takeoff_valid"] = clearance_takeoff_valid 

        return clearance_landing_valid, clearance_takeoff_valid

class execute_aircraft_landing(CodedTool):
    """
    CodedTool implementation that calls function for aircraft landing.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"
        aircraft_base = "/Users/971244/workspace/airline-turnaround/coded_tools/aircraft_operation/aircraft_base.csv"
        runway_base = "/Users/971244/workspace/airline-turnaround/coded_tools/aircraft_operation/runways_base.csv"

        # Check aircraft type parameter passed by the agent
        flight_status: str = sly_data.get("flight_status", None) 
        aircraft_type: str = sly_data.get("aircraft_type", None)   
        flight_number: str = sly_data.get("flight_number", None)   
        traffic_direction: str = sly_data.get("traffic_direction", None) 
        clearance_type: str = sly_data.get("clearance_type", None)   
        assigned_runway_id: str = sly_data.get("assigned_runway_id", None)  
        assigned_runway_length: str = sly_data.get("assigned_runway_length", None)  

        if flight_status is None: 
            flight_status: str = args.get(flight_status, None)

        if aircraft_type is None: 
            aircraft_type: str = args.get(aircraft_type, None)

        if flight_number is None: 
            flight_number: str = args.get(flight_number, None)

        if traffic_direction is None: 
            traffic_direction: str = args.get(traffic_direction, None)

        if clearance_type is None: 
            clearance_type: str = args.get(clearance_type, None)
 
        if assigned_runway_id is None: 
            assigned_runway_id: str = args.get(assigned_runway_id, None)

        if assigned_runway_length is None: 
            assigned_runway_length: str = args.get(assigned_runway_length, None)

        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ aircraft landing agent $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print("clearance_type: ", clearance_type)
        print("flight_status: ", flight_status)
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("traffic_direction: ", traffic_direction)
        print("assigned_runway_id: ", assigned_runway_id)
        print("assigned_runway_length: ", assigned_runway_length)
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

        if (((clearance_type == 'cleared for landing') | ('landing' in clearance_type)) & ((flight_status is None) | (flight_status == 'approach'))):    
            time.sleep(0.5) 
            flight_status = 'landed'

            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ aircraft operation status $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("flight_status: ", flight_status)

            timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line = f"{timenow}: flight {flight_number} has landed on runway {assigned_runway_id}"

            with open(file_path_log, mode="a", encoding="utf-8") as f:  
                f.write(line + "\n")

            sly_data["flight_status"] = flight_status 

            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ aircraft operation status update $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("flight_status: ", flight_status)
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$") 

        else: 
            flight_status = 'pending'

            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ aircraft operation status $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("flight_status: ", flight_status)

            timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line = f"{timenow}: flight {flight_number} needs clearance for landing"

            with open(file_path_log, mode="a", encoding="utf-8") as f:  
                f.write(line + "\n")

            sly_data["flight_status"] = flight_status 

            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ aircraft operation status update $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("flight_status: ", flight_status)
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$") 

        return flight_status

#############################################################################
# Tracker API for all parameters in the aircraft turnaround agentic system  #
# This coded tool proceeds as folloes:                                      #
#   - Check the sly data to read the latest value of parameters             #
#   - Update parameters with the value from args when sly data is empty     #
# Given the large number of parameters, a separate version of this coded    #
# tool will be edited for each agents so that it aonly returns the relevant # 
# one for the agent.                                                        #
#############################################################################
class trackerAPI(CodedTool):
    """
    Read and return sly data in read mode, or write and update sly data in write. 
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: an empty dictionary (not used).

        :param sly_data: a dictionary with the following keys:
            - flight_status
            - flight_number
            - aircraft_type
            - gate_id 
            - ground_services_request_type 
            - wheels_chocks_readiness_status
            - acu_connection_status 
            - gpu_connection_status 
            - wheels_chocks_installation status
            - engines_stop_status
            - jetbridge_connection_status
            - door_opening_status
            - aircraft_direction
            - assigned_runway_id 
            - assigned_runway_length
            - traffic_direction
            - clearance_type    

        :return: None in write mode or any of teh parameters in read mode
        """

        file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"

        print("\n")
        print("\n")
        print(" #################### API TRACKER GENERIC - AIRCRAFT DOOR OPENING #################### ")
        print("\n")
        print("\n")
        # Check and update flight_number
        flight_number: str = args.get("flight_number", None)
        print("\n")
        print("\n")
        print("####### flight_number read from args: #######", flight_number)
        print("\n")
        print("\n")
        if not flight_number:
            print("flight_number has not been provided in user inquiry. Trying to get it from sly_data")
            flight_number = sly_data.get("flight_number")
            if flight_number: 
                print("\n")
                print("\n")
                print("####### flight_number read from sly data: #######", flight_number)
                print("\n")
                print("\n")
        else: 
            sly_data["flight_number"] = flight_number       
            print("\n")
            print("\n")
            print("####### flight_number read from args: #######", flight_number)
            print("\n")
            print("\n")

        # Check and update aircraft_type
        aircraft_type: str = args.get("aircraft_type", None)
        print("\n")
        print("\n")
        print("####### aircraft_type read from args: #######", aircraft_type)
        print("\n")
        print("\n")        
        if not aircraft_type:
            print("aircraft_type has not been provided in user inquiry. Trying to get it from sly_data")
            aircraft_type = sly_data.get("aircraft_type")
            if aircraft_type: 
                print("\n")
                print("\n")
                print("####### aircraft_type read from sly data: #######", aircraft_type)
                print("\n")
                print("\n")
        else: 
            sly_data["aircraft_type"] = aircraft_type       
            print("\n")
            print("\n")
            print("####### aircraft_type read from args: #######", aircraft_type)
            print("\n")
            print("\n")

        # Check and update flight_status
        flight_status: str = args.get("flight_status", None)
        print("\n")
        print("\n")
        print("####### flight_status read from args: #######", flight_status)
        print("\n")
        print("\n")
        if not flight_status:
            print("flight_status has not been provided in user inquiry. Trying to get it from sly_data")
            flight_status = sly_data.get("flight_status")
            if flight_status: 
                print("\n")
                print("\n")
                print("####### flight_status read from sly data: #######", flight_status)
                print("\n")
                print("\n")
        else: 
            sly_data["flight_status"] = flight_status       
            print("\n")
            print("\n")
            print("####### flight_status read from args: #######", flight_status)
            print("\n")
            print("\n")

        # Check and update gate_id
        gate_id: str = args.get("gate_id", None)
        print("\n")
        print("\n")
        print("####### gate_id read from args: #######", gate_id)
        print("\n")
        print("\n")
        if not gate_id:
            print("gate_id has not been provided in user inquiry. Trying to get it from sly_data")
            gate_id = sly_data.get("gate_id")
            if gate_id: 
                print("\n")
                print("\n")
                print("####### gate_id read from sly data: #######", flight_status)
                print("\n")
                print("\n")
        else: 
            sly_data["gate_id"] = gate_id       
            print("\n")
            print("\n")
            print("####### gate_id read from args: #######", gate_id)
            print("\n")
            print("\n")

        # Check and update acu_connection_status
        acu_connection_status: str = args.get("acu_connection_status", None)
        print("\n")
        print("\n")
        print("####### acu_connection_status read from args: #######", acu_connection_status)
        print("\n")
        print("\n")        
        if not acu_connection_status:
            print("acu_connection_status has not been provided in user inquiry. Trying to get it from sly_data")
            acu_connection_status = sly_data.get("acu_connection_status")
            if acu_connection_status: 
                print("\n")
                print("\n")
                print("####### acu_connection_status read from sly data: #######", acu_connection_status)
                print("\n")
                print("\n")
        else: 
            sly_data["acu_connection_status"] = acu_connection_status       
            print("\n")
            print("\n")
            print("####### acu_connection_status read from args: #######", acu_connection_status)
            print("\n")
            print("\n")

        # Check and update gpu_connection_status
        gpu_connection_status: str = args.get("gpu_connection_status", None)
        print("\n")
        print("\n")
        print("####### gpu_connection_status read from args: #######", gpu_connection_status)
        print("\n")
        print("\n")
        if not gpu_connection_status:
            print("gpu_connection_status has not been provided in user inquiry. Trying to get it from sly_data")
            gpu_connection_status = sly_data.get("gpu_connection_status")
            if gpu_connection_status: 
                print("\n")
                print("\n")
                print("####### gpu_connection_status read from sly data: #######", gpu_connection_status)
                print("\n")
                print("\n")
        else: 
            sly_data["gpu_connection_status"] = gpu_connection_status       
            print("\n")
            print("\n")
            print("####### gpu_connection_status read from args: #######", gpu_connection_status)
            print("\n")
            print("\n")

        # Check and update wheels_chocks_installation_status
        wheels_chocks_installation_status: str = args.get("wheels_chocks_installation_status", None)
        print("\n")
        print("\n")
        print("####### wheels_chocks_installation_status read from args: #######", wheels_chocks_installation_status)
        print("\n")
        print("\n")
        if not wheels_chocks_installation_status:
            print("wheels_chocks_installation_status has not been provided in user inquiry. Trying to get it from sly_data")
            wheels_chocks_installation_status = sly_data.get("wheels_chocks_installation_status")
            if wheels_chocks_installation_status: 
                print("\n")
                print("\n")
                print("####### wheels_chocks_installation_status read from sly data: #######", wheels_chocks_installation_status)
                print("\n")
                print("\n")
        else: 
            sly_data["wheels_chocks_installation_status"] = wheels_chocks_installation_status       
            print("\n")
            print("\n")
            print("####### wheels_chocks_installation_status read from args: #######", wheels_chocks_installation_status)
            print("\n")
            print("\n")

        # Check and update engines_stop_status
        engines_stop_status: str = args.get("engines_stop_status", None)
        print("\n")
        print("\n")
        print("####### engines_stop_status read from args: #######", engines_stop_status)
        print("\n")
        print("\n")
        if not engines_stop_status:
            print("engines_stop_status has not been provided in user inquiry. Trying to get it from sly_data")
            engines_stop_status = sly_data.get("engines_stop_status")
            if engines_stop_status: 
                print("\n")
                print("\n")
                print("####### engines_stop_status read from sly data: #######", engines_stop_status)
                print("\n")
                print("\n")
        else: 
            sly_data["engines_stop_status"] = engines_stop_status       
            print("\n")
            print("\n")
            print("####### engines_stop_status read from args: #######", engines_stop_status)
            print("\n")
            print("\n")

        # Check and update jetbridge_connection_status
        jetbridge_connection_status: str = args.get("jetbridge_connection_status", None)
        print("\n")
        print("\n")
        print("####### jetbridge_connection_status read from args: #######", jetbridge_connection_status)
        print("\n")
        print("\n")        
        if not jetbridge_connection_status:
            print("jetbridge_connection_status has not been provided in user inquiry. Trying to get it from sly_data")
            jetbridge_connection_status = sly_data.get("jetbridge_connection_status")
            if jetbridge_connection_status: 
                print("\n")
                print("\n")
                print("####### jetbridge_connection_status read from sly data: #######", jetbridge_connection_status)
                print("\n")
                print("\n")
        else: 
            sly_data["jetbridge_connection_status"] = jetbridge_connection_status       
            print("\n")
            print("\n")
            print("####### jetbridge_connection_status read from args: #######", jetbridge_connection_status)
            print("\n")
            print("\n")

        # Check and update door_opening_status
        door_opening_status: str = args.get("door_opening_status", None)
        print("\n")
        print("\n")
        print("####### door_opening_status read from args: #######", door_opening_status)
        print("\n")
        print("\n")
        if not door_opening_status:
            print("door_opening_status has not been provided in user inquiry. Trying to get it from sly_data")
            door_opening_status = sly_data.get("door_opening_status")
            if door_opening_status: 
                print("\n")
                print("\n")
                print("####### door_opening_status read from sly data: #######", door_opening_status)
                print("\n")
                print("\n")
        else: 
            sly_data["door_opening_status"] = door_opening_status       
            print("\n")
            print("\n")
            print("####### door_opening_status read from args: #######", door_opening_status)
            print("\n")
            print("\n")
            
        # Check and update ground_services_request_type
        ground_services_request_type: str = args.get("ground_services_request_type", None)
        print("\n")
        print("\n")
        print("####### ground_services_request_type read from args: #######", ground_services_request_type)
        print("\n")
        print("\n")
        if not ground_services_request_type:
            print("ground_services_request_type has not been provided in user inquiry. Trying to get it from sly_data")
            ground_services_request_type = sly_data.get("ground_services_request_type")
            if ground_services_request_type: 
                print("\n")
                print("\n")
                print("####### ground_services_request_type read from sly data: #######", ground_services_request_type)
                print("\n")
                print("\n")
        else: 
            sly_data["ground_services_request_type"] = ground_services_request_type       
            print("\n")
            print("\n")
            print("####### ground_services_request_type read from args: #######", ground_services_request_type)
            print("\n")
            print("\n")

        # Check and update wheels_chocks_readiness_status
        wheels_chocks_readiness_status: str = args.get("wheels_chocks_readiness_status", None)
        print("\n")
        print("\n")
        print("####### wheels_chocks_readiness_status read from args: #######", wheels_chocks_readiness_status)
        print("\n")
        print("\n")
        if not wheels_chocks_readiness_status:
            print("wheels_chocks_readiness_status has not been provided in user inquiry. Trying to get it from sly_data")
            wheels_chocks_readiness_status = sly_data.get("wheels_chocks_readiness_status")
            if wheels_chocks_readiness_status: 
                print("\n")
                print("\n")
                print("####### wheels_chocks_readiness_status read from sly data: #######", wheels_chocks_readiness_status)
                print("\n")
                print("\n")
        else: 
            sly_data["wheels_chocks_readiness_status"] = wheels_chocks_readiness_status       
            print("\n")
            print("\n")
            print("####### wheels_chocks_readiness_status read from args: #######", wheels_chocks_readiness_status)
            print("\n")
            print("\n")

        # Check and update aircraft_direction
        aircraft_direction: str = args.get("aircraft_direction", None)
        print("\n")
        print("\n")
        print("####### aircraft_direction read from args: #######", aircraft_direction)
        print("\n")
        print("\n")
        if not aircraft_direction:
            print("aircraft_direction has not been provided in user inquiry. Trying to get it from sly_data")
            aircraft_direction = sly_data.get("aircraft_direction")
            if aircraft_direction: 
                print("\n")
                print("\n")
                print("####### aircraft_direction read from sly data: #######", aircraft_direction)
                print("\n")
                print("\n")
        else: 
            sly_data["aircraft_direction"] = aircraft_direction       
            print("\n")
            print("\n")
            print("####### aircraft_direction read from args: #######", aircraft_direction)
            print("\n")
            print("\n")

        # Check and update assigned_runway_id
        assigned_runway_id: str = args.get("assigned_runway_id", None)
        print("\n")
        print("\n")
        print("####### assigned_runway_id read from args: #######", assigned_runway_id)
        print("\n")
        print("\n")
        if not assigned_runway_id:
            print("assigned_runway_id has not been provided in user inquiry. Trying to get it from sly_data")
            assigned_runway_id = sly_data.get("assigned_runway_id")
            if assigned_runway_id: 
                print("\n")
                print("\n")
                print("####### assigned_runway_id read from sly data: #######", assigned_runway_id)
                print("\n")
                print("\n")
        else: 
            sly_data["assigned_runway_id"] = assigned_runway_id       
            print("\n")
            print("\n")
            print("####### assigned_runway_id read from args: #######", assigned_runway_id)
            print("\n")
            print("\n")

        # Check and update assigned_runway_length
        assigned_runway_length: str = args.get("assigned_runway_length", None)
        print("\n")
        print("\n")
        print("####### assigned_runway_length read from args: #######", assigned_runway_length)
        print("\n")
        print("\n")
        if not assigned_runway_length:
            print("assigned_runway_length has not been provided in user inquiry. Trying to get it from sly_data")
            assigned_runway_length = sly_data.get("assigned_runway_length")
            if assigned_runway_length: 
                print("\n")
                print("\n")
                print("####### assigned_runway_length read from sly data: #######", assigned_runway_length)
                print("\n")
                print("\n")
        else: 
            sly_data["assigned_runway_length"] = assigned_runway_length       
            print("\n")
            print("\n")
            print("####### assigned_runway_length read from args: #######", assigned_runway_length)
            print("\n")
            print("\n")

        # Check and update traffic_direction
        traffic_direction: str = args.get("traffic_direction", None)
        print("\n")
        print("\n")
        print("####### traffic_direction read from args: #######", traffic_direction)
        print("\n")
        print("\n")
        if not traffic_direction:
            print("traffic_direction has not been provided in user inquiry. Trying to get it from sly_data")
            traffic_direction = sly_data.get("traffic_direction")
            if traffic_direction: 
                print("\n")
                print("\n")
                print("####### traffic_direction read from sly data: #######", traffic_direction)
                print("\n")
                print("\n")
        else: 
            sly_data["traffic_direction"] = traffic_direction       
            print("\n")
            print("\n")
            print("####### traffic_direction read from args: #######", traffic_direction)
            print("\n")
            print("\n")

        # Check and update clearance_type
        clearance_type: str = args.get("clearance_type", None)
        print("\n")
        print("\n")
        print("####### clearance_type read from args: #######", clearance_type)
        print("\n")
        print("\n")
        if not clearance_type:
            print("clearance_type has not been provided in user inquiry. Trying to get it from sly_data")
            clearance_type = sly_data.get("clearance_type")
            if clearance_type: 
                print("\n")
                print("\n")
                print("####### clearance_type read from sly data: #######", clearance_type)
                print("\n")
                print("\n")
        else: 
            sly_data["clearance_type"] = clearance_type       
            print("\n")
            print("\n")
            print("####### clearance_type read from args: #######", clearance_type)
            print("\n")
            print("\n")

        #####################################################################################################################################
        # This return list will be trimmed to contain only parameters relevant to the agentic system where this generic coded tool is used. #
        #####################################################################################################################################
        return flight_status, clearance_type, assigned_runway_id, assigned_runway_length

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)
 