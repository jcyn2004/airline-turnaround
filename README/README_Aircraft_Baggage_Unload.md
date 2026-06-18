# Aircraft Baggage Unload
## Agentic AI Network – README

> **Configuration file:** `aircraft_baggage_unload.hocon`
> **Implementation file:** `aircraft_baggage_unload.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Unload baggage from an aircraft at the gate during turnaround, after verifying that deplaning equipment (jetbridge or stairtruck) is connected and the aircraft door is open.

---

## 1. Overview

`aircraft_baggage_unload` is an agentic network that orchestrates the baggage unloading process for an arriving aircraft. It is part of the broader **AirlineTurnaround** agentic system.

The network combines:

- An LLM-based orchestration agent (`baggage_unload_agent`) that interprets intent and drives the workflow
- One coded execution tool (`baggage_unload_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_jetbridge_connect`, `aircraft_stairtruck_connect`, `aircraft_door_opening`) resolved from the shared registry `registries/aaosa_basic.hocon`

A key characteristic of this network compared to simpler turnaround agents is that it handles two mutually exclusive deplaning equipment types — **jetbridge (jetway)** and **stairtruck (stair)** — and routes prerequisite fulfillment accordingly.

---

## 2. Repository Structure

```
aircraft_baggage_unload.hocon        # Agent network configuration
aircraft_baggage_unload.py           # Coded tool implementations (baggage_unload_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_jetbridge_connect, aircraft_stairtruck_connect, aircraft_door_opening)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
aicraft_baggage_unload_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                              (Coded tool: read/write turnaround state via sly_data)
   │
   ├── baggage_unload_operator                 (Coded tool: perform baggage unloading)
   │
   ├── /AirlineTurnaround/aircraft_jetbridge_connect    (External tool — jetway gates only)
   │
   ├── /AirlineTurnaround/aircraft_stairtruck_connect   (External tool — stairtruck gates only)
   │
   └── /AirlineTurnaround/aircraft_door_opening         (External tool — when door not yet open)
```

### Design principles

- **Equipment-aware prerequisite gating:** The agent routes the equipment connection step to the correct external tool based on `deplaning_equipment_type`. If the type is unknown, either a connected jetbridge or stairtruck is accepted.
- **Tool-first execution:** All operational actions are performed by coded or external tools; the LLM orchestrates, not executes.
- **sly_data as shared state:** `TrackerAPI` and `baggage_unload_operator` exchange state through the `sly_data` mechanism — parameters flow between tools without re-passing through the LLM.
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

### 5.1 aicraft_baggage_unload_agent (LLM Orchestrator)

The entry-point agent. It parses the user inquiry, enforces prerequisites for the correct equipment type, delegates operational actions, and returns the final summary.

#### Input parameters

|--------------------------------|--------|:--------:|-----------------------------------------------------------------|
| Parameter                      | Type   | Required | Description                                                     |
|--------------------------------|--------|:--------:|-----------------------------------------------------------------|
| `flight_number`                | string | ✅       | Flight identifier                                               |
| `aircraft_type`                | string | ✅       | Aircraft model/type                                             |
| `flight_status`                | string | ✅       | Flight status (expected: `on blocks`)                           |
| `gate_id`                      | string | ✅       | Gate where the aircraft is parked                               |
| `door_opening_status`          | string | ✅       | Aircraft door state (expected: contains `open`)                 |
| `jetbridge_connection_status`  | string | ❌       | Jetbridge state — null on stairtruck gates                      |
| `stairtruck_connection_status` | string | ❌.      | Stairtruck state — null on jetway gates                         |
| `deplaning_equipment_type`     | string | ❌       | Equipment at gate: `jetway`/`jetbridge` or `stairtruck`/`stair` |
| `baggage_unload_status`        | string | ❌       | Current or previous unload status                               |
|--------------------------------|--------|:--------:|-----------------------------------------------------------------|

#### Orchestration flow

1. Parse the inquiry and identify all available parameters.
2. Call `TrackerAPI` — read and store all available parameters.
3. Determine equipment readiness based on `deplaning_equipment_type`:
   - `jetway` / `jetbridge` → equipment ready if `jetbridge_connection_status` contains `connected`
   - `stairtruck` / `stair` → equipment ready if `stairtruck_connection_status` contains `connected`
   - Unknown type → either connection status is accepted
4. If equipment is connected AND `door_opening_status` contains `open` → skip to step 7.
5. If equipment is NOT connected:
   - Jetway gate → call `/AirlineTurnaround/aircraft_jetbridge_connect`
   - Stairtruck gate → call `/AirlineTurnaround/aircraft_stairtruck_connect` (passing `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`)
   - Return to step 2.
6. If door is not open → call `/AirlineTurnaround/aircraft_door_opening` (passing `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`). Return to step 2.
7. Equipment connected and door open → call `baggage_unload_operator`. Capture result as `baggage_unload_status`.
8. Call `TrackerAPI` to persist `baggage_unload_status`.
9. Return the formatted summary block.

#### sly_data contract

|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Direction           | Parameters                                                                                                                                                                                              |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `baggage_unload_status`                                                                                                                                                        |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `door_opening_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `door_opening_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status`, `baggage_unload_status`    |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

