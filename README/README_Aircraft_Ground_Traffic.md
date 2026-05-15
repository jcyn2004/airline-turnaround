# Aircraft Ground Traffic
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_traffic.hocon`
> **Implementation file:** `aircraft_ground_traffic.py`
> **Data files:** `aircraft_traffic_controller/aircraft_base.csv`, `aircraft_traffic_controller/runways_base.csv`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Issue ground traffic clearances for aircraft taxi-in (after landing) and taxi-out (after pushback), routing through a three-level agent chain that validates flight status and runway compatibility.

---

## 1. Overview

`aircraft_ground_traffic` is the most architecturally complex network in the **AirlineTurnaround** system. It is the only network with a **three-level LLM agent chain** — an orchestrator delegates to a controller, which delegates to an executor — and one of only two networks that reads external CSV data files. Unlike `aircraft_gate_selection` which selects from a gate inventory, this network validates aircraft-runway compatibility from separate aircraft and runway specification tables.

The network combines:

- `ground_traffic_orchestrator` — LLM agent; entry point, parses requests, enforces flight-status prerequisites, delegates clearance
- `ground_traffic_controller` — LLM agent; second-tier router, delegates to the execution tool
- `ground_clearance_agent` — thin LLM wrapper over the coded tool
- `execute_ground_clearance` — the actual clearance logic, implemented in Python; the only class registered for execution
- `TrackerAPI` — shared state manager

Two external CSV files are required: `aircraft_base.csv` (aircraft landing/takeoff run requirements) and `runways_base.csv` (runway lengths), both in the `aircraft_traffic_controller` directory.

---

## 2. Repository Structure

```
aircraft_ground_traffic.hocon            # Agent network configuration
aircraft_ground_traffic.py               # Coded tool implementations (execute_ground_clearance, TrackerAPI)
coded_tools/AirlineTurnaround/aircraft_traffic_controller/aircraft_base.csv    # Aircraft landing/takeoff run requirements
coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv     # Runway lengths
registries/aaosa_basic.hocon             # Shared registry (no external tools used)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
ground_traffic_orchestrator  (LLM Agent — entry point)
   │
   ├── TrackerAPI             (Coded tool: read/write turnaround state via sly_data)
   │
   └── ground_traffic_controller  (LLM Agent — clearance routing)
          │
          └── ground_clearance_agent  (LLM wrapper over coded tool)
                 │
                 └── execute_ground_clearance  (Coded tool: clearance decision + CSV validation)
