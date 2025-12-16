from typing import Any, Dict, Union
from datetime import datetime
import time
from neuro_san.interfaces.coded_tool import CodedTool

# ---------- helpers ----------

def _from_args_or_sly(args: Dict[str, Any], sly: Dict[str, Any], key: str) -> Any:
    """Prefer args[key]; fallback to sly_data[key]."""
    v = args.get(key)
    return v if v is not None else sly.get(key)

def _from_sly_or_args(sly: Dict[str, Any], args: Dict[str, Any], key: str) -> Any:
    """Prefer args[key]; fallback to sly_data[key]."""
    v = sly.get(key)
    return v if v is not None else args.get(key)

def _norm(s: Union[str, None]) -> str:
    """Lowercase+strip (safe for None)."""
    return (s or "").strip().lower()

# def build_tracker_status(
#     flight_number: str,
#     flight_status: str,
#     aircraft_type: str,
#     ground_clearance_type: str,
#     assigned_runway: str,
#     gate_id: str,
# ) -> ClearanceDict:

#     return {
#         "flight_status": flight_status.strip().upper(),
#         "flight_number": flight_number.strip().upper(),
#         "aircraft_type": aircraft_type.strip().upper(),
#         "ground_clearance_type": ground_clearance_type,
#         "assigned_runway": assigned_runway,
#         "gate_id": gate_id,
#     }
# ---------- tool ----------

