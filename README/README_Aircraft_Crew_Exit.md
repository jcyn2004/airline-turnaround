# Aircraft Crew Exit
## Agentic AI Network – README

> **Configuration file:** `aircraft_crew_exit.hocon`
> **Implementation file:** `aircraft_crew_exit.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Exit the crew from an aircraft at the gate during turnaround, after verifying that the deplaning equipment (jetbridge or stairtruck) is connected and the aircraft door is open.

---

## 1. Overview

`aircraft_crew_exit` is an agentic network that orchestrates crew disembarkation for an arriving aircraft. It is part of the broader **AirlineTurnaround** agentic system.

The network combines:

- An LLM-based orchestration agent (`crew_exit_agent`) that interprets intent and drives the workflow
- One coded execution tool (`crew_exit_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_jetbridge_connect`, `aircraft_stairtruck_connect`, `aircraft_door_opening`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network's architecture mirrors `aircraft_baggage_unload` and `aircraft_crew_debrief`: it uses equipment-based access prerequisites (jetbridge or stairtruck connected, door open) before performing the crew exit. A distinctive feature compared to other networks is the orchestrator's **terminal-status validation loop** — it explicitly retries `TrackerAPI` up to twice after the operator call to confirm `crew_exit_status` has reached a terminal value before reporting success.

---

## 2. Repository Structure

```
aircraft_crew_exit.hocon             # Agent network configuration
aircraft_crew_exit.py                # Coded tool implementations (crew_exit_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_jetbridge_connect, aircraft_stairtruck_connect, aircraft_door_opening)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
crew_exit_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                                       (Coded tool: read/write turnaround state via sly_data)
   │
   ├── crew_exit_operator                               (Coded tool: perform crew exit)
   │
   ├── /AirlineTurnaround/aircraft_jetbridge_connect    (External tool — jetway gates only)
   │
   ├── /AirlineTurnaround/aircraft_stairtruck_connect   (External tool — stairtruck gates only)
   │
   └── /AirlineTurnaround/aircraft_door_opening         (External tool — when door not yet open)
