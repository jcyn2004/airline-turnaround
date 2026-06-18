# Aircraft ACU Connect
## Agentic AI Network – README

> **Configuration file:** `aircraft_acu_connect.hocon`
> **Implementation file:** `aircraft_acu_connect.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Connect an aircraft's ACU (Air Conditioning Unit) at the gate during turnaround, after verifying that the aircraft is on blocks, engines are stopped, and wheel chocks are installed.

---

## 1. Overview

`aircraft_acu_connect` is a production-oriented agentic network that orchestrates the steps required to connect an ACU unit to an aircraft parked at a gate. It is part of the broader **AirlineTurnaround** agentic system.

The network combines:

- An LLM-based orchestration agent (`acu_connect_agent`) that interprets intent and drives the workflow
- Two coded execution tools (`acu_operator`, `TrackerAPI`) implemented in Python
- Two external tool references (`aircraft_engines_stop`, `aircraft_chocks_install`) resolved from the shared registry `registries/aaosa_basic.hocon`
- An explicit safety gate that blocks ACU connection when any prerequisite is unmet

---

## 2. Repository Structure

```
aircraft_acu_connect.hocon       # Agent network configuration
aircraft_acu_connect.py          # Coded tool implementations (acu_operator, TrackerAPI)
registries/aaosa_basic.hocon     # Shared registry (aircraft_engines_stop, aircraft_chocks_install)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
aircraft_acu_connect_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                        (Coded tool: read/write turnaround state via sly_data)
   │
   ├── aircraft_engines_stop             (External tool from aaosa_basic registry)
   │
   ├── aircraft_chocks_install           (External tool from aaosa_basic registry)
   │
   └── acu_operator                      (Coded tool: perform ACU connection)
```

### Design principles

- **Prerequisite gating:** ACU connection is only attempted when the aircraft is on blocks, engines are stopped, and wheel chocks are installed. Any unmet prerequisite halts the flow.
- **Tool-first execution:** All operational actions are performed by coded or external tools; the LLM orchestrates, not executes.
- **sly_data as shared state:** `TrackerAPI` and `acu_operator` exchange state through the `sly_data` mechanism — parameters flow between tools without re-passing through the LLM.
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

These bounds accommodate multi-step retry loops (e.g., engines stop → re-check → chocks install → re-check → ACU connect).

---

## 5. Components

### 5.1 aircraft_acu_connect_agent (LLM Orchestrator)

The entry-point agent. It parses the user inquiry, enforces prerequisites, delegates operational actions, and returns the final summary.

#### Input parameters

|-------------------------------------|--------|:--------:|---------------------------------------------|
| Parameter                           | Type   | Required | Description                                 |
|-------------------------------------|--------|:--------:|---------------------------------------------|
| `flight_number`                     | string | ✅       | Flight identifier                           |
| `aircraft_type`                     | string | ✅       | Aircraft model/type                         |
| `flight_status`                     | string | ✅       | Flight status (expected: `on blocks`)       |
| `gate_id`                           | string | ✅       | Gate where the aircraft is parked           |
| `engines_stop_status`               | string | ❌       | Engine state (`stopped`, `running`)         |
| `wheels_chocks_installation_status` | string | ❌       | Chocks state (`installed`, `not installed`) |
|-------------------------------------|--------|:--------:|---------------------------------------------|

#### Orchestration flow

1. Parse the inquiry and extract all available parameters.
2. Call `TrackerAPI` — read and store `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`.
3. If `flight_status ≠ on blocks` → abort and report that ACU cannot be connected.
4. If `engines_stop_status ≠ stopped` → call `aircraft_engines_stop`, then return to step 2.
5. If `wheels_chocks_installation_status ≠ installed` → call `aircraft_chocks_install`, then return to step 2.
6. When all prerequisites are met → call `acu_operator` and capture `acu_connection_status`.
7. Call `TrackerAPI` again to persist the updated state.
8. Return the formatted summary block.

#### sly_data contract

|---------------------|---------------------------------------------------------------------------------------------------------------------------------|
| Direction           | Parameters                                                                                                                      |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------|
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`        |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`        |
| **To upstream**     | `acu_connection_status`                                                                                                         |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`        |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------|

#### Down-chain tools

```
["acu_operator", "/AirlineTurnaround/aircraft_engines_stop", "/AirlineTurnaround/aircraft_chocks_install", "TrackerAPI"]
```

---

### 5.2 acu_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_acu_connect.aircraft_acu_connect.acu_operator`