class baggage_unload_operator(CodedTool):
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
            - jetbridge_connection_status
            - door_opening_status
        :return: None in write mode or any of the parameters in read mode
        """


        file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"
        baggage_unload_status = 'pending'

        print("\n")
        print("\n")
        print(" #################### BAGGAGE UNLOAD OPERATOR #################### ")
        print("\n")
        print("\n")
        
        # # flight number is needed in particular. 
        # flight_number: str = sly_data.get("flight_number", None)
        # if not flight_number:
        #     print("No flight number provided. Trying to get it from sly_data")
        #     flight_number = args.get("flight_number")
        #     sly_data["flight_number"] = flight_number
        # if not flight_number:
        #     error = "Error: Please provide a flight number for the request."
        #     print(error)
        #     return error       

        # # aircraft type is required to fulfill the request.
        # aircraft_type: str = sly_data.get("aircraft_type", None)
        # if not aircraft_type:
        #     print("No aircraft type provided. Trying to get it from sly_data")
        #     aircraft_type = args.get("aircraft_type")
        #     sly_data["aircraft_type"] = aircraft_type
        # if not aircraft_type:
        #     error = "Error: Please provide an aircraft type for the request."
        #     print(error)
        #     return error  

        # # flight status is required to fulfill the request.
        # flight_status: str = sly_data.get("flight_status", None)
        # if not flight_status:
        #     print("No flight status provided. Trying to get it from sly_data")
        #     flight_status = args.get("flight_status")
        #     sly_data["flight_status"] = flight_status
        # if not flight_status:
        #     error = "Error: Please provide a flight status for the request."
        #     print(error)
        #     return error  
        
        # # flight status is required to fulfill the request.
        # gate_id: str = sly_data.get("gate_id", None)
        # if not flight_status:
        #     print("No gate id provided. Trying to get it from sly_data")
        #     gate_id = args.get("gate_id")
        #     sly_data["gate_id"] = gate_id
        # if not gate_id:
        #     error = "Error: Please provide a gate id for the request."
        #     print(error)
        #     return error  

        print("\n")
        print("\n")
        print(" #################### BAGGAGE UNLOAD OPERATOR - PARAMETERS #################### ")
        print("\n")
        print("\n")

        # flight number is needed in particular. 
        flight_number: str = args.get("flight_number", None)
        if not flight_number:
            print("No flight number provided. Trying to get it from sly_data")
            flight_number = sly_data.get("flight_number")
            # sly_data["flight_number"] = flight_number
        if not flight_number:
            error = "Error: Please provide a flight number for the request."
            print(error)
            return error       

        # aircraft type is required to fulfill the request.
        aircraft_type: str = args.get("aircraft_type", None)
        if not aircraft_type:
            print("No aircraft type provided. Trying to get it from sly_data")
            aircraft_type = sly_data.get("aircraft_type")
            # sly_data["aircraft_type"] = aircraft_type
        if not aircraft_type:
            error = "Error: Please provide an aircraft type for the request."
            print(error)
            return error  

        # flight status is required to fulfill the request.
        flight_status: str = args.get("flight_status", None)
        if not flight_status:
            print("No flight status provided. Trying to get it from sly_data")
            flight_status = sly_data.get("flight_status")
            # sly_data["flight_status"] = flight_status
        if not flight_status:
            error = "Error: Please provide a flight status for the request."
            print(error)
            return error  
        
        # gate id is required to fulfill the request.
        gate_id: str = args.get("gate_id", None)
        if not flight_status:
            print("No gate id provided. Trying to get it from sly_data")
            gate_id = sly_data.get("gate_id")
            # sly_data["gate_id"] = gate_id
        if not gate_id:
            error = "Error: Please provide a gate id for the request."
            print(error)
            return error  

        # # wheels chocks installation status is required to fulfill the request.
        # wheels_chocks_installation_status: str = args.get("wheels_chocks_installation_status", None)
        # if not wheels_chocks_installation_status:
        #     print("No wheels chocks installation status provided. Trying to get it from sly_data")
        #     wheels_chocks_installation_status = sly_data.get("wheels_chocks_installation_status")
        #     # sly_data["wheels_chocks_installation_status"] = wheels_chocks_installation_status
        # if not wheels_chocks_installation_status:
        #     error = "Error: Please provide wheels chocks installation status for the request."
        #     print(error)
        #     return error  

        # jetbridge connection status is required to fulfill the request.
        jetbridge_connection_status: str = args.get("jetbridge_connection_status", None)
        if not jetbridge_connection_status:
            print("No jetbridge_connection_status provided. Trying to get it from sly_data")
            jetbridge_connection_status = sly_data.get("jetbridge_connection_status")
            # sly_data["jetbridge_connection_status"] = jetbridge_connection_status
        if not jetbridge_connection_status:
            error = "Error: Please provide jetbridge connection status for the request."
            print(error)
            return error  

        # door opening status is required to fulfill the request.
        door_opening_status: str = args.get("door_opening_status", None)
        if not door_opening_status:
            print("No door opening status provided. Trying to get it from sly_data")
            door_opening_status = sly_data.get("door_opening_status")
            # sly_data["door_opening_status"] = door_opening_status
        if not door_opening_status:
            error = "Error: Please provide door opening status for the request."
            print(error)
            return error  

        print("\n")
        print("\n")
        print(" #################### BAGGAGE UNLOAD OPERATOR - JERTBRIDGE CONNECT STATUS UPDATE - DOOR OPENING STATUS #################### ")
        print("\n")
        print("\n")
        print('jetbridge_connection_status is: ', jetbridge_connection_status)
        print("\n")
        print("\n")
        print('door_opening_status is: ', door_opening_status)
        print("\n")
        print("\n")

        if jetbridge_connection_status == 'connected' and door_opening_status == 'open':
            baggage_unload_status = 'completed'
            message = f"Flight {flight_number} with airplane type {aircraft_type} {flight_status} at gate {gate_id} has jetbridge {jetbridge_connection_status} and aircraft door {door_opening_status}.  installed. Its baggage unload status is status is {baggage_unload_status}."
            print(message)
            print("\n")
            print("\n")
            print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

            timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line = timenow + ": " + message
            with open(file_path_log, mode="a", encoding="utf-8") as f:  
                f.write(line + "\n")   

            sly_data["baggage_unload_status"] = baggage_unload_status

        # return message
        return baggage_unload_status

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)


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
            - passenger_disembarkation_status

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

        # This return list will be trimmed to contain only parameters relevant to the agentic system where this generic coded tool is used. 
        # return flight_status,flight_number,aircraft_type,gate_id,acu_connection_status,gpu_connection_status,wheels_chocks_installation_status,engines_stop_status,jetbridge_connection_status,door_opening_status, ground_services_request_type, wheels_chocks_readiness_status
        return jetbridge_connection_status, door_opening_status

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)

#########################################################

# class trackerAPI(CodedTool):

#     """
#     Taxiing information.
#     """

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - flight_number: the name of the shop to order from.
#             - aircraft_type: the name of the person to order for.
#             - ground_clearance_type: the details of the order.
#             - ground_clearance_status: the details of the order.
#             - flight_status: the details of the order.
#             - assigned_runway: the details of the order.
#             - gate_id: the details of the order.
#             - gpu_readiness_status: readines status of ground poer unit at the gate. 
#             - chocks_readiness_status: readiness of wheels chocks unit at the gate.  

