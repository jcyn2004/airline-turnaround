from typing import Any, Dict, Union, TypedDict, Literal, Optional
from datetime import datetime
import pandas as pd
from neuro_san.interfaces.coded_tool import CodedTool


# =========================
# Typed payload contracts
# =========================

class GateDict(TypedDict):
    gate_id: str
    deplaning_equipment_type: str
    deplaning_equipment_id: str
    deplaning_equipment_score: float
    deplaning_equipment_availability: Literal["yes", "no"]


class JetwayDict(TypedDict):
    jetway_gate_id: str
    jetway_id: str
    jetway_availability: Literal["yes", "no"]
    jetway_readiness_time: int     # seconds
    jetway_score: float


class StairtruckDict(TypedDict):
    stairtruck_gate_id: str
    stairtruck_id: str
    stairtruck_availability: Literal["yes", "no"]
    stairtruck_readiness_time: int # seconds
    stairtruck_score: float


# =========================
# Builders (validation)
# =========================

def build_gate(
    gate_id: str,
    deplaning_equipment_type: str,
    deplaning_equipment_id: str,
    deplaning_equipment_score: Union[int, float],
    deplaning_equipment_availability: str,
) -> GateDict:
    if not gate_id or not deplaning_equipment_type or not deplaning_equipment_id:
        raise ValueError("gate_id, deplaning_equipment_type, deplaning_equipment_id are required")
    avail = (deplaning_equipment_availability or "").strip().lower()
    if avail not in {"yes", "no"}:
        raise ValueError("deplaning_equipment_availability must be 'yes' or 'no'")
    return {
        "gate_id": gate_id.strip().upper(),
        "deplaning_equipment_type": deplaning_equipment_type.strip().lower(),
        "deplaning_equipment_id": deplaning_equipment_id.strip(),  # preserve case
        "deplaning_equipment_score": float(deplaning_equipment_score),
        "deplaning_equipment_availability": avail,
    }


def build_jetway(
    jetway_gate_id: str,
    jetway_id: str,
    jetway_availability: str,
    jetway_readiness_time: Union[int, float],
    jetway_score: Union[int, float],
) -> JetwayDict:
    if not jetway_gate_id or not jetway_id:
        raise ValueError("jetway_gate_id and jetway_id are required")
    avail = (jetway_availability or "").strip().lower()
    if avail not in {"yes", "no"}:
        raise ValueError("jetway_availability must be 'yes' or 'no'")
    return {
        "jetway_gate_id": jetway_gate_id.strip().upper(),
        "jetway_id": jetway_id.strip(),  # preserve case to avoid write mismatches
        "jetway_availability": avail,
        "jetway_readiness_time": int(jetway_readiness_time),
        "jetway_score": float(jetway_score),
    }


def build_stairtruck(
    stairtruck_gate_id: str,
    stairtruck_id: str,
    stairtruck_availability: str,
    stairtruck_readiness_time: Union[int, float],
    stairtruck_score: Union[int, float],
) -> StairtruckDict:
    if not stairtruck_gate_id or not stairtruck_id:
        raise ValueError("stairtruck_gate_id and stairtruck_id are required")
    avail = (stairtruck_availability or "").strip().lower()
    if avail not in {"yes", "no"}:
        raise ValueError("stairtruck_availability must be 'yes' or 'no'")
    return {
        "stairtruck_gate_id": stairtruck_gate_id.strip().upper(),
        "stairtruck_id": stairtruck_id.strip(),  # preserve case
        "stairtruck_availability": avail,
        "stairtruck_readiness_time": int(stairtruck_readiness_time),
        "stairtruck_score": float(stairtruck_score),
    }

# =========================
# Helpers
# =========================

def _load_equipment_df(csv_path: str) -> pd.DataFrame:
    """
    Load and normalize the equipment CSV:
    - Trim strings
    - Lowercase 'type' and 'availability'
    - Ensure 'readiness' is numeric (int)
    """
    df = pd.read_csv(
        csv_path,
        dtype={"unit_id": str, "type": str, "gate_id": str, "aircraft_type": str, "availability": str, "readiness": str},
    )
    for col in ["unit_id", "type", "gate_id", "aircraft_type", "availability", "readiness"]:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df["type"] = df["type"].str.lower()
    df["availability"] = df["availability"].str.lower()
    df["readiness"] = pd.to_numeric(df["readiness"], errors="coerce").fillna(0).astype(int)
    return df


