# Aircraft Inspection & Maintenance
## Agentic AI Network – README

> **Configuration file:** `aircraft_inspection_maintenance.hocon`
> **Implementation file:** `aircraft_inspection_maintenance.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Perform aircraft inspection and maintenance at the gate during turnaround, after verifying that passengers have disembarked, crew has exited, and baggage has been unloaded.

---

## 1. Overview

`aircraft_inspection_maintenance` is an agentic network that orchestrates post-flight inspection and maintenance activities for an aircraft in turnaround. It is part of the broader **AirlineTurnaround** agentic system and is called by `aircraft_ground_servicing` (Branch B).

The network combines:

- An LLM-based orchestration agent (`inspection_maintenance_agent`) that interprets intent and drives the workflow
- One coded execution tool (`inspection_maintenance_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_disembark`, `aircraft_crew_exit`, `aircraft_baggage_unload`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network's prerequisite model and orchestration structure closely mirror `aircraft_cabin_cleaning`, `aircraft_catering_loading`, and `aircraft_fueling` — all requiring the same three human-clearance gates before the service operator is called.

> **Important note on scope:** The previous documentation described separate `inspection_status`, `maintenance_status`, and `detected_defects` fields, along with complex defect tracking. The actual implementation uses a single consolidated `inspection_maintenance_status` field that returns `'completed'` when all three human-clearance prerequisites are met. No defect tracking logic exists.

---

## 2. Repository Structure

```
aircraft_inspection_maintenance.hocon    # Agent network configuration
aircraft_inspection_maintenance.py       # Coded tool implementations (inspection_maintenance_operator, TrackerAPI)
registries/aaosa_basic.hocon             # Shared registry (aircraft_disembark, aircraft_crew_exit, aircraft_baggage_unload)
```

---

## 3. System Architecture

```
User / Caller  (or aircraft_ground_servicing Branch B)
   │
   ▼
inspection_maintenance_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                                   (Coded tool: read/write turnaround state via sly_data)
   │
   ├── inspection_maintenance_operator              (Coded tool: perform inspection and maintenance)
   │
   ├── /AirlineTurnaround/aircraft_disembark        (External tool — if passengers not yet off)
   │
   ├── /AirlineTurnaround/aircraft_crew_exit        (External tool — if crew not yet off)
   │
   └── /AirlineTurnaround/aircraft_baggage_unload   (External tool — if baggage not yet unloaded)
```

### Design principles

- **Human-clearance prerequisite gating:** Inspection and maintenance only initiates once the cabin is cleared of passengers, crew, and baggage.
- **Active prerequisite resolution:** If any prerequisite is unmet, the agent calls the relevant external network (steps 4–6) and loops back to re-read state from TrackerAPI (step 2).
- **Single consolidated status:** The entire inspection and maintenance operation produces one output field: `inspection_maintenance_status = 'completed'`.
- **Tool-first execution:** The LLM orchestrates; all actions are performed by coded or external tools.

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

### 5.1 inspection_maintenance_agent (LLM Orchestrator)

The entry-point agent. It reads all available parameters, resolves human-clearance prerequisites by delegating to external networks as needed, calls the operator, persists the result, and returns the final summary.

> Note: The agent is named `inspection_maintenance_agent` in the HOCON. The previous documentation referred to it as `aircraft_inspection_maintenance_agent`.

#### Input parameters

| Parameter | Type | Required | Description |
|---|---|:---:|---|
| `flight_number` | string | ✅ | Flight identifier |
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `gate_id` | string | ✅ | Gate where the aircraft is parked |
| `flight_status` | string | ❌ | Flight status (expected: contains `on blocks`) |
| `passenger_disembarkation_status` | string | ❌ | Expected: contains `completed` |
| `crew_exit_status` | string | ❌ | Expected: contains `completed` or `exited` |
| `baggage_unload_status` | string | ❌ | Expected: contains `completed` or `unloaded` |
| `inspection_maintenance_status` | string | ❌ | Current or previous status |

> Note: The HOCON agent schema has a commented-out `required` array (line 131) that would have required all three clearance status fields. The active `required` array only requires `flight_number`, `aircraft_type`, and `gate_id`. The orchestrator instructions treat the clearance statuses as functionally required but the schema does not enforce this.

> Note: `crew_exit_status` appears as an **unquoted property key** in the agent, operator, and TrackerAPI HOCON schemas (`crew_exit_status: {...}` instead of `"crew_exit_status": {...}`). HOCON allows unquoted keys in some parsers but this is non-standard and may cause parse errors in strict implementations.

#### Orchestration flow

The instructions use older numbered-prose style (not `CRITICAL: sequential executor` / `STEP`):

1. Read: `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`.
2. Call `TrackerAPI` — store all available parameters.
3. If all three clearance statuses contain expected values (`completed`/`exited`/`unloaded`) → skip to step 7.
4. If `passenger_disembarkation_status` is not `'completed'` → call `/AirlineTurnaround/aircraft_disembark`. Return to step 2.
5. If `crew_exit_status` does not contain `'completed'` → call `/AirlineTurnaround/aircraft_crew_exit`. Return to step 2.
6. If `baggage_unload_status` does not contain `'completed'` or `'unloaded'` → call `/AirlineTurnaround/aircraft_baggage_unload`. Return to step 2.
7. All prerequisites met → call `inspection_maintenance_operator`. Save as `inspection_maintenance_status`.
8. Return summary.

> Note: Step 8 in the HOCON instructions includes a summary template that shows 8 fields including `inspection_maintenance_status`. The TrackerAPI call to persist this status is not mentioned between steps 7 and 8 — unlike `aircraft_cabin_cleaning` which has an explicit TrackerAPI write step after the operator. The status is written to sly_data by the operator directly, but a TrackerAPI persist call is missing from the instructions.

> Note: Steps 4–6 call external tools without explicit "stop if still unmet" guards (unlike `aircraft_disembark` which has fail-fast semantics). The orchestrator loops back to step 2 after each external call, which could cycle indefinitely if an external network fails without updating the status.

#### sly_data contract

| Direction | Parameters |
|---|---|
| **To upstream** | `inspection_maintenance_status` |
| **To downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |
| **From upstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |

> Note: `inspection_maintenance_status` propagates upstream only. It is absent from `to_downstream`, `from_upstream`, and `from_downstream`. Downstream networks cannot receive the inspection result via sly_data from this network.

#### Down-chain tools

```
["TrackerAPI", "inspection_maintenance_operator",
 "/AirlineTurnaround/aircraft_disembark",
 "/AirlineTurnaround/aircraft_crew_exit",
 "/AirlineTurnaround/aircraft_baggage_unload"]