#         :param sly_data: a dictionary with the following keys:
#             - username: optional - the name of the person to order for, if already known.

#         :return:
#             In case of successful execution:
#                 all parameters available.
#             otherwise:
#                 a string error message in the format:
#                 "Error: <error message>"
#         """
#         print(">>>>>>>>>>>>>>>>>>> trackerAPI aircraft taxiing >>>>>>>>>>>>>>>>>>")
#         print("\n")
#         print("\n")
#         # # Client name is required to place an order.
#         # customer_name: str = sly_data.get("customer_name", None)
#         # if not customer_name:
#         #     print("No customer name provided. Trying to get it from sly_data")
#         #     customer_name = args.get("username")
#         # if not customer_name:
#         #     error = "Error: Please provide a valid customer name for the order."
#         #     print(error)
#         #     return error


#         file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"

#         # flight number is required to fulfill the request.
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
#         ground_clearance_type: str = sly_data.get("ground_clearance_type", None)
#         if not ground_clearance_type:
#             print("No ground clearance type provided. Trying to get it from sly_data")
#             ground_clearance_type = args.get("ground_clearance_type")
#             sly_data["ground_clearance_type"] = ground_clearance_type
#         # if not ground_clearance_type:
#         #     error = "Error: Please provide a ground clearance type for the request."
#         #     print(error)
#         #     return error    
        

#         # ground clearance status is required to fulfill the request.
#         ground_clearance_status: str = sly_data.get("ground_clearance_status", None)
#         if not ground_clearance_status:
#             print("No ground clearance status provided. Trying to get it from sly_data")
#             ground_clearance_status = args.get("ground_clearance_status")
#             sly_data["ground_clearance_status"] = ground_clearance_status
#         # if not ground_clearance_status:
#         #     error = "Error: Please provide a ground clearance status for the request."
#         #     print(error)
#         #     return error    
        

#         # flight status is required to fulfill the request.
#         flight_status: str = sly_data.get("flight_status", None)
#         if not flight_status:
#             print("No flight status provided. Trying to get it from sly_data")
#             flight_status = args.get("flight_status")
#             sly_data["flight_status"] = flight_status
#         # if not flight_status:
#         #     error = "Error: Please provide flight status for the request."
#         #     print(error)
#         #     return error      
        
        
#         # assigned runway is required to fulfill the request.
#         assigned_runway_id: str = sly_data.get("assigned_runway_id", None)
#         if not assigned_runway_id:
#             print("No assigned runway id provided. Trying to get it from sly_data")
#             assigned_runway_id = args.get("assigned_runway_id")
#             sly_data["assigned_runway_id"] = assigned_runway_id
#         # if not assigned_runway_id:
#         #     error = "Error: Please provide assigned runway id for the request."
#         #     print(error)
#         #     return error    
        
        
#         # assigned runway is required to fulfill the request.
#         gate_id: str = sly_data.get("gate_id", None)
#         if not gate_id:
#             print("No gate id provided. Trying to get it from sly_data")
#             gate_id = args.get("gate_id")
#             sly_data["gate_id"] = gate_id
#         # if not gate_id:
#         #     error = "Error: Please provide gate id for the request."
#         #     print(error)
#         #     return error 
        

