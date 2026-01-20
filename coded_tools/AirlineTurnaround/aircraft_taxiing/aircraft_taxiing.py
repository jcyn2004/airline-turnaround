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
        # file_path_log = "/Users/971244/workspace/airline-turnaround/test_debug/airlineturnaround.txt"
        file_path_log = Path.cwd() / "test_debug" / "airlineturnaround.txt"

        # Read inputs (sly_data first, then args)
        flight_status         = _from_sly_or_args(sly_data, args, "flight_status")
        if flight_status: 
            flight_status = flight_status.lower().replace("_", " ").strip()
            
        aircraft_type         = _from_sly_or_args(sly_data, args, "aircraft_type")
        flight_number         = _from_sly_or_args(sly_data, args, "flight_number")
        gate_id               = _from_sly_or_args(sly_data, args, "gate_id")
        ground_clearance_type = _from_sly_or_args(sly_data, args, "ground_clearance_type")
        if ground_clearance_type: 
            ground_clearance_type = ground_clearance_type.lower().replace("_", " ").strip()
        ground_clearance_status = _from_sly_or_args(sly_data, args, "ground_clearance_status")
        if ground_clearance_status: 
            ground_clearance_status = ground_clearance_status.lower().replace("_", " ").strip()
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
        # if (('in' not in ground_clearance_type) & ('landed' in flight_status)):
        if (('taxi' in ground_clearance_type) & (('landed' in flight_status) | ('taxi' in flight_status))):
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
            # time.sleep(0.5)
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
            # time.sleep(0.5)
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
    "acu_readiness_status", 
    "aircraft_direction",
    "aircraft_type",
    "assigned_runway_id",
    "flight_number",
    "flight_status",
    "gate_id", 
    "gpu_readiness_status", 
    "ground_clearance_status", 
    "ground_clearance_type", 
    "wheels_chocks_readiness_status", 
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

