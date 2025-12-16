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

##################
# execute_clearance_validation

class execute_clearance_validation(CodedTool):
    """
    CodedTool implementation that calls function for clearance validation.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"
        aircraft_base = "/Users/971244/workspace/neuro-san-studio/coded_tools/aircraft_operation/aircraft_base.csv"
        runway_base = "/Users/971244/workspace/neuro-san-studio/coded_tools/aircraft_operation/runways_base.csv"

        # flight_status = 'pending'

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

# ########
#         aircraft_type         = _from_sly_or_args(sly_data, args, "aircraft_type")
#         clearance_type         = _from_sly_or_args(sly_data, args, "clearance_type")
#         assigned_runway_id               = _from_sly_or_args(sly_data, args, "assigned_runway_id")
#         assigned_runway_length = _from_sly_or_args(sly_data, args, "assigned_runway_length")
# ########

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

            # min_runway_length_for_landing = df1.loc[df1['Aircraft_Model'] == aircraft_type]
            min_runway_length_for_landing = df1[df1['Aircraft_Model'] == aircraft_type]                                                
            # print("---------------------- raw aircraft data for airfraft_type ------------------------")
            # print(min_runway_length_for_landing)        

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

                # sly_data["clearance_landing_valid"] = clearance_landing_valid 

            # return clearance_landing_valid
        
        if ((clearance_type == 'cleared for takeoff') | ('takeoff' in clearance_type)):    

            df1 = pd.read_csv(aircraft_base)
            print("---------------------- raw aircraft data ------------------------")
            print(df1)

            # min_runway_length_for_landing = df1.loc[df1['Aircraft_Model'] == aircraft_type]
            min_runway_length_for_takeoff = df1[df1['Aircraft_Model'] == aircraft_type]                                                
            # print("---------------------- raw aircraft data for airfraft_type ------------------------")
            # print(min_runway_length_for_landing)        

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

                # sly_data["clearance_takeoff_valid"] = clearance_takeoff_valid 

            # return clearance_takeoff_valid

        sly_data["clearance_landing_valid"] = clearance_landing_valid 
        sly_data["clearance_takeoff_valid"] = clearance_takeoff_valid 

        return clearance_landing_valid, clearance_takeoff_valid
        
####

                # "parameters": {
                #     "type": "object", 
                #     "properties": {
                #         "aircraft_type": {
                #             "type": "string", 
                #             "description": "This is the type of the incoming aircraft."
                #         },                
                #         "clearance_type": {
                #             "type": "string", 
                #             "description": "This is the type of clearance given to the aircrfat."
                #         },         
                #         "assigned_runway_id": {
                #             "type": "string", 
                #             "description": "This is the runway assigned to the aircraft movement autorized by the clearance."
                #         },         
                #         "assigned_runway_length": {
                #             "type": "string", 
                #             "description": "This is the length of assigned runway."
                #         },        
                #     }, 
##################
# execute_aircraft_landing

class execute_aircraft_landing(CodedTool):
    """
    CodedTool implementation that calls function for aircraft landing.
    """

    def __init__(self):
        pass

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"
        aircraft_base = "/Users/971244/workspace/neuro-san-studio/coded_tools/aircraft_operation/aircraft_base.csv"
        runway_base = "/Users/971244/workspace/neuro-san-studio/coded_tools/aircraft_operation/runways_base.csv"

        # flight_status = 'pending'

        # # Check aircraft type parameter passed by the agent
        # flight_status: str = args.get("flight_status", None) 
        # aircraft_type: str = args.get("aircraft_type", None)   
        # flight_number: str = args.get("flight_number", None)   
        # traffic_direction: str = args.get("traffic_direction", None) 
        # clearance_type: str = args.get("clearance_type", None)   
        # assigned_runway_id: str = args.get("assigned_runway_id", None)  
        # assigned_runway_length: str = args.get("assigned_runway_length", None)  

        # if flight_status is None: 
        #     flight_status: str = sly_data.get(flight_status, None)

        # if aircraft_type is None: 
        #     aircraft_type: str = sly_data.get(aircraft_type, None)

        # if flight_number is None: 
        #     flight_number: str = sly_data.get(flight_number, None)

        # if traffic_direction is None: 
        #     traffic_direction: str = sly_data.get(traffic_direction, None)

        # if clearance_type is None: 
        #     clearance_type: str = sly_data.get(clearance_type, None)
 
        # if assigned_runway_id is None: 
        #     assigned_runway_id: str = sly_data.get(assigned_runway_id, None)

        # if assigned_runway_length is None: 
        #     assigned_runway_length: str = sly_data.get(assigned_runway_length, None)

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

# #########
#         clearance_type         = _from_sly_or_args(sly_data, args, "clearance_type")
#         flight_status         = _from_sly_or_args(sly_data, args, "flight_status")
#         aircraft_type               = _from_sly_or_args(sly_data, args, "aircraft_type")
#         flight_number = _from_sly_or_args(sly_data, args, "flight_number")
#         traffic_direction         = _from_sly_or_args(sly_data, args, "traffic_direction")
#         assigned_runway_id               = _from_sly_or_args(sly_data, args, "assigned_runway_id")
#         assigned_runway_length = _from_sly_or_args(sly_data, args, "assigned_runway_length")
# #########

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

##################
##################
# # execute_aircraft_takeoff

# class execute_aircraft_takeoff(CodedTool):
#     """
#     CodedTool implementation that calls function for aircraft takeoff.
#     """

