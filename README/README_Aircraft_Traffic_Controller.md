# Aircraft Traffic Controller
## Agentic AI Network – README

> **Configuration file:** `aircraft_traffic_controller.hocon`
> **Implementation file:** `aircraft_traffic_controller.py`
> **Data files:** `aircraft_base.csv` (aircraft run requirements), `runways_base.csv` (runway lengths)
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Issue landing or takeoff clearances for aircraft, selecting the optimal runway based on aircraft-specific run requirements from reference CSV data.

---

## 1. Overview

`aircraft_traffic_controller` is the clearance-issuing network in the AirlineTurnaround system. Unlike most other networks, its core value is **data-driven runway selection** — it reads actual aircraft run requirements and runway lengths from CSV files to make a deterministic runway assignment decision. It is called by `aircraft_landing`, `aircraft_taxiing` (STEP 2 via `aircraft_ground_traffic`), and any other network that needs landing or takeoff clearance.

The network combines:

- `air_traffic_orchestrator` — LLM entry point; validates parameters, coordinates TrackerAPI, delegates to the controller
- `aircraft_traffic_controller` — LLM routing agent; delegates all execution to the coded tool
- `air_clearance_agent` — HOCON name for the coded class `execute_air_clearance`
- `execute_air_clearance` — the actual clearance logic; reads CSVs, selects runway, returns a typed `ClearanceDict`
- `TrackerAPI` — coded state manager
- `tracker_aircraft_traffic_controller` — an older-style TrackerAPI class in the Python file, **not registered in the HOCON**

The coded class path uses the `coded_tools.` prefix — the same unusual prefix used by `aircraft_gate_selection`, distinguishing this network from those using the `AirlineTurnaround.` root prefix.

> **Important note on prior documentation:** The old doc described the model as `claude-haiku-4-5-20251001`. The actual deployed model is `gpt-5.4-mini`. The old doc also missed the `commondefs` absence, the `coded_tools.` class prefix, the `tracker_aircraft_traffic_controller` unregistered class, and the runway selection algorithm details.

---

## 2. Repository Structure

```
aircraft_traffic_controller.hocon                         # Agent network configuration
aircraft_traffic_controller.py                            # Coded tool implementations
coded_tools/AirlineTurnaround/aircraft_traffic_controller/aircraft_base.csv    # Aircraft run requirements
coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv     # Runway inventory
registries/aaosa_basic.hocon                              # Provides commondefs (aaosa_instructions, aaosa_command)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
air_traffic_orchestrator  (LLM Agent — entry point)
   │
   ├── TrackerAPI                    (Coded tool: read/write state via sly_data)
   │
   └── aircraft_traffic_controller   (LLM Agent — clearance router)
          │
          └── air_clearance_agent   (HOCON name for execute_air_clearance)
                 │
                 └── execute_air_clearance  (Coded tool: CSV-based runway selection + clearance issuance)
```

### Design principles

- **Deterministic runway selection:** All safety-critical logic is in `execute_air_clearance`. No runway assignment occurs inside LLM prompts.
- **Data-driven decisions:** Run requirements read from `aircraft_base.csv`; runway lengths from `runways_base.csv`.
- **Direction-aware selection:** Incoming → shortest runway that meets landing requirement. Departing → longest runway that meets takeoff requirement.
- **Typed output contract:** `execute_air_clearance` returns a validated `ClearanceDict` TypedDict (or error string).

---

## 4. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

> Note: The HOCON contains a commented-out block showing `"model_name": "gemini-3-flash"` was tested previously (lines 14–17).

> Note: The `commondefs` block is absent from this HOCON — no `instructions_prefix`, `aaosa_instructions`, or `aaosa_command` are defined locally. Both `air_traffic_orchestrator` and `aircraft_traffic_controller` instructions reference `${aaosa_instructions}` (line 70, 202). These substitutions must be provided by `registries/aaosa_basic.hocon` for the instructions to be complete.

---

## 5. Components

### 5.1 air_traffic_orchestrator (LLM Orchestrator — Entry Point)

Validates the three required inputs, reads state from TrackerAPI, delegates to `aircraft_traffic_controller`, then logs state again and returns the clearance summary.

> Note: The HOCON tool name is `air_traffic_orchestrator`. The previous documentation used `Air Traffic Orchestrator` as a label but did not call it by the runtime HOCON name.

#### Input parameters

