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

class execute_aircraft_taxiing(CodedTool):
    # """
    # Update flight_status based on ground_clearance_type:
    #   - contains 'taxi in'  -> flight_status = 'ON_BLOCKS'
    #   - contains 'taxi out' -> flight_status = 'TAKEOFF_READY'
    # Returns the new flight_status, or an error string.
    # """

    def __init__(self):
        super().__init__()

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"

        # Read inputs (sly_data first, then args)
        flight_status         = _from_sly_or_args(sly_data, args, "flight_status")
        aircraft_type         = _from_sly_or_args(sly_data, args, "aircraft_type")
        flight_number         = _from_sly_or_args(sly_data, args, "flight_number")
        gate_id               = _from_sly_or_args(sly_data, args, "gate_id")
        ground_clearance_type = _from_sly_or_args(sly_data, args, "ground_clearance_type")
        ground_clearance_status = _from_sly_or_args(sly_data, args, "ground_clearance_status")
        assigned_runway_id    = _from_sly_or_args(sly_data, args, "assigned_runway_id")
        gpu_readiness_status      = _from_sly_or_args(sly_data, args, "gpu_readiness_status")
        wheels_chocks_readiness_status = _from_sly_or_args(sly_data, args, "wheels_chocks_readiness_status")

        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ aircraft taxiing agent $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print("\n")
        print("\n")
        print("ground_clearance_type: ", ground_clearance_type)
        print("ground_clearance_status: ", ground_clearance_status)
        print("flight_status: ", flight_status)
        print("aircraft_type: ", aircraft_type)
        print("flight_number: ", flight_number)
        print("gate_id: ", gate_id)
        print("assigned_runway_id: ", assigned_runway_id)
        print("gpu_readiness_status: ", gpu_readiness_status)
        print("wheels_chocks_readiness_status: ", wheels_chocks_readiness_status)
        print("\n")
        print("\n")
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

        # Normalize for matching (prevents: TypeError: NoneType is not iterable)
        gct = _norm(ground_clearance_type)

        # Mitigate LLM variability on ground clearance 
        if (('in' not in ground_clearance_type) & ('landed' in flight_status)):
            gct = "taxi in"

        print("\n")
        print("\n")
        print("ground_clearance_type normalized as gct: ", gct)
        print("------------------------------------------------------------")
        print("\n")
        print("\n")

        if not gct:
            return "Error: ground_clearance_type is required."

        # ----- TAXI IN -----
        if ("taxi" in gct):
            time.sleep(0.5)
            new_status = "ON_BLOCKS"

            # Log
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line1 = f"{ts}: flight {flight_number} taxied from runway {assigned_runway_id} to gate {gate_id}"
            line2 = f"{ts}: flight {flight_number} status updated to {new_status} at gate {gate_id}"
            with open(file_path_log, "a", encoding="utf-8") as f:
                f.write(line1 + "\n")
                f.write(line2 + "\n")

            # Update context
            sly_data["flight_status"] = new_status
            sly_data["ground_clearance_status"] = ground_clearance_status
            flight_status = new_status

            # return new_status
            return flight_status, ground_clearance_status

        # ----- TAXI OUT -----
        if "taxi out" in gct:
            time.sleep(0.5)
            new_status = "TAKEOFF_READY"

            # Log
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line1 = f"{ts}: flight {flight_number} taxied from gate {gate_id} to runway {assigned_runway_id}"
            line2 = f"{ts}: flight {flight_number} status updated to {new_status} at gate {gate_id}"
            with open(file_path_log, "a", encoding="utf-8") as f:
                f.write(line1 + "\n")
                f.write(line2 + "\n")

            # Update context
            sly_data["flight_status"] = new_status
            sly_data["ground_clearance_status"] = ground_clearance_status
            flight_status = new_status

            # return new_status
            return flight_status, ground_clearance_status

        # No recognized directive
        return "Error: Unsupported ground_clearance_type (expected contains 'taxi in' or 'taxi out')."

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
            - clearance_type
            - clearance_status  

        :return: None in write mode or any of teh parameters in read mode
        """

        file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"

        print("\n")
        print("\n")
        print(" #################### API TRACKER GENERIC - AIRCRAFT GROUND TRAFFIC #################### ")
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

        # Check and update gpu_readiness_status
        gpu_readiness_status: str = args.get("gpu_readiness_status", None)
        print("\n")
        print("\n")
        print("####### gpu_readiness_status read from args: #######", gpu_readiness_status)
        print("\n")
        print("\n")
        if not gpu_readiness_status:
            print("gpu_readiness_status has not been provided in user inquiry. Trying to get it from sly_data")
            gpu_readiness_status = sly_data.get("gpu_readiness_status")
            if gpu_readiness_status: 
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

        # Check and update ground_clearance_type
        ground_clearance_type: str = args.get("ground_clearance_type", None)
        print("\n")
        print("\n")
        print("####### ground_clearance_type read from args: #######", ground_clearance_type)
        print("\n")
        print("\n")
        if not ground_clearance_type:
            print("ground_clearance_type has not been provided in user inquiry. Trying to get it from sly_data")
            ground_clearance_type = sly_data.get("ground_clearance_type")
            if ground_clearance_type: 
                print("\n")
                print("\n")
                print("####### ground_clearance_type read from sly data: #######", ground_clearance_type)
                print("\n")
                print("\n")
        else: 
            sly_data["ground_clearance_type"] = ground_clearance_type       
            print("\n")
            print("\n")
            print("####### ground_clearance_type read from args: #######", ground_clearance_type)
            print("\n")
            print("\n")

        # Check and update ground_clearance_status
        ground_clearance_status: str = args.get("ground_clearance_status", None)
        print("\n")
        print("\n")
        print("####### ground_clearance_status read from args: #######", ground_clearance_status)
        print("\n")
        print("\n")
        if not ground_clearance_status:
            print("ground_clearance_status has not been provided in user inquiry. Trying to get it from sly_data")
            ground_clearance_status = sly_data.get("ground_clearance_status")
            if ground_clearance_status: 
                print("\n")
                print("\n")
                print("####### ground_clearance_status read from sly data: #######", ground_clearance_status)
                print("\n")
                print("\n")
        else: 
            sly_data["ground_clearance_status"] = ground_clearance_status       
            print("\n")
            print("\n")
            print("####### ground_clearance_status read from args: #######", ground_clearance_status)
            print("\n")
            print("\n")

        #####################################################################################################################################
        # This return list will be trimmed to contain only parameters relevant to the agentic system where this generic coded tool is used. #
        #####################################################################################################################################
        return flight_status, gate_id, gpu_readiness_status, wheels_chocks_readiness_status, ground_clearance_type, ground_clearance_status

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)
