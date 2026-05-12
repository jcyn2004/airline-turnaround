# Aircraft Lavatory Service
## Agentic AI Network – README

> **Configuration file:** `aircraft_lavatory_service.hocon`
> **Implementation file:** `aircraft_lavatory_service.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Perform lavatory servicing on an aircraft at the gate during turnaround, after verifying that passengers have disembarked, crew has exited, and baggage has been unloaded.

---

## 1. Overview

`aircraft_lavatory_service` is a human-clearance–gated service network in the **AirlineTurnaround** agentic system. It is structurally nearly identical to `aircraft_inspection_maintenance` — both require the same three prerequisite statuses, use the same operator pattern, and share the same TrackerAPI field configuration.

The network combines:

- An LLM-based orchestration agent (`lavatory_service_agent`) that interprets intent and drives the workflow
- One coded execution tool (`lavatory_service_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_disembark`, `aircraft_crew_exit`, `aircraft_baggage_unload`) resolved from the shared registry `registries/aaosa_basic.hocon`

> **Important note on scope:** The previous documentation described `potable_water_refill_required`, waste disposal confirmation, water refill confirmation, and status values like `service_pending`, `service_in_progress`, and `service_failed`. None of these exist in the actual implementation. The operator produces a single `lavatory_service_status` field returning `'completed'` or `'pending'`.

---

## 2. Repository Structure

```
aircraft_lavatory_service.hocon    # Agent network configuration
aircraft_lavatory_service.py       # Coded tool implementations (lavatory_service_operator, TrackerAPI)
registries/aaosa_basic.hocon       # Shared registry (aircraft_disembark, aircraft_crew_exit, aircraft_baggage_unload)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
lavatory_service_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                                    (Coded tool: read/write turnaround state via sly_data)
   │
   ├── lavatory_service_operator                     (Coded tool: perform lavatory servicing)
   │
   ├── /AirlineTurnaround/aircraft_disembark         (External — if passengers not yet off)
   │
   ├── /AirlineTurnaround/aircraft_crew_exit         (External — if crew not yet off)
   │
   └── /AirlineTurnaround/aircraft_baggage_unload    (External — if baggage not yet unloaded)
```

### Design principles

- **Human-clearance prerequisite gating:** Lavatory service only initiates once passengers have disembarked, crew has exited, and baggage has been unloaded.
- **Active prerequisite resolution:** If any prerequisite is unmet, the agent calls the relevant external network (steps 4–6) and loops back to re-check state via TrackerAPI (step 2).
- **Single consolidated status:** The entire operation produces one output field: `lavatory_service_status = 'completed'`.

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

### 5.1 lavatory_service_agent (LLM Orchestrator)

The entry-point agent. It reads available parameters via TrackerAPI, resolves the three human-clearance prerequisites by delegating to external networks as needed, calls the operator, persists the result, and returns the summary.

> Note: The agent is named `lavatory_service_agent` in the HOCON. The previous documentation referred to it as `aircraft_lavatory_service_agent`.

#### Input parameters

| Parameter | Type | Required | Description |
|---|---|:---:|---|
| `flight_number` | string | ✅ | Flight identifier |
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `gate_id` | string | ✅ | Gate where the aircraft is parked |
| `passenger_disembarkation_status` | string | ✅ (schema) | Expected: `completed` |
| `crew_exit_status` | string | ✅ (schema) | Expected: contains `completed` or `exited` |
| `baggage_unload_status` | string | ✅ (schema) | Expected: contains `completed` or `unloaded` |
| `flight_status` | string | ❌ | Flight status |
| `lavatory_service_status` | string | ❌ | Current or previous service status |

> Note: `crew_exit_status` appears as an **unquoted property key** (`crew_exit_status: {...}` without quotes) in the agent, operator, and TrackerAPI HOCON schemas — the same syntax issue present in `aircraft_inspection_maintenance`. HOCON requires string keys and strict parsers may reject this.

#### Orchestration flow

The instructions use older numbered-prose style:

1. Read: `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`.
2. Call `TrackerAPI` — store all available parameters.
3. If all three clearance statuses are confirmed → skip to step 7.
4. If `passenger_disembarkation_status` not `'completed'` → call `aircraft_disembark`. Return to step 2.
5. If `crew_exit_status` not `'completed'`/`'exited'` → call `aircraft_crew_exit`. Return to step 2.
6. If `baggage_unload_status` not `'completed'`/`'unloaded'` → call `baggage_unload`. Return to step 2.
7. All three confirmed → call `lavatory_service_operator`. Save as `lavatory_service_status`.
8. Call `TrackerAPI` — store `lavatory_service_status`.
9. Return summary.

> Note: Step 6 refers to the tool as `baggage_unload`, but the external tool registered in the HOCON tools list is `/AirlineTurnaround/aircraft_baggage_unload`. Inconsistent naming — the LLM must match the registered tool name.

> Note: Steps 4–6 loop back to step 2 without a maximum retry count. If an external network fails silently, the agent could loop indefinitely.

> Note: Unlike `aircraft_inspection_maintenance`, this network has step 8 (an explicit TrackerAPI persist call after the operator), which is the correct pattern.

#### sly_data contract

| Direction | Parameters |
|---|---|
| **To upstream** | `lavatory_service_status` |
| **To downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |
| **From upstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |

> Note: `lavatory_service_status` propagates upstream only. It is absent from `to_downstream`, `from_upstream`, and `from_downstream`. Downstream networks cannot receive the lavatory service result via sly_data — identical to the pattern in `aircraft_inspection_maintenance`.

#### Down-chain tools (HOCON line 224)

```
["TrackerAPI", "lavatory_service_operator",
 "/AirlineTurnaround/aircraft_disembark",
 "/AirlineTurnaround/aircraft_crew_exit",
 "/AirlineTurnaround/aircraft_crew_exit",   ← duplicate
 "/AirlineTurnaround/aircraft_baggage_unload"]