| Parameter                | Type   | Required | Description                          |
|--------------------------|--------|:--------:|--------------------------------------|
| `flight_number`          | string |    ✅     | Flight identifier                    |
| `aircraft_type`          | string |    ✅     | Aircraft model (e.g. `B747`, `A320`) |
| `aircraft_direction`     | string |    ✅     | `incoming` or `departing`            |
| `flight_status`          | string |    ❌     | Set by `execute_air_clearance`       |
| `clearance_type`         | string |    ❌     | Set by `execute_air_clearance`       |
| `assigned_runway_id`     | string |    ❌     | Set by `execute_air_clearance`       |
| `assigned_runway_length` | string |    ❌     | Set by `execute_air_clearance`       |
| `clearance_summary`      | dict   |    ❌     | Final summary                        |

> Note: `clearance_summary` has type `"dict"` in the HOCON schema (line 104). JSON Schema does not have a `"dict"` type — it should be `"object"`. This may cause schema validation warnings.

#### Orchestration flow

1. Extract `flight_number`, `aircraft_type`, `aircraft_direction` from the inquiry.
2. Call `TrackerAPI` — store all available parameters.
3. If any of the three required fields is `None` → ask user to provide.
4. All three present → call `aircraft_traffic_controller`.
5. Call `TrackerAPI` again — store all updated parameters.
6. Return clearance summary.

> Note: Step 4 says "call aircraft_traffic_controller to request clearance for landing" — the instruction hardcodes "landing" even though the network also handles departing traffic. A minor wording issue.

> Note: Step 3 creates a user-facing interactive wait loop — the same automated-context stall risk present in `aircraft_engines_stop` and others.

#### sly_data contract

| Direction         | Parameters                                                                                                                                |
|-------------------|-------------------------------------------------------------------------------------------------------------------------------------------|
| **From upstream** | `flight_number`, `aircraft_type`, `aircraft_direction`                                                                                    |
| **To downstream** | `flight_number`, `aircraft_type`, `aircraft_direction`, `flight_status`, `clearance_type`, `assigned_runway_id`, `runway_length`          |
| **To upstream**   | `flight_number`, `aircraft_type`, `aircraft_direction`, `flight_status`, `clearance_type`, `assigned_runway_id`, `assigned_runway_length` |

> Note: `to_downstream` uses `runway_length` (line 129) while `to_upstream` uses `assigned_runway_length` (line 141). These are different field names for the same value. Downstream networks should use `assigned_runway_length`.

#### Down-chain tools

```
["aircraft_traffic_controller", "TrackerAPI"]
```

---

### 5.2 aircraft_traffic_controller (LLM Agent — Router)

A thin routing agent that receives validated flight information and delegates to `air_clearance_agent`. Its instructions say "Return flight_status, clearance_type, assigned_runway_id, and assigned_runway_length."

#### Down-chain tools

```
["air_clearance_agent"]
```

---

### 5.3 air_clearance_agent / execute_air_clearance (Coded Tool)

**HOCON name:** `air_clearance_agent`  
**Python class:** `coded_tools.AirlineTurnaround.aircraft_traffic_controller.aircraft_traffic_controller.execute_air_clearance`

> Note: The class path uses the `coded_tools.` prefix, identical to `aircraft_gate_selection`'s `deplaning_path_selector` and `TrackerAPI`. All other coded tools in the system use `AirlineTurnaround.` as the root.

The core execution tool. It reads aircraft run requirements from `aircraft_base.csv` and runway lengths from `runways_base.csv`, selects the optimal runway, validates the result, writes clearance data into sly_data, and returns a typed `ClearanceDict`.

#### Constructor paths

| Attribute       | Default path                                                                                             |
|-----------------|----------------------------------------------------------------------------------------------------------|
| `aircraft_base` | `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_traffic_controller" / "aircraft_base.csv"` |
| `runway_base`   | `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_traffic_controller" / "runways_base.csv"`  |
| `log_path`      | `Path.cwd() / "test_debug" / "airlineturnaround.txt"`                                                    |

#### Input parameters (args-first, fall back to sly_data)

`aircraft_type`, `flight_number`, `aircraft_direction` — all required. All others are determined by the tool.

#### CSV data reference

**aircraft_base.csv** (7 aircraft types):

| Aircraft | Landing (m) | Takeoff (m) |
|----------|-------------|-------------|
| ATR72    | 1,210       | 1,410       |
| E175     | 1,259       | 1,261       |
| E190     | 1,280       | 1,463       |
| A320     | 1,500       | 2,100       |
| A330     | 1,750       | 2,200       |
| B737     | 1,372       | 2,300       |
| B747     | 1,500       | 3,000       |

