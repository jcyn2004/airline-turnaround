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
from pathlib import Path

class execute_time_estimator(CodedTool):
    """
    CodedTool implementation that calls function that estimates cabin cleaning time duration.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        # file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"
        file_path_log = Path.cwd() / "test_debug" / "airlineturnaround.txt"
        # ground_equipments_base = "/Users/971244/workspace/airline-turnaround/coded_tools/ground_services/ground_equipments_base.csv"
        ground_equipments_base = Path.cwd() / "coded_tools" / "ground_services" / "ground_equipments_base.csv"

        # Check parameters in sly data
        aircraft_type: str = sly_data.get("aircraft_type", None)   
        flight_number: str = sly_data.get("flight_number", None)   
        gate_id: str = sly_data.get("gate_id", None)
        cabin_dirthiness_level: str = sly_data.get("cabin_dirthiness_level", None)

        print("################################################################")
        print("SLY DATA - CABIN CLEANING")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("gate_id: ", gate_id)
        print("cabin_dirthiness_level: ", cabin_dirthiness_level)
        print("################################################################")

        # Add redundancy with another check in args data
        if aircraft_type is None: 
            aircraft_type: str = args.get("aircraft_type", None)

        if flight_number is None: 
            flight_number: str = args.get("flight_number", None) 

        if gate_id is None: 
            gate_id: str = args.get("gate_id", None)

        if cabin_dirthiness_level is None: 
            cabin_dirthiness_level: str = args.get("cabin_dirthiness_level", None)

        print("################################################################")
        print("SLY DATA - CABIN CLEANING")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("gate_id: ", gate_id)
        print("cabin_dirthiness_level: ", cabin_dirthiness_level)
        print("################################################################")

        cabin_cleaning_time_estimate = 10

        if ('medium' in cabin_dirthiness_level): 
            cabin_cleaning_time_estimate = 15

        if ('high' in cabin_dirthiness_level): 
            cabin_cleaning_time_estimate = 20 

        sly_data["cabin_cleaning_time_estimate"] = cabin_cleaning_time_estimate     

        timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"{timenow} cabin cleaning for the aircraft with {cabin_dirthiness_level} dirthiness will take {cabin_cleaning_time_estimate} minutes"
        with open(file_path_log, mode="a", encoding="utf-8") as f:  
            f.write(line + "\n")        

        return cabin_cleaning_time_estimate

class execute_staff_provider(CodedTool):
    """
    CodedTool implementation that calls function that estimates cabin cleaning staff count.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        # file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"
        file_path_log = Path.cwd() / "test_debug" / "airlineturnaround.txt"
        # ground_equipments_base = "/Users/971244/workspace/airline-turnaround/coded_tools/ground_services/ground_equipments_base.csv"
        ground_equipments_base = Path.cwd() / "coded_tools" / "ground_services" / "ground_equipments_base.csv"

        # Check parameters in sly data
        aircraft_type: str = sly_data.get("aircraft_type", None)   
        flight_number: str = sly_data.get("flight_number", None)   
        gate_id: str = sly_data.get("gate_id", None)
        cabin_dirthiness_level: str = sly_data.get("cabin_dirthiness_level", None)

        print("################################################################")
        print("SLY DATA - CABIN CLEANING")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("gate_id: ", gate_id)
        print("cabin_dirthiness_level: ", cabin_dirthiness_level)
        print("################################################################")

        # Add redundancy with another check in args data
        if aircraft_type is None: 
            aircraft_type: str = args.get("aircraft_type", None)

        if flight_number is None: 
            flight_number: str = args.get("flight_number", None) 

        if gate_id is None: 
            gate_id: str = args.get("gate_id", None)

        if cabin_dirthiness_level is None: 
            cabin_dirthiness_level: str = args.get("cabin_dirthiness_level", None)

        print("################################################################")
        print("SLY DATA - CABIN CLEANING")
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("gate_id: ", gate_id)
        print("cabin_dirthiness_level: ", cabin_dirthiness_level)
        print("################################################################")

        cabin_cleaning_staff_estimate = 10

        if ('medium' in cabin_dirthiness_level): 
            cabin_cleaning_staff_estimate = 15

        if ('high' in cabin_dirthiness_level): 
            cabin_cleaning_staff_estimate = 20 

        sly_data["cabin_cleaning_staff_estimate"] = cabin_cleaning_staff_estimate     

        timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = f"{timenow} cabin cleaning for the aircraft with {cabin_dirthiness_level} dirthiness will need {cabin_cleaning_staff_estimate} staff"
        with open(file_path_log, mode="a", encoding="utf-8") as f:  
            f.write(line + "\n")        

        return cabin_cleaning_staff_estimate

