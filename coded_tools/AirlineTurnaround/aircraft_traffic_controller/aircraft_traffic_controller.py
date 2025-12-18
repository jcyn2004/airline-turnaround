from typing import Any, Dict, Union, TypedDict, Literal
from datetime import datetime
import pandas as pd
import re
from neuro_san.interfaces.coded_tool import CodedTool


# =========================
# Types & validation
# =========================

# Allowed clearance values
ClearanceType = Literal["CLEARED_FOR_LANDING", "CLEARED_FOR_TAKEOFF", "HOLD", "GO_AROUND", "DENY"]

# Structured payload returned to other agents/tools
class ClearanceDict(TypedDict):
    flight_status: str                 # e.g., "APPROACH" or "DEPARTING"
    flight_number: str                 # canonical uppercase
    aircraft_type: str                 # canonical uppercase
    clearance_type: ClearanceType
    assigned_runway_id: str            # e.g., "28L"
    assigned_runway_length: int        # meters

# Runway designator: 1–3 digits, optional L/R/C
_RUNWAY_RE = re.compile(r"^(?:[0-3]?\d|[0-2]\d|3[0-6])[LRC]?$")  # 01..36, optional L/R/C


def build_clearance(
    flight_status: str,
    flight_number: str,
    aircraft_type: str,
    clearance_type: ClearanceType,
    assigned_runway_id: str,
    assigned_runway_length: Union[int, float],
) -> ClearanceDict:
    """
    Return a standardized clearance dict for multi-agent handoffs.
    Raises ValueError on invalid input.
    """
    if not flight_number or not aircraft_type or not flight_status:
        raise ValueError("flight_number, aircraft_type, and flight_status are required")

    if clearance_type not in ("CLEARED_FOR_LANDING", "CLEARED_FOR_TAKEOFF", "HOLD", "GO_AROUND", "DENY"):
        raise ValueError("clearance_type must be one of CLEARED_FOR_LANDING, CLEARED_FOR_TAKEOFF, HOLD, GO_AROUND, DENY")

    rwy = (assigned_runway_id or "").strip().upper()
    if not _RUNWAY_RE.match(rwy):
        raise ValueError("assigned_runway_id must look like 10, 28L, 04R, etc.")

    try:
        length_m = int(float(assigned_runway_length))
    except (TypeError, ValueError):
        raise ValueError("assigned_runway_length must be a number (meters)")

    if length_m <= 0:
        raise ValueError("assigned_runway_length must be > 0 meters")

    return {
        "flight_status": flight_status.strip().upper(),
        "flight_number": flight_number.strip().upper(),
        "aircraft_type": aircraft_type.strip().upper(),
        "clearance_type": clearance_type,
        "assigned_runway_id": rwy,
        "assigned_runway_length": length_m,
    }


# =========================
# Tool implementation
# =========================

