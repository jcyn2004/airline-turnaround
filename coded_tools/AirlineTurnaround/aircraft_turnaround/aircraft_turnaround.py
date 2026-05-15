from datetime import datetime
import json
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
    """Prefer sly_data[key]; fallback to args[key]."""
    v = sly.get(key)
    return v if v is not None else args.get(key)

def _norm(s: Union[str, None]) -> str:
    """Lowercase+strip (safe for None)."""
    return (s or "").strip().lower()

# ---------- tool ----------

#############################################################################
# Tracker API for all parameters in the aircraft turnaround agentic system  #
# This coded tool proceeds as follows:                                      #
#   - Check the value passed by LLM args                                    #
#   - Check the sly data to read the latest value of parameters             #
#   - Update parameters with the value from args when sly data is empty     #
#   - Return the requested parameters as a JSON string / dict               #
#                                                                           #
# CHANGE: invoke() now returns a JSON string (dict) instead of a bare       #
# tuple.  The caller can pass a list of field names it wants back via       #
# args["_return_fields"].  If that key is absent the full                   #
# FLIGHT_TURNAROUND_RETURN_FIELDS list is used.                             #
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
    """Configuration for TrackerAPI defining the fields to track.

    All tracked fields are always returned by TrackerAPI; consuming agents
    select whichever values are relevant to their own task.
    """

    tracked_fields: List[str]

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.tracked_fields:
            raise ValueError("tracked_fields cannot be empty")


