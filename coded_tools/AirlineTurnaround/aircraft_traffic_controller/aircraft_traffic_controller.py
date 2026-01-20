from datetime import datetime
import time
from neuro_san.interfaces.coded_tool import CodedTool
import logging
from typing import Dict, Any, Union, Optional, Tuple, List, Literal, TypedDict
from enum import Enum
from dataclasses import dataclass
import re
import pandas as pd
from pathlib import Path


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
        # aircraft_base = "/Users/971244/workspace/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_traffic_controller/aircraft_base.csv"
        aircraft_base = Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_traffic_controller" / "aircraft_base.csv",
        # runway_base = "/Users/971244/workspace/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv"
        runway_base = Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_traffic_controller" / "runways_base.csv",
        # log_path: str = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt",
        log_path = Path.cwd() / "test_debug" / "airlineturnaround.txt",
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

        # file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"
        file_path_log = Path.cwd() / "test_debug" / "airlineturnaround.txt"

        # ground clearance type is required to fulfill the request.
        flight_status: str = args.get("flight_status", None)
        if not flight_status:
            print("No ground flight status provided. Trying to get it from sly_data")
            flight_status = sly_data.get("flight_status")   
        else: 
            sly_data["flight_status"] = flight_status
        if flight_status: 
            flight_status = flight_status.lower().replace("_", " ").strip()
            
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
# This coded tool proceeds as follows:                                      #
#   - Check the value passed by LLM args                                    #
#   - Check the sly data to read the latest value of parameters             #
#   - Update parameters with the value from args when sly data is empty     #
#   - Return the parameter relevant to the agentic system                   #
# Given the large number of parameters, a separate version of this coded    #
# tool will be edited for each agents so that it aonly returns the relevant #
# one for the agent.                                                        #
#############################################################################

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Enum to track where data originated from"""
    ARGS = "args"
    SLY_DATA = "sly_data"
    NOT_FOUND = "not_found"


@dataclass
class TrackerConfig:
    """Configuration for TrackerAPI defining tracked and return fields"""
    tracked_fields: List[str]
    return_fields: List[str]
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.tracked_fields:
            raise ValueError("tracked_fields cannot be empty")
        
        if not self.return_fields:
            raise ValueError("return_fields cannot be empty")
        
        # Validate that all return fields are in tracked fields
        invalid_fields = set(self.return_fields) - set(self.tracked_fields)
        if invalid_fields:
            raise ValueError(
                f"Return fields must be subset of tracked fields. "
                f"Invalid fields: {invalid_fields}"
            )


class TrackerAPI(CodedTool):
    """
    Manages flight turnaround data by reading from or writing to a shared data store.
    
    This API handles aircraft turnaround status information including flight details,
    ground services, and various operational statuses during aircraft servicing.
    """
    
    # NO CONSTRUCTOR - configuration comes through args or sly_data
    
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Tuple[Optional[str], ...]:
        """
        Process flight turnaround data by reading from args or sly_data, and updating sly_data.
        
        Args:
            args: Dictionary containing:
                - Field values to write to sly_data
                - '_config': Optional TrackerConfig for this invocation
            sly_data: Shared data store containing current flight turnaround state
            
        Returns:
            Tuple containing values for all fields defined in config.return_fields
            
        Note:
            - If a field exists in args, it's written to sly_data (write mode)
            - If a field doesn't exist in args, it's read from sly_data (read mode)
        """
        logger.info("=" * 60)
        logger.info("TrackerAPI invoked")
        logger.info("=" * 60)
        
        # Get or create configuration
        config = self._get_config(args, sly_data)
        
        # Process all tracked fields
        field_values = self._process_all_fields(args, sly_data, config)
        
        # Log final state summary
        self._log_data_summary(field_values, config)
        
        # Return specific fields as defined in configuration
        return self._build_return_tuple(field_values, config)
    
    def _get_config(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> TrackerConfig:
        """
        Get configuration from args or sly_data, with lazy initialization.
        
        Priority:
        1. args['_config'] - Config passed for this specific invocation
        2. sly_data['_tracker_config'] - Shared config initialized once per request
        3. Default config - Create and store in sly_data for reuse
        
        Args:
            args: Input arguments
            sly_data: Shared data store
            
        Returns:
            TrackerConfig instance
        """
        # Check if config passed in args for this specific invocation
        if '_config' in args:
            logger.debug("Using config from args")
            return args['_config']
        
        # Check if config already exists in sly_data (lazy initialization)
        if '_tracker_config' not in sly_data:
            logger.info("Initializing default config in sly_data")
            sly_data['_tracker_config'] = self._create_default_config()
        
        logger.debug("Using config from sly_data")
        return sly_data['_tracker_config']
    
    def _create_default_config(self) -> TrackerConfig:
        """
        Create the default configuration for flight turnaround tracking.
        
        Returns:
            Default TrackerConfig instance
        """
        return TrackerConfig(
            tracked_fields=FLIGHT_TURNAROUND_TRACKED_FIELDS,
            return_fields=FLIGHT_TURNAROUND_RETURN_FIELDS
        )
    
    def _process_all_fields(
        self, 
        args: Dict[str, Any], 
        sly_data: Dict[str, Any],
        config: TrackerConfig
    ) -> Dict[str, Optional[str]]:
        """
        Process all tracked fields by checking args first, then falling back to sly_data.
        
        Args:
            args: Input arguments potentially containing new values
            sly_data: Existing data store to read from or write to
            config: Configuration defining which fields to track
            
        Returns:
            Dictionary mapping field names to their current values
        """
        field_values = {}
        
        for field_name in config.tracked_fields:
            # Skip internal config fields
            if field_name.startswith('_'):
                continue
                
            value, source = self._process_field(field_name, args, sly_data)
            field_values[field_name] = value
            
        return field_values
    
    def _process_field(
        self, 
        field_name: str, 
        args: Dict[str, Any], 
        sly_data: Dict[str, Any]
    ) -> Tuple[Optional[str], DataSource]:
        """
        Process a single field by attempting to read from args, then sly_data.
        
        Args:
            field_name: Name of the field to process
            args: Input arguments (write mode if field exists here)
            sly_data: Shared data store (read mode if field not in args)
            
        Returns:
            Tuple of (field_value, data_source)
        """
        # Check if value provided in args (write mode)
        value = args.get(field_name)
        
        if value is not None:
            # Write mode: update sly_data with new value
            sly_data[field_name] = value
            logger.info(f"[WRITE] {field_name}: '{value}' (source: args)")
            return value, DataSource.ARGS
        
        # Read mode: try to get from sly_data
        logger.debug(f"[READ] {field_name} not in args, checking sly_data")
        value = sly_data.get(field_name)
        
        if value is not None:
            logger.info(f"[READ] {field_name}: '{value}' (source: sly_data)")
            return value, DataSource.SLY_DATA
        
        # Field not found in either location
        logger.warning(f"[NOT FOUND] {field_name}: No value in args or sly_data")
        return None, DataSource.NOT_FOUND
    
    def _build_return_tuple(
        self, 
        field_values: Dict[str, Optional[str]],
        config: TrackerConfig
    ) -> Tuple[Optional[str], ...]:
        """
        Build return tuple from field values based on configured return fields.
        
        Args:
            field_values: Dictionary of all processed field values
            config: Configuration defining which fields to return
            
        Returns:
            Tuple of values corresponding to config.return_fields
        """
        return_values = tuple(field_values.get(field) for field in config.return_fields)
        logger.info(f"Returning {len(return_values)} fields: {config.return_fields}")
        return return_values
    
    def _log_data_summary(
        self, 
        field_values: Dict[str, Optional[str]],
        config: TrackerConfig
    ) -> None:
        """
        Log a summary of all field values for traceability.
        
        Args:
            field_values: Dictionary of all processed field values
            config: Configuration defining tracked fields
        """
        logger.info("-" * 60)
        logger.info("DATA SUMMARY")
        logger.info("-" * 60)
        
        for field_name in config.tracked_fields:
            if field_name.startswith('_'):
                continue
                
            value = field_values.get(field_name)
            status = "SET" if value is not None else "UNSET"
            return_marker = " [RETURN]" if field_name in config.return_fields else ""
            logger.info(f"{field_name:40s} | {status:6s} | {value}{return_marker}")
        
        logger.info("=" * 60)
    
    async def async_invoke(
        self, 
        args: Dict[str, Any], 
        sly_data: Dict[str, Any]
    ) -> Tuple[Optional[str], ...]:
        """
        Asynchronous wrapper for invoke method.
        
        Delegates to synchronous invoke since operations are fast and non-blocking.
        
        Args:
            args: Dictionary containing new field values to write to sly_data
            sly_data: Shared data store containing current flight turnaround state
            
        Returns:
            Tuple containing values for all fields defined in config.return_fields
        """
        logger.debug("Async invoke called, delegating to synchronous invoke")
        return self.invoke(args, sly_data)


# =============================================================================
# Configuration Definitions
# =============================================================================

# Define tracked fields for flight turnaround operations
FLIGHT_TURNAROUND_TRACKED_FIELDS = [
    "acu_connection_status", 
    "acu_readiness_status",
    "aircraft_direction",
    "aircraft_landing_report",
    "aircraft_type",
    "assigned_runway_id",
    "assigned_runway_length",
    "baggage_unload_status", 
    "catering_loading_status", 
    "cleaning_cabin_status", 
    "clearance_landing_valid",
    "clearance_takeoff_valid", 
    "clearance_type",
    "crew_debrief_status", 
    "crew_exit_status", 
    "door_opening_status", 
    "engines_stop_status", 
    "flight_number",
    "flight_status",
    "fueling_status", 
    "gate_id",
    "gpu_connection_status", 
    "gpu_readiness_status",
    "ground_clearance_status",
    "ground_clearance_type",
    "ground_services_inquiry_type", 
    "ground_services_request_type",
    "inspection_maintenance_status", 
    "jetbridge_connection_status", 
    "jetbridge_status", 
    "lavatory_service_status", 
    "passenger_disembarkation_status", 
    "runway_length",
    "wheels_chocks_installation_status", 
    "wheels_chocks_readiness_status",
]

# Define which fields should be returned from the API
FLIGHT_TURNAROUND_RETURN_FIELDS = [
    "aircraft_direction",
    "aircraft_type", 
    "assigned_runway_id", 
    "assigned_runway_length", 
    "flight_number",
    "flight_status", 
    "clearance_type",
]

# =============================================================================
# Usage Examples
# =============================================================================

if __name__ == "__main__":
    # Example 1: Using default configuration (stored in sly_data)
    tracker = TrackerAPI()
    
    args = {
        "flight_number": "AA123",
        "passenger_disembarkation_status": "in_progress"
    }
    sly_data = {
        "crew_exit_status": "completed",
        "baggage_unload_status": "pending"
    }
    
    result = tracker.invoke(args, sly_data)
    print(f"Result: {result}")
    
    # Example 2: Using custom configuration passed in args
    custom_config = TrackerConfig(
        tracked_fields=["flight_number", "gate_id", "flight_status"],
        return_fields=["flight_status"]
    )
    
    custom_args = {
        "_config": custom_config,  # Pass config in args
        "flight_number": "UA456"
    }
    custom_sly_data = {
        "flight_status": "on_time"
    }
    
    result2 = tracker.invoke(custom_args, custom_sly_data)
    print(f"Custom Result: {result2}")

