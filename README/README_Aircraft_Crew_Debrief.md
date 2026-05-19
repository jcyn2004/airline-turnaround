# Aircraft Crew Debrief
## Agentic AI Network – README

> **Configuration file:** `aircraft_crew_debrief.hocon`
> **Implementation file:** `aircraft_crew_debrief.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Conduct the crew debrief session at the gate during turnaround, after verifying that the deplaning equipment (jetbridge or stairtruck) is connected and the aircraft door is open.

---

## 1. Overview

`aircraft_crew_debrief` is an agentic network that orchestrates the crew debrief process for an arriving aircraft. It is part of the broader **AirlineTurnaround** agentic system.

The network combines:

- An LLM-based orchestration agent (`crew_debrief_agent`) that interprets intent and drives the workflow
- One coded execution tool (`crew_debrief_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_jetbridge_connect`, `aircraft_stairtruck_connect`, `aircraft_door_opening`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network's architecture and orchestration logic are structurally identical to `aircraft_baggage_unload`: both require equipment-based access prerequisites (jetbridge or stairtruck connected, door open) before performing their core operation. Unlike the cabin cleaning and catering loading networks, crew debrief does not check human-clearance prerequisites (passenger disembarkation, baggage unload).

> **Important note on scope:** The previous documentation described this network as a structured reporting system with a `crew_debrief_recorder` component, `debrief_notes` parameter, and report persistence logic. None of these exist in the actual implementation. The network performs an access-gated debrief completion check — it does not capture or persist debrief content.

---

## 2. Repository Structure

```
aircraft_crew_debrief.hocon          # Agent network configuration
aircraft_crew_debrief.py             # Coded tool implementations (crew_debrief_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_jetbridge_connect, aircraft_stairtruck_connect, aircraft_door_opening)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
crew_debrief_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                                       (Coded tool: read/write turnaround state via sly_data)
   │
   ├── crew_debrief_operator                            (Coded tool: perform crew debrief)
   │
   ├── /AirlineTurnaround/aircraft_jetbridge_connect    (External tool — jetway gates only)
   │
   ├── /AirlineTurnaround/aircraft_stairtruck_connect   (External tool — stairtruck gates only)
   │
   └── /AirlineTurnaround/aircraft_door_opening         (External tool — when door not yet open)
```

### Design principles

- **Equipment-aware prerequisite gating:** The agent routes equipment connection to the correct external tool based on `deplaning_equipment_type`. If the type is unknown, either a connected jetbridge or stairtruck is accepted.
- **Access-based (not human-clearance-based) prerequisites:** The gate is equipment connectivity and door status — not passenger or baggage clearance.
- **Tool-first execution:** All operational actions are performed by coded or external tools; the LLM orchestrates, not executes.
- **sly_data as shared state:** Parameters flow between tools without re-passing through the LLM.
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

### 5.1 crew_debrief_agent (LLM Orchestrator)

The entry-point agent. It parses the user inquiry, enforces equipment-access prerequisites, delegates prerequisite resolution to external networks, executes the debrief, and returns the final summary.

> Note: The agent is named `crew_debrief_agent` in the HOCON. The previous documentation referred to it as `aircraft_crew_debrief_agent`, which does not match the actual runtime tool name.

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

1. Determine what is provided from the inquiry: `jetbridge_connection_status` or `stairtruck_connection_status`, `door_opening_status`, `flight_status`, `deplaning_equipment_type`.
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
7. Equipment connected and door open → call `crew_debrief_operator`. Capture result as `crew_debrief_status`.
8. Call `TrackerAPI` to persist `crew_debrief_status`.
9. Return the formatted summary block.

#### sly_data contract

|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Direction           | Parameters                                                                                                                                                                                            |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `crew_debrief_status`                                                                                                                                                          |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `door_opening_status`, `jetbridge_connection_status`, `stairtruck_connection_status`                             |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

> Note: Unlike `aircraft_baggage_unload`, where `to_downstream` carries the full parameter set, this network's `to_upstream` and `to_downstream` each carry only `crew_debrief_status`. The full context parameters flow in both `from_upstream` and `from_downstream` directions.

#### Down-chain tools

```
["TrackerAPI", "crew_debrief_operator", "/AirlineTurnaround/aircraft_door_opening",
 "/AirlineTurnaround/aircraft_jetbridge_connect", "/AirlineTurnaround/aircraft_stairtruck_connect"]
```

---

### 5.2 crew_debrief_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_crew_debrief.aircraft_crew_debrief.crew_debrief_operator`

Performs the crew debrief completion check. It validates all required parameters, verifies that at least one piece of deplaning equipment is connected and the door is open, then sets `crew_debrief_status = completed`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

> Note: The previous documentation described a `crew_debrief_recorder` component that persists structured debrief reports and captures `debrief_notes`. No such component exists. The operator confirms access conditions are met and records completion status only.

#### Input parameters

|--------------------------------|--------|:--------:|---------------------|
| Parameter                      | Type   | Required | Source priority     |
|--------------------------------|--------|:--------:|---------------------|
| `flight_number`                | string | ✅       | `args` → `sly_data` |
| `aircraft_type`                | string | ✅       | `args` → `sly_data` |
| `flight_status`                | string | ❌       | `args` → `sly_data` |
| `gate_id`                      | string | ✅       | `args` → `sly_data` |
| `door_opening_status`          | string | ✅       | `args` → `sly_data` |
| `jetbridge_connection_status`  | string | ❌       | `args` → `sly_data` |
| `stairtruck_connection_status` | string | ❌       | `args` → `sly_data` |
|--------------------------------|--------|:--------:|---------------------|