```

### Design principles

- **Equipment-aware prerequisite gating:** The agent routes the equipment connection step to the correct external tool based on `deplaning_equipment_type`. If the type is unknown, either a connected jetbridge or stairtruck is accepted.
- **Terminal-status validation:** After calling the operator, the orchestrator validates that `crew_exit_status` contains `completed` or `exited` before reporting success. If not, it retries `TrackerAPI` up to 2 more times before issuing a failure message.
- **Tool-first execution:** All operational actions are performed by coded or external tools; the LLM orchestrates, not executes.
- **sly_data as shared state:** Parameters flow between tools without re-passing through the LLM.
- **Structured output:** The agent returns a formatted summary block, but only after terminal status is confirmed.

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

### 5.1 crew_exit_agent (LLM Orchestrator)

The entry-point agent. It parses the user inquiry, enforces equipment-access prerequisites, delegates prerequisite resolution to external networks, executes the crew exit, validates the terminal status, and returns the final summary.

#### Input parameters

|--------------------------------|--------|:--------:|-----------------------------------------------------------------|
| Parameter                      | Type   | Required | Description                                                     |
|--------------------------------|--------|:--------:|-----------------------------------------------------------------|
| `flight_number`                | string | ✅       | Flight identifier                                               |
| `aircraft_type`                | string | ✅       | Aircraft model/type                                             |
| `gate_id`                      | string | ✅       | Gate where the aircraft is parked                               |
| `flight_status`                | string | ✅       | Flight status                                                   |
| `door_opening_status`          | string | ✅       | Aircraft door state (expected: contains `open`)                 |
| `jetbridge_connection_status`  | string | ❌       | Jetbridge state — null on stairtruck gates                      |
| `stairtruck_connection_status` | string | ❌       | Stairtruck state — null on jetway gates                         |
| `deplaning_equipment_type`     | string | ❌       | Equipment at gate: `jetway`/`jetbridge` or `stairtruck`/`stair` |
|--------------------------------|--------|:--------:|-----------------------------------------------------------------|

#### Orchestration flow

1. Determine what is provided: `jetbridge_connection_status` or `stairtruck_connection_status`, `door_opening_status`, `flight_status`, `deplaning_equipment_type`.
2. Call `TrackerAPI` — read and store all available parameters.
3. Determine equipment readiness based on `deplaning_equipment_type`:
   - `jetway` / `jetbridge` → equipment ready if `jetbridge_connection_status` contains `connected`
   - `stairtruck` / `stair` → equipment ready if `stairtruck_connection_status` contains `connected`
   - Unknown type → either connection status is accepted
4. If equipment is connected AND `door_opening_status` contains `open` → skip to step 6.
5. If equipment is NOT connected:
   - Jetway gate → call `/AirlineTurnaround/aircraft_jetbridge_connect`
   - Stairtruck gate → call `/AirlineTurnaround/aircraft_stairtruck_connect` (passing `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`)
   - Return to step 2.
6. If door is not open → call `/AirlineTurnaround/aircraft_door_opening` (passing `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`). Return to step 2.
7. Equipment connected and door open → call `crew_exit_operator`. **Do NOT report yet.** Save result as `crew_exit_status`.
8. Call `TrackerAPI` to confirm `crew_exit_status`.
   - **VALIDATION:** `crew_exit_status` MUST contain `completed` or `exited`.
   - If status is non-terminal (`requested`, `in progress`, etc.) → retry `TrackerAPI` up to 2 more times.
   - If still non-terminal after retries → report failure: `"crew_exit_status FAILED: status did not reach completed. Raw status: [crew_exit_status]"`
9. Return summary block **only** after terminal status is confirmed.

> Note: The retry logic in step 8 anticipates intermediate statuses (`requested`, `in progress`) from `crew_exit_operator`. However, the actual operator only ever returns `completed` or `pending` — it has no mechanism to produce intermediate values. The retry guard will therefore fire only if `pending` is returned, which indicates a prerequisite failure rather than an intermediate processing state.

#### sly_data contract

|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Direction           | Parameters                                                                                                                                                                                         |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `crew_exit_status`                                                                                                                                                             |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `door_opening_status`, `jetbridge_connection_status`, `stairtruck_connection_status`                             |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

> Note: `to_upstream` carries only 4 fields (`crew_exit_status`, `flight_status`, `door_opening_status`, `jetbridge_connection_status`), while `to_downstream` carries the full 9-field context set. `stairtruck_connection_status` and `deplaning_equipment_type` propagate downstream but not upstream. The HOCON file additionally contains a duplicate `to_downstream` block with only 4 fields; HOCON merge semantics make the 9-field block the effective configuration.

#### Down-chain tools

```
["TrackerAPI", "crew_exit_operator", "/AirlineTurnaround/aircraft_door_opening",
 "/AirlineTurnaround/aircraft_jetbridge_connect", "/AirlineTurnaround/aircraft_stairtruck_connect"]
```

---

### 5.2 crew_exit_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_crew_exit.aircraft_crew_exit.crew_exit_operator`

Performs the crew exit completion check. It validates all required parameters, verifies that at least one piece of deplaning equipment is connected and the door is open, then sets `crew_exit_status = completed`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

#### Input parameters

|--------------------------------|--------|:--------:|---------------------|
| Parameter                      | Type   | Required | Source priority     |
|--------------------------------|--------|:--------:|---------------------|
| `flight_number`                | string | ✅       | `args` → `sly_data` |
| `aircraft_type`                | string | ✅       | `args` → `sly_data` |
| `gate_id`                      | string | ✅       | `args` → `sly_data` |
| `door_opening_status`          | string | ✅       | `args` → `sly_data` |
| `flight_status`                | string | ❌       | `args` → `sly_data` |
| `jetbridge_connection_status`  | string | ❌       | `args` → `sly_data` |
| `stairtruck_connection_status` | string | ❌       | `args` → `sly_data` |
|--------------------------------|--------|:--------:|---------------------|

