# Aircraft Fueling
## Agentic AI Network – README

> **Configuration file:** `aircraft_fueling.hocon`
> **Implementation file:** `aircraft_fueling.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Fuel an aircraft at the gate during turnaround, after verifying that passengers have disembarked, crew has exited, and baggage has been unloaded.

---

## 1. Overview

`aircraft_fueling` is an agentic network that orchestrates the aircraft fueling process during turnaround. It is part of the broader **AirlineTurnaround** agentic system.

The network combines:

- An LLM-based orchestration agent (`fueling_agent`) that interprets intent and drives the workflow
- One coded execution tool (`fueling_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_disembark`, `aircraft_crew_exit`, `aircraft_baggage_unload`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network's prerequisite model closely mirrors `aircraft_cabin_cleaning` and `aircraft_catering_loading`: fueling requires the same three human-clearance gates — passengers off, crew off, baggage unloaded. A notable difference from most other networks is that `fueling_operator` uses `sly_data`-first parameter resolution (the inverse of the `args`-first pattern used elsewhere), and returns an **explicit error string** on prerequisite failure rather than silently returning `pending`.

> **Important note on prerequisites:** The previous documentation described the fueling prerequisites as "on blocks + engines stopped + chocks installed" — consistent with real-world aviation safety requirements. The actual implementation checks only the three human-clearance statuses. `engines_stop_status`, `wheels_chocks_installation_status`, `requested_fuel_quantity`, and `actual_fuel_quantity` do not exist anywhere in the actual HOCON or Python files.

---

## 2. Repository Structure

```
aircraft_fueling.hocon               # Agent network configuration
aircraft_fueling.py                  # Coded tool implementations (fueling_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_disembark, aircraft_crew_exit, aircraft_baggage_unload)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
fueling_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                                   (Coded tool: read/write turnaround state via sly_data)
   │
   ├── fueling_operator                             (Coded tool: perform aircraft fueling)
   │
   ├── /AirlineTurnaround/aircraft_disembark        (External tool — if passengers not yet off)
   │
   ├── /AirlineTurnaround/aircraft_crew_exit        (External tool — if crew not yet off)
   │
   └── /AirlineTurnaround/aircraft_baggage_unload   (External tool — if baggage not yet unloaded)
```

### Design principles

- **Human-clearance prerequisite gating:** Fueling is only initiated once the cabin is cleared of passengers, crew, and baggage. The orchestrator performs a hard stop in Step 3 rather than delegating if prerequisites are unmet — external tools are present in the toolset but the instructions do not direct the agent to call them.
- **Explicit operator failure reporting:** When prerequisites are not met, `fueling_operator` returns a detailed error string (rather than `pending`), enabling the calling agent to report a specific failure message.
- **sly_data-first parameter resolution:** `fueling_operator` reads parameters from `sly_data` first, falling back to `args`. This is the inverse of the `args`-first pattern used by most other operators in the system.
- **Tool-first execution:** All operational actions are performed by coded or external tools; the LLM orchestrates, not executes.
- **Structured output:** The agent returns a formatted summary block containing all relevant operational parameters.

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

### 5.1 fueling_agent (LLM Orchestrator)

The entry-point agent. It uses the `CRITICAL: sequential executor` / `STEP` pattern. It reads prerequisites, performs a hard-abort if any are unmet, calls the operator, validates the result, and returns the summary.

> Note: The agent is named `fueling_agent` in the HOCON. The previous documentation referred to it as `aircraft_fueling_agent`, which does not match the actual runtime tool name.

#### Input parameters

|-----------------------------------|--------|:--------:|-----------------------------------------------------------|
| Parameter                         | Type   | Required | Description                                               |
|-----------------------------------|--------|:--------:|-----------------------------------------------------------|
| `flight_number`                   | string | ✅       | Flight identifier                                         |
| `aircraft_type`                   | string | ✅       | Aircraft model/type                                       |
| `gate_id`                         | string | ✅       | Gate where the aircraft is parked                         |
| `passenger_disembarkation_status` | string | ✅       | Expected: contains `completed`                            |
| `crew_exit_status`                | string | ✅       | Expected: contains `completed` or `exited`                |
| `baggage_unload_status`           | string | ✅       | Expected: contains `completed` or `unloaded`              |
| `flight_status`                   | string | ❌       | Flight status (expected: contains `on blocks` or `block`) |
| `fueling_status`                  | string | ❌       | Current or previous fueling status                        |
|-----------------------------------|--------|:--------:|-----------------------------------------------------------|

> Note: `flight_status` is not declared `required` in the HOCON schema, but the orchestrator will stop in Step 2 if it does not contain `on blocks` or `block`. It is functionally required for the workflow to proceed.

#### Orchestration flow

1. **STEP 1 — Resolve prerequisites:** Call `TrackerAPI` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`. Read back all seven values.
2. **STEP 2 — Verify flight status:** Must contain `on blocks` or `block`. If not → stop and report `"Cannot fuel aircraft — not on blocks."`
3. **STEP 3 — Verify human-clearance prerequisites:** All three must be true:
   - `passenger_disembarkation_status` contains `completed`
   - `crew_exit_status` contains `completed` or `exited`
   - `baggage_unload_status` contains `completed` or `unloaded`
   - If any is missing or failed → **stop and report which prerequisite is unmet. Do NOT call fueling_operator.**
