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
from pathlib import Path


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
        # equipments_csv_path: str = "/Users/971244/workspace/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv",
        equipments_csv_path = Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv", 

        # log_path: str = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt", 
        log_path = Path.cwd() / "test_debug" / "airlineturnaround.txt", 
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

            print("\n")
            print("\n")
            print(">>>>>>>>>>>>>>>>>>> jetway_park_inquiry read mode >>>>>>>>>>>>>>>>>>")
            print("\n")
            print("\n")

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

            print("\n")
            print("\n")
            print(">>>>>>>>>>>>>>>>>>> jetway_park_inquiry write mode >>>>>>>>>>>>>>>>>>")
            print("\n")
            print("\n")

            deplaning_equipment_id: Optional[str] = args.get("deplaning_equipment_id")
            deplaning_equipment_type: str = (args.get("deplaning_equipment_type") or "jetway")
            deplaning_equipment_score: Union[int, float, None] = args.get("deplaning_equipment_score")
            gate_id: Optional[str] = sly_data.get("gate_id") or args.get("gate_id")

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
        # equipments_csv_path: str = "/Users/971244/workspace/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv",
        equipments_csv_path = Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv", 

        # log_path: str = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt", 
        log_path = Path.cwd() / "test_debug" / "airlineturnaround.txt", 
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

            print("\n")
            print("\n")
            print(">>>>>>>>>>>>>>>>>>> stairtruck_park_inquiry read mode >>>>>>>>>>>>>>>>>>")
            print("\n")
            print("\n")

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

            print("\n")
            print("\n")
            print(">>>>>>>>>>>>>>>>>>> stairtruck_park_inquiry write mode >>>>>>>>>>>>>>>>>>")
            print("\n")
            print("\n")

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
    "aircraft_type", 
    "deplaning_equipment_type", 
    "deplaning_equipment_id", 
    "deplaning_equipment_readiness_time", 
    "deplaning_equipment_score", 
    "flight_number", 
    "gate_id",
]


# [
#     "acu_connection_status", 
#     "acu_readiness_status",
#     "aircraft_direction",
#     "aircraft_landing_report",
#     "aircraft_type",
#     "assigned_runway_id",
#     "assigned_runway_length",
#     "baggage_unload_status", 
#     "catering_loading_status", 
#     "cleaning_cabin_status", 
#     "clearance_landing_valid",
#     "clearance_takeoff_valid", 
#     "clearance_type",
#     "crew_debrief_status", 
#     "crew_exit_status", 
#     "door_opening_status", 
#     "engines_stop_status", 
#     "flight_number",
#     "flight_status",
#     "fueling_status", 
#     "gate_id",
#     "gpu_connection_status", 
#     "gpu_readiness_status",
#     "ground_clearance_status",
#     "ground_clearance_type",
#     "ground_services_inquiry_type", 
#     "ground_services_request_type",
#     "inspection_maintenance_status", 
#     "jetbridge_connection_status", 
#     "jetbridge_status", 
#     "lavatory_service_status", 
#     "passenger_disembarkation_status", 
#     "runway_length",
#     "wheels_chocks_installation_status", 
#     "wheels_chocks_readiness_status",
# ]

# Define which fields should be returned from the API
FLIGHT_TURNAROUND_RETURN_FIELDS = [
    "aircraft_type", 
    "deplaning_equipment_type", 
    "deplaning_equipment_id", 
    "deplaning_equipment_readiness_time", 
    "deplaning_equipment_score", 
    "flight_number", 
    "gate_id",
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
