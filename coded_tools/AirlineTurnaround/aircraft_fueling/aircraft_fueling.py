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

# ---------- tool ----------

class fueling_operator(CodedTool):
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
            - passenger_disembarkation_status
            - crew_exit_status 
            - baggage_unload_status
        :return: None in write mode or any of the parameters in read mode
        """

        file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"
        fueling_status = 'pending'

        print("\n")
        print("\n")
        print(" #################### FUELING OPERATOR #################### ")
        print("\n")
        print("\n")

        print("\n")
        print("\n")
        print(" #################### FUELING OPERATOR - PARAMETERS #################### ")
        print("\n")
        print("\n")

        # flight number is needed in particular. 
        flight_number: str = args.get("flight_number", None)
        if not flight_number:
            print("No flight number provided. Trying to get it from sly_data")
            flight_number = sly_data.get("flight_number")
        if not flight_number:
            error = "Error: Please provide a flight number for the request."
            print(error)
            return error       

        # aircraft type is required to fulfill the request.
        aircraft_type: str = args.get("aircraft_type", None)
        if not aircraft_type:
            print("No aircraft type provided. Trying to get it from sly_data")
            aircraft_type = sly_data.get("aircraft_type")
        if not aircraft_type:
            error = "Error: Please provide an aircraft type for the request."
            print(error)
            return error  

        # flight status is required to fulfill the request.
        flight_status: str = args.get("flight_status", None)
        if not flight_status:
            print("No flight status provided. Trying to get it from sly_data")
            flight_status = sly_data.get("flight_status")
        if not flight_status:
            error = "Error: Please provide a flight status for the request."
            print(error)
            return error  
        
        # gate id is required to fulfill the request.
        gate_id: str = args.get("gate_id", None)
        if not flight_status:
            print("No gate id provided. Trying to get it from sly_data")
            gate_id = sly_data.get("gate_id")
        if not gate_id:
            error = "Error: Please provide a gate id for the request."
            print(error)
            return error  

        # passenger disembarkation status is required to fulfill the request.
        passenger_disembarkation_status: str = args.get("passenger_disembarkation_status", None)
        if not passenger_disembarkation_status:
            print("No passenger_disembarkation_status provided. Trying to get it from sly_data")
            passenger_disembarkation_status = sly_data.get("passenger_disembarkation_status")
        if not passenger_disembarkation_status:
            error = "Error: Please provide passenger disembarkation status for the request."
            print(error)
            return error  

        # crew exit status is required to fulfill the request.
        crew_exit_status: str = args.get("crew_exit_status", None)
        if not crew_exit_status:
            print("No crew exit status provided. Trying to get it from sly_data")
            crew_exit_status = sly_data.get("crew_exit_status")
        if not crew_exit_status:
            error = "Error: Please provide crew exit status for the request."
            print(error)
            return error  
        
        # baggage unload status is required to fulfill the request.
        baggage_unload_status: str = args.get("baggage_unload_status", None)
        if not baggage_unload_status:
            print("No baggage unload status provided. Trying to get it from sly_data")
            baggage_unload_status = sly_data.get("baggage_unload_status")
        if not baggage_unload_status:
            error = "Error: Please provide baggage unload status for the request."
            print(error)
            return error  

        print("\n")
        print("\n")
        print(" #################### FUELING OPERATOR - PASSENGER DISEMBARKATION STATUS - CREW EXIT STATUS - BAGGAGE UNLOAD STATUS #################### ")
        print("\n")
        print("\n")
        print('passenger_disembarkation_status is: ', passenger_disembarkation_status)
        print("\n")
        print("\n")
        print('crew_exit_status is: ', crew_exit_status)
        print("\n")
        print("\n")
        print('baggage_unload_status is: ', baggage_unload_status)
        print("\n")
        print("\n")

        if passenger_disembarkation_status: 
            passenger_disembarkation_status = passenger_disembarkation_status.strip().lower()

        if crew_exit_status: 
            crew_exit_status = crew_exit_status.strip().lower()

        if baggage_unload_status: 
            baggage_unload_status = baggage_unload_status.strip().lower()

        if (((passenger_disembarkation_status == 'completed') | (passenger_disembarkation_status == 'done')) & ((crew_exit_status == 'completed') | (crew_exit_status == 'exited')) & ((baggage_unload_status == 'completed') | (baggage_unload_status == 'unloaded'))):
            fueling_status = 'completed'
            message = f"Flight {flight_number} with airplane type {aircraft_type} {flight_status} at gate {gate_id} has fueling {fueling_status}. Its fueling status is {fueling_status}."
            print(message)
            print("\n")
            print("\n")
            print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

            timenow = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line = timenow + ": " + message
            with open(file_path_log, mode="a", encoding="utf-8") as f:  
                f.write(line + "\n")   

            sly_data["fueling_status"] = fueling_status

        # return message
        return fueling_status

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
            - crew_exit_status
            - baggage_unload_status

        :return: None in write mode or any of teh parameters in read mode
        """

        file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"

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

        #####################################################################################################################################
        # This return list will be trimmed to contain only parameters relevant to the agentic system where this generic coded tool is used. #
        #####################################################################################################################################
        return passenger_disembarkation_status, crew_exit_status, baggage_unload_status

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)