#         # gpu readiness at the gate is required to fulfill the request.
#         gpu_readiness_status: str = sly_data.get("gpu_readiness_status", None)
#         if not gpu_readiness_status:
#             print("No gate id provided. Trying to get it from sly_data")
#             gpu_readiness_status = args.get("gpu_readiness_status")
#             sly_data["gpu_readiness_status"] = gpu_readiness_status
#         # if not gpu_readiness_status:
#         #     error = "Error: Please provide gate id for the request."
#         #     print(error)
#         #     return error 
        

#         # wheels chocks readiness at the gate is required to fulfill the request.
#         chocks_readiness_status: str = sly_data.get("chocks_readiness_status", None)
#         if not chocks_readiness_status:
#             print("No gate id provided. Trying to get it from sly_data")
#             chocks_readiness_status = args.get("chocks_readiness_status")
#             sly_data["chocks_readiness_status"] = chocks_readiness_status
#         # if not chocks_readiness_status:
#         #     error = "Error: Please provide gate id for the request."
#         #     print(error)
#         #     return error 
        

#         message = f"Flight {flight_number} with airplane type {aircraft_type} with status {flight_status} at runway {assigned_runway_id} has {ground_clearance_type} type clearance to gate {gate_id} with status {ground_clearance_status}"
#         print(message)
#         print("\n")
#         print("\n")
#         print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#         timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#         line = timenow + ": " + message
#         with open(file_path_log, mode="a", encoding="utf-8") as f:  
#             f.write(line + "\n")   

#         return message

#     async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         Delegates to the synchronous invoke method because it's quick, non-blocking.
#         """
#         return self.invoke(args, sly_data)


# # execute_summary

# class ExecuteSummary(CodedTool):

#     """
#     Taxiing summary information.
#     """

#     """
#     Taxiing information.
#     """

#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - flight_number: the name of the shop to order from.
#             - aircraft_type: the name of the person to order for.
#             - ground_clearance_type: the details of the order.
#             - ground_clearance_status: the details of the order.
#             - flight_status: the details of the order.
#             - assigned_runway: the details of the order.
#             - gate_id: the details of the order.
#             - gpu_readiness_status: readines status of ground poer unit at the gate. 
#             - chocks_readiness_status: readiness of wheels chocks unit at the gate.  

#         :param sly_data: a dictionary with the following keys:
#             - username: optional - the name of the person to order for, if already known.

#         :return:
#             In case of successful execution:
#                 all parameters available.
#             otherwise:
#                 a string error message in the format:
#                 "Error: <error message>"
#         """

#         flight_number = sly_data.get("flight_number")
#         aircraft_type = sly_data.get("aircraft_type")
#         ground_clearance_type = sly_data.get("ground_clearance_type")
#         ground_clearance_status = sly_data.get("ground_clearance_status")
#         flight_status = sly_data.get("flight_status")
#         assigned_runway_id = sly_data.get("assigned_runway_id")
#         gate_id = sly_data.get("gate_id")
#         gpu_readiness_status = sly_data.get("gpu_readiness_status")
#         chocks_readiness_status = sly_data.get("chocks_readiness_status")

#         taxi_summary = {
#             "flight_number": flight_number,
#             "aircraft_type": aircraft_type,
#             "ground_clearance_type": ground_clearance_type,
#             "ground_clearance_status": ground_clearance_status,
#             "flight_status": flight_status,
#             "assigned_runway_id": assigned_runway_id,
#             "gate_id": gate_id,
#             "gpu_readiness_status": gpu_readiness_status,
#             "chocks_readiness_status": chocks_readiness_status,
#         }

#         sly_data["taxi_summary"] = taxi_summary

#         # sly_data["taxi_summary"] = taxi_summary
#         return taxi_summary

#     # async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#     #     """
#     #     Delegates to the synchronous invoke method because it's quick, non-blocking.
#     #     """
#     #     return self.invoke(args, sly_data)

# ######
# class ground_clearance_status_check(CodedTool):