#### Down-chain tools

```
["TrackerAPI", "baggage_unload_operator", "/AirlineTurnaround/aircraft_door_opening",
 "/AirlineTurnaround/aircraft_jetbridge_connect", "/AirlineTurnaround/aircraft_stairtruck_connect"]
```

---

### 5.2 baggage_unload_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_baggage_unload.aircraft_baggage_unload.baggage_unload_operator`

Performs the baggage unloading action. It validates all required parameters, checks that at least one piece of deplaning equipment is connected and the door is open, then sets `baggage_unload_status = completed`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

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

#### Connection logic

The operator evaluates `equipment_connected` as:

```
jetbridge_connection_status contains 'connected'
OR
stairtruck_connection_status contains 'connected'
```

`baggage_unload_status` is set to `completed` when both of the following are true (case-insensitive):

- `equipment_connected` is `True`
- `door_opening_status` contains `open`

If either condition fails, the tool returns an error string and does not update `sly_data`. The initial value of `baggage_unload_status` is `pending` (set at the top of `invoke`); this value is returned if conditions are unmet.

#### Output

- Writes `baggage_unload_status` into `sly_data`
- Returns `baggage_unload_status` string (`completed` or `pending`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_baggage_unload.aircraft_baggage_unload.TrackerAPI`

Manages shared turnaround state. Called at the start of the workflow to read current values, and again after `baggage_unload_operator` to persist the updated status.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `baggage_unload_status`, `deplaning_equipment_type`, `door_opening_status`, `flight_number`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`

**Return fields:**
`baggage_unload_status`, `deplaning_equipment_type`, `door_opening_status`, `flight_status`, `jetbridge_connection_status`, `stairtruck_connection_status`

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
The plane has been connected to the jetbridge. The aircraft door is open. Unload baggages."

# Prerequisites not yet confirmed — agent will resolve them
"The B747 aircraft of flight AF84 is on blocks at gate A1. Unload baggages."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. The plane has been connected to the jetbridge. The aircraft door is open. Unload baggages."

**Execution steps:**

1. `TrackerAPI` called — reads: `flight_status=on blocks`, `jetbridge_connection_status=connected`, `door_opening_status=open`
2. Equipment check: jetbridge connected ✅, door open ✅
3. `baggage_unload_operator` called — returns `baggage_unload_status=completed`
4. `TrackerAPI` called again — persists `baggage_unload_status=completed`
5. Summary returned

**Output:**

```
**************************************
* Summary of aircraft baggage unload *
**************************************
** flight status                 **: on blocks
** deplaning equipment type      **: jetway
** jetbridge connection status   **: connected
** stairtruck connection status  **: null
** door opening status           **: open
** baggage unload status         **: completed
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
  "baggage_unload_status": "completed"
}
```

---

## 9. Known Issues and Maintenance Notes

|---------------------------------------------------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| Issue                                                         | Location                                                                 | Notes                                                                                                                                       |
|---------------------------------------------------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| `baggage_unload_operator` HOCON description                   | `aircraft_baggage_unload.hocon`                                          | The tool description says `"This agent unloads baggages from the aircraft."` — should use `"coded tool"` rather than `"agent"` for clarity. |
|---------------------------------------------------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|

---

## 10. Extensibility Guidance

- Add retry and error-code handling to `baggage_unload_operator` for failure scenarios (belt loader unavailable, hold door jammed, etc.)
- Model intermediate statuses: `unloading_started`, `unloading_in_progress`, `unloading_completed` (currently only `completed` or `pending` are returned)
- Back `TrackerAPI` with a persistent store for multi-session traceability
- Add concurrency controls when multiple turnaround networks update the same flight record simultaneously
- Integrate container-level or ULD tracking for cargo flights
- Add parallel unload team modeling for wide-body aircraft with multiple hold doors
- Add `acu_connection_status` and `gpu_connection_status` to the tracked fields, since they are already passed to `aircraft_stairtruck_connect`

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operations.