4. **STEP 4 — Execute fueling:** Call `fueling_operator` with all seven parameters. Read `fueling_status`.
   - **VALIDATION:** `fueling_status` must be `completed`. If not → report failure with raw response.
   - Call `TrackerAPI` to store `fueling_status`.
5. **RETURN SUMMARY.**

> Note: Unlike `aircraft_cabin_cleaning` and `aircraft_catering_loading`, this network's instructions explicitly instruct the agent to **stop and report** when prerequisites are unmet (Step 3), rather than delegating to external tools to resolve them. The external tools (`aircraft_disembark`, `aircraft_crew_exit`, `aircraft_baggage_unload`) appear in the `tools` array but are not referenced in the instruction steps — they are available for the agent to use autonomously via aaosa, but the sequential executor instructions do not direct it to call them.

> Note: Step 4 includes an explicit `VALIDATION` guard on the operator's return value — the same pattern seen in `aircraft_crew_exit`. The agent must confirm `fueling_status = 'completed'` before declaring success.

#### sly_data contract

|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Direction           | Parameters                                                                                                                                                     |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `fueling_status`                                                                                                                                               |
| **To downstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `fueling_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`                   |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`                   |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|

> Note: `fueling_status` propagates in `to_upstream` and `to_downstream`, but is absent from `from_upstream` and `from_downstream`. Upstream networks pushing context into this network do not send `fueling_status` — it is generated here and only flows outward.

#### Down-chain tools

```
["TrackerAPI", "fueling_operator", "/AirlineTurnaround/aircraft_disembark",
 "/AirlineTurnaround/aircraft_crew_exit", "/AirlineTurnaround/aircraft_baggage_unload"]
```

---

### 5.2 fueling_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_fueling.aircraft_fueling.fueling_operator`

Performs the fueling completion check. It validates all required parameters, evaluates the three human-clearance conditions, then either sets `fueling_status = completed` and writes to `sly_data`, or returns an explicit structured error string.

> Note: This operator uses `_from_sly_or_args` (sly_data first, args fallback) for all parameter lookups. All other operators in the system use `_from_args_or_sly` (args first). This means if `sly_data` holds an outdated or stale value, it will take precedence over a fresh value in `args`.

#### Input parameters

|-----------------------------------|--------|:--------:|---------------------|
| Parameter                         | Type   | Required | Source priority     |
|-----------------------------------|--------|:--------:|---------------------|
| `flight_number`                   | string | ✅       | `sly_data` → `args` |
| `aircraft_type`                   | string | ✅       | `sly_data` → `args` |
| `flight_status`                   | string | ✅       | `sly_data` → `args` |
| `gate_id`                         | string | ✅       | `sly_data` → `args` |
| `passenger_disembarkation_status` | string | ✅       | `sly_data` → `args` |
| `crew_exit_status`                | string | ✅       | `sly_data` → `args` |
| `baggage_unload_status`           | string | ✅       | `sly_data` → `args` |
|-----------------------------------|--------|:--------:|---------------------|

#### Fueling logic

`fueling_status` is set to `completed` when **all three** of the following conditions are true (case-insensitive, after stripping whitespace):

|-----------------------------------|-------------------------|
| Field                             | Accepted values         |
|-----------------------------------|-------------------------|
| `passenger_disembarkation_status` | `completed`, `done`     |
| `crew_exit_status`                | `completed`, `exited`   |
| `baggage_unload_status`           | `completed`, `unloaded` |
|-----------------------------------|-------------------------|

If any condition fails, the operator returns an **explicit error string** with details:

```
Error: fueling prerequisites not met for flight {flight_number}.
passenger_disembarkation_status='{...}', crew_exit_status='{...}', baggage_unload_status='{...}'.
All three must be completed/exited/unloaded before fueling can proceed.
```

This error string design — with an accompanying code comment explaining it — is a deliberate improvement over the silent `pending` return used in earlier operator implementations.

#### Output