#     """
#     Taxiing information.
#     """
#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - flight_number: the name of the shop to order from.
#             - aircraft_type: the name of the person to order for.
#             - flight_status: this is the flight status. 
#             - ground_clearance_type: this is the ground clearance type requested for taxi. 
#             - ground_clearance_status: this is the status of the ground clearance type requested for taxi. 
#             - assigned_runway_id: this is the id of the runway assigned for landing or for takeoff. 
#             - gate_id: this is the gate id. 

#         :param sly_data: a dictionary with the following keys:

#         :return:
#             In case of successful execution:
#                 all parameters available.
#             otherwise:
#                 a string error message in the format:
#                 "Error: <error message>"
#         """
#         print(">>>>>>>>>>>>>>>>>>> Ground clearance status check >>>>>>>>>>>>>>>>>>")
#         print("\n")
#         print("\n")
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
#         ground_clearance_type: str = sly_data.get("clearance_type", None)
#         if not ground_clearance_type:
#             print("No ground clearance type provided. Trying to get it from sly_data")
#             ground_clearance_type = args.get("ground_clearance_type")
#             sly_data["ground_clearance_type"] = ground_clearance_type
#         # if not clearance_type:
#         #     error = "Error: Please provide a ground clearance status for the request."
#         #     print(error)
#         #     return error    

#         # groundn clearance status is required to fulfill the request.
#         ground_clearance_status: str = sly_data.get("ground_clearance_status", None)
#         if not ground_clearance_status:
#             print("No ground clearance status provided. Trying to get it from sly_data")
#             ground_clearance_status = args.get("ground_clearance_status")
#             sly_data["ground_clearance_status"] = ground_clearance_status
#         # if not clearance_type:
#         #     error = "Error: Please provide a ground clearance status for the request."
#         #     print(error)
#         #     return error    

#         # flight status is required to fulfill the request.
#         flight_status: str = sly_data.get("flight_status", None)
#         if not flight_status:
#             print("No flight status provided. Trying to get it from sly_data")
#             flight_status = args.get("flight_status")
#             sly_data["flight_status"] = flight_status
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
#         gate_id: str = sly_data.get("gate_id", None)
#         if not gate_id:
#             print("No gate id provided. Trying to get it from sly_data")
#             gate_id = args.get("gate_id")
#             sly_data["gate_id"] = gate_id
#         # if not assigned_runway_length:
#         #     error = "Error: Please provide assigned runway for the request."
#         #     print(error)
#         #     return error    
        
#         if ((ground_clearance_status is not None) & ((('taxi' in ground_clearance_status) | ('Taxi' in ground_clearance_status) | ('TAXI' in ground_clearance_status)) | (('clear' in ground_clearance_status) | ('Clear' in ground_clearance_status) | ('CLEAR' in ground_clearance_status)))): 
#             message = f"Flight {flight_number} with airplane type {aircraft_type} that needs {ground_clearance_type} type clearance from runway {assigned_runway_id} to gate {gate_id} has received cleareance to taxi in."
#             print(message)
#             print("\n")
#             print("\n")
#             print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#             # Log
#             ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#             line = ts + ": " + message

#             with open(file_path_log, "a", encoding="utf-8") as f:
#                 f.write(line + "\n")

#         else: 
#             # message = f"Flight {flight_number} with airplane type {aircraft_type} has not received ground clearance for taxi"
#             # message = f"Flight {flight_number} with airplane type {aircraft_type} that needs ground clearance {ground_clearance_type} type from runway {assigned_runway_id} to gate {gate_id} has NOT received cleareance {ground_clearance_status} to taxi in."
#             message = f"Flight {flight_number} with airplane type {aircraft_type} that needs {ground_clearance_type} type clearancd from runway {assigned_runway_id} to gate {gate_id} has NOT received cleareance to taxi in."
#             print(message)
#             print("\n")
#             print("\n")
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
#             #         "required": ["flight_number", "aircraft_type","flight_status","gate_id"] 
#             #     }
#             # },
#             # "class": "aircraft_landing.ground_services_readiness_check" 

#                         # "wheels_chocks_readiness_status": {
#                         #     "type": "string", 
#                         #     "description": "This is the wheels chocks readiness status."
#                         # },   
#                         # "gpu_readiness_status": {
#                         #     "type": "string", 
#                         #     "description": "This is the gpu readiness status."
#                         # },      
# ######
# class ground_services_readiness_check(CodedTool):