```

### Design principles

- **Three-level agent delegation:** The orchestrator handles prerequisites and flow control; the controller handles clearance routing; the execution tool makes the decision. This separation allows each level to be swapped or extended independently.
- **Status-driven clearance:** `execute_ground_clearance` grants clearance based on `flight_status` keyword matching (`'landed'` → taxi-in, `'off blocks'` → taxi-out). CSV data is loaded and validated but not currently used to filter runway selection.
- **Typed clearance contract:** The operator uses Python `Literal` types and a `TypedDict` (`ClearanceDict`) for structured output, providing stronger type guarantees than any other network in the system.
- **Runway regex validation:** `assigned_runway_id` is validated against a regex (`^(?:[0-3]?\d| [0-2]\d |3[0-6])[LRC]?$`) before clearance is issued.

---

## 4. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

---

## 5. Components

### 5.1 ground_traffic_orchestrator (LLM Agent — Entry Point)

Parses taxi requests, resolves all parameters, enforces the flight-status prerequisite, and delegates to `ground_traffic_controller`.

> Note: The agent is named `ground_traffic_orchestrator` in the HOCON. The previous documentation referred to it as `aircraft_ground_traffic_agent`, which does not match the actual runtime tool name.

> Note: In the HOCON, this tool's `parameters` block is placed **after** the `instructions` block (lines 140–173). All other networks place `parameters` before `instructions`. This is a structural anomaly that may affect how the schema is parsed.

#### Input parameters

| Parameter                 | Type   | Required | Description                                             |
|---------------------------|--------|:--------:|---------------------------------------------------------|
| `flight_number`           | string |    ✅     | Flight identifier                                       |
| `aircraft_type`           | string |    ✅     | Aircraft model/type                                     |
| `flight_status`           | string |    ✅     | Expected: `landed` (taxi-in) or `off blocks` (taxi-out) |
| `assigned_runway_id`      | string |    ✅     | Runway designator (e.g. `28L`, `04R`)                   |
| `gate_id`                 | string |    ✅     | Assigned gate                                           |
| `ground_clearance_type`   | string |    ❌     | Auto-set from taxi-in/taxi-out phrasing                 |
| `ground_clearance_status` | string |    ❌     | Clearance outcome                                       |

#### Orchestration flow

1. Parse inquiry — extract `flight_number`, `aircraft_type`, `flight_status`, `assigned_runway_id`, `gate_id`. Auto-detect `ground_clearance_type` from phrasing ("taxi in" → `taxi in`, "taxi out"/"pushback" → `taxi out`).
2. Call `TrackerAPI` — read/store all available parameters.
3. If `ground_clearance_type` is still `None` → ask user to provide it. Wait for response. Return to step 1.
4. If `flight_status` is NOT `landed` or `off blocks` → do not issue clearance. Return to step 2.
5. If `flight_status` IS `landed` or `off blocks` → call `ground_traffic_controller` for taxi-in or taxi-out based on `ground_clearance_type`. Update `flight_status` with the returned value before displaying the summary.
6. Display results.

> Note: Step 3 contains an interactive user-wait loop — one of only two networks in the system with this pattern (the other is `aircraft_engines_stop`). In automated upstream-calling contexts, this loop may stall indefinitely if no user is present.

> Note: Step 4's "return to step 2" creates a potential loop — if `TrackerAPI` has no better `flight_status` value in sly_data, the agent will loop between steps 4 and 2 indefinitely. There is no maximum retry count.

#### sly_data contract

| Direction           | Parameters                                                                                                                             |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `flight_number`, `aircraft_type`, `ground_clearance_type`, `ground_clearance_status`, `assigned_runway_id`, `flight_status`, `gate_id` |
| **To downstream**   | `flight_number`, `aircraft_type`, `ground_clearance_type`, `ground_clearance_status`, `assigned_runway_id`, `flight_status`, `gate_id` |
| **From upstream**   | `flight_number`, `aircraft_type`, `ground_clearance_type`, `ground_clearance_status`, `assigned_runway_id`, `flight_status`, `gate_id` |
| **From downstream** | `flight_number`, `aircraft_type`, `ground_clearance_type`, `ground_clearance_status`, `assigned_runway_id`, `flight_status`, `gate_id` |

All four directions carry identical 7-field sets — the most symmetric full-context contract in the system.

#### Down-chain tools

```
["ground_traffic_controller", "TrackerAPI"]
```

---

### 5.2 ground_traffic_controller (LLM Agent — Second Tier)

A thin routing agent. It receives the clearance request from the orchestrator and passes it to `ground_clearance_agent`. Its instructions say only "report the returned values" and "use only your tools."

> Note: The `ground_traffic_controller` HOCON definition has no `parameters` block — only `function.description` and `instructions`. Unlike every other tool in the system, it accepts arguments implicitly through aaosa inquiry mode rather than a declared parameter schema. This means the LLM at this level has no schema guidance for what fields to expect.

#### Down-chain tools

```
["ground_clearance_agent"]
```

---

### 5.3 ground_clearance_agent (LLM Wrapper)

A thin LLM shell over `execute_ground_clearance`. Its only instruction is the standard aaosa loop. It passes all parameters through to the coded tool.

**Class resolved:** `AirlineTurnaround.aircraft_ground_traffic.aircraft_ground_traffic.execute_ground_clearance`

> Note: The previous documentation called this tool `ground_traffic_operator`. The actual HOCON name is `ground_clearance_agent` and the Python class is `execute_ground_clearance`.

---

### 5.4 execute_ground_clearance (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_traffic.aircraft_ground_traffic.execute_ground_clearance`