class execute_wheels_chocks_operator(CodedTool):
    """
    CodedTool implementation that calls function that operates wheels chocks on the ground at the gate.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        # file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"
        file_path_log = Path.cwd() / "test_debug" / "airlineturnaround.txt"
        # ground_equipments_base = "/Users/971244/workspace/airline-turnaround/coded_tools/ground_services/ground_equipments_base.csv"
        ground_equipments_base = Path.cwd() / "coded_tools" / "ground_services" / "ground_equipments_base.csv"

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
                line = f"{timenow} wheels chocks set is ready for flight {flight_number} of aircraft type {aircraft_type} assigned to gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")
            else: 
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow} Wheels chocks set is NOT ready for flight {flight_number} of aircraft type {aircraft_type} assigned to gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")      

            sly_data["wheels_chocks_readiness_status"] = wheels_chocks_readiness_status     

            return wheels_chocks_readiness_status

        else: 
            flight_status = flight_status.lower()
            if ('block' in flight_status): 

                time.sleep(3)  # Simulates long-running work
                wheels_chocks_placed_status = 'placed'
                sly_data["wheels_chocks_placed_status"] = wheels_chocks_placed_status  

                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow} wheels chocks to flight {flight_number} aircraft of type {aircraft_type} has been placedd at gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")     

                return wheels_chocks_placed_status 
            else: 
                timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                line = f"{timenow} wheels chocks cannot be placed to flight {flight_number} aircraft of type {aircraft_type} because it is not on blocks at gate {gate_id}"
                with open(file_path_log, mode="a", encoding="utf-8") as f:  
                    f.write(line + "\n")  
                
                return f"Error: wheels chocks cannot be placed until flight {flight_number} aircraft of type {aircraft_type} is on blocks at gate {gate_id}."

class execute_tug_operator(CodedTool):
    """
    CodedTool implementation that calls function that operates wheels chocks on the ground at the gate.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        # file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"
        file_path_log = Path.cwd() / "test_debug" / "airlineturnaround.txt"
        # ground_equipments_base = "/Users/971244/workspace/airline-turnaround/coded_tools/ground_services/ground_equipments_base.csv"
        ground_equipments_base = Path.cwd() / "coded_tools" / "ground_services" / "ground_equipments_base.csv"

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

class trackerAPI(CodedTool):

    """
    Taxiing information.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: a dictionary with the following keys:
            - flight_number: the name of the shop to order from.
            - aircraft_type: the name of the person to order for.
            - flight_status: the details of the order.
            - assigned_runway_id: the details of the order.
            - gate_id: the details of the order.
            - ground_servics_inquiry_type: determine if the request is about readiness or else. 

        :param sly_data: a dictionary with the following keys:
            - username: optional - the name of the person to order for, if already known.

        :return:
            In case of successful execution:
                all parameters available.
            otherwise:
                a string error message in the format:
                "Error: <error message>"
        """
        print(">>>>>>>>>>>>>>>>>>> trackerAPI flight operation agent >>>>>>>>>>>>>>>>>>")

        # flight number is required to fulfill the request.
        flight_number: str = args.get("flight_number", None)
        if not flight_number:
            print("No flight number provided. Trying to get it from sly_data")
            flight_number = sly_data.get("flight_number")
        if not flight_number:
            error = "Error: Please provide a flight number for the request."
            print(error)
            return error
        sly_data["flight_number"] = flight_number

        # aircraft type is required to fulfill the request.
        aircraft_type: str = args.get("aircraft_type", None)
        if not aircraft_type:
            print("No aircraft type provided. Trying to get it from sly_data")
            aircraft_type = sly_data.get("aircraft_type")
        if not aircraft_type:
            error = "Error: Please provide an aircraft type for the request."
            print(error)
            return error
        sly_data["aircraft_type"] = aircraft_type

        # ground services inquiry type is required to fulfill the request.
        ground_services_request_type: str = args.get("ground_services_request_type", None)
        if not ground_services_request_type:
            print("No ground clearance provided. Trying to get it from sly_data")
            ground_services_request_type = sly_data.get("ground_services_request_type")
        if not ground_services_request_type:
            error = "Error: Please provide a ground service inquiry type for the request."
            print(error)
            return error    
        sly_data["ground_services_request_type"] = ground_services_request_type

        # flight status is required to fulfill the request.
        flight_status: str = args.get("flight_status", None)
        if not flight_status:
            print("No flight status provided. Trying to get it from sly_data")
            flight_status = sly_data.get("flight_status")
        if not flight_status:
            error = "Error: Please provide flight status for the request."
            print(error)
            return error      
        sly_data["flight_status"] = flight_status

        # assigned runway id is required to fulfill the request.
        assigned_runway_id: str = args.get("assigned_runway_id", None)
        if not assigned_runway_id:
            print("No assigned runway provided. Trying to get it from sly_data")
            assigned_runway_id = sly_data.get("assigned_runway_id")
        if not assigned_runway_id:
            error = "Error: Please provide assigned runway id for the request."
            print(error)
            return error    
        sly_data["assigned_runway_id"] = assigned_runway_id
        
        # assigned runway is required to fulfill the request.
        gate_id: str = args.get("gate_id", None)
        if not gate_id:
            print("No gate id provided. Trying to get it from sly_data")
            gate_id = sly_data.get("gate_id")
        if not gate_id:
            error = "Error: Please provide gate id for the request."
            print(error)
            return error 
        sly_data["gate_id"] = gate_id

        message = f"Flight {flight_number} with airplane type {aircraft_type} with status {flight_status} at runway {assigned_runway_id} has inquired the ground services {ground_services_request_type} at gate {gate_id}"
        print(message)
        print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")
        return message

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)

