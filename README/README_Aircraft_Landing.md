# Aircraft Landing
## Agentic AI Network – README

> **Configuration file:** `aircraft_landing.hocon`
> **Implementation file:** `aircraft_landing.py`
> **Data files:** `aircraft_traffic_controller/aircraft_base.csv`, `aircraft_traffic_controller/runways_base.csv` (paths declared but not used)
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Coordinate aircraft landing during approach, obtaining landing clearance via an external traffic controller, then executing the actual landing to transition flight status to `'landed'`.

---

## 1. Overview

`aircraft_landing` is a multi-agent network that orchestrates the aircraft landing sequence. It contains the most layered agent chain in the system — three LLM agents plus a coded execution class — and several significant code-level bugs, most notably a broken `sly_data` fallback pattern that affects every parameter in the coded tool.

The network combines:

- `flight_operation_agent` — LLM orchestrator; entry point, coordinates the full landing workflow
- `aircraft_pilot` — LLM agent; validates clearance before instructing landing
- `aircraft_landing_agent` — LLM wrapper name for the coded tool `execute_aircraft_landing`
- `execute_aircraft_landing` — coded tool; sets `flight_status = 'landed'` when clearance is confirmed
- `TrackerAPI` — coded tool; shared state manager
- One external tool reference (`/AirlineTurnaround/aircraft_traffic_controller`) resolved from `registries/aaosa_basic.hocon`

> **Important note on previous documentation:** The old doc described a flat two-component architecture (`aircraft_landing_agent` → `landing_operator`). The actual network has three LLM agents, a distinct class name (`execute_aircraft_landing`), and a fundamentally different parameter model — `clearance_type` and `assigned_runway_length` replace `landing_status`, `aircraft_direction`, and `assigned_runway`. The fields `landing_status`, `clearance_pending`, `cleared_to_land`, `clearance_denied` do not exist in the implementation.

---

## 2. Repository Structure

```
aircraft_landing.hocon              # Agent network configuration
aircraft_landing.py                 # Coded tool implementations (execute_aircraft_landing, TrackerAPI)
coded_tools/AirlineTurnaround/aircraft_traffic_controller/aircraft_base.csv   # Declared but not used
coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv    # Declared but not used
registries/aaosa_basic.hocon        # Shared registry (/AirlineTurnaround/aircraft_traffic_controller)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
flight_operation_agent  (LLM Orchestrator — entry point)
   │
   ├── TrackerAPI                                          (Coded tool: read/write state via sly_data)
   │
   ├── /AirlineTurnaround/aircraft_traffic_controller      (External — request landing clearance)
   │
   └── aircraft_pilot  (LLM Agent — clearance validator)
          │
          └── aircraft_landing_agent  (LLM name for coded tool execute_aircraft_landing)
                 │
                 └── execute_aircraft_landing  (Coded tool: sets flight_status = 'landed')
```

> Note: `aircraft_pilot`'s tools list is `["aircraft_landing_agent"]`, and `aircraft_landing_agent` in the HOCON maps to the coded class `execute_aircraft_landing`. This is a clean delegation chain, not a circular reference.

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

### 5.1 flight_operation_agent (LLM Orchestrator — Entry Point)

The top-level agent. It resolves all parameters, requests clearance from the external traffic controller if needed, then delegates to `aircraft_pilot` to execute the landing.

> Note: The true entry point is `flight_operation_agent`, not `aircraft_landing_agent` as the previous documentation stated. `aircraft_landing_agent` in this network is the HOCON name for the coded tool `execute_aircraft_landing`.

#### Input parameters

| Parameter | Type | Required | Description |
|---|---|:---:|---|
| `aircraft_direction` | string | ✅ | Direction: `incoming` or `departing` |
| `flight_number` | string | ✅ | Flight identifier |
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `flight_status` | string | ❌ | e.g. `approach`, `cleared for landing` |
| `clearance_type` | string | ❌ | Expected: contains `cleared for landing` |
| `assigned_runway_id` | string | ❌ | Assigned runway designator |
| `assigned_runway_length` | string | ❌ | Length of assigned runway in meters |
| `landing_summary` | string | ❌ | Landing outcome summary |

#### Orchestration flow