#     def __init__(self):
#         pass

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
#         file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"
#         aircraft_base = "/Users/971244/workspace/neuro-san-studio/coded_tools/aircraft_operation/aircraft_base.csv"
#         runway_base = "/Users/971244/workspace/neuro-san-studio/coded_tools/aircraft_operation/runways_base.csv"

#         aircraft_operation_status = 'pending'

#         # Check aircraft type parameter passed by the agent
#         aircraft_type: str = args.get("aircraft_type", None)   
#         flight_number: str = args.get("flight_number", None)   
#         traffic_direction: str = args.get("traffic_direction", None)  
#         clearance_type: str = args.get("clearance_type", None)  
#         assigned_runway_id: str = args.get("assigned_runway_id", None)  
#         assigned_runway_length: str = args.get("assigned_runway_length", None)  

#         if clearance_type == 'cleared for takeoff':    
#             time.sleep(0.5) 
#             aircraft_operation_status = 'aircraft takeoff completed'
#             sly_data["aircraft_operation_status"] = aircraft_operation_status 
#             return aircraft_operation_status

# ##################

# # In airline/airport operations jargon, the status of an aircraft after a movement (landing or takeoff) is usually tracked as part of its “aircraft movement status” or “flight phase/status.”

# # The most common terms are:
# # Arrival / Arrived → after landing (used in flight status boards, ATC logs).
# # Departure / Departed → after takeoff.
# # On-blocks / Off-blocks → more operational terms:
# # On-blocks = aircraft has landed and is parked at the gate/stand (chocks in place).
# # Off-blocks = aircraft has pushed back from the gate (before taxi/takeoff).
# # Aircraft Movement (Landing/Takeoff) → ICAO/airport stats formally call each landing or takeoff an aircraft movement.

# # ✈️ In airline/ground handling systems (turnaround context):
# # After landing → the aircraft is typically set to “On-blocks” (or “Arrived”).
# # After takeoff → the aircraft is set to “Airborne” (or “Departed”).
# # These are the most standard IATA/ICAO terms used in ops logs and turnaround systems.

# # ✅ So, the jargon term you’re looking for is:
# # “On-blocks” (post-landing)
# # “Airborne/Departed” (post-takeoff)

#     # # # async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
#     # # def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
#     # #     """Run invoke asynchronously."""
#     # #     # return await asyncio.to_thread(self.invoke, args, sly_data)
#     # #     return self.invoke(args, sly_data)  

# #####################

# class tracker_aircraft_landing(CodedTool):

#     """
#     Taxiing information.
#     """

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - flight_number: the name of the shop to order from.
#             - aircraft_type: the name of the person to order for.
#             - aircraft_direction: this is the aircraft traffic direction. 
#             - clearance_type: this is the clrearance type. 
#             - assigned_runway_id: this is the assigned runway id. 
#             - assigned_runway_length: this is the assigned runway length. 
#             - flight_status: this is the flight status. 