```

---

### 5.2 inspection_maintenance_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_inspection_maintenance.aircraft_inspection_maintenance.inspection_maintenance_operator`

Performs the inspection and maintenance completion check. It validates all required parameters, evaluates the three human-clearance conditions, then sets `inspection_maintenance_status = 'completed'`, writes to `sly_data`, and appends a timestamped log entry.

> Note: The previous documentation described a `maintenance_operator` with defect tracking and multiple status fields. The actual operator is `inspection_maintenance_operator`, produces a single `'completed'` / `'pending'` status, and performs no actual inspection logic — it confirms prerequisites are met and returns a completion signal.

#### Input parameters

| Parameter | Type | Required | Source priority |
|---|---|:---:|---|
| `flight_number` | string | ✅ | `args` → `sly_data` |
| `aircraft_type` | string | ✅ | `args` → `sly_data` |
| `flight_status` | string | ✅ | `args` → `sly_data` |
| `gate_id` | string | ✅ | `args` → `sly_data` |
| `passenger_disembarkation_status` | string | ✅ | `args` → `sly_data` |
| `crew_exit_status` | string | ✅ | `args` → `sly_data` |
| `baggage_unload_status` | string | ✅ | `args` → `sly_data` |

#### Inspection logic

`inspection_maintenance_status` is set to `'completed'` when **all three** conditions are true (case-insensitive):

| Field | Accepted values |
|---|---|
| `passenger_disembarkation_status` | `completed`, `done` |
| `crew_exit_status` | `completed`, `exited` |
| `baggage_unload_status` | `completed`, `unloaded` |

If any condition fails, `inspection_maintenance_status` remains `'pending'` (the initial value). `sly_data` is not updated on failure.

#### Output

