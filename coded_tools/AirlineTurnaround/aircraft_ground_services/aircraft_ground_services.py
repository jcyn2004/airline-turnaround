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

class execute_cpu_gpu_operator(CodedTool):
    """
    CodedTool implementation that calls function that operates ground power unit on the ground at the gate.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"
        ground_equipments_base = "/Users/971244/workspace/neuro-san-studio/coded_tools/aircraft_gate_selection/gate_equipments_base.csv"

        # Check parameters in sly data
        aircraft_type: str = sly_data.get("aircraft_type", None)   
        flight_number: str = sly_data.get("flight_number", None)   
        flight_status: str = sly_data.get("flight_status", None)
        gate_id: str = sly_data.get("gate_id", None)
        ground_services_request_type: str = sly_data.get("ground_services_request_type", None)

        print("################################################################")
        print("SLY DATA - GPU OPERATOR")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("flight_status: ", flight_status)
        print("gate_id: ", gate_id)
        print("ground_services_request_type: ", ground_services_request_type)
        print("################################################################")

        # Add redundancy with another check in args data
        if aircraft_type is None: 
            aircraft_type: str = args.get("aircraft_type", None)

        if flight_number is None: 
            flight_number: str = args.get("flight_number", None) 

        if gate_id is None: 
            gate_id: str = args.get("gate_id", None)

        if flight_status is None: 
            flight_status: str = args.get("flight_status", None)

        if ground_services_request_type is None: 
            ground_services_request_type: str = args.get("ground_services_request_type", None)

        print("################################################################")
        print("ARGS - GPU OPERATOR")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("flight_status: ", flight_status)
        print("gate_id: ", gate_id)
        print("ground_services_request_type: ", ground_services_request_type)
        print("################################################################")

        gpu_readiness_status = 'no'
        gpu_connect_status = 'not connected'

        if (('readiness' in ground_services_request_type) | ('ready' in ground_services_request_type)):  
            df = pd.read_csv(ground_equipments_base)
            df1 = df.loc[df['gate_id'] == gate_id]
            gate_item_count = df1.shape[0]
            print("---------------------------------------------")
            print(df)
            print("READINESS INQUIRY")
            print("gate_item_count: ", gate_item_count)
            print(df1)
            if df1.shape[0] > 0:
                gpu_readiness_status = df.loc[df['gate_id'] == gate_id, 'gpu_readiness'].iloc[0]
                print("gpu_readiness_status: ", gpu_readiness_status)
                print("---------------------------------------------")
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow}: ground power unit is ready for flight {flight_number} of aircraft type {aircraft_type} assigned to gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")
            else: 
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow}: ground power unit is NOT ready for flight {flight_number} of aircraft type {aircraft_type} assigned to gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")      

            sly_data["gpu_readiness_status"] = gpu_readiness_status     

            return gpu_readiness_status

        else: 
            if (('block' in flight_status) | ('Block' in flight_status) | ('BLOCK' in flight_status)): 

                time.sleep(3)  # Simulates long-running work
                gpu_connect_status = 'connected'
                sly_data["gpu_connect_status"] = gpu_connect_status  

                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow}: ground power has been connected to flight {flight_number} aircraft of type {aircraft_type} at gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")     

                return gpu_connect_status 
            else: 
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow}: ground power unit cannot be connected to flight {flight_number} aircraft of type {aircraft_type} because it is not on blocks at gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")  

                return f"Error: wheels chocks cannot be placed until flight {flight_number} aircraft of type {aircraft_type} is on blocks at gate {gate_id}."

        # else: 
        #     if 'On_Blocks' in flight_status: 
        #         time.sleep(5)
        #         gpu_connect_status = 'connected'

        #     sly_data["gpu_connect_status"] = gpu_connect_status   
        #     return gpu_connect_status


            # # # async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
            # # def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
            # #     """Run invoke asynchronously."""
            # #     # return await asyncio.to_thread(self.invoke, args, sly_data)
            # #     return self.invoke(args, sly_data)  

class execute_wheels_chocks_operator(CodedTool):
    """
    CodedTool implementation that calls function that operates wheels chocks on the ground at the gate.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"
        ground_equipments_base = "/Users/971244/workspace/neuro-san-studio/coded_tools/aircraft_gate_selection/gate_equipments_base.csv"

        # Check parameters in sly data
        aircraft_type: str = sly_data.get("aircraft_type", None)   
        flight_number: str = sly_data.get("flight_number", None)   
        flight_status: str = sly_data.get("flight_status", None)
        gate_id: str = sly_data.get("gate_id", None)
        ground_services_request_type: str = sly_data.get("ground_services_request_type", None)

        print("################################################################")
        print("SLYDATA - WHEELS CHOCKS OPERATOR")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("flight_status: ", flight_status)
        print("gate_id: ", gate_id)
        print("ground_services_request_type: ", ground_services_request_type)
        print("################################################################")

        # Add redundancy with another check in args data
        if aircraft_type is None: 
            aircraft_type: str = args.get("aircraft_type", None)

        if flight_number is None: 
            flight_number: str = args.get("flight_number", None) 

        if gate_id is None: 
            gate_id: str = args.get("gate_id", None)

        if flight_status is None: 
            flight_status: str = args.get("flight_status", None)

        if ground_services_request_type is None: 
            ground_services_request_type: str = args.get("ground_services_request_type", None)

        print("################################################################")
        print("ARGS - WHEELS CHOCKS OPERATOR")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("flight_status: ", flight_status)
        print("gate_id: ", gate_id)
        print("ground_services_request_type: ", ground_services_request_type)
        print("################################################################")

        wheels_chocks_readiness_status = 'no'
        wheels_chocks_placed_status = 'not placed'

        if (('readiness' in ground_services_request_type) | ('ready' in ground_services_request_type)):  
            df = pd.read_csv(ground_equipments_base)
            df1 = df.loc[df['gate_id'] == gate_id]
            gate_item_count = df1.shape[0]
            print("---------------------------------------------")
            print(df)
            print("READINESS INQUIRY")
            print("gate_item_count: ", gate_item_count)
            print(df1)
            if df1.shape[0] > 0:
                wheels_chocks_readiness_status = df.loc[df['gate_id'] == gate_id, 'wheels_chocks_readiness'].iloc[0]
                print("wheels_chocks_readiness_status: ", wheels_chocks_readiness_status)
                print("---------------------------------------------")
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow}: wheels chocks set is ready for flight {flight_number} of aircraft type {aircraft_type} assigned to gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")
            else: 
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow}: Wheels chocks set is NOT ready for flight {flight_number} of aircraft type {aircraft_type} assigned to gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")      

            sly_data["wheels_chocks_readiness_status"] = wheels_chocks_readiness_status     

            return wheels_chocks_readiness_status

        else: 
            if (('block' in flight_status) | ('Block' in flight_status) | ('BLOCK' in flight_status)): 

                time.sleep(3)  # Simulates long-running work
                wheels_chocks_placed_status = 'placed'
                sly_data["wheels_chocks_placed_status"] = wheels_chocks_placed_status  

                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow}: wheels chocks to flight {flight_number} aircraft of type {aircraft_type} has been placed at gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")     

                return wheels_chocks_placed_status 
            else: 
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow}: wheels chocks cannot be placed to flight {flight_number} aircraft of type {aircraft_type} because it is not on blocks at gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")  
                
                return f"Error: wheels chocks cannot be placed until flight {flight_number} aircraft of type {aircraft_type} is on blocks at gate {gate_id}."

        # else: 
        #     if 'On_Blocks' in flight_status: 
        #         time.sleep(5)
        #         wheels_chocks_placed_status = 'placed'

        #     sly_data["wheels_chocks_placed_status"] = wheels_chocks_placed_status   
        #     return wheels_chocks_placed_status

            # # # async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
            # # def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
            # #     """Run invoke asynchronously."""
            # #     # return await asyncio.to_thread(self.invoke, args, sly_data)
            # #     return self.invoke(args, sly_data)  