class TrackerAPI(CodedTool):
    """
    Manages flight turnaround data by reading from / writing to a shared
    data store (sly_data) and always returning the COMPLETE set of tracked
    parameters as a single JSON string.

    Behaviour
    ---------
    * Any field present in ``args`` is written to ``sly_data`` (write mode).
    * Any field absent from ``args`` is read from ``sly_data`` (read mode).
    * The return value is always a JSON-encoded dict containing ALL tracked
      fields. Fields with no known value are included as ``null``.

    Consuming agents are responsible for reading whichever keys are relevant
    to their own task from the returned dict.  No field selection is needed
    on the TrackerAPI side.
    """

    # NO CONSTRUCTOR – configuration comes through args or sly_data

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> str:
        """
        Process flight turnaround data and return ALL tracked fields as JSON.

        Args:
            args: Dictionary that may contain field values to write to
                  sly_data (any tracked field name), and optionally
                  ``_config`` (TrackerConfig) to override the session config.
            sly_data: Shared data store holding the current turnaround state.

        Returns:
            A JSON string containing every tracked field, e.g.::

                {
                    "flight_number": "AF84",
                    "flight_status": "on blocks",
                    "gate_id": "A1",
                    "gpu_readiness_status": null,
                    ...
                }

            Fields with no known value are included as ``null``.
            Agents should read whichever keys are relevant to their task.
        """
        logger.info("=" * 60)
        logger.info("TrackerAPI invoked")
        logger.info("=" * 60)

        # 1. Resolve configuration
        config = self._get_config(args, sly_data)

        # 2. Process (read/write) every tracked field
        field_values = self._process_all_fields(args, sly_data, config)

        # 3. Log summary
        self._log_data_summary(field_values, config.tracked_fields)

        # 4. Return ALL tracked fields as JSON
        return self._build_return_json(field_values, config.tracked_fields)

    async def async_invoke(
        self,
        args: Dict[str, Any],
        sly_data: Dict[str, Any],
    ) -> str:
        """
        Asynchronous wrapper – delegates to synchronous invoke.

        Returns:
            JSON string containing all tracked fields; see :meth:`invoke`.
        """
        logger.debug("Async invoke called, delegating to synchronous invoke")
        return self.invoke(args, sly_data)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_config(
        self, args: Dict[str, Any], sly_data: Dict[str, Any]
    ) -> TrackerConfig:
        """
        Resolve the TrackerConfig to use for this invocation.

        Priority:
          1. ``args['_config']``            – per-call override
          2. ``sly_data['_tracker_config']``– session-level config
          3. default config                 – created once and cached in sly_data

        Args:
            args: Input arguments.
            sly_data: Shared data store.

        Returns:
            TrackerConfig instance.
        """
        if "_config" in args:
            logger.debug("Using config from args")
            return args["_config"]

        if "_tracker_config" not in sly_data:
            logger.info("Initializing default config in sly_data")
            sly_data["_tracker_config"] = self._create_default_config()

        logger.debug("Using config from sly_data")
        return sly_data["_tracker_config"]

    def _create_default_config(self) -> TrackerConfig:
        """
        Create the default TrackerConfig for full turnaround tracking.

        Returns:
            Default TrackerConfig instance.
        """
        return TrackerConfig(tracked_fields=FLIGHT_TURNAROUND_TRACKED_FIELDS)

    def _process_all_fields(
        self,
        args: Dict[str, Any],
        sly_data: Dict[str, Any],
        config: TrackerConfig,
    ) -> Dict[str, Optional[str]]:
        """
        Read or write every tracked field.

        For each field:
          - If present in ``args``: write to ``sly_data``, record value.
          - Otherwise: read from ``sly_data``.

        Args:
            args: Input arguments potentially containing new values.
            sly_data: Existing data store.
            config: Configuration defining which fields to track.

        Returns:
            Dict mapping every tracked field name to its current value
            (``None`` when not found in either source).
        """
        field_values: Dict[str, Optional[str]] = {}

        for field_name in config.tracked_fields:
            if field_name.startswith("_"):
                continue  # internal / reserved keys
            value, _ = self._process_field(field_name, args, sly_data)
            field_values[field_name] = value

        return field_values

    def _process_field(
        self,
        field_name: str,
        args: Dict[str, Any],
        sly_data: Dict[str, Any],
    ) -> Tuple[Optional[str], DataSource]:
        """
        Resolve a single field, preferring the already-stored sly_data value.

        Priority:
          1. sly_data[field_name] – the authoritative running state; used
             as-is when present.  args is ignored for this field.
          2. args[field_name]     – fallback when sly_data has no value yet;
             the value is also written into sly_data so subsequent calls
             can find it under rule 1.
          3. Neither source       – returns (None, NOT_FOUND).

        Args:
            field_name: Name of the field to resolve.
            args: Input arguments used only when sly_data has no value.
            sly_data: Shared data store; always consulted first.

        Returns:
            ``(value, DataSource)`` tuple.
        """
        # 1. sly_data is authoritative
        value = sly_data.get(field_name)
        if value is not None:
            logger.info(f"[READ]  {field_name}: '{value}' (source: sly_data)")
            # print("----------------------------------------------------------------")
            # print(f"[READ]  {field_name}: '{value}' (source: sly_data)")
            # print("----------------------------------------------------------------")
            return value, DataSource.SLY_DATA

        # 2. Fall back to args and promote the value into sly_data
        value = args.get(field_name)
        if value is not None:
            sly_data[field_name] = value
            logger.info(f"[WRITE] {field_name}: '{value}' (source: args → sly_data)")
            # print("----------------------------------------------------------------")
            # print(f"[WRITE] {field_name}: '{value}' (source: args → sly_data)")
            # print("----------------------------------------------------------------")
            return value, DataSource.ARGS

        # 3. Not found anywhere
        logger.warning(f"[MISS]  {field_name}: not found in sly_data or args")
        return None, DataSource.NOT_FOUND

    # ------------------------------------------------------------------
    # Return-value builder  (CHANGED: JSON instead of tuple)
    # ------------------------------------------------------------------

    def _build_return_json(
        self,
        field_values: Dict[str, Optional[str]],
        return_fields: List[str],
    ) -> str:
        """
        Build a JSON string containing only the requested fields.

        Fields with no value are included as ``null`` so the caller always
        receives every key it asked for – making downstream parsing robust.

        Args:
            field_values: All processed field values keyed by field name.
            return_fields: Ordered list of fields to include in the output.

        Returns:
            Pretty-printed JSON string, e.g.::

                {
                    "flight_number": "AF84",
                    "flight_status": "on blocks",
                    "gate_id": null
                }
        """
        result: Dict[str, Optional[str]] = {
            field: field_values.get(field)  # None when not found
            for field in return_fields
        }
        logger.info(
            "Returning %d fields as JSON: %s", len(result), list(result.keys())
        )
        return json.dumps(result, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Logging helper
    # ------------------------------------------------------------------

    def _log_data_summary(
        self,
        field_values: Dict[str, Optional[str]],
        return_fields: List[str],
    ) -> None:
        """
        Log a human-readable summary of all field values.

        Args:
            field_values: All processed field values.
            return_fields: Fields that will be included in the return JSON.
        """
        logger.info("-" * 60)
        logger.info("DATA SUMMARY")
        logger.info("-" * 60)

        return_set = set(return_fields)
        for field_name, value in field_values.items():
            status = "SET  " if value is not None else "UNSET"
            marker = " [RETURN]" if field_name in return_set else ""
            logger.info(f"  {field_name:40s} | {status} | {value}{marker}")

        logger.info("=" * 60)


# =============================================================================
# Configuration Definitions
# =============================================================================

# All parameters tracked across the full turnaround lifecycle.
# TrackerAPI always returns every field in this list; consuming agents
# read whichever values are relevant to their own task.
FLIGHT_TURNAROUND_TRACKED_FIELDS: List[str] = [
    "acu_connection_status",
    "acu_readiness_status",
    "aircraft_direction",
    "aircraft_landing_report",
    "aircraft_type",
    "assigned_runway_id",
    "assigned_runway_length",
    "baggage_unload_status",
    "cabin_cleaning_status",
    "catering_loading_status",
    "clearance_type",
    "crew_debrief_status",
    "crew_exit_status",
    "deplaning_equipment_type",
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
    "inspection_maintenance_status",
    "jetbridge_connection_status",
    "lavatory_service_status",
    "stairtruck_connection_status",
    "passenger_disembarkation_status",
    "wheels_chocks_installation_status",
    "wheels_chocks_readiness_status",
]


# =============================================================================
# Usage Examples
# =============================================================================

if __name__ == "__main__":
    tracker = TrackerAPI()

    # ------------------------------------------------------------------
    # Example 1 – write a few fields; all tracked fields come back in JSON.
    # The agent reading the result picks out only the keys it cares about.
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Example 1: write subset of fields, receive full JSON back")
    print("=" * 60)

    args1 = {
        "flight_number": "AF84",
        "flight_status": "on blocks",
        "gate_id": "A1",
    }
    sly_data1: Dict[str, Any] = {
        "aircraft_type": "B747",
        "aircraft_direction": "incoming",
    }

    result1 = tracker.invoke(args1, sly_data1)
    print("Full JSON returned:\n", result1)

    # Agent picks out only what it needs:
    data1 = json.loads(result1)
    print("\nAgent reading its relevant fields:")
    print("  flight_number    :", data1["flight_number"])
    print("  flight_status    :", data1["flight_status"])
    print("  aircraft_type    :", data1["aircraft_type"])       # from sly_data
    print("  gpu_readiness    :", data1["gpu_readiness_status"]) # null – not set yet

    # ------------------------------------------------------------------
    # Example 2 – subsequent call adds more fields; full snapshot returned.
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Example 2: second call enriches sly_data; full snapshot returned")
    print("=" * 60)

    args2 = {
        "engines_stop_status": "stopped",
        "wheels_chocks_installation_status": "installed",
    }
    # sly_data1 is already populated from Example 1 – pass it through
    result2 = tracker.invoke(args2, sly_data1)
    data2 = json.loads(result2)

    print("Agent (ramp services) reading its relevant fields:")
    print("  engines_stop_status          :", data2["engines_stop_status"])
    print("  wheels_chocks_installation_status:", data2["wheels_chocks_installation_status"])
    print("  flight_number                :", data2["flight_number"])  # carried over
    print("  gate_id                      :", data2["gate_id"])         # carried over

    # ------------------------------------------------------------------
    # Example 3 – custom TrackerConfig (narrow tracked set).
    # Still returns every tracked field – just a smaller set.
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Example 3: custom TrackerConfig – all tracked fields returned")
    print("=" * 60)

    custom_config = TrackerConfig(
        tracked_fields=["flight_number", "gate_id",
                        "flight_status", "engines_stop_status"],
    )
    args3 = {
        "_config": custom_config,
        "flight_number": "UA456",
        "engines_stop_status": "stopped",
    }
    sly_data3: Dict[str, Any] = {"flight_status": "on blocks", "gate_id": "B3"}

    result3 = tracker.invoke(args3, sly_data3)
    print("Full JSON returned:\n", result3)
    data3 = json.loads(result3)
    print(f"\nAll {len(data3)} tracked fields present: {list(data3.keys())}")