The instructions use older numbered-prose style:

1. Read all parameters from the inquiry.
2. Call `TrackerAPI` — store all available parameters.
3. If `flight_status` is `None`, or `clearance_type` is not `"cleared for landing"`, or `assigned_runway_id` is `None`, or `assigned_runway_length` is `None` → call `/AirlineTurnaround/aircraft_traffic_controller`. Wait. Return to step 2.
4. If aircraft is cleared for landing (clearance_type contains `'clear'` AND `'landing'`) and both runway fields are set → **land the aircraft.** (No explicit tool name given — relies on LLM to choose between `aircraft_pilot` and `aircraft_landing_agent`)
5. Call `TrackerAPI` — store `flight_number`, `aircraft_type`, `flight_status`.
6. Return landing summary.

> Note: Step 4 says "Land the aircraft" without naming which tool to call. The agent must autonomously select from its toolset. Given that `aircraft_pilot` is a role-based agent with clearance validation logic, it is the intended target, but the instruction is ambiguous.

> Note: Step 3 creates a loop back to step 2 with no maximum retry count. If `aircraft_traffic_controller` repeatedly fails to supply clearance, the agent will loop indefinitely.

#### sly_data contract

| Direction | Parameters |
|---|---|
| **To upstream** | `clearance_type`, `flight_status`, `flight_number`, `aircraft_type`, `assigned_runway_id`, `assigned_runway_length` |
| **To downstream** | same 6 fields |
| **From upstream** | same 6 fields |
| **From downstream** | same 6 fields |

> Note: All four directions carry the same 6-field set. `aircraft_direction` and `landing_summary` are in the agent parameter schema but absent from all sly_data allow blocks.

#### Down-chain tools

```
["/AirlineTurnaround/aircraft_traffic_controller", "aircraft_pilot", "TrackerAPI"]
```

---

### 5.2 aircraft_pilot (LLM Agent — Clearance Validator)

A role-based agent that enforces the clearance-before-landing safety policy. Its instructions state it must never land without clearance and it reports `flight_status`.

#### Instructions (verbatim behaviour rules)

- "You must receive clearance for landing before landing."
- "You should never land the aircraft without a landing clearance."
- "You report the flight status of the aircraft as flight_status."
- Uses only its own tools to execute tasks.

#### Down-chain tools

```
["aircraft_landing_agent"]
```

`aircraft_landing_agent` in this context resolves to `execute_aircraft_landing` — the coded tool.

---

### 5.3 aircraft_landing_agent / execute_aircraft_landing (Coded Tool)

**HOCON name:** `aircraft_landing_agent`
**Python class:** `AirlineTurnaround.aircraft_landing.aircraft_landing.execute_aircraft_landing`

> Note: The HOCON wraps `execute_aircraft_landing` under the name `aircraft_landing_agent`. This naming creates potential confusion with `flight_operation_agent` (the true orchestrator), which the previous documentation called `aircraft_landing_agent`. The coded class name `execute_aircraft_landing` is the authoritative identifier.

The coded tool confirms landing clearance conditions and, if met, sets `flight_status = 'landed'` in sly_data. It also loads two CSV files (aircraft_base and runway_base) but never uses them — the paths are assigned to local variables and passed nowhere.

#### Input parameters (args-first, broken sly_data fallback — see Known Issues)

| Parameter | Type | Source |
|---|---|---|
| `flight_status` | string | `args` (sly_data fallback broken) |
| `aircraft_type` | string | `args` (sly_data fallback broken) |
| `flight_number` | string | `args` (sly_data fallback broken) |
| `aircraft_direction` | string | `args` (sly_data fallback broken) |
| `clearance_type` | string | `args` (sly_data fallback broken) |
| `assigned_runway_id` | string | `args` (sly_data fallback broken) |
| `assigned_runway_length` | string | `args` (sly_data fallback broken) |

#### Landing condition

```python
if clearance_type and flight_status:
    if (('clear' in clearance_type OR 'land' in clearance_type)
        AND (flight_status is None OR 'approach' in flight_status)):
        flight_status = 'landed'
```

Note the condition uses `|` (bitwise OR) not `or` (logical OR), and `&` (bitwise AND) not `and`. For string boolean expressions this works in Python but is non-standard and fragile.