#### Exit logic

The operator evaluates `equipment_connected` as:

```
jetbridge_connection_status contains 'connected'
OR
stairtruck_connection_status contains 'connected'
```

`crew_exit_status` is set to `completed` when both of the following are true (case-insensitive):

- `equipment_connected` is `True`
- `door_opening_status` contains `open`

If `equipment_connected` is False, the tool returns an error string immediately without updating `sly_data`. If the door condition fails after equipment is confirmed connected, `pending` (the initial value) is returned. If `door_opening_status` is missing entirely, the tool also returns an error string.

#### Output

- Writes `crew_exit_status` into `sly_data`
- Returns `crew_exit_status` string (`completed` or `pending`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_crew_exit.aircraft_crew_exit.TrackerAPI`

Manages shared turnaround state. Called at the start of the workflow, during any prerequisite retry loops, and in step 8 to confirm the terminal status of `crew_exit_status`.

This network's `TrackerAPI` has the **largest tracked fields list** in the entire system. Unlike other networks that use a trimmed subset, this instance tracks the full master turnaround field set — 30+ fields spanning every stage of the turnaround lifecycle.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields (30+ — full master list):**
`acu_connection_status`, `acu_readiness_status`, `aircraft_direction`, `aircraft_landing_report`, `aircraft_type`, `assigned_runway_id`, `assigned_runway_length`, `baggage_unload_status`, `catering_loading_status`, `cleaning_cabin_status`, `clearance_landing_valid`, `clearance_takeoff_valid`, `clearance_type`, `crew_debrief_status`, `crew_exit_status`, `deplaning_equipment_type`, `door_opening_status`, `engines_stop_status`, `flight_number`, `flight_status`, `fueling_status`, `gate_id`, `gpu_connection_status`, `gpu_readiness_status`, `ground_clearance_status`, `ground_clearance_type`, `ground_services_inquiry_type`, `ground_services_request_type`, `inspection_maintenance_status`, `jetbridge_connection_status`, `jetbridge_status`, `lavatory_service_status`, `passenger_disembarkation_status`, `runway_length`, `stairtruck_connection_status`, `wheels_chocks_installation_status`, `wheels_chocks_readiness_status`

> Note: This is the same field list that appears commented-out in other networks (e.g. `aircraft_cabin_cleaning`, `aircraft_catering_loading`). This network is where it is active. The HOCON `TrackerAPI` tool definition itself exposes only a subset (~18 fields) in its `parameters.properties` block; the full master list lives in the Python `FLIGHT_TURNAROUND_TRACKED_FIELDS` constant.

**Return fields:**
`crew_exit_status`, `deplaning_equipment_type`, `door_opening_status`, `flight_status`, `jetbridge_connection_status`, `stairtruck_connection_status`

> Note: The HOCON `TrackerAPI` tool definition is missing a `"required": []` field in its `parameters` object — the schema closes with just `}`. This is consistent with `aircraft_crew_debrief`. No runtime impact, but should be corrected for schema consistency across the system.

---

## 6. External Tool Dependencies

These tools are not defined in this network. They are resolved at runtime from `registries/aaosa_basic.hocon`:

|--------------------------------------------------|--------------------------------|------------------------------------------------|
| Tool path                                        | Purpose                        | Condition triggering call                      |
|--------------------------------------------------|--------------------------------|------------------------------------------------|
| `/AirlineTurnaround/aircraft_jetbridge_connect`  | Connect jetbridge to aircraft  | Equipment not connected on a jetway gate       |
| `/AirlineTurnaround/aircraft_stairtruck_connect` | Connect stairtruck to aircraft | Equipment not connected on a stairtruck gate   |
| `/AirlineTurnaround/aircraft_door_opening`       | Open aircraft door             | Door not yet open after equipment is connected |
|--------------------------------------------------|--------------------------------|------------------------------------------------|

---

## 7. Sample Queries

```
# All prerequisites already met
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The plane has been connected to the jetbridge. The aircraft door is open.
Exit the crew."