**runways_base.csv** (4 runways at a simulated SFO-style airport):

| Runway | Length (m) | Availability |
|--------|------------|--------------|
| 28L    | 3,500      | yes          |
| 28R    | 3,650      | yes          |
| 19L    | 2,650      | yes          |
| 19R    | 2,350      | yes          |

> Note: `availability` and `readiness` columns exist in `runways_base.csv` but are not read by `execute_air_clearance`. All four runways are considered available unconditionally.

#### Runway selection algorithm

**Incoming (landing):**
1. Look up aircraft's `Landing(m)` from `aircraft_base.csv`
2. Filter runways where `length(m) >= Landing(m)`
3. Sort by length **ascending** — select the **shortest** qualifying runway (most conservative)

**Departing (takeoff):**
1. Look up aircraft's `Takeoff(m)` from `aircraft_base.csv`
2. Filter runways where `length(m) >= Takeoff(m)`
3. Sort by length **ascending** — select the **longest** qualifying runway (most runway available)

**Example — B747 incoming:**
- Landing requirement: 1,500 m
- Qualifying runways: 28L (3,500), 28R (3,650), 19L (2,650), 19R (2,350)
- Selected: **19R** (2,350 m — shortest qualifying)

**Example — B747 departing:**
- Takeoff requirement: 3,000 m
- Qualifying runways: 28L (3,500), 28R (3,650)
- Selected: **28R** (3,650 m — longest qualifying)

#### Clearance output

On success, `execute_air_clearance`:

1. Writes to sly_data: `clearance_type`, `assigned_runway_id`, `assigned_runway_length` (numeric), `flight_status`, `clearance_report`
2. Returns a `ClearanceDict`:

```python
{
    "flight_status": str,           # "APPROACH" (incoming) or "DEPARTING" (departing)
    "flight_number": str,           # uppercased
    "aircraft_type": str,           # uppercased
    "clearance_type": str,          # "CLEARED_FOR_LANDING" or "CLEARED_FOR_TAKEOFF"
    "assigned_runway_id": str,      # validated runway designator
    "assigned_runway_length": int,  # meters
}
```

`build_clearance()` validates: `clearance_type` must be one of `CLEARED_FOR_LANDING`, `CLEARED_FOR_TAKEOFF`, `HOLD`, `GO_AROUND`, `DENY`; `assigned_runway_id` must match `^(?:[0-3]?\d| [0-2]\d |3[0-6])[LRC]?$`; `assigned_runway_length` must be a positive integer.

#### `clearance_report` tuple bug (line 195)

```python
clearance_report = line1 + line2,   # trailing comma creates a tuple!
```

`clearance_report` is assigned as a tuple `(str,)` rather than a string. It is then written to sly_data on line 202 as `line1 + line2` (without the comma — the correct string), so the sly_data value is correct. But the local variable `clearance_report` is a tuple, which is also passed into `build_clearance()`. Since `build_clearance` does not reference `clearance_report` in its signature, this has no runtime impact on the returned dict — but the variable is inconsistent with its intended string type.

---

### 5.4 TrackerAPI (Coded Tool)

**Class:** `coded_tools.AirlineTurnaround.aircraft_traffic_controller.aircraft_traffic_controller.TrackerAPI`

Standard sly_data-first implementation. Called in step 2 before clearance and again in step 5 after clearance to persist state.

#### Configuration

**Tracked fields:**
`aircraft_direction`, `aircraft_type`, `assigned_runway_id`, `assigned_runway_length`, `clearance_type`, `flight_number`, `flight_status`

**Return fields:** Identical to tracked fields (all 7 returned).

> Note: `crew_exit_status` appears as an **unquoted property key** (`crew_exit_status: {...}`) in the HOCON TrackerAPI schema (line 317). Same syntax issue as `aircraft_inspection_maintenance` and `aircraft_lavatory_service`.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

### 5.5 tracker_aircraft_traffic_controller (Unregistered Class)

Lines 218–297 contain a fully active Python class `tracker_aircraft_traffic_controller` that is **not registered in the HOCON tools list**. It is an older-style args-first TrackerAPI — it reads `flight_status`, `clearance_type`, `assigned_runway_id`, `assigned_runway_length` from args (with sly_data fallback), writes them to sly_data, constructs a log message, and returns the message string.

This class predates the configuration-driven `TrackerAPI` and represents the original hand-written tracker for this network. It is reachable from Python import but not from the HOCON agent graph.

---

## 6. External Tool Dependencies

This network has no external tool dependencies via the registry — it is a leaf service called by other networks.