#         :param sly_data: a dictionary with the following keys:

#         :return:
#             In case of successful execution:
#                 all parameters available.
#             otherwise:
#                 a string error message in the format:
#                 "Error: <error message>"
#         """
#         print(">>>>>>>>>>>>>>>>>>> trackerAPI flight operation agent >>>>>>>>>>>>>>>>>>")
#         # # Client name is required to place an order.
#         # customer_name: str = args.get("customer_name", None)
#         # if not customer_name:
#         #     print("No customer name provided. Trying to get it from sly_data")
#         #     customer_name = sly_data.get("username")
#         # if not customer_name:
#         #     error = "Error: Please provide a valid customer name for the order."
#         #     print(error)
#         #     return error

#         file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"

#         # flight number is needed in particular. 
#         flight_number: str = args.get("flight_number", None)
#         if not flight_number:
#             print("No flight number provided. Trying to get it from sly_data")
#             flight_number = sly_data.get("flight_number")
#         # if not flight_number:
#         #     error = "Error: Please provide a flight number for the request."
#         #     print(error)
#         #     return error
#         sly_data["flight_number"] = flight_number

#         # aircraft type is required to fulfill the request.
#         aircraft_type: str = args.get("aircraft_type", None)
#         if not aircraft_type:
#             print("No aircraft type provided. Trying to get it from sly_data")
#             aircraft_type = sly_data.get("aircraft_type")
#         # if not aircraft_type:
#         #     error = "Error: Please provide an aircraft type for the request."
#         #     print(error)
#         #     return error
#         sly_data["aircraft_type"] = aircraft_type

#         # ground clearance type is required to fulfill the request.
#         aircraft_direction: str = args.get("aircraft_direction", None)
#         if not aircraft_direction:
#             print("No aircraft direction provided. Trying to get it from sly_data")
#             aircraft_direction = sly_data.get("aircraft_direction")
#         # if not traffic_direction:
#         #     error = "Error: Please provide a ground clearance type for the request."
#         #     print(error)
#         #     return error    
#         sly_data["aircraft_direction"] = aircraft_direction

#         # ground clearance status is required to fulfill the request.
#         clearance_type: str = args.get("clearance_type", None)
#         if not clearance_type:
#             print("No clearance type provided. Trying to get it from sly_data")
#             clearance_type = sly_data.get("clearance_type")
#         # if not clearance_type:
#         #     error = "Error: Please provide a ground clearance status for the request."
#         #     print(error)
#             # return error    
#         sly_data["clearance_type"] = clearance_type

#         # flight status is required to fulfill the request.
#         assigned_runway_id: str = args.get("assigned_runway_id", None)
#         if not assigned_runway_id:
#             print("No assigned runway id provided. Trying to get it from sly_data")
#             assigned_runway_id = sly_data.get("assigned_runway_id")
#         # if not assigned_runway_id:
#         #     error = "Error: Please provide flight status for the request."
#         #     print(error)
#         #     return error      
#         sly_data["assigned_runway_id"] = assigned_runway_id

#         # assigned runway is required to fulfill the request.
#         assigned_runway_length: str = args.get("assigned_runway_length", None)
#         if not assigned_runway_length:
#             print("No assigned runway length provided. Trying to get it from sly_data")
#             assigned_runway_length = sly_data.get("assigned_runway_length")
#         # if not assigned_runway_length:
#         #     error = "Error: Please provide assigned runway for the request."
#         #     print(error)
#         #     return error    
#         sly_data["assigned_runway_length"] = assigned_runway_length

#         # assigned runway is required to fulfill the request.
#         flight_status: str = args.get("flight_status", None)
#         if not flight_status:
#             print("No flight status provided. Trying to get it from sly_data")
#             flight_status = sly_data.get("flight_status")
#         # if not assigned_runway_length:
#         #     error = "Error: Please provide assigned runway for the request."
#         #     print(error)
#         #     return error    
#         sly_data["flight_status"] = flight_status