The only coded execution tool in this network (besides TrackerAPI). It loads two CSV reference files, validates the aircraft type and runway ID, then grants clearance based on `flight_status` keywords.

#### Constructor paths

| Attribute       | Default path                                                                                             |
|-----------------|----------------------------------------------------------------------------------------------------------|
| `aircraft_base` | `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_traffic_controller" / "aircraft_base.csv"` |
| `runway_base`   | `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_traffic_controller" / "runways_base.csv"`  |
| `log_path`      | `Path.cwd() / "test_debug" / "airlineturnaround.txt"`                                                    |

#### Required CSV schemas

**aircraft_base.csv** — required columns: `Aircraft_Model`, `Landing(m)`, `Takeoff(m)`

**runways_base.csv** — required columns: `unit_id`, `length(m)`

If either file is missing or a required column is absent, the tool returns an error string immediately.

#### Input parameters

| Parameter                 | Type   | Required | Source priority     |
|---------------------------|--------|:--------:|---------------------|
| `aircraft_type`           | string |    ✅     | `args` → `sly_data` |
| `flight_number`           | string |    ✅     | `args` → `sly_data` |
| `flight_status`           | string |    ✅     | `args` → `sly_data` |
| `assigned_runway_id`      | string |    ✅     | `args` → `sly_data` |
| `gate_id`                 | string |    ✅     | `args` → `sly_data` |
| `ground_clearance_type`   | string |    ✅     | `args` → `sly_data` |
| `ground_clearance_status` | string |    ❌     | `args` → `sly_data` |

All inputs are written to sly_data immediately on entry (unconditional persist), before any validation.

#### Clearance decision logic

Clearance is granted based on `flight_status` keyword matching only:

| `flight_status` contains | `ground_clearance_type` set to | `ground_clearance_status` | `flight_status` updated to |
|--------------------------|--------------------------------|---------------------------|----------------------------|
| `'landed'`               | `CLEARANCE_TO_TAXI_IN`         | `GRANTED`                 | `TAXIING_IN`               |
| `'off blocks'`           | `CLEARANCE_TO_TAXI_OUT`        | `GRANTED`                 | `TAXIING_OUT`              |
| neither                  | (no change)                    | (no change)               | (no change)                |

> Note: The runway CSVs are loaded and validated but **not used in the clearance decision**. The aircraft's landing/takeoff run requirements are loaded from `aircraft_base.csv` and the runway lengths from `runways_base.csv`, but no comparison between them takes place. Clearance is always `GRANTED` when `flight_status` matches, regardless of runway length compatibility. This appears to be incomplete runway validation logic.

#### Runway ID validation

`assigned_runway_id` is validated against the regex `^(?:[0-3]?\d| [0-2]\d |3[0-6])[LRC]?$` (accepts runway numbers 01–36 with optional L/R/C suffix). If it does not match, `build_clearance()` raises `ValueError` and the tool returns an error string.

#### Return value

On success, returns a `ClearanceDict` (Python `TypedDict`):

```python
{
    "flight_status": str,           # uppercased, e.g. "TAXIING_IN"
    "flight_number": str,           # uppercased
    "aircraft_type": str,           # uppercased
    "ground_clearance_type": str,   # e.g. "CLEARANCE_TO_TAXI_IN"
    "ground_clearance_status": str, # e.g. "GRANTED"
    "assigned_runway_id": str,      # uppercased, validated
    "clearance_report": str         # log line(s)
}
```

#### Valid `ground_clearance_type` values (enforced by `build_clearance`)