```

> Note: `/AirlineTurnaround/aircraft_crew_exit` appears **twice** in the tools list. `/AirlineTurnaround/aircraft_baggage_unload` appears once at the end but is the tool step 6 needs. While `aircraft_baggage_unload` is listed, the duplicate `aircraft_crew_exit` is dead and should be removed.

---

### 5.2 lavatory_service_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_lavatory_service.aircraft_lavatory_service.lavatory_service_operator`

Performs the lavatory service completion check. It validates all required parameters, evaluates the three human-clearance conditions, then sets `lavatory_service_status = 'completed'`, writes to `sly_data`, and appends a timestamped log entry.

The operator is functionally identical to `inspection_maintenance_operator` in `aircraft_inspection_maintenance.py` — same parameter set, same condition logic, same return behaviour.

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

#### Service logic

`lavatory_service_status` is set to `'completed'` when **all three** conditions are true (case-insensitive):

| Field | Accepted values |
|---|---|
| `passenger_disembarkation_status` | `completed`, `done` |
| `crew_exit_status` | `completed`, `exited` |
| `baggage_unload_status` | `completed`, `unloaded` |

If any condition fails, `lavatory_service_status` remains `'pending'` (initial value). `sly_data` is not updated on failure.

#### Output

- Writes `lavatory_service_status = 'completed'` into `sly_data` on success
- Returns `lavatory_service_status` string (`'completed'` or `'pending'`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt` on success

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_lavatory_service.aircraft_lavatory_service.TrackerAPI`

Standard sly_data-first implementation. Called in step 2 to read available parameters, and again in step 8 after the operator to persist `lavatory_service_status`.

#### Configuration

**Tracked fields:**
`aircraft_type`, `baggage_unload_status`, `crew_exit_status`, `flight_number`, `flight_status`, `gate_id`, `lavatory_service_status`, `passenger_disembarkation_status`

**Return fields:**
`aircraft_type`, `baggage_unload_status`, `crew_exit_status`, `flight_number`, `flight_status`, `gate_id`, `lavatory_service_status`, `passenger_disembarkation_status`

> Note: Tracked fields and return fields are **identical** (8 fields each) — TrackerAPI returns everything it tracks. This is different from `aircraft_inspection_maintenance` where `gate_id` is tracked but not returned.

> Note: The HOCON TrackerAPI schema exposes many additional turnaround fields (`wheels_chocks_*`, `gpu_*`, `acu_*`, `engines_stop_status`, `jetbridge_connection_status`, `door_opening_status`) that are not tracked by the Python config — wide-schema copy-paste artifacts.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

These tools are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path | Purpose | Condition triggering call |
|---|---|---|
| `/AirlineTurnaround/aircraft_disembark` | Complete passenger disembarkation | Step 4 |
| `/AirlineTurnaround/aircraft_crew_exit` | Complete crew exit | Step 5 |
| `/AirlineTurnaround/aircraft_baggage_unload` | Complete baggage unloading | Step 6 |

---

## 7. Sample Queries

```
# All prerequisites confirmed
"The B747 aircraft of flight AF84 is on blocks at gate A1.
Baggages have been unloaded. All passengers have disembarked.
The crew has exited the aircraft. Perform lavatory service to the aircraft."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. Baggages have been unloaded. All passengers have disembarked. The crew has exited the aircraft. Perform lavatory service to the aircraft."

**Execution steps:**

1. `TrackerAPI` called (step 2) — stores: `flight_status=on blocks`, `passenger_disembarkation_status=completed`, `crew_exit_status=exited`, `baggage_unload_status=completed`
2. All prerequisite check: passengers ✅, crew ✅, baggage ✅ (step 3 → skip to step 7)
3. `lavatory_service_operator` called — returns `lavatory_service_status=completed`
4. `TrackerAPI` called (step 8) — persists `lavatory_service_status=completed`
5. Summary returned

**Output:**

```
****************************************
* Summary of aircraft lavatory service *
** flight_number **:                         AF84
** aircraft_type **:                         B747
** flight_status **:                         on blocks
** gate_id **:                               A1
** passenger disembarkation status **:       completed
** crew exit status **:                      exited
** baggage unload status **:                 completed
** lavatory service status **:               completed
```

*(Note: The summary header is missing the closing `*` banner line — a typo in the HOCON instructions template)*

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
  "lavatory_service_status": "completed"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| **`crew_exit_status` unquoted as HOCON property key** | `aircraft_lavatory_service.hocon` lines 117, 256, 345 | **High** | `crew_exit_status: {...}` without quotes in agent, operator, and TrackerAPI schemas. Strict HOCON parsers will reject this. Fix: `"crew_exit_status": {...}`. Same bug as `aircraft_inspection_maintenance`. |
| `/AirlineTurnaround/aircraft_crew_exit` duplicated in tools list | `aircraft_lavatory_service.hocon` line 224 | Medium | Listed twice. The duplicate entry is dead and should be removed. |
| Step 6 tool name inconsistency | `aircraft_lavatory_service.hocon` line 158 | Low | Instructions say "call baggage_unload" but the registered tool is `/AirlineTurnaround/aircraft_baggage_unload`. |
| Agent name mismatch with prior documentation | `aircraft_lavatory_service.hocon` line 89 | Low | Agent is `lavatory_service_agent`, not `aircraft_lavatory_service_agent`. |
| Prior documentation invented fields that don't exist | Prior documentation | — | `potable_water_refill_required`, waste disposal confirmation, water refill confirmation, `service_pending`/`service_in_progress`/`service_failed` status values do not exist. Only `lavatory_service_status` (`'completed'` or `'pending'`) is present. |
| `lavatory_service_status` absent from `to_downstream` | `aircraft_lavatory_service.hocon` sly_data | Low | Propagates upstream only. Downstream networks cannot receive the result via sly_data. |
| Summary header missing closing banner line | `aircraft_lavatory_service.hocon` line 169–179 | Low | The `*` banner line that should follow the title is absent, so the header reads `****************************************\n* Summary of aircraft lavatory service *` with no closing `*...` line. |
| Step 6 instruction says `flight statuys` | `aircraft_lavatory_service.hocon` line 140 | Low | Typo: "statuys" for "status". No runtime impact. |
| Steps 4–6 loop has no fail-fast guard | `aircraft_lavatory_service.hocon` steps 4–6 | Low | No maximum retry count. Could loop indefinitely if an external network fails. |
| Wide-schema HOCON TrackerAPI exposes non-tracked fields | `aircraft_lavatory_service.hocon` lines 309–356 | Low | Copy-paste artifact. |

---

## 10. Comparison with `aircraft_inspection_maintenance`

This network is the closest structural twin to `aircraft_inspection_maintenance` in the system. The differences are minimal:

| Aspect | `aircraft_inspection_maintenance` | `aircraft_lavatory_service` |
|---|---|---|
| Output field | `inspection_maintenance_status` | `lavatory_service_status` |
| Explicit TrackerAPI persist after operator | No (missing) | Yes (step 8) |
| `gate_id` in TrackerAPI return fields | No | Yes |
| TrackerAPI tracked = return | No (gate_id missing from return) | Yes (all 8 fields match) |
| Duplicate tool in tools list | No | Yes (`aircraft_crew_exit` twice) |
| `crew_exit_status` unquoted | Yes (3 places) | Yes (3 places) |

---

## 11. Extensibility Guidance

- Fix the unquoted `crew_exit_status` key in all three HOCON tool definitions
- Remove the duplicate `/AirlineTurnaround/aircraft_crew_exit` entry from the tools list
- Align step 6 tool name to `aircraft_baggage_unload` for consistency with the registered tool path
- Add `lavatory_service_status` to `to_downstream` if downstream networks need to read the result
- Add fail-fast guards to steps 4–6
- If actual lavatory servicing logic is needed (waste tank levels, water fill levels, compliance checks), extend the operator beyond the current prerequisite-confirmation model

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