> Note: The HOCON `required` list for `crew_debrief_operator` is `["flight_number", "aircraft_type", "gate_id", "door_opening_status"]` — `flight_status` is not in that list. The Python implementation, however, returns an error if `flight_status` cannot be resolved from `args` or `sly_data`. Treat `flight_status` as functionally required by the operator at runtime even though the HOCON schema does not mark it required.

#### Debrief logic

The operator evaluates `equipment_connected` as:

```
jetbridge_connection_status contains 'connected'
OR
stairtruck_connection_status contains 'connected'
```

`crew_debrief_status` is set to `completed` when both of the following are true (case-insensitive):

- `equipment_connected` is `True`
- `door_opening_status` contains `open`

If `equipment_connected` is False, the tool returns an error string immediately without updating `sly_data`. If conditions are met, the status is written to `sly_data` and returned. If the conditions check passes but `door_opening_status` is missing, the tool also returns an error string.

The initial value of `crew_debrief_status` is `pending`; this is returned if the door check fails after equipment is confirmed connected.

#### Output

- Writes `crew_debrief_status` into `sly_data`
- Returns `crew_debrief_status` string (`completed` or `pending`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_crew_debrief.aircraft_crew_debrief.TrackerAPI`

Manages shared turnaround state. Called at the start of the workflow to read current values, and again after `crew_debrief_operator` to persist the updated status.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `crew_debrief_status`, `deplaning_equipment_type`, `door_opening_status`, `flight_number`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`

**Return fields:**
`crew_debrief_status`, `deplaning_equipment_type`, `door_opening_status`, `flight_status`, `jetbridge_connection_status`, `stairtruck_connection_status`

> Note: The HOCON `TrackerAPI` parameters schema also exposes additional fields (e.g. `ground_services_request_type`, `wheels_chocks_readiness_status`, `wheels_chocks_installation_status`, `gpu_readiness_status`, `acu_connection_status`, `gpu_connection_status`, `engines_stop_status`, `passenger_disembarkation_status`, `baggage_unload_status`). These are accepted on the LLM-facing interface but are not part of the Python default `tracked_fields` / `return_fields` for this network — they are not persisted or returned by default.

> Note: The HOCON `TrackerAPI` tool definition declares `"required": []` in its `parameters` object — no fields are required at the schema level. All field resolution is handled at runtime by the Python tracker.

---

## 6. External Tool Dependencies

These tools are not defined in this network. They are resolved at runtime from `registries/aaosa_basic.hocon`:

|--------------------------------------------------|------------------------------- |------------------------------------------------|
| Tool path                                        | Purpose                        | Condition triggering call                      |
|--------------------------------------------------|------------------------------- |------------------------------------------------|
| `/AirlineTurnaround/aircraft_jetbridge_connect`  | Connect jetbridge to aircraft  | Equipment not connected on a jetway gate       |
| `/AirlineTurnaround/aircraft_stairtruck_connect` | Connect stairtruck to aircraft | Equipment not connected on a stairtruck gate   |
| `/AirlineTurnaround/aircraft_door_opening`       | Open aircraft door             | Door not yet open after equipment is connected |
|--------------------------------------------------|------------------------------- |------------------------------------------------|

---

## 7. Sample Queries

```
# All prerequisites already met
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The plane has been connected to the jetbridge. The aircraft door is open.
Debrief the crew."

# Prerequisites not yet confirmed — agent will resolve them
"The B747 aircraft of flight AF84 is on blocks at gate A1. Debrief the crew."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. The plane has been connected to the jetbridge. The aircraft door is open. Debrief the crew."

**Execution steps:**

1. `TrackerAPI` called — reads: `flight_status=on blocks`, `jetbridge_connection_status=connected`, `door_opening_status=open`
2. Equipment check: jetbridge connected ✅, door open ✅
3. `crew_debrief_operator` called — returns `crew_debrief_status=completed`
4. `TrackerAPI` called again — persists `crew_debrief_status=completed`
5. Summary returned

**Output:**

```
************************************
* Summary of aircraft crew debrief *
************************************
** flight status                 **: on blocks
** deplaning equipment type      **: jetway
** jetbridge connection status   **: connected
** stairtruck connection status  **: null
** door opening status           **: open
** crew debrief status           **: completed
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
  "crew_debrief_status": "completed"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Notes |
|---|---|---|
| `debrief_notes` parameter does not exist | Previous documentation vs. actual implementation | The prior doc listed `debrief_notes` as an input parameter and described a `crew_debrief_recorder` component. Neither exists. The operator only records `crew_debrief_status = completed`. |
| `flight_status` not in HOCON `required` for `crew_debrief_operator` | `aircraft_crew_debrief.hocon` | The Python implementation validates `flight_status` and errors if missing, but the HOCON parameter `required` list omits it. Functional requirement is enforced at runtime by Python rather than at the schema level. |

---

## 10. Extensibility Guidance

- Add structured debrief content capture if actual crew debrief recording is required — a `debrief_notes` field and a persistence step (database write or document store) would need to be added to both the HOCON schema and the operator
- Add integration with safety management systems (SMS) for incident reporting triggered by debrief content
- Consider adding `crew_exit_status` as a tracked field since crew debrief logically follows crew exit

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation regulatory reporting systems.