def _normalize_aircraft(s: Optional[str]) -> str:
    return (s or "").strip().upper()


def _mask_unit_id(df: pd.DataFrame, unit_id: str) -> pd.Series:
    """Case/whitespace-insensitive mask to match a unit_id in df."""
    key = (unit_id or "").strip().upper()
    return df["unit_id"].str.upper() == key


def _select_best_equipment(df: pd.DataFrame, aircraft_type: str, eq_type: str) -> Optional[pd.Series]:
    """
    Filter by aircraft type, equipment type (jetway/stairtruck) and availability 'yes',
    then pick the row with the smallest readiness.
    """
    if df.empty:
        return None
    dff = df[
        (df["aircraft_type"].str.upper() == _normalize_aircraft(aircraft_type)) &
        (df["type"] == eq_type) &
        (df["availability"] == "yes")
    ].sort_values(by="readiness", ascending=True)
    return None if dff.empty else dff.iloc[0]


def _select_alternate_equipment(
    df: pd.DataFrame, aircraft_type: str, eq_type: str, sly_gate_id: Optional[str]
) -> Optional[pd.Series]:
    """
    Same as best selection but constrained to a specific gate_id, then pick lowest readiness.
    """
    if df.empty or not sly_gate_id:
        return None
    dff = df[
        (df["aircraft_type"].str.upper() == _normalize_aircraft(aircraft_type)) &
        (df["type"] == eq_type) &
        (df["availability"] == "yes") &
        (df["gate_id"].str.upper() == sly_gate_id.strip().upper())
    ].sort_values(by="readiness", ascending=True)
    return None if dff.empty else dff.iloc[0]


def _log_line(path: str, text: str) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(text + "\n")


# =========================
# Tools
# =========================