# Prerequisites not yet confirmed — agent will resolve them
"The B747 aircraft of flight AF84 is on blocks at gate A1. Exit the crew."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. The plane has been connected to the jetbridge. The aircraft door is open. Exit the crew."

**Execution steps:**

1. `TrackerAPI` called — reads: `flight_status=on blocks`, `jetbridge_connection_status=connected`, `door_opening_status=open`
2. Equipment check: jetbridge connected ✅, door open ✅
3. `crew_exit_operator` called — returns `crew_exit_status=completed`
4. `TrackerAPI` called — confirms `crew_exit_status=completed` (terminal ✅)
5. Summary returned

**Output:**

```
*********************************
* Summary of aircraft crew exit *
*********************************
** flight status                 **: on blocks
** deplaning equipment type      **: jetway
** jetbridge connection status   **: connected
** stairtruck connection status  **: null
** door opening status           **: open
** crew exit status              **: completed
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "deplaning_equipment_type": "jetway",
  "jetbridge_connection_status": "connected",
  "stairtruck_connection_status": null,
  "door_opening_status": "open",
  "crew_exit_status": "completed"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Notes |
|---|---|---|
| Terminal-status retry logic guards against statuses the operator cannot produce | `aircraft_crew_exit.hocon` instructions steps 6–7 | The orchestrator retries if status is `requested` or `in progress`, but `crew_exit_operator` only returns `completed` or `pending`. Retries will fire only when `pending` is returned, indicating a prerequisite failure rather than an intermediate processing state. The guard is harmless but misleading. |
| Log message copy-paste artifact | `aircraft_crew_exit.py` line 150 | Message reads `"...door {door_opening_status}.  installed. Its crew exit status is status is {crew_exit_status}."` — contains `"installed"` (from earlier networks) and a duplicated `"status is"`. |
| HOCON TrackerAPI missing `"required": []` | `aircraft_crew_exit.hocon` line 379 | The `parameters` object closes without `"required": []`. Same issue as `aircraft_crew_debrief`. No runtime impact. |
| Duplicate `to_downstream` block in `allow` | `aircraft_crew_exit.hocon` `allow` (lines 196-203 and 230-242) | Two `to_downstream` blocks are defined — a 4-field block and a 9-field block. HOCON merge semantics retain the 9-field block as effective. Should be deduplicated. |
| `stairtruck_connection_status` and `deplaning_equipment_type` absent from `to_upstream` | `aircraft_crew_exit.hocon` `allow.to_upstream` | Both fields are tracked internally and propagate downstream, but are not sent upstream. Upstream networks must receive them via their own `from_downstream` blocks. |
| TrackerAPI tracks 30+ fields — full master list active | `aircraft_crew_exit.py` `FLIGHT_TURNAROUND_TRACKED_FIELDS` | This is the only network where the full master field list is uncommented and active. Fields irrelevant to crew exit (e.g. `runway_length`, `clearance_type`) will be tracked and logged on every invocation. Consider scoping to only the fields used by the workflow. |
| Hardcoded log path comment | `aircraft_crew_exit.py` line 50 | Commented-out absolute path remains; active path uses `Path.cwd()`. |

---

## 10. Extensibility Guidance

- Align the terminal-status retry logic with the operator's actual output values (`completed`/`pending`) — remove references to `requested` and `in progress` unless the operator is extended to produce them
- Trim `FLIGHT_TURNAROUND_TRACKED_FIELDS` to only the fields relevant to crew exit, or document explicitly that this TrackerAPI is intended as the system-wide state store
- Add `stairtruck_connection_status` and `deplaning_equipment_type` to `to_upstream` for symmetric context propagation
- Add `"required": []` to the HOCON `TrackerAPI` parameters schema for consistency with other networks
- Deduplicate the two `to_downstream` blocks under `allow` so the intended field set is unambiguous
- Fix the log message artifacts (`"installed"`, duplicated `"status is"`)

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety systems.