| Condition | Accepted values |
|---|---|
| `clearance_type` | Contains `'clear'` OR contains `'land'` |
| `flight_status` | `None` OR contains `'approach'` |

> Note: `clearance_type` containing `'land'` would accept `"no landing"`, `"Iceland"`, or any string with the substring. Similarly `'clear'` accepts `"not cleared"`. Exact matching is safer.

> Note: The `flight_status is None` branch inside the `if clearance_type and flight_status:` block is unreachable — if `flight_status` were `None`, the outer `if` would be `False` and the inner block would never execute.

#### Output

- Writes `flight_status = 'landed'` into `sly_data` on success
- Returns `flight_status` string (`'landed'` or the original value if condition not met)
- Appends a log line to `test_debug/airlineturnaround.txt` on success

> Note: The operator returns `flight_status` (a string), not a structured dict. The old documentation described a `ClearanceDict` return — this does not exist in this network.

---

### 5.4 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_landing.aircraft_landing.TrackerAPI`

Standard sly_data-first implementation. Called in step 2 to store available parameters, and again in step 5 after landing to persist `flight_status`.

#### Configuration

**Tracked fields:**
`aircraft_type`, `assigned_runway_id`, `assigned_runway_length`, `clearance_type`, `flight_number`, `flight_status`

**Return fields:** Identical to tracked fields (all 6 returned).

> Note: TrackerAPI tracked = return fields, consistent with the gate selection and setup networks.

> Note: The HOCON TrackerAPI definition has `"required": {}` (a JSON object) instead of `"required": []` (an empty array). This is a syntax error in strict HOCON/JSON-schema parsers and may cause schema validation failures at runtime.

> Note: The HOCON TrackerAPI parameter uses `"traffic_direction"` (line 333) rather than `"aircraft_direction"`. This field name mismatch means the LLM will see `traffic_direction` in the schema description but the network uses `aircraft_direction` throughout.

---

## 6. External Tool Dependencies

| Tool path | Purpose | Condition triggering call |
|---|---|---|
| `/AirlineTurnaround/aircraft_traffic_controller` | Request landing clearance, receive `clearance_type`, `assigned_runway_id`, `assigned_runway_length` | Step 3 — when any of those three values is missing |

---

## 7. Sample Queries

```
# Full information provided
"Land flight AF84 that is on approach and has been cleared for landing on runway 19L
that has a length of 2350 meters. It is a B747."

# Minimal — agent will request clearance from traffic controller
"Land the incoming flight AF84. It is a B747."
```

---

## 8. Example Execution Trace

**Input:**
> "Land flight AF84 that is on approach and has been cleared for landing on runway 19L that has a length of 2350 meters. It is a B747."

**Execution steps:**

1. `TrackerAPI` called (step 2) — stores: `flight_number=AF84`, `aircraft_type=B747`, `flight_status=approach`, `clearance_type=cleared for landing`, `assigned_runway_id=19L`, `assigned_runway_length=2350`
2. All required values present ✅ (step 3 skipped)
3. `aircraft_pilot` called (step 4) — validates clearance present → calls `aircraft_landing_agent` (`execute_aircraft_landing`)
4. `execute_aircraft_landing`: clearance condition met → `flight_status = 'landed'`
5. `TrackerAPI` called (step 5) — persists updated `flight_status`
6. Summary returned

**Output:**