`CLEARANCE_TO_TAXI_IN`, `TAXIING_IN`, `TAXI_IN`, `CLEARANCE_TO_TAXI_OUT`, `TAXIING_OUT`, `TAXI_OUT`, `HOLD`, `DENY`

> Note: The `GroundClearanceType` Literal on line 18 defines a different set (`CLEARED_FOR_TAXI`, `CLEARED_FOR_TAXI_IN`, etc.) from the validation list in `build_clearance` (line 63). The type annotation and the runtime check are inconsistent.

#### sly_data writes

Only `flight_status` is written to sly_data at the end of the operator. The commented-out `sly_data.update(...)` block (lines 257–268) and the commented-out individual writes (lines 280–283) show that `ground_clearance_type` and `ground_clearance_status` were intentionally disabled from sly_data propagation pending validation. Currently only `flight_status` flows back via sly_data.

#### Class-level `print` statements (lines 101–107)

`execute_ground_clearance` has `print()` statements at class body level (outside any method). These execute at **class definition time** — when the Python module is imported, not when the tool is invoked. This means the `EXECUTE GROUND CLEARANCE` banner prints once at startup, not per invocation.

#### `clearance_report` tuple bug (line 247)

```python
clearance_report = line1 + line2,   # trailing comma creates a tuple!
```

`clearance_report` is assigned as a **tuple** (`(str,)`) rather than a string. `build_clearance` accepts it without error since it only stores the value, but downstream consumers expecting a string will receive a one-element tuple.

---

### 5.5 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_traffic.aircraft_ground_traffic.TrackerAPI`

Manages shared turnaround state. Called in step 2 to read/store all available parameters.

#### Configuration

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `flight_status`, `flight_number`, `gate_id`, `ground_clearance_status`, `ground_clearance_type`, `assigned_runway_id`, `assigned_runway_id` *(duplicate)*, `assigned_runway_length`

**Return fields:**
`aircraft_type`, `flight_status`, `flight_number`, `gate_id`, `ground_clearance_status`, `ground_clearance_type`, `assigned_runway_id`, `assigned_runway_id` *(duplicate)*, `assigned_runway_length`

> Note: `assigned_runway_id` appears **twice** in both `FLIGHT_TURNAROUND_TRACKED_FIELDS` and `FLIGHT_TURNAROUND_RETURN_FIELDS`. The duplicate has no runtime impact (the same value would be returned twice in the tuple) but should be deduplicated.

> Note: `assigned_runway_length` is tracked and returned but is not written to sly_data by `execute_ground_clearance` or the orchestrator. It will always be `None` unless provided in args by an upstream caller.

> Note: Tracked fields and return fields are identical — the same pattern as `aircraft_gate_selection` and the setup networks.

> Note: `_log_data_summary` in this TrackerAPI contains `print()` statements alongside `logger.info()` calls (lines 568–575). All other TrackerAPI implementations use only `logger.info()`. This results in additional stdout output on every TrackerAPI invocation.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

This network has no external tool dependencies via the registry. The `registries/aaosa_basic.hocon` include is present but no external networks are called.

---

## 7. Sample Queries

```
# Taxi-in clearance
"Provide flight AF84 the ground clearance to taxi in toward gate A1.
The aircraft is a B747 and has landed on runway 28L."

# Alternative phrasing (also triggers taxi-in)
"Flight AF84 has landed on runway 28L. The aircraft is a B747 and it has been assigned to gate A1."
```

---

## 8. Example Execution Trace

**Input:**
> "Provide flight AF84 the ground clearance to taxi in toward gate A1. The aircraft is a B747 and has landed on runway 28L."

**Execution steps:**

1. `TrackerAPI` called (step 2) — stores `flight_number=AF84`, `aircraft_type=B747`, `flight_status=landed`, `gate_id=A1`, `assigned_runway_id=28L`, `ground_clearance_type=taxi in`
2. Flight status check: `landed` ✅ (step 5)
3. `ground_traffic_controller` called → `ground_clearance_agent` called → `execute_ground_clearance` called
4. CSVs loaded and validated. `flight_status` contains `'landed'` → `CLEARANCE_TO_TAXI_IN` / `GRANTED` / `TAXIING_IN`
5. `flight_status=TAXIING_IN` written to sly_data; `ClearanceDict` returned
6. Summary displayed