#         message = f"Flight {flight_number} with airplane type {aircraft_type} with flight direction {aircraft_direction} seeking clearance type {clearance_type} has been cleared for {assigned_runway_id} which length is {assigned_runway_length}. The flight status is {flight_status}"
#         print(message)
#         print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#         # Log
#         ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#         line = ts + ": " + message
#         with open(file_path_log, "a", encoding="utf-8") as f:
#             f.write(line + "\n")

#         return message

#     async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         Delegates to the synchronous invoke method because it's quick, non-blocking.
#         """
#         return self.invoke(args, sly_data)
    


# class tracker_aircraft_pilot(CodedTool):

#     """
#     Landing information.
#     """

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - flight_number: the name of the shop to order from.
#             - aircraft_type: the name of the person to order for.
#             - aircraft_direction: this is the aircraft traffic direction. 
#             - clearance_type: this is the clrearance type. 
#             - assigned_runway_id: this is the assigned runway id. 
#             - assigned_runway_length: this is the assigned runway length. 
#             - flight_status: this is the flight status. 

#         :param sly_data: a dictionary with the following keys:

#         :return:
#             In case of successful execution:
#                 all parameters available.
#             otherwise:
#                 a string error message in the format:
#                 "Error: <error message>"
#         """
#         print(">>>>>>>>>>>>>>>>>>> trackerAPI flight operation agent >>>>>>>>>>>>>>>>>>")
#         # # Client name is required to place an order.
#         # customer_name: str = args.get("customer_name", None)
#         # if not customer_name:
#         #     print("No customer name provided. Trying to get it from sly_data")
#         #     customer_name = sly_data.get("username")
#         # if not customer_name:
#         #     error = "Error: Please provide a valid customer name for the order."
#         #     print(error)
#         #     return error

#         file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"

#         # flight number is needed in particular. 
#         flight_number = sly_data.get("flight_number")
#         aircraft_type = sly_data.get("aircraft_type")
#         traffic_direction = sly_data.get("traffic_direction")
#         clearance_type = sly_data.get("clearance_type")
#         assigned_runway_id = sly_data.get("assigned_runway_id")
#         assigned_runway_length = sly_data.get("assigned_runway_length")
#         flight_status = args.get("flight_status") 
#         sly_data["flight_status"] = flight_status

#         message = f"Flight {flight_number} with airplane type {aircraft_type} in flight direction {traffic_direction} with clearance type {clearance_type} has landed on on {assigned_runway_id} which length is {assigned_runway_length}. The new flight status is {flight_status}"
#         print(message)
#         print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#         # Log
#         ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#         line = ts + ": " + message
#         with open(file_path_log, "a", encoding="utf-8") as f:
#             f.write(line + "\n")

#         landing_summary = message

#         return landing_summary

#     async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         Delegates to the synchronous invoke method because it's quick, non-blocking.
#         """
#         return self.invoke(args, sly_data)

# ######
# class report_aircraft_landing(CodedTool):

#     """
#     Landing information.
#     """

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - flight_number: this is the flight number.
#             - aircraft_type: this is the aircraft type.
#             - traffic_direction: this is the traffic direction.
#             - flight_status: this is the flight status. 
#             - clearance_type: this is the air clearance type requested for landing or for takeoff. 
#             - assigned_runway_id: this is the id of the runway assigned for landing or for takeoff. 
#             - assigned_runway_length: this is the length of the runway assigned for landing or for takeoff. 

#         :param sly_data: a dictionary with the following keys:

#         :return:
#             In case of successful execution:
#                 all parameters available.
#             otherwise:
#                 a string error message in the format:
#                 "Error: <error message>"
#         """
#         print(">>>>>>>>>>>>>>>>>>> trackerAPI flight operation agent >>>>>>>>>>>>>>>>>>")
#         # # Client name is required to place an order.
#         # customer_name: str = args.get("customer_name", None)
#         # if not customer_name:
#         #     print("No customer name provided. Trying to get it from sly_data")
#         #     customer_name = sly_data.get("username")
#         # if not customer_name:
#         #     error = "Error: Please provide a valid customer name for the order."
#         #     print(error)
#         #     return error

#         file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"