class jetway_park_inquiry(CodedTool):
    """
    Inquiry/update of JETWAY availability.
    execution_mode: 'read' -> select best jetway; 'write' -> mark chosen jetway unavailable.
    """

    print("\n")
    print("\n")
    print(">>>>>>>>>>>>>>>>>>> jetway_park_inquiry loaded >>>>>>>>>>>>>>>>>>")
    print("\n")
    print("\n")

    def __init__(
        self,
        equipments_csv_path: str = "/Users/971244/workspace/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv",
        log_path: str = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt",
    ):
        super().__init__()
        self.equipments_csv_path = equipments_csv_path
        self.log_path = log_path

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        agent_name = "jetway_park_agent"

        # Prefer sly_data (as per your pattern)
        flight_number: Optional[str] = sly_data.get("flight_number")
        aircraft_type: Optional[str] = sly_data.get("aircraft_type")
        gate_id: Optional[str] = sly_data.get("gate_id")
        execution_mode: Optional[str] = sly_data.get("execution_mode")  # 'read' | 'write'

        # Fallback to args if missing
        if not flight_number:
            flight_number = args.get("flight_number")
        if not aircraft_type:
            aircraft_type = args.get("aircraft_type")
        if not gate_id:
            gate_id = args.get("gate_id")
        if not execution_mode:
            execution_mode = args.get("execution_mode")

        # defaults 
        jetway_gate_id = "UNKNOWN"
        jetway_id = "NONE"
        jetway_availability = "no"
        jetway_readiness_time = 1000  # seconds
        jetway_score = 1.0 / (1.0 + jetway_readiness_time)

        if execution_mode == "read":
            if not aircraft_type:
                return "Error: No aircraft type provided."

            df = _load_equipment_df(self.equipments_csv_path)
            row = _select_best_equipment(df, aircraft_type, eq_type="jetway")

            if row is not None:
                jetway_readiness_time = int(row["readiness"])
                jetway_id = str(row["unit_id"])                # preserve case
                jetway_gate_id = str(row["gate_id"]).upper()
                jetway_availability = "yes"
                jetway_score = 1.0 / (1.0 + jetway_readiness_time)

                # log + stash
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                _log_line(self.log_path, f"{ts}: agent [{agent_name}] found JETWAY {jetway_id} at GATE {jetway_gate_id} readiness {jetway_readiness_time}s")

                # If caller provided a preferred gate_id, try to prioritize it
                if gate_id and jetway_gate_id != gate_id.strip().upper():
                    row_alt = _select_alternate_equipment(df, aircraft_type, eq_type="jetway", sly_gate_id=gate_id)
                    if row_alt is not None:
                        jetway_readiness_time = int(row_alt["readiness"])
                        jetway_id = str(row_alt["unit_id"])
                        jetway_gate_id = str(row_alt["gate_id"]).upper()
                        jetway_availability = "yes"
                        jetway_score = 1.0 / (1.0 + jetway_readiness_time)

                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        _log_line(self.log_path, f"{ts}: agent [{agent_name}] switched JETWAY to {jetway_id} at GATE {jetway_gate_id} to honor requested gate_id")

                sly_data.update({
                    "jetway_id": jetway_id,
                    "jetway_availability": jetway_availability,
                    "jetway_gate_id": jetway_gate_id,
                    "jetway_readiness_time": jetway_readiness_time,
                    "jetway_score": jetway_score,
                })

            # Log
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line = f"{ts}: jetway {jetway_id} availability is {jetway_availability} with a readiness time {jetway_readiness_time} and score of {jetway_score} for deplaning at gate {jetway_gate_id}"
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

            return build_jetway(jetway_gate_id, jetway_id, jetway_availability, jetway_readiness_time, jetway_score)

        if execution_mode == "write":
            deplaning_equipment_id: Optional[str] = args.get("deplaning_equipment_id")
            deplaning_equipment_type: str = (args.get("deplaning_equipment_type") or "jetway")
            deplaning_equipment_score: Union[int, float, None] = args.get("deplaning_equipment_score")
            gate_id_arg: Optional[str] = sly_data.get("gate_id") or args.get("gate_id")

            if not deplaning_equipment_id:
                return "Error: No equipment id provided."

            df = _load_equipment_df(self.equipments_csv_path)
            mask = _mask_unit_id(df, deplaning_equipment_id)
            if not mask.any():
                return f"Error: equipment id {deplaning_equipment_id} not found."

            equipment_type = str(df.loc[mask, "type"].iloc[0])  # already lowercased
            if equipment_type != "jetway":
                return f"Error: equipment id {deplaning_equipment_id} is type '{equipment_type}', expected 'jetway'."

            df.loc[mask, "availability"] = "no"
            gate_id_final = str(df.loc[mask, "gate_id"].iloc[0]).upper()
            df.to_csv(self.equipments_csv_path, index=False)

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line = f"{ts} flight {str(flight_number or '').upper()} aircraft {str(aircraft_type or '').upper()} assigned gate {gate_id_final} (jetway)"
            _log_line(self.log_path, line)

            sly_data["gate_id"] = gate_id_final
            sly_data["deplaning_equipment_report"] = line

            return build_gate(
                gate_id=gate_id_final,
                deplaning_equipment_type=deplaning_equipment_type,
                deplaning_equipment_id=deplaning_equipment_id,   # preserve case
                deplaning_equipment_score=float(deplaning_equipment_score or 0.0),
                deplaning_equipment_availability="no",
            )

        else: 
            return "Error: execution_mode must be 'read' or 'write'."

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)