class execute_air_clearance(CodedTool):
    """
    Decide and emit air clearance for incoming or departing traffic.
    - For incoming: find the shortest runway meeting the landing requirement.
    - For departing: find the longest runway meeting the takeoff requirement.
    Returns a ClearanceDict or an error string.
    """

    # Optional reference of possible statuses (not strictly enforced)
    flight_status_set = [
        "APPROACH", "LANDED", "AIRBORNE", "TAXI_IN", "TAXI_OUT",
        "ON_BLOCKS", "ARRIVED", "OFF_BLOCKS", "PUSHBACK",
        "LEFT_GATE", "AT_GATE", "PARKED", "DEPARTING"
    ]

    def __init__(
        self,
        aircraft_base: str = "/Users/971244/workspace/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_traffic_controller/aircraft_base.csv",
        runway_base: str = "/Users/971244/workspace/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv",
        log_path: str = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt",
    ):
        super().__init__()
        self.aircraft_base = aircraft_base
        self.runway_base = runway_base
        self.log_path = log_path

    # ---------- helpers ----------
    @staticmethod
    def _log(path: str, text: str) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")

    @staticmethod
    def _load_aircraft_base(path: str) -> pd.DataFrame:
        # Expect columns: Aircraft_Model, Landing(m), Takeoff(m)
        df = pd.read_csv(path, dtype=str).fillna("")
        for c in ["Aircraft_Model", "Landing(m)", "Takeoff(m)"]:
            if c not in df.columns:
                raise ValueError(f"aircraft_base missing required column '{c}'")
        df["Aircraft_Model"] = df["Aircraft_Model"].str.strip().str.upper()
        df["Landing(m)"] = pd.to_numeric(df["Landing(m)"], errors="coerce").fillna(0).astype(int)
        df["Takeoff(m)"] = pd.to_numeric(df["Takeoff(m)"], errors="coerce").fillna(0).astype(int)
        return df

    @staticmethod
    def _load_runway_base(path: str) -> pd.DataFrame:
        # Expect columns: unit_id, length(m)
        df = pd.read_csv(path, dtype=str).fillna("")
        for c in ["unit_id", "length(m)"]:
            if c not in df.columns:
                raise ValueError(f"runway_base missing required column '{c}'")
        df["unit_id"] = df["unit_id"].str.strip().str.upper()
        df["length(m)"] = pd.to_numeric(df["length(m)"], errors="coerce").fillna(0).astype(int)
        return df

    # ---------- main entry ----------
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        # Inputs (args first, fall back to sly_data)
        aircraft_type: str = args.get("aircraft_type") or sly_data.get("aircraft_type")
        flight_number: str = args.get("flight_number") or sly_data.get("flight_number")
        aircraft_direction: str = args.get("aircraft_direction") or sly_data.get("aircraft_direction")

        # Persist context
        if aircraft_type: sly_data["aircraft_type"] = aircraft_type
        if flight_number: sly_data["flight_number"] = flight_number
        if aircraft_direction: sly_data["aircraft_direction"] = aircraft_direction

        if not aircraft_type or not flight_number or not aircraft_direction:
            return "Error: aircraft_type, flight_number, and aircraft_direction are required."

        aircraft_direction = aircraft_direction.strip().lower()
        if aircraft_direction not in {"incoming", "departing"}:
            return "Error: aircraft_direction must be 'incoming' or 'departing'."

        try:
            ac_df = self._load_aircraft_base(self.aircraft_base)
            rw_df = self._load_runway_base(self.runway_base)
        except Exception as e:
            return f"Error: failed to load bases: {e}"

        ac_key = aircraft_type.strip().upper()
        ac_rows = ac_df[ac_df["Aircraft_Model"] == ac_key]
        if ac_rows.empty:
            return f"Error: aircraft type '{aircraft_type}' not found in aircraft_base."

        if aircraft_direction == "incoming":
            min_len = int(ac_rows["Landing(m)"].iloc[0])
            candidates = rw_df[rw_df["length(m)"] >= min_len].sort_values(by="length(m)", ascending=True)
            if candidates.empty:
                return f"Error: no runway meets landing requirement ({min_len} m) for {aircraft_type}."
            assigned_runway_id = str(candidates["unit_id"].iloc[0])
            assigned_runway_length = int(candidates["length(m)"].iloc[0])
            flight_status = "APPROACH"
            clearance_type: ClearanceType = "CLEARED_FOR_LANDING"

        else:  # departing
            min_len = int(ac_rows["Takeoff(m)"].iloc[0])
            candidates = rw_df[rw_df["length(m)"] >= min_len].sort_values(by="length(m)", ascending=True)
            if candidates.empty:
                return f"Error: no runway meets takeoff requirement ({min_len} m) for {aircraft_type}."
            # choose the longest suitable runway
            assigned_runway_id = str(candidates["unit_id"].iloc[-1])
            assigned_runway_length = int(candidates["length(m)"].iloc[-1])
            flight_status = "DEPARTING"
            clearance_type: ClearanceType = "CLEARED_FOR_TAKEOFF"

        # Log and stash
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line1 = f"{ts} :flight {flight_number.upper()} granted clearance [{clearance_type}] on runway {assigned_runway_id}"
        line2 = f"{ts} :flight {flight_number.upper()} status updated to {flight_status}"
        self._log(self.log_path, line1)
        self._log(self.log_path, line2) 

        clearance_report = line1 + line2,

        sly_data.update({
            "clearance_type": clearance_type,
            "assigned_runway_id": assigned_runway_id,
            "assigned_runway_length": assigned_runway_length,  # keep numeric
            "flight_status": flight_status,
            "clearance_report": line1 + line2,
        })

        try:
            return build_clearance(
                flight_status=flight_status,
                flight_number=flight_number,
                aircraft_type=aircraft_type,
                clearance_type=clearance_type,
                assigned_runway_id=assigned_runway_id,
                assigned_runway_length=assigned_runway_length,
            )
        except Exception as e:
            return f"Error: failed to build clearance: {e}"