---

## 7. Sample Queries

```
# Landing clearance
"Incoming flight AF84, a B747, needs clearance for landing."

# Takeoff clearance
"Departing flight UA123, an A320, requests takeoff clearance."
```

---

## 8. Example Execution Trace

**Input:**
> "Incoming flight AF84, a B747, needs clearance for landing."

**Execution steps:**

1. `TrackerAPI` called — stores `flight_number=AF84`, `aircraft_type=B747`, `aircraft_direction=incoming`
2. `aircraft_traffic_controller` called → `air_clearance_agent` (`execute_air_clearance`) called
3. CSV lookup: B747 landing requirement = 1,500 m; shortest qualifying runway = 19R (2,350 m)
4. `clearance_type = CLEARED_FOR_LANDING`, `flight_status = APPROACH`
5. sly_data updated; `ClearanceDict` returned to controller
6. `TrackerAPI` called (step 5) — persists all clearance fields
7. Summary returned

**Output:**

```
*****************************************
* Summary of aircraft traffic clearance *
*****************************************
** aircraft direction **:       incoming
** flight number **:            AF84
** aircraft type **:            B747
** flight status **:            APPROACH
** clearance type **:           CLEARED_FOR_LANDING
** assigned runway id **:       19R
** assigned runway length **:   2350
** clearance report **:         [log line 1][log line 2]
```

**JSON equivalent:**

```json
{
  "aircraft_direction": "incoming",
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "APPROACH",
  "clearance_type": "CLEARED_FOR_LANDING",
  "assigned_runway_id": "19R",
  "assigned_runway_length": 2350
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue                                                                 | Location                                             | Severity | Notes                                                                                                                                                                        |
|-----------------------------------------------------------------------|------------------------------------------------------|:--------:|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `availability` and `readiness` columns in `runways_base.csv` not used | `execute_air_clearance` selection logic              |   Low    | All runways treated as available regardless of `availability` or `readiness` values. If any runway is unavailable, the selection logic would still include it.               |
| Module-level diagnostic `print()` statements                          | `aircraft_traffic_controller.py` lines 13–15         |   Low    | `sys.path`, `__file__`, `__package__` print at import time. Same issue seen in `aircraft_ground_servicing.py`.                                                               |

---

## 10. Runway Selection Summary Table

For all currently registered aircraft against the four available runways:

| Aircraft | Direction     | Min run (m) | Qualifying runways                                 | **Selected**      |
|----------|---------------|-------------|----------------------------------------------------|-------------------|
| ATR72    | Incoming      | 1,210       | 19R (2,350), 19L (2,650), 28L (3,500), 28R (3,650) | **19R**           |
| ATR72    | Departing     | 1,410       | 19R, 19L, 28L, 28R                                 | **28R** (longest) |
| E175     | Incoming      | 1,259       | 19R, 19L, 28L, 28R                                 | **19R**           |
| E190     | Incoming      | 1,280       | 19R, 19L, 28L, 28R                                 | **19R**           |
| A320     | Incoming      | 1,500       | 19R, 19L, 28L, 28R                                 | **19R**           |
| A320     | Departing     | 2,100       | 19L (2,650), 28L (3,500), 28R (3,650)              | **28R**           |
| A330     | Incoming      | 1,750       | 19R, 19L, 28L, 28R                                 | **19R**           |
| A330     | Departing     | 2,200       | 19L, 28L, 28R                                      | **28R**           |
| B737     | Incoming      | 1,372       | 19R, 19L, 28L, 28R                                 | **19R**           |
| B737     | Departing     | 2,300       | 19L, 28L, 28R                                      | **28R**           |
| **B747** | **Incoming**  | **1,500**   | **19R, 19L, 28L, 28R**                             | **19R**           |
| **B747** | **Departing** | **3,000**   | **28L (3,500), 28R (3,650)**                       | **28R**           |

> Note: All aircraft currently use `19R` for landing (2,350 m is sufficient for every aircraft in the CSV). For takeoffs, A320/A330/B737 can use 19L; B747 requires 28L or 28R. Aircraft with takeoff requirements above 3,650 m would return an error.

---

## 11. Extensibility Guidance

- Incorporate `availability` and `readiness` from `runways_base.csv` into runway selection to filter out unavailable runways
- Add more aircraft types to `aircraft_base.csv` as needed

---

## 12. Compliance Notice

This network models simulated ATC clearance workflows and is intended for software prototyping and workflow automation development. It is not certified for real-world air traffic control or aviation safety-critical systems.