#     """
#     Taxiing information.
#     """
#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - flight_number: this is the flight number. 
#             - aircraft_type: this is the aircraft type. 
#             - flight_status: this is the flight status. 
#             - gpu_readiness_status: the gpu readiness status.
#             - wheels_chocks_readiness_status: the wheels chocks readiness status.
#             - gate_id: this is the gate id. 

#         :param sly_data: a dictionary with the following keys:

#         :return:
#             In case of successful execution:
#                 all parameters available.
#             otherwise:
#                 a string error message in the format:
#                 "Error: <error message>"
#         """
#         print(">>>>>>>>>>>>>>>>>>> Ground services readiness check >>>>>>>>>>>>>>>>>>")
#         print("\n")
#         print("\n")
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

#         # flight status is required to fulfill the request.
#         flight_status: str = sly_data.get("flight_status", None)
#         if not flight_status:
#             print("No flight status provided. Trying to get it from sly_data")
#             flight_status = args.get("flight_status")
#             sly_data["flight_status"] = flight_status
#         # if not clearance_type:
#         #     error = "Error: Please provide a ground clearance status for the request."
#         #     print(error)
#         #     return error  

#         # assigned runway length is required to fulfill the request.
#         gate_id: str = sly_data.get("gate_id", None)
#         if not gate_id:
#             print("No gate id provided. Trying to get it from sly_data")
#             gate_id = args.get("gate_id")
#             sly_data["gate_id"] = gate_id
#         # if not assigned_runway_length:
#         #     error = "Error: Please provide assigned runway for the request."
#         #     print(error)
#         #     return error   

#         # wheels chocks readiness status is required to fulfill the request.
#         wheels_chocks_readiness_status: str = sly_data.get("wheels_chocks_readiness_status", None)
#         if not wheels_chocks_readiness_status:
#             print("No wheels chocks readiness status provided. Trying to get it from sly_data")
#             wheels_chocks_readiness_status = args.get("wheels_chocks_readiness_status")
#             sly_data["wheels_chocks_readiness_status"] = wheels_chocks_readiness_status
#         # if not wheels_chocks_readiness_status:
#         #     error = "Error: Please provide wheels chocks readiness status for the request."
#         #     print(error)
#         #     return error    

#         # gpu readiness status is required to fulfill the request.
#         gpu_readiness_status: str = sly_data.get("gpu_readiness_status", None)
#         if not gpu_readiness_status:
#             print("No gpu readiness status provided. Trying to get it from sly_data")
#             gpu_readiness_status = args.get("gpu_readiness_status")
#             sly_data["gpu_readiness_status"] = gpu_readiness_status
#         # if not gpu_readiness_status:
#         #     error = "Error: Please provide gpu readiness status for the request."
#         #     print(error)
#         #     return error     

#         # ground services readiness status is required to fulfill the request.
#         ground_services_readiness_status: str = sly_data.get("gpu_readiness_status", None)
#         if not ground_services_readiness_status:
#             print("No ground services readiness status provided. Trying to get it from sly_data")
#             ground_services_readiness_status = args.get("ground_services_readiness_status")
#             sly_data["ground_services_readiness_status"] = ground_services_readiness_status
#         # if not gpu_readiness_status:
#         #     error = "Error: Please provide ground services readiness status for the request."
#         #     print(error)
#         #     return error    

#         if (('ready' in ground_services_readiness_status) | ('Ready' in ground_services_readiness_status) | ('READY' in ground_services_readiness_status) | ('complete' in ground_services_readiness_status) | ('Complete' in ground_services_readiness_status) | ('confirmed' in ground_services_readiness_status) | ('Confirmed' in ground_services_readiness_status)): 
#             message = f"Ground services for {flight_number} with airplane type {aircraft_type} at gate {gate_id} are ready"
#             print(message)
#             print("\n")
#             print("\n")
#             print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#             sly_data["ground_services_readiness_status"] = ground_services_readiness_status