#         # read sly data for consolidated report
#         # flight_number = sly_data.get("flight_number")
#         # aircraft_type = sly_data.get("aircraft_type")
#         # traffic_direction = sly_data.get("traffic_direction")
#         # flight_status = sly_data.get("flight_status")
#         # clearance_type = sly_data.get("clearance_type")
#         # assigned_runway_id = sly_data.get("assigned_runway_id")
#         # assigned_runway_length = sly_data.get("assigned_runway_length")

#         flight_number: str = sly_data.get("flight_number", None)   
#         aircraft_type: str = sly_data.get("aircraft_type", None)   
#         traffic_direction: str = sly_data.get("traffic_direction", None) 
#         flight_status: str = sly_data.get("flight_status", None)   
#         clearance_type: str = sly_data.get("clearance_type", None)   
#         assigned_runway_id: str = sly_data.get("assigned_runway_id", None)  
#         assigned_runway_length: str = sly_data.get("assigned_runway_length", None)  

#         landing_summary = {
#             "flight_number": flight_number,
#             "aircraft_type": aircraft_type,
#             "traffic_direction": traffic_direction,
#             "flight_status": flight_status,
#             "clearance_type": clearance_type,
#             "assigned_runway_id": assigned_runway_id,
#             "assigned_runway_length": assigned_runway_length
#         }

#         message = f"landing completed with summary {landing_summary}"
#         print(message)
#         print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#         # Log
#         ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#         line = ts + ": " + message

#         with open(file_path_log, "a", encoding="utf-8") as f:
#             f.write(line + "\n")

#         return landing_summary

#     async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         Delegates to the synchronous invoke method because it's quick, non-blocking.
#         """
#         return self.invoke(args, sly_data)

# ######
# class clearance_status_check(CodedTool):

#     """
#     Taxiing information.
#     """

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - flight_number: the name of the shop to order from.
#             - aircraft_type: the name of the person to order for.
#             - traffic_direction: this is the direction of the aircraft as incoming or departing. 
#             - clearance_type: this is the air clearance type requested for landing or for takeoff. 
#             - assigned_runway_id: this is the id of the runway assigned for landing or for takeoff. 
#             - assigned_runway_length: this is the length of the runway assigned for landing or for takeoff. 

#         :param sly_data: a dictionary with the following keys:

#         :return:
#             In case of successful execution:
#                 all parameters available.
#             otherwise:
#                 a string error message in the format:
#                 "Error: <error message>"
#         """
#         print(">>>>>>>>>>>>>>>>>>> trackerAPI flight operation agent >>>>>>>>>>>>>>>>>>")
#         # # Client name is required to place an order.
#         # customer_name: str = args.get("customer_name", None)
#         # if not customer_name:
#         #     print("No customer name provided. Trying to get it from sly_data")
#         #     customer_name = sly_data.get("username")
#         # if not customer_name:
#         #     error = "Error: Please provide a valid customer name for the order."
#         #     print(error)
#         #     return error

#         file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"

#         # flight number is needed in particular. 
#         flight_number: str = sly_data.get("flight_number", None)
#         if not flight_number:
#             print("No flight number provided. Trying to get it from sly_data")
#             flight_number = args.get("flight_number")
#             sly_data["flight_number"] = flight_number
#         # if not flight_number:
#         #     error = "Error: Please provide a flight number for the request."
#         #     print(error)
#         #     return error
        

#         # aircraft type is required to fulfill the request.
#         aircraft_type: str = sly_data.get("aircraft_type", None)
#         if not aircraft_type:
#             print("No aircraft type provided. Trying to get it from sly_data")
#             aircraft_type = args.get("aircraft_type")
#             sly_data["aircraft_type"] = aircraft_type
#         # if not aircraft_type:
#         #     error = "Error: Please provide an aircraft type for the request."
#         #     print(error)
#         #     return error

#         # ground clearance type is required to fulfill the request.
#         clearance_type: str = sly_data.get("clearance_type", None)
#         if not clearance_type:
#             print("No ground clearance status provided. Trying to get it from sly_data")
#             clearance_type = args.get("clearance_type")
#             sly_data["clearance_type"] = clearance_type
#         # if not clearance_type:
#         #     error = "Error: Please provide a ground clearance status for the request."
#         #     print(error)
#         #     return error    