- Writes `fueling_status = 'completed'` into `sly_data` on success
- Returns `fueling_status` string (`completed`) or an explicit error string on failure
- Appends a timestamped log line to `test_debug/airlineturnaround.txt` on success

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_fueling.aircraft_fueling.TrackerAPI`

Manages shared turnaround state. Called in Step 1 to read all current values, and again in Step 4 after the operator to persist `fueling_status`.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `baggage_unload_status`, `crew_exit_status`, `flight_number`, `flight_status`, `fueling_status`, `gate_id`, `passenger_disembarkation_status`

> Note: `gate_id` is correctly included in tracked fields here — unlike several other networks where it was absent. This resolves a gap seen in `aircraft_disembark`, `aircraft_cabin_cleaning`, and `aircraft_engines_stop`.

**Return fields:**
`baggage_unload_status`, `crew_exit_status`, `flight_status`, `fueling_status`, `passenger_disembarkation_status`

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

These tools are in the `tools` array but are not explicitly called in the sequential instruction steps. They are available for autonomous aaosa-mode dispatch:

|----------------------------------------------|-----------------------------------|
| Tool path                                    | Nominal purpose                   |
|----------------------------------------------|-----------------------------------|
| `/AirlineTurnaround/aircraft_disembark`      | Complete passenger disembarkation |
| `/AirlineTurnaround/aircraft_crew_exit`      | Complete crew exit                |
| `/AirlineTurnaround/aircraft_baggage_unload` | Complete baggage unloading        |
|----------------------------------------------|-----------------------------------|

---

## 7. Sample Queries

```
# All prerequisites already confirmed
"The B747 aircraft of flight AF84 is on blocks at gate A1. Baggages have been unloaded.
All passengers have disembarked. The crew has exited the aircraft.
Perform the fueling of the aircraft."

# Prerequisites not yet confirmed (agent will stop and report in Step 3 rather than resolve)
"The B747 aircraft of flight AF84 is on blocks at gate A1.
Perform the fueling of the aircraft."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. Baggages have been unloaded. All passengers have disembarked. The crew has exited the aircraft. Perform the fueling of the aircraft."

**Execution steps:**

1. `TrackerAPI` called (Step 1) — reads: `flight_status=on blocks`, `passenger_disembarkation_status=completed`, `crew_exit_status=exited`, `baggage_unload_status=completed`
2. Flight status check: on blocks ✅ (Step 2)
3. Prerequisite check: all three conditions met ✅ (Step 3)
4. `fueling_operator` called — returns `fueling_status=completed` (Step 4)
5. Validation: `completed` ✅
6. `TrackerAPI` called — persists `fueling_status=completed`
7. Summary returned

**Output:**

```
*******************************
* Summary of aircraft fueling *
*******************************
** flight status                    **: on blocks
** passenger disembarkation status  **: completed
** crew exit status                 **: exited
** baggage unload status            **: completed
** fueling status summary           **: completed
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
  "fueling_status": "completed"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Notes |
|---|---|---|
| Previous doc described wrong prerequisites | Prior documentation | Old doc listed engines stopped, chocks installed, and `requested_fuel_quantity`/`actual_fuel_quantity` as parameters. None of these exist in the actual implementation. Actual prerequisites are passenger disembarkation, crew exit, baggage unload. |
| `fueling_operator` uses sly_data-first resolution | `aircraft_fueling.py` line 68 | All other operators use `_from_args_or_sly` (args first). This operator uses `_from_sly_or_args` (sly_data first). Stale sly_data values will take precedence over fresher args values. |
| External tools in `tools` array not called by sequential instructions | `aircraft_fueling.hocon` instructions + line 226 | The three external tools are available for aaosa dispatch but Step 3 instructs a hard stop rather than delegation when prerequisites are unmet. The agent's behavior on encountering unmet prerequisites may therefore vary depending on whether aaosa mode overrides the sequential executor instructions. |
| Hardcoded log path comment | `aircraft_fueling.py` line 51 | Commented-out absolute path remains; active path uses `Path.cwd()`. |

---

## 10. Extensibility Guidance

- Align `fueling_operator` parameter resolution to `args`-first (using `_from_args_or_sly`) for consistency with all other operators in the system, unless the sly_data-first behavior is intentional
- If the intent is for the agent to resolve unmet prerequisites by calling external tools, explicitly add those calls as STEP 3a–3c in the orchestrator instructions (mirroring the pattern in `aircraft_cabin_cleaning`)
- Add `engines_stop_status` and `wheels_chocks_installation_status` as checked prerequisites if real-world safety requirements need to be enforced at the orchestrator level
- The explicit error string from `fueling_operator` is a pattern worth propagating to other operators in the system (replacing silent `pending` returns with structured error messages)

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation fueling or safety-critical systems.