#             # Log
#             ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#             line = ts + ": " + message

#             with open(file_path_log, "a", encoding="utf-8") as f:
#                 f.write(line + "\n")            

#         if ((gpu_readiness_status is not None) & (wheels_chocks_readiness_status is not None)): 
#             gpu_readiness_status = gpu_readiness_status.lower()
#             wheels_chocks_readiness_status = wheels_chocks_readiness_status.lower()        
#             if ((('ready' in gpu_readiness_status) | ('yes' in gpu_readiness_status) | ('complete' in gpu_readiness_status)) & (('ready' in wheels_chocks_readiness_status) | ('yes' in wheels_chocks_readiness_status) | ('complete' in wheels_chocks_readiness_status))): 
#                 message = f"Ground services for {flight_number} with airplane type {aircraft_type} at gate {gate_id} are ready"
#                 print(message)
#                 print("\n")
#                 print("\n")
#                 print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#                 sly_data["ground_services_readiness_status"] = ground_services_readiness_status

#                 # Log
#                 ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#                 line = ts + ": " + message

#                 with open(file_path_log, "a", encoding="utf-8") as f:
#                     f.write(line + "\n")
#         else: 
#             message = f"Ground services for {flight_number} with airplane type {aircraft_type} at gate {gate_id} are NOT ready"
#             print(message)
#             print("\n")
#             print("\n")
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

# class aircraft_taxi_report(CodedTool):

#     """
#     Taxiing information.
#     """
#     def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         :param args: a dictionary with the following keys:
#             - flight_number: this is the flight number. 
#             - aircraft_type: this is the aircraft type. 
#             - flight_status: this is the flight status. 
#             - gate_id: this is the gate id. 
#             - ground_clearance_type: this is the ground clearance type. 
#             - ground_clearance_status: this is the ground clearance status. 
#             - gpu_readiness_status: the gpu readiness status.
#             - wheels_chocks_readiness_status: the wheels chocks readiness status.

#         :param sly_data: a dictionary with the following keys:

#         :return:
#             In case of successful execution:
#                 all parameters available.
#             otherwise:
#                 a string error message in the format:
#                 "Error: <error message>"
#         """
#         print(">>>>>>>>>>>>>>>>>>> Ground services readiness check >>>>>>>>>>>>>>>>>>")
#         print("\n")
#         print("\n")
#         file_path_log = "/Users/971244/workspace/neuro-san-studio/test_debug/airlineturnaround.txt"

#         # flight number is needed in particular. 
#         flight_number: str = sly_data.get("flight_number", None)
#         # if not flight_number:
#         #     print("No flight number provided. Trying to get it from sly_data")
#         #     flight_number = args.get("flight_number")
#         #     sly_data["flight_number"] = flight_number

#         # if not flight_number:
#         #     error = "Error: Please provide a flight number for the request."
#         #     print(error)
#         #     return error

#         # aircraft type is required to fulfill the request.
#         aircraft_type: str = sly_data.get("aircraft_type", None)
#         # if not aircraft_type:
#         #     print("No aircraft type provided. Trying to get it from sly_data")
#         #     aircraft_type = args.get("aircraft_type")
#         #     sly_data["aircraft_type"] = aircraft_type

#         # if not aircraft_type:
#         #     error = "Error: Please provide an aircraft type for the request."
#         #     print(error)
#         #     return error

#         # flight status is required to fulfill the request.
#         flight_status: str = sly_data.get("flight_status", None)
#         # if not flight_status:
#         #     print("No flight status provided. Trying to get it from sly_data")
#         #     flight_status = args.get("flight_status")
#         #     sly_data["flight_status"] = flight_status 

#         # if not clearance_type:
#         #     error = "Error: Please provide a ground clearance status for the request."
#         #     print(error)
#         #     return error  

#         # assigned runway length is required to fulfill the request.
#         gate_id: str = sly_data.get("gate_id", None)
#         # if not gate_id:
#         #     print("No gate id provided. Trying to get it from sly_data")
#         #     gate_id = args.get("gate_id")
#         #     sly_data["gate_id"] = gate_id 