class stairtruck_park_inquiry(CodedTool):
    """
    Inquiry/update of STAIRTRUCK availability.
    execution_mode: 'read' -> select best stairtruck; 'write' -> mark chosen stairtruck unavailable.
    """

    print("\n")
    print("\n")
    print(">>>>>>>>>>>>>>>>>>> stairtruck_park_inquiry loaded >>>>>>>>>>>>>>>>>>")
    print("\n")
    print("\n")

    def __init__(
        self,
        equipments_csv_path: str = "/Users/971244/workspace/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv",
        log_path: str = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt",
    ):
        super().__init__()
        self.equipments_csv_path = equipments_csv_path
        self.log_path = log_path

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        agent_name = "stairtruck_park_agent"

        # Prefer sly_data
        flight_number: Optional[str] = sly_data.get("flight_number")
        aircraft_type: Optional[str] = sly_data.get("aircraft_type")
        gate_id: Optional[str] = sly_data.get("gate_id")
        execution_mode: Optional[str] = sly_data.get("execution_mode")  # 'read' | 'write'

        # Fallback to args if missing
        if not flight_number:
            flight_number = args.get("flight_number")
        if not aircraft_type:
            aircraft_type = args.get("aircraft_type")
        if not gate_id:
            gate_id = args.get("gate_id")
        if not execution_mode:
            execution_mode = args.get("execution_mode")

        # defaults
        stairtruck_gate_id = "UNKNOWN"
        stairtruck_id = "NONE"
        stairtruck_availability = "no"
        stairtruck_readiness_time = 1000  
        stairtruck_score = 1.0 / (1.0 + stairtruck_readiness_time)

        if execution_mode == "read":
            if not aircraft_type:
                return "Error: No aircraft type provided."

            df = _load_equipment_df(self.equipments_csv_path)
            row = _select_best_equipment(df, aircraft_type, eq_type="stairtruck")
            if row is not None:
                stairtruck_readiness_time = int(row["readiness"])
                stairtruck_id = str(row["unit_id"])              # preserve case
                stairtruck_gate_id = str(row["gate_id"]).upper()
                stairtruck_availability = "yes"
                stairtruck_score = 1.0 / (1.0 + stairtruck_readiness_time)

                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                _log_line(self.log_path, f"{ts}: agent [{agent_name}] found STAIRTRUCK {stairtruck_id} at GATE {stairtruck_gate_id} readiness {stairtruck_readiness_time}s")

                if gate_id and stairtruck_gate_id != gate_id.strip().upper():
                    row_alt = _select_alternate_equipment(df, aircraft_type, eq_type="stairtruck", sly_gate_id=gate_id)
                    if row_alt is not None:
                        stairtruck_readiness_time = int(row_alt["readiness"])
                        stairtruck_id = str(row_alt["unit_id"])
                        stairtruck_gate_id = str(row_alt["gate_id"]).upper()
                        stairtruck_availability = "yes"
                        stairtruck_score = 1.0 / (1.0 + stairtruck_readiness_time)

                        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                        _log_line(self.log_path, f"{ts}: agent [{agent_name}] switched STAIRTRUCK to {stairtruck_id} at GATE {stairtruck_gate_id} to honor requested gate_id")

                sly_data.update({
                    "stairtruck_id": stairtruck_id,
                    "stairtruck_availability": stairtruck_availability,
                    "stairtruck_gate_id": stairtruck_gate_id,
                    "stairtruck_readiness_time": stairtruck_readiness_time,
                    "stairtruck_score": stairtruck_score,
                })

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line = f"{ts}: stairtruck {stairtruck_id} availability is {stairtruck_availability} with a readiness time {stairtruck_readiness_time} and score of {stairtruck_score} for deplaning at gate {stairtruck_gate_id}"
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

            return build_stairtruck(stairtruck_gate_id, stairtruck_id, stairtruck_availability, stairtruck_readiness_time, stairtruck_score)

        if execution_mode == "write":
            deplaning_equipment_id: Optional[str] = args.get("deplaning_equipment_id")
            deplaning_equipment_type: str = (args.get("deplaning_equipment_type") or "stairtruck")
            deplaning_equipment_score: Union[int, float, None] = args.get("deplaning_equipment_score")
            gate_id_arg: Optional[str] = sly_data.get("gate_id") or args.get("gate_id")

            if not deplaning_equipment_id:
                return "Error: No equipment id provided."

            df = _load_equipment_df(self.equipments_csv_path)
            mask = _mask_unit_id(df, deplaning_equipment_id)
            if not mask.any():
                return f"Error: equipment id {deplaning_equipment_id} not found."

            equipment_type = str(df.loc[mask, "type"].iloc[0]) 
            if equipment_type != "stairtruck":
                return f"Error: equipment id {deplaning_equipment_id} is type '{equipment_type}', expected 'stairtruck'."

            df.loc[mask, "availability"] = "no"
            gate_id_final = str(df.loc[mask, "gate_id"].iloc[0]).upper()
            df.to_csv(self.equipments_csv_path, index=False)

            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            line = f"{ts} flight {str(flight_number or '').upper()} aircraft {str(aircraft_type or '').upper()} assigned gate {gate_id_final} (stairtruck)"
            _log_line(self.log_path, line)

            sly_data["gate_id"] = gate_id_final
            sly_data["deplaning_equipment_report"] = line

            return build_gate(
                gate_id=gate_id_final,
                deplaning_equipment_type=deplaning_equipment_type,
                deplaning_equipment_id=deplaning_equipment_id, 
                deplaning_equipment_score=float(deplaning_equipment_score or 0.0),
                deplaning_equipment_availability="no",
            )

        else: 
            return "Error: execution_mode must be 'read' or 'write'."

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

        #####################################################################################################################################
        # This return list will be trimmed to contain only parameters relevant to the agentic system where this generic coded tool is used. #
        #####################################################################################################################################
        return jetbridge_connection_status

    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Union[Dict[str, Any], str]:
        """
        Delegates to the synchronous invoke method because it's quick, non-blocking.
        """
        return self.invoke(args, sly_data)