Performs the physical ACU connection. It validates all required parameters, checks that engines are stopped and chocks are installed, sets `acu_connection_status = connected`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

#### Input parameters

|-------------------------------------|--------|:--------:|---------------------|
| Parameter                           | Type   | Required | Source priority     |
|-------------------------------------|--------|:--------:|---------------------|
| `flight_number`                     | string | ✅       | `args` → `sly_data` |
| `aircraft_type`                     | string | ✅       | `args` → `sly_data` |
| `flight_status`                     | string | ✅       | `args` → `sly_data` |
| `gate_id`                           | string | ✅       | `args` → `sly_data` |
| `acu_connection_status`             | string | ❌       | `args` → `sly_data` |
|-------------------------------------|--------|:--------:|---------------------|

#### Connection logic

`acu_connection_status` is set to `connected` when both of the following conditions are true (case-insensitive):

- `engines_stop_status` contains `stopped` or `done`
- `wheels_chocks_installation_status` contains `installed` or `done`

If either condition is not met, no status is written and the tool returns without updating `sly_data`.

#### Output

- Writes `acu_connection_status` into `sly_data`
- Returns `acu_connection_status` string
- Appends a log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_acu_connect.aircraft_acu_connect.TrackerAPI`

Acts as the shared state manager for the turnaround network. It is called multiple times during a workflow — first to read current status, and again after each action to persist updated values.

#### Data resolution priority

For each tracked field, `TrackerAPI` applies this precedence:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; the value is written into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass. Configuration is resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `acu_connection_status`, `engines_stop_status`, `flight_number`, `flight_status`, `gate_id`, `wheels_chocks_installation_status`

**Return fields:**
`acu_connection_status`, `engines_stop_status`, `flight_status`, `wheels_chocks_installation_status`

#### Notes

- The HOCON uses the field name `wheels_chucks_installation_status` (typo: "chucks") in the agent instructions and in the TrackerAPI description, while the Python code and the HOCON parameter schema use `wheels_chocks_installation_status`. The coded tools use the correct spelling; the typo exists only in the LLM instruction text and description.

---

## 6. External Tool Dependencies

These tools are not defined in this network. They are resolved at runtime from `registries/aaosa_basic.hocon`:

|----------------------------------------------|--------------------------------------------------------------|
| Tool path                                    | Purpose                                                      |
|----------------------------------------------|--------------------------------------------------------------|
| `/AirlineTurnaround/aircraft_engines_stop`   | Commands engine shutdown when engines are still running      |
| `/AirlineTurnaround/aircraft_chocks_install` | Commands chock installation when chocks are not yet in place |
|----------------------------------------------|--------------------------------------------------------------|

---

## 7. Sample Queries

```
# All prerequisites already met
"The B747 aircraft of flight AF84 is on blocks at gate A1. 
The engines are stopped and wheels chocks have been installed. Connect the ACU."

# Prerequisites not yet confirmed — agent will resolve them
"The B747 aircraft of flight AF84 is on blocks at gate A1. Connect the ACU."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. The engines are stopped and wheels chocks have been installed. Connect the ACU."

**Execution steps:**

1. `TrackerAPI` called — reads: `flight_status=on blocks`, `engines_stop_status=stopped`, `wheels_chocks_installation_status=installed`
2. Prerequisites validated: on blocks ✅, engines stopped ✅, chocks installed ✅
3. `acu_operator` called — returns `acu_connection_status=connected`
4. `TrackerAPI` called again — persists `acu_connection_status=connected`
5. Summary returned

**Output:**

```
***********************************
* Summary of aircraft acu connect *
***********************************
** engines stop status **:               stopped
** wheels chocks installation status **: installed
** acu connection status summary **:     connected
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "engines_stop_status": "stopped",
  "wheels_chocks_installation_status": "installed",
  "acu_connection_status": "connected"
}
```

---

## 9. Known Issues and Maintenance Notes

|-------|----------|--------|
| Issue | Location | Notes  |
|-------|----------|--------|
|       |          |        |
|-------|----------|--------|

---

## 10. Extensibility Guidance

- Add retry and error code handling to `acu_operator` for connection failures
- Back `TrackerAPI` with a persistent store (database, message queue) for multi-session traceability
- Add concurrency controls when multiple turnaround networks update the same flight record simultaneously
- Implement `acu_readiness_status` pre-checks (already tracked in HOCON) before attempting connection
- Add structured telemetry (traces, metrics) around all tool calls

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operations.