```
*******************************
* Summary of aircraft landing *
*******************************
** flight number **:          AF84
** aircraft type **:          B747
** flight status **:          landed
** clearance type **:         cleared for landing
** assigned runway id **:     19L
** assigned runway length **:  2350
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| **Broken sly_data fallback — variable used as key** | `aircraft_landing.py` lines 61, 66, 69, 72, 75, 78, 81 | **Critical** | `sly_data.get(flight_status, None)` passes the variable's *value* (e.g. `None`) as the key, not the string `"flight_status"`. When `flight_status is None`, `sly_data.get(None, None)` always returns `None`. The sly_data fallback is completely non-functional for all 7 parameters. Fix: `sly_data.get("flight_status", None)` (quoted string). |
| **`"required": {}` in TrackerAPI HOCON** | `aircraft_landing.hocon` line 350 | **High** | Object `{}` instead of array `[]`. Strict parsers will reject this as a JSON Schema error. Fix: `"required": []`. |
| Agent hierarchy name confusion | `aircraft_landing.hocon` lines 90, 271 | Medium | `aircraft_landing_agent` in the HOCON is a coded-tool wrapper, not the orchestrator. The true entry point is `flight_operation_agent`. Previous documentation called the orchestrator `aircraft_landing_agent`, which matches the coded wrapper's name — not the orchestrator. |
| CSV files declared but never used | `aircraft_landing.py` lines 38–39 | Medium | `aircraft_base` and `runway_base` paths are assigned but never read. The operator makes no runway compatibility check. |
| `'land' in clearance_type` is overly broad | `aircraft_landing.py` line 97 | Medium | Matches `"no landing"`, `"Iceland"`, etc. Use exact matching or require both `'clear'` and `'landing'` as co-present substrings. |
| `flight_status is None` branch unreachable | `aircraft_landing.py` line 97 | Low | `if clearance_type and flight_status:` (line 93) is `False` when `flight_status is None`, so the inner `or (flight_status is None)` on line 97 is never reached. |
| Step 4 does not name which tool to call | `aircraft_landing.hocon` line 155–156 | Low | "Land the aircraft" — ambiguous between `aircraft_pilot` and `aircraft_landing_agent`. LLM must autonomously select. |
| Loop in step 3 has no retry limit | `aircraft_landing.hocon` step 3 | Low | Returns to step 2 indefinitely if `aircraft_traffic_controller` fails to supply clearance. |
| `aircraft_direction` absent from sly_data allow blocks | `aircraft_landing.hocon` | Low | Present in agent parameters but not propagated in any of the four sly_data directions. |
| `traffic_direction` vs `aircraft_direction` mismatch | `aircraft_landing.hocon` line 333 | Low | TrackerAPI HOCON parameter uses `traffic_direction`; the network uses `aircraft_direction`. |
| Unix-only imports not used | `aircraft_landing.py` lines 10, 12 | Low | `fcntl` (Unix-only, will fail on Windows) and `asyncio` are imported but never called. |
| Operator returns string, not dict | `aircraft_landing.py` line 113 | Low | Returns `flight_status` (string). Previous documentation described a structured `ClearanceDict` return — this does not exist. |
| `random`, `os`, `platform` imported but unused | `aircraft_landing.py` lines 7–9 | Low | Dead imports. |

---

## 10. Key Differences from Prior Documentation

| Aspect | Old documentation | Actual implementation |
|---|---|---|
| Top-level agent name | `aircraft_landing_agent` | `flight_operation_agent` |
| Number of LLM agents | 1 | 3 (`flight_operation_agent`, `aircraft_pilot`, `aircraft_landing_agent`) |
| Coded tool name | `landing_operator` | `execute_aircraft_landing` |
| Primary prerequisite | `aircraft_direction = incoming` | `clearance_type` contains `'clear'` or `'land'`, `flight_status` contains `'approach'` |
| Fields `landing_status`, `clearance_pending`, etc. | ✅ Present | ❌ Do not exist |
| Output | `ClearanceDict` (structured) | `flight_status` string only |
| Runway CSV usage | Yes (selection logic) | Paths declared, never read |

---

## 11. Extensibility Guidance

- **Fix the sly_data fallback immediately** — change all seven `sly_data.get(variable, None)` calls to `sly_data.get("field_name", None)` with quoted string keys
- Fix `"required": {}` to `"required": []` in the TrackerAPI HOCON definition
- Remove unused imports: `fcntl`, `asyncio`, `random`, `os`, `platform`
- Make the CSV paths functional — read `aircraft_base.csv` to validate that the assigned runway length meets the aircraft's landing run requirement
- Replace the `'land' in clearance_type` substring check with an exact-match or combined-substring check
- Name the landing tool explicitly in step 4 instructions (`"Call aircraft_pilot to land the aircraft"`)
- Add a maximum retry count to the step 3 clearance request loop

---

## 12. Compliance Notice

This network models simulated aircraft landing workflows and is intended for software prototyping and workflow automation development. It is not certified for real-world air traffic control or aviation safety-critical systems.