**Output:**

```
***************************************
* Summary of ground traffic clearance *
***************************************
** flight number **:          AF84
** aircraft type **:          B747
** flight status **:          TAXIING_IN
** gate id **:                A1
** assigned runway id **:     28L
** ground clearance type **:  CLEARANCE_TO_TAXI_IN
** ground clearance status **: GRANTED
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "TAXIING_IN",
  "gate_id": "A1",
  "assigned_runway_id": "28L",
  "ground_clearance_type": "CLEARANCE_TO_TAXI_IN",
  "ground_clearance_status": "GRANTED"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue                                                                             | Location                                      | Severity | Notes                                                                                                                                                                                                                 |
|-----------------------------------------------------------------------------------|-----------------------------------------------|:--------:|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **Runway CSV data loaded but not used for clearance decision**                    | `aircraft_ground_traffic.py` lines 184–193    | **High** | `aircraft_base.csv` and `runways_base.csv` are loaded and column-validated but the aircraft run requirements are never compared against runway lengths. Clearance is always `GRANTED` on `flight_status` match alone. |
| Class-level `print` statements in `execute_ground_clearance`                      | `aircraft_ground_traffic.py` lines 101–107    |  Medium  | `print()` at class body level executes at import time, not at invocation. Banner prints once when the module loads.                                                                                                   |
| Duplicate `assigned_runway_id` in tracked/return fields                           | `aircraft_ground_traffic.py` lines 613, 626   |   Low    | Listed twice in both `FLIGHT_TURNAROUND_TRACKED_FIELDS` and `RETURN_FIELDS`. Deduplicate.                                                                                                                             |
| `off blocks` logic set twice (double assignment)                                  | `aircraft_ground_traffic.py` lines 218–228    |   Low    | `ground_clearance_type` and `ground_clearance_status` are assigned to the same values twice (lines 218–219 and 227–228) before lowercasing. Redundant.                                                                |
| Interactive user-wait loop in step 3                                              | `aircraft_ground_traffic.hocon` lines 116–118 |   Low    | If `ground_clearance_type` is None, the agent waits for user response — same risk as `aircraft_engines_stop` in automated contexts.                                                                                   |
| `TrackerAPI._log_data_summary` has `print()` calls                                | `aircraft_ground_traffic.py` lines 568–575    |   Low    | Produces extra stdout output not present in other TrackerAPI implementations.                                                                                                                                         |

---

## 10. Extensibility Guidance

- **Complete the runway validation logic:** Compare aircraft landing/takeoff run requirements from `aircraft_base.csv` against runway lengths from `runways_base.csv` to actually select or validate the assigned runway, rather than always granting clearance on status alone
- **Uncomment the sly_data writes** for `ground_clearance_type` and `ground_clearance_status` (lines 280–283) once the validation that "the update command above works fine" is completed
- Fix the `clearance_report` tuple bug (remove trailing comma on line 247)
- Align the `GroundClearanceType` Literal definition with the `build_clearance` validation list
- Deduplicate `assigned_runway_id` in `FLIGHT_TURNAROUND_TRACKED_FIELDS` and `RETURN_FIELDS`
- Move the class-level `print()` statements inside `invoke()` or remove them
- Add a `parameters` schema to `ground_traffic_controller` for explicit field validation
- Consider collapsing `ground_traffic_controller` + `ground_clearance_agent` into a single step; the two-step routing adds complexity without current functional differentiation

---

## 11. Compliance Notice

This network models simulated aircraft surface movement and ground traffic workflows, and is intended for software prototyping and workflow automation development. It is not certified for real-world air traffic control or aviation safety-critical systems.