#         # assigned runway id is required to fulfill the request.
#         assigned_runway_id: str = sly_data.get("assigned_runway_id", None)
#         if not assigned_runway_id:
#             print("No flight status provided. Trying to get it from sly_data")
#             assigned_runway_id = args.get("assigned_runway_id")
#             sly_data["assigned_runway_id"] = assigned_runway_id
#         # if not assigned_runway_id:
#         #     error = "Error: Please provide flight status for the request."
#         #     print(error)
#         #     return error      
        
#         # assigned runway length is required to fulfill the request.
#         assigned_runway_length: str = sly_data.get("assigned_runway_length", None)
#         if not assigned_runway_length:
#             print("No assigned runway provided. Trying to get it from sly_data")
#             assigned_runway_length = args.get("assigned_runway_length")
#             sly_data["assigned_runway_length"] = assigned_runway_length
#         # if not assigned_runway_length:
#         #     error = "Error: Please provide assigned runway for the request."
#         #     print(error)
#         #     return error    
        
#         if ((clearance_type is not None) & ((('landing' in clearance_type) | ('Landing' in clearance_type) | ('LANDING' in clearance_type)) | (('clear' in clearance_type) | ('Clear' in clearance_type) | ('CLEAR' in clearance_type)))): 
#             message = f"Flight {flight_number} with airplane type {aircraft_type} has received clearance {clearance_type} type to runway {assigned_runway_id} which has a length of {assigned_runway_length}"
#             print(message)
#             print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#             # Log
#             ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#             line = ts + ": " + message

#             with open(file_path_log, "a", encoding="utf-8") as f:
#                 f.write(line + "\n")

#         else: 
#             message = f"Flight {flight_number} with airplane type {aircraft_type} has not received clearance for landing"
#             print(message)
#             print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#             # Log
#             ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#             line = ts + ": " + message

#             with open(file_path_log, "a", encoding="utf-8") as f:
#                 f.write(line + "\n")
#         return message

#     async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         Delegates to the synchronous invoke method because it's quick, non-blocking.
#         """
#         return self.invoke(args, sly_data)
    
# ######


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

        file_path_log = "/Users/971244/demospace/neuro-san-studio/test_debug/airlineturnaround.txt"

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
                sly_data["flight_number"] = flight_number
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
                sly_data["aircraft_type"] = aircraft_type
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
                sly_data["flight_status"] = flight_status
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
                sly_data["gate_id"] = gate_id
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
                sly_data["acu_connection_status"] = acu_connection_status
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
                sly_data["gpu_connection_status"] = gpu_connection_status
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
                sly_data["wheels_chocks_installation_status"] = wheels_chocks_installation_status
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
                sly_data["engines_stop_status"] = engines_stop_status
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
                sly_data["jetbridge_connection_status"] = jetbridge_connection_status
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
                sly_data["door_opening_status"] = door_opening_status
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
        print("\n")
        print("\n")
        print("####### wheels_chocks_readiness_status read from args: #######", wheels_chocks_readiness_status)
        print("\n")
        print("\n")
        if not wheels_chocks_readiness_status:
            print("wheels_chocks_readiness_status has not been provided in user inquiry. Trying to get it from sly_data")
            wheels_chocks_readiness_status = sly_data.get("wheels_chocks_readiness_status")
            if wheels_chocks_readiness_status: 
                sly_data["wheels_chocks_readiness_status"] = wheels_chocks_readiness_status
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
                sly_data["aircraft_direction"] = aircraft_direction
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
                sly_data["assigned_runway_id"] = assigned_runway_id
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
                sly_data["assigned_runway_length"] = assigned_runway_length
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
                sly_data["traffic_direction"] = traffic_direction
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
                sly_data["clearance_type"] = clearance_type
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

        # This return list will be trimmed to contain only parameters relevant to the agentic system where this generic coded tool is used. 
        # return flight_status,flight_number,aircraft_type,gate_id,acu_connection_status,gpu_connection_status,wheels_chocks_installation_status,engines_stop_status,jetbridge_connection_status,door_opening_status, ground_services_request_type, wheels_chocks_readiness_status
        # return flight_status, clearance_type, assigned_runway_id, assigned_runway_length

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)

#########################################################    