class execute_tug_operator(CodedTool):
    """
    CodedTool implementation that calls function that operates wheels chocks on the ground at the gate.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"
        ground_equipments_base = "/Users/971244/workspace/neuro-san-studio/coded_tools/aircraft_gate_selection/gate_equipments_base.csv"

        # Check parameters in sly data
        aircraft_type: str = sly_data.get("aircraft_type", None)   
        flight_number: str = sly_data.get("flight_number", None)   
        flight_status: str = sly_data.get("flight_status", None)
        gate_id: str = sly_data.get("gate_id", None)
        ground_services_request_type: str = sly_data.get("ground_services_request_type", None)

        print("################################################################")
        print("SLYDATA - WHEELS CHOCKS OPERATOR")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("flight_status: ", flight_status)
        print("gate_id: ", gate_id)
        print("ground_services_request_type: ", ground_services_request_type)
        print("################################################################")

        # Add redundancy with another check in args data
        if aircraft_type is None: 
            aircraft_type: str = args.get("aircraft_type", None)

        if flight_number is None: 
            flight_number: str = args.get("flight_number", None) 

        if gate_id is None: 
            gate_id: str = args.get("gate_id", None)

        if flight_status is None: 
            flight_status: str = args.get("flight_status", None)

        print("################################################################")
        print("ARGS - WHEELS CHOCKS OPERATOR")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("flight_status: ", flight_status)
        print("gate_id: ", gate_id)
        print("ground_services_request_type: ", ground_services_request_type)
        print("################################################################")

        tug_readiness_status = 'no'
        tug_connect_status = 'not connected'

        if (('readiness' in ground_services_request_type) | ('ready' in ground_services_request_type)):  
            df = pd.read_csv(ground_equipments_base)
            df1 = df.loc[df['gate_id'] == gate_id]
            gate_item_count = df1.shape[0]
            print("---------------------------------------------")
            print(df)
            print("READINESS INQUIRY")
            print("gate_item_count: ", gate_item_count)
            print(df1)
            if df1.shape[0] > 0:
                tug_readiness_status = df.loc[df['gate_id'] == gate_id, 'tug_readiness'].iloc[0]
                print("tug_readiness_status: ", tug_readiness_status)
                print("---------------------------------------------")
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow} tug unit is ready for flight {flight_number} of aircraft type {aircraft_type} assigned to gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")
            else: 
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow} Wheels chocks set is NOT ready for flight {flight_number} of aircraft type {aircraft_type} assigned to gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")      

            sly_data["tug_readiness_status"] = tug_readiness_status     

            return tug_readiness_status

        else: 
            if 'On_Blocks' in flight_status: 
                time.sleep(5)
                tug_connect_status = 'connected'

            sly_data["tug_connect_status"] = tug_connect_status   
            return tug_connect_status

            # # # async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
            # # def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
            # #     """Run invoke asynchronously."""
            # #     # return await asyncio.to_thread(self.invoke, args, sly_data)
            # #     return self.invoke(args, sly_data)  

class execute_flight_tracker(CodedTool):
    """
    Read and return sly data in read mode, or write and update sly data in write. 
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: an empty dictionary (not used).

        :param sly_data: a dictionary with the following keys:
            - flight_number
            - aircraft_type
            - ground_clearance_type
            - flight_status
            - assigned_runway_id
            - gate_id
            - flight_tracker_inquiry_mode

        :return: None in write mode or any of teh parameters in read mode
        """

        # Read parameters from args
        flight_number: str = args.get("flight_number", None)   
        aircraft_type: str = args.get("aircraft_type", None)   
        ground_clearance_type: str = args.get("ground_clearance_type", None)   
        flight_status: str = args.get("flight_status", None)   
        assigned_runway_id: str = args.get("assigned_runway_id", None)   
        gate_id: str = args.get("gate_id", None)   
        ground_services_request_type: str = args.get("ground_services_request_type", None)   
        gpu_readiness_status: str = args.get("gpu_readiness_status", None)   
        chocks_readiness_status: str = args.get("chocks_readiness_status", None)  

        # Write parameters to sly_data
        sly_data["flight_number"] = flight_number   
        sly_data["aircraft_type"] = aircraft_type   
        sly_data["ground_clearance_type"] = ground_clearance_type   
        sly_data["flight_status"] = flight_status   
        sly_data["assigned_runway_id"] = assigned_runway_id   
        sly_data["gate_id"] = gate_id   
        sly_data["ground_services_request_type"] = ground_services_request_type     
        sly_data["gpu_readiness_status"] = gpu_readiness_status    
        sly_data["chocks_readiness_status"] = chocks_readiness_status   

# Flight AF84 has just landed and is set to deplane at gate A1. What is the ground services readiness? 

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
            - gpu_readiness_status
            - acu_connection_status 
            - gpu_connection_status 
            - wheels_chocks_installation status
            - engines_stop_status
            - jetbridge_connection_status
            - door_opening_status
            - passenger_disembarkation_status
            - crew_exit_status
            - baggage_unload_status

        :return: None in write mode or any of teh parameters in read mode
        """

        file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"

        print("\n")
        print("\n")
        print(" #################### API TRACKER GENERIC #################### ")
        print("\n")
        print("\n")
        # Check and update flight_number
        flight_number: str = args.get("flight_number", None)
        if not flight_number:
            print("flight_number has not been provided in user inquiry. Trying to get it from sly_data")
            flight_number = sly_data.get("flight_number")
            if flight_number: 
                # sly_data["flight_number"] = flight_number
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
        if not aircraft_type:
            print("aircraft_type has not been provided in user inquiry. Trying to get it from sly_data")
            aircraft_type = sly_data.get("aircraft_type")
            if aircraft_type: 
                # sly_data["aircraft_type"] = aircraft_type
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
        if not flight_status:
            print("flight_status has not been provided in user inquiry. Trying to get it from sly_data")
            flight_status = sly_data.get("flight_status")
            if flight_status: 
                # sly_data["flight_status"] = flight_status
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
        if not gate_id:
            print("gate_id has not been provided in user inquiry. Trying to get it from sly_data")
            gate_id = sly_data.get("gate_id")
            if gate_id: 
                # sly_data["gate_id"] = gate_id
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
        if not acu_connection_status:
            print("acu_connection_status has not been provided in user inquiry. Trying to get it from sly_data")
            acu_connection_status = sly_data.get("acu_connection_status")
            if acu_connection_status: 
                # sly_data["acu_connection_status"] = acu_connection_status
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
        if not gpu_connection_status:
            print("gpu_connection_status has not been provided in user inquiry. Trying to get it from sly_data")
            gpu_connection_status = sly_data.get("gpu_connection_status")
            if gpu_connection_status: 
                # sly_data["gpu_connection_status"] = gpu_connection_status
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
        if not wheels_chocks_installation_status:
            print("wheels_chocks_installation_status has not been provided in user inquiry. Trying to get it from sly_data")
            wheels_chocks_installation_status = sly_data.get("wheels_chocks_installation_status")
            if wheels_chocks_installation_status: 
                # sly_data["wheels_chocks_installation_status"] = wheels_chocks_installation_status
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
        if not engines_stop_status:
            print("engines_stop_status has not been provided in user inquiry. Trying to get it from sly_data")
            engines_stop_status = sly_data.get("engines_stop_status")
            if engines_stop_status: 
                # sly_data["engines_stop_status"] = engines_stop_status
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
        if not jetbridge_connection_status:
            print("jetbridge_connection_status has not been provided in user inquiry. Trying to get it from sly_data")
            jetbridge_connection_status = sly_data.get("jetbridge_connection_status")
            if jetbridge_connection_status: 
                # sly_data["jetbridge_connection_status"] = jetbridge_connection_status
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
        if not door_opening_status:
            print("door_opening_status has not been provided in user inquiry. Trying to get it from sly_data")
            door_opening_status = sly_data.get("door_opening_status")
            if door_opening_status: 
                # sly_data["door_opening_status"] = door_opening_status
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
        if not ground_services_request_type:
            print("ground_services_request_type has not been provided in user inquiry. Trying to get it from sly_data")
            ground_services_request_type = sly_data.get("ground_services_request_type")
            if ground_services_request_type: 
                sly_data["ground_services_request_type"] = ground_services_request_type
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
        if not wheels_chocks_readiness_status:
            print("wheels_chocks_readiness_status has not been provided in user inquiry. Trying to get it from sly_data")
            wheels_chocks_readiness_status = sly_data.get("wheels_chocks_readiness_status")
            if wheels_chocks_readiness_status: 
                # sly_data["wheels_chocks_readiness_status"] = wheels_chocks_readiness_status
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

        # Check and update gpu_readiness_status
        gpu_readiness_status: str = args.get("gpu_readiness_status", None)
        if not gpu_readiness_status:
            print("gpu_readiness_status has not been provided in user inquiry. Trying to get it from sly_data")
            gpu_readiness_status = sly_data.get("gpu_readiness_status")
            if gpu_readiness_status: 
                # sly_data["gpu_readiness_status"] = gpu_readiness_status
                print("\n")
                print("\n")
                print("####### gpu_readiness_status read from sly data: #######", gpu_readiness_status)
                print("\n")
                print("\n")
        else: 
            sly_data["gpu_readiness_status"] = gpu_readiness_status       
            print("\n")
            print("\n")
            print("####### gpu_readiness_status read from args: #######", gpu_readiness_status)
            print("\n")
            print("\n")

        # Check and update passenger_disembarkation_status
        passenger_disembarkation_status: str = args.get("passenger_disembarkation_status", None)
        if not passenger_disembarkation_status:
            print("passenger_disembarkation_status has not been provided in user inquiry. Trying to get it from sly_data")
            passenger_disembarkation_status = sly_data.get("passenger_disembarkation_status")
            if passenger_disembarkation_status: 
                # sly_data["passenger_disembarkation_status"] = passenger_disembarkation_status
                print("\n")
                print("\n")
                print("####### passenger_disembarkation_status read from sly data: #######", passenger_disembarkation_status)
                print("\n")
                print("\n")
        else: 
            sly_data["passenger_disembarkation_status"] = passenger_disembarkation_status       
            print("\n")
            print("\n")
            print("####### passenger_disembarkation_status read from args: #######", passenger_disembarkation_status)
            print("\n")
            print("\n")

        # Check and update crew_exit_status
        crew_exit_status: str = args.get("crew_exit_status", None)
        if not crew_exit_status:
            print("crew_exit_status has not been provided in user inquiry. Trying to get it from sly_data")
            crew_exit_status = sly_data.get("crew_exit_status")
            if crew_exit_status: 
                # sly_data["crew_exit_status"] = crew_exit_status
                print("\n")
                print("\n")
                print("####### crew_exit_status read from sly data: #######", crew_exit_status)
                print("\n")
                print("\n")
        else: 
            sly_data["crew_exit_status"] = crew_exit_status       
            print("\n")
            print("\n")
            print("####### crew_exit_status read from args: #######", crew_exit_status)
            print("\n")
            print("\n")

        # Check and update baggage_unload_status
        baggage_unload_status: str = args.get("baggage_unload_status", None)
        if not baggage_unload_status:
            print("baggage_unload_status has not been provided in user inquiry. Trying to get it from sly_data")
            baggage_unload_status = sly_data.get("baggage_unload_status")
            if baggage_unload_status: 
                # sly_data["baggage_unload_status"] = baggage_unload_status
                print("\n")
                print("\n")
                print("####### baggage_unload_status read from sly data: #######", baggage_unload_status)
                print("\n")
                print("\n")
        else: 
            sly_data["baggage_unload_status"] = baggage_unload_status       
            print("\n")
            print("\n")
            print("####### baggage_unload_status read from args: #######", baggage_unload_status)
            print("\n")
            print("\n")

        # This return list will be trimmed to contain only parameters relevant to the agentic system where this generic coded tool is used. 
        # return flight_status,flight_number,aircraft_type,gate_id,acu_connection_status,gpu_connection_status,wheels_chocks_installation_status,engines_stop_status,jetbridge_connection_status,door_opening_status, ground_services_request_type, wheels_chocks_readiness_status
        return gpu_readiness_status, wheels_chocks_readiness_status, gpu_connection_status, wheels_chocks_installation_status, ground_services_request_type

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)

#########################################################