- Writes `inspection_maintenance_status = 'completed'` into `sly_data` on success
- Returns `inspection_maintenance_status` string (`'completed'` or `'pending'`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_inspection_maintenance.aircraft_inspection_maintenance.TrackerAPI`

Manages shared turnaround state. Called in step 2 to read and store all available parameters, and called again when prerequisite resolution networks return (before re-checking in step 3).

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

**Tracked fields:**
`aircraft_type`, `baggage_unload_status`, `crew_exit_status`, `flight_number`, `flight_status`, `gate_id`, `inspection_maintenance_status`, `passenger_disembarkation_status`

**Return fields:**
`passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `inspection_maintenance_status`

> Note: `gate_id` is tracked but **not returned**. TrackerAPI will persist `gate_id` into sly_data but will not echo it back in the return tuple.

> Note: The HOCON `TrackerAPI` schema exposes many additional fields beyond what Python tracks (`wheels_chocks_readiness_status`, `gpu_readiness_status`, `acu_connection_status`, `gpu_connection_status`, `engines_stop_status`, `jetbridge_connection_status`, `door_opening_status`) — all are wide-schema copy-paste artifacts not tracked by this network's Python config.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

These tools are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path | Purpose | Condition triggering call |
|---|---|---|
| `/AirlineTurnaround/aircraft_disembark` | Complete passenger disembarkation | `passenger_disembarkation_status` not `completed` (step 4) |
| `/AirlineTurnaround/aircraft_crew_exit` | Complete crew exit | `crew_exit_status` not `completed`/`exited` (step 5) |
| `/AirlineTurnaround/aircraft_baggage_unload` | Complete baggage unloading | `baggage_unload_status` not `completed`/`unloaded` (step 6) |

---

## 7. Sample Queries

```
# All prerequisites already confirmed
"The B747 aircraft of flight AF84 is on blocks at gate A1.
Baggages have been unloaded. All passengers have disembarked.
The crew has exited the aircraft. Perform inspection and maintenance."

# Prerequisites not yet confirmed — agent will resolve them
"The B747 aircraft of flight AF84 is on blocks at gate A1.
Perform inspection and maintenance."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. Baggages have been unloaded. All passengers have disembarked. The crew has exited the aircraft. Perform inspection and maintenance."

**Execution steps:**

1. `TrackerAPI` called (step 2) — stores: `flight_status=on blocks`, `passenger_disembarkation_status=completed`, `crew_exit_status=exited`, `baggage_unload_status=completed`
2. All prerequisite check: passengers ✅, crew ✅, baggage ✅ (step 3 → skip to step 7)
3. `inspection_maintenance_operator` called — returns `inspection_maintenance_status=completed`
4. Summary returned (step 8)

**Output:**

```
**********************************************
* Summary of aircraft inspection maintenance *
**********************************************
** inspection maintenance summary **:
** flight number **:                        AF84
** aircraft type **:                        B747
** gate id **:                              A1
** flight status **:                        on blocks
** passenger disembarkation status **:      completed
** crew exit status **:                     exited
** baggage unload status **:                completed
** inspection maintenance status **:        completed
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "passenger_disembarkation_status": "completed",
  "crew_exit_status": "exited",
  "baggage_unload_status": "completed",
  "inspection_maintenance_status": "completed"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| **`crew_exit_status` unquoted as HOCON property key** | `aircraft_inspection_maintenance.hocon` lines 118, 256, 345 | **High** | `crew_exit_status: {...}` without quotes. HOCON spec requires string keys. Strict parsers may reject this. Should be `"crew_exit_status": {...}`. |
| Agent name mismatch with prior documentation | `aircraft_inspection_maintenance.hocon` line 90 | Low | Agent is `inspection_maintenance_agent`, not `aircraft_inspection_maintenance_agent`. |
| Old doc invented fields that don't exist | Prior documentation | — | `inspection_status`, `maintenance_status`, `detected_defects`, `maintenance_required` status do not exist. There is only `inspection_maintenance_status`. |
| `inspection_maintenance_status` absent from `to_downstream` | `aircraft_inspection_maintenance.hocon` sly_data | Low | The field propagates upstream only. Downstream networks cannot receive inspection results via sly_data. |
| No explicit TrackerAPI persist call in step 7→8 | `aircraft_inspection_maintenance.hocon` instructions | Low | Unlike `aircraft_cabin_cleaning` (which calls TrackerAPI after the operator), the inspection maintenance instructions have no TrackerAPI write between steps 7 and 8. The operator writes to sly_data directly, but no explicit TrackerAPI persist step exists. |
| `gate_id` tracked but not returned by TrackerAPI | `aircraft_inspection_maintenance.py` | Low | `gate_id` is in `FLIGHT_TURNAROUND_TRACKED_FIELDS` but not `FLIGHT_TURNAROUND_RETURN_FIELDS`. It will be persisted but not echoed back. |
| Loops 4–6 have no fail-fast guard | `aircraft_inspection_maintenance.hocon` instructions | Low | Steps 4–6 call external tools and return to step 2 without a maximum retry count or stop-on-failure guard. Could loop indefinitely if an external network fails silently. |
| HOCON TrackerAPI schema exposes non-tracked fields | `aircraft_inspection_maintenance.hocon` lines 309–356 | Low | Wide-schema copy-paste artifact exposes `wheels_chocks_*`, `gpu_*`, `acu_*`, `engines_stop_status`, `jetbridge_connection_status`, `door_opening_status` — none of which are tracked by the Python config. |
| Commented-out `required` array shows design intent | `aircraft_inspection_maintenance.hocon` line 131 | Info | The original `required` array included all three clearance status fields. The active one requires only core identity fields. The comment preserves the design history. |
| Hardcoded log path comment | `aircraft_inspection_maintenance.py` line 50 | Low | Commented-out absolute path remains; active path uses `Path.cwd()`. |

---

## 10. Extensibility Guidance

- Fix the unquoted `crew_exit_status` HOCON key in all three tool definitions (agent, operator, TrackerAPI)
- Add `inspection_maintenance_status` to `to_downstream` sly_data for downstream consumers
- Add an explicit TrackerAPI persist call in the instructions between the operator response and the summary (step 7c → step 8)
- Add fail-fast guards to steps 4–6: if a prerequisite is still not met after one external tool call, stop and report which prerequisite failed
- If actual inspection logic is needed (defect detection, airworthiness checks, MEL review), add it as additional operator logic or a dedicated downstream service; the current operator is only a prerequisite confirmation signal
- Consider renaming the field to `inspection_status` and adding separate `maintenance_status` if the workflow ever needs to distinguish between inspection completion and maintenance completion

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation regulatory or safety-critical maintenance systems.