#         # if not assigned_runway_length:
#         #     error = "Error: Please provide assigned runway for the request."
#         #     print(error)
#         #     return error   

#         # wheels chocks readiness status is required to fulfill the request.
#         wheels_chocks_readiness_status: str = sly_data.get("wheels_chocks_readiness_status", None)
#         # if not wheels_chocks_readiness_status:
#         #     print("No wheels chocks readiness status provided. Trying to get it from sly_data")
#         #     wheels_chocks_readiness_status = args.get("wheels_chocks_readiness_status")
#         #     sly_data["wheels_chocks_readiness_status"] = wheels_chocks_readiness_status

#         # if not wheels_chocks_readiness_status:
#         #     error = "Error: Please provide wheels chocks readiness status for the request."
#         #     print(error)
#         #     return error    

#         # gpu readiness status is required to fulfill the request.
#         gpu_readiness_status: str = sly_data.get("gpu_readiness_status", None)
#         # if not gpu_readiness_status:
#         #     print("No gpu readiness status provided. Trying to get it from sly_data")
#         #     gpu_readiness_status = args.get("gpu_readiness_status")
#         #     sly_data["gpu_readiness_status"] = gpu_readiness_status

#         # if not gpu_readiness_status:
#         #     error = "Error: Please provide gpu readiness status for the request."
#         #     print(error)
#         #     return error       

#             # - ground_clearance_type: this is the ground clearance type. 
#             # - ground_clearance_status: this is the ground clearance status. 

#         # ground clearance type is required to fulfill the request.
#         ground_clearance_type: str = sly_data.get("ground_clearance_type", None)
#         # if not ground_clearance_type:
#         #     print("No ground clearance type provided. Trying to get it from sly_data")
#         #     ground_clearance_type = args.get("ground_clearance_type")
#         #     sly_data["ground_clearance_type"] = ground_clearance_type 

#         # if not ground_clearance_type:
#         #     error = "Error: Please provide ground clearance type for the request."
#         #     print(error)
#         #     return error  

#         # ground clearance status is required to fulfill the request.
#         ground_clearance_status: str = sly_data.get("ground_clearance_status", None)
#         # if not ground_clearance_status:
#         #     print("No ground clearance status provided. Trying to get it from sly_data")
#         #     ground_clearance_status = args.get("ground_clearance_status")
#         #     sly_data["ground_clearance_status"] = ground_clearance_status 

#         # if not ground_clearance_status:
#         #     error = "Error: Please provide ground clearance status for the request."
#         #     print(error)
#         #     return error  

#         # read sly data for consolidated report
#         flight_number = sly_data.get("flight_number")
#         aircraft_type = sly_data.get("aircraft_type")
#         flight_status = sly_data.get("flight_status")
#         gate_id = sly_data.get("gate_id")
#         gpu_readiness_status = sly_data.get("gpu_readiness_status")
#         wheels_chocks_readiness_status = sly_data.get("wheels_chocks_readiness_status")
#         ground_clearance_type = sly_data.get("ground_clearance_type")
#         ground_clearance_status = sly_data.get("ground_clearance_status")

#         taxi_summary = {
#             "flight_number": flight_number,
#             "aircraft_type": aircraft_type,
#             "flight_status": flight_status,
#             "gate_id": gate_id,
#             "gpu_readiness_status": gpu_readiness_status,
#             "wheels_chocks_readiness_status": wheels_chocks_readiness_status, 
#             "ground_clearance_type": ground_clearance_type,
#             "ground_clearance_status": ground_clearance_status
#         }

#         message = f"aircraft taxi procedure completed with summary {taxi_summary}"
#         print(message)
#         print("\n")
#         print("\n")
#         print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

#         # Log
#         ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#         line = ts + ": " + message

#         with open(file_path_log, "a", encoding="utf-8") as f:
#             f.write(line + "\n")

#         sly_data["taxi_summary"] = taxi_summary

#         return taxi_summary

#     async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
#         """
#         Delegates to the synchronous invoke method because it's quick, non-blocking.
#         """
#         return self.invoke(args, sly_data)
    
# ######