class trackerAPI(CodedTool):

    """
    Taxiing information.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: a dictionary with the following keys:
            - flight_number: the name of the shop to order from.
            - aircraft_type: the name of the person to order for.
            - aircraft_direction: this is the direction of the aircraft as incoming or departing. 
            - clearance_type: this is the air clearance type requested for landing or for takeoff. 
            - assigned_runway_id: this is the id of the runway assigned for landing or for takeoff. 
            - assigned_runway_length: this is the length of the runway assigned for landing or for takeoff. 

        :param sly_data: a dictionary with the following keys:

        :return:
            In case of successful execution:
                all parameters available.
            otherwise:
                a string error message in the format:
                "Error: <error message>"
        """
        print(">>>>>>>>>>>>>>>>>>> trackerAPI flight operation agent >>>>>>>>>>>>>>>>>>")

        file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"

        # flight number is needed in particular. 
        flight_number: str = args.get("flight_number", None)
        if not flight_number:
            print("No flight number provided. Trying to get it from sly_data")
            flight_number = sly_data.get("flight_number")
        else: 
            sly_data["flight_number"] = flight_number

        # aircraft type is required to fulfill the request.
        aircraft_type: str = args.get("aircraft_type", None)
        if not aircraft_type:
            print("No aircraft type provided. Trying to get it from sly_data")
            aircraft_type = sly_data.get("aircraft_type")
        else: 
            sly_data["aircraft_type"] = aircraft_type

        # ground clearance type is required to fulfill the request.
        aircraft_direction: str = args.get("aircraft_direction", None)
        if not aircraft_direction:
            print("No ground clearance type provided. Trying to get it from sly_data")
            aircraft_direction = sly_data.get("aircraft_direction")
        else: 
            sly_data["aircraft_direction"] = aircraft_direction

        # ground clearance status is required to fulfill the request.
        clearance_type: str = args.get("clearance_type", None)
        if not clearance_type:
            print("No ground clearance status provided. Trying to get it from sly_data")
            clearance_type = sly_data.get("clearance_type")   
        else: 
            sly_data["clearance_type"] = clearance_type

        # flight status is required to fulfill the request.
        assigned_runway_id: str = args.get("assigned_runway_id", None)
        if not assigned_runway_id:
            print("No flight status provided. Trying to get it from sly_data")
            assigned_runway_id = sly_data.get("assigned_runway_id")   
        else: 
            sly_data["assigned_runway_id"] = assigned_runway_id
        
        # assigned runway is required to fulfill the request.
        assigned_runway_length: str = args.get("assigned_runway_length", None)
        if not assigned_runway_length:
            print("No assigned runway provided. Trying to get it from sly_data")
            assigned_runway_length = sly_data.get("assigned_runway_length") 
        else: 
            sly_data["assigned_runway_length"] = assigned_runway_length

        message = f"Flight {flight_number} with airplane type {aircraft_type} with traffic direction {aircraft_direction} at runway {assigned_runway_id} has {clearance_type} type clearance at runway {assigned_runway_id} with length {assigned_runway_length}"
        print(message)
        print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

        # Log
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = ts + ": " + message

        with open(file_path_log, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        return message

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)
    
class tracker_aircraft_traffic_controller(CodedTool):

    """
    Taxiing information.
    """

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        :param args: a dictionary with the following keys:
            - flight_status: this is the flight status. 
            - clearance_type: this is the air clearance type requested for landing or for takeoff. 
            - assigned_runway_id: this is the id of the runway assigned for landing or for takeoff. 
            - assigned_runway_length: this is the length of the runway assigned for landing or for takeoff. 

        :param sly_data: a dictionary with the following keys:

        :return:
            In case of successful execution:
                all parameters available.
            otherwise:
                a string error message in the format:
                "Error: <error message>"
        """
        print(">>>>>>>>>>>>>>>>>>> trackerAPI flight operation agent >>>>>>>>>>>>>>>>>>")

        file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"

        # ground clearance type is required to fulfill the request.
        flight_status: str = args.get("flight_status", None)
        if not flight_status:
            print("No ground flight status provided. Trying to get it from sly_data")
            flight_status = sly_data.get("flight_status")   
        else: 
            sly_data["flight_status"] = flight_status

        # ground clearance status is required to fulfill the request.
        clearance_type: str = args.get("clearance_type", None)
        if not clearance_type:
            print("No ground clearance status provided. Trying to get it from sly_data")
            clearance_type = sly_data.get("clearance_type")
        else: 
            sly_data["clearance_type"] = clearance_type

        # flight status is required to fulfill the request.
        assigned_runway_id: str = args.get("assigned_runway_id", None)
        if not assigned_runway_id:
            print("No flight status provided. Trying to get it from sly_data")
            assigned_runway_id = sly_data.get("assigned_runway_id")  
        else: 
            sly_data["assigned_runway_id"] = assigned_runway_id
        
        # assigned runway is required to fulfill the request.
        assigned_runway_length: str = args.get("assigned_runway_length", None)
        if not assigned_runway_length:
            print("No assigned runway provided. Trying to get it from sly_data")
            assigned_runway_length = sly_data.get("assigned_runway_length")
        else:  
            sly_data["assigned_runway_length"] = assigned_runway_length

        message = f"{clearance_type} type clearance given at runway {assigned_runway_id} with length {assigned_runway_length} and flight status updated to {flight_status}"
        print(message)
        print(">>>>>>>>>>>>>>>>>>> DONE !!! >>>>>>>>>>>>>>>>>>")

        # Log
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        line = ts + ": " + message

        with open(file_path_log, "a", encoding="utf-8") as f:
            f.write(line + "\n")

        return message

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

        #####################################################################################################################################
        # This return list will be trimmed to contain only parameters relevant to the agentic system where this generic coded tool is used. #
        #####################################################################################################################################
        return aircraft_direction,flight_number,aircraft_type

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)
 
