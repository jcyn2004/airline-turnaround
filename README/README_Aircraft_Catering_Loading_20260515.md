# Aircraft Catering Loading
## Agentic AI Network – README

> **Configuration file:** `aircraft_catering_loading.hocon`
> **Implementation file:** `aircraft_catering_loading.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Load catering onto an aircraft at the gate during turnaround, after verifying that passengers have disembarked, crew has exited, and baggage has been unloaded.

---

## 1. Overview

`aircraft_catering_loading` is an agentic network that orchestrates the catering loading process for an aircraft in turnaround. It is part of the broader **AirlineTurnaround** agentic system.

The network combines:

- An LLM-based orchestration agent (`catering_loading_agent`) that interprets intent and drives the workflow
- One coded execution tool (`catering_loading_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_disembark`, `aircraft_crew_exit`, `aircraft_baggage_unload`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network shares the same human-clearance prerequisite pattern as `aircraft_cabin_cleaning`: catering cannot be loaded until the cabin is clear of passengers, crew, and hold baggage. Like the cabin cleaning network, this network uses explicit numbered sequential steps (STEP 1 through STEP 6) in its LLM instructions, and the agent is declared a "sequential executor" that must not return until reaching RETURN SUMMARY.

---

## 2. Repository Structure

```
aircraft_catering_loading.hocon      # Agent network configuration
aircraft_catering_loading.py         # Coded tool implementations (catering_loading_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_disembark, aircraft_crew_exit, aircraft_baggage_unload)
```

---

## 3. System Architecture

```
User / Caller
   |
   v
catering_loading_agent  (LLM Orchestrator)
   |
   |-- TrackerAPI                                   (Coded tool: read/write turnaround state via sly_data)
   |
   |-- catering_loading_operator                    (Coded tool: perform catering loading)
   |
   |-- /AirlineTurnaround/aircraft_disembark        (External tool -- if passengers not yet off)
   |
   |-- /AirlineTurnaround/aircraft_crew_exit        (External tool -- if crew not yet off)
   |
   `-- /AirlineTurnaround/aircraft_baggage_unload   (External tool -- if baggage not yet unloaded)
```

### Design principles

- **Human-clearance prerequisite gating:** Catering loading is only initiated once passengers have disembarked, crew has exited, and baggage has been unloaded. All three must be confirmed before the operator is called.
- **Active prerequisite resolution:** If any prerequisite is unmet, the agent calls the relevant external turnaround network to resolve it rather than aborting.
- **Tool-first execution:** All operational actions are performed by coded or external tools; the LLM orchestrates, not executes.
- **sly_data as shared state:** `TrackerAPI` and `catering_loading_operator` exchange state through `sly_data` — parameters flow between tools without re-passing through the LLM.
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

### 5.1 catering_loading_agent (LLM Orchestrator)

The entry-point agent. It parses the user inquiry, enforces a flight-status precondition and human-clearance prerequisites, delegates resolution to external networks as needed, executes catering loading, and returns the final summary.

#### Input parameters

|-----------------------------------|--------|:--------:|-------------------------------------------------------------|
| Parameter                         | Type   | Required | Description                                                 |
|-----------------------------------|--------|:--------:|-------------------------------------------------------------|
| `gate_id`                         | string | Yes      | Gate where the aircraft is parked                           |
| `passenger_disembarkation_status` | string | Yes      | Expected: contains `completed`                              |
| `crew_exit_status`                | string | Yes      | Expected: contains `completed` or `exited`                  |
| `baggage_unload_status`           | string | Yes      | Expected: contains `completed` or `unloaded`                |
| `flight_number`                   | string | No       | Flight identifier                                           |
| `aircraft_type`                   | string | No       | Aircraft model/type                                         |
| `flight_status`                   | string | No       | Flight status (expected: contains `on blocks` or `block`)   |
|-----------------------------------|--------|:--------:|-------------------------------------------------------------|

> Note: The HOCON `required` array for the agent includes `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, and `baggage_unload_status`, but not `flight_number`, `aircraft_type`, or `flight_status`. The `catering_loading_operator` HOCON `required` array adds `flight_number` and `aircraft_type` (but still not `flight_status`). Fields omitted from the orchestrator's required list are expected to be available from `sly_data`.

#### Orchestration flow

The HOCON instructions declare the agent a "sequential executor" that must execute every numbered step in order and not return until reaching RETURN SUMMARY:

1. **STEP 1 — Collect parameters.** Read `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` from the inquiry or from `sly_data` via `TrackerAPI`. Call `TrackerAPI` to store available values and read back any missing ones.
2. **STEP 2 — Verify flight status.** `flight_status` must contain `on blocks` or `block`. If not, report that the aircraft is not yet on blocks and stop.
3. **STEP 3 — Verify passenger disembarkation.** If `passenger_disembarkation_status` does not contain `completed`, call `/AirlineTurnaround/aircraft_disembark` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`. Wait. Store `passenger_disembarkation_status`.
4. **STEP 4 — Verify crew exit.** If `crew_exit_status` does not contain `completed` or `exited`, call `/AirlineTurnaround/aircraft_crew_exit` with the same four parameters. Wait. Store `crew_exit_status`.
5. **STEP 5 — Verify baggage unload.** If `baggage_unload_status` does not contain `completed` or `unloaded`, call `/AirlineTurnaround/aircraft_baggage_unload` with the same four parameters. Wait. Store `baggage_unload_status`.
6. **STEP 6 — Execute catering loading.** With all prerequisites confirmed, call `catering_loading_operator` with all seven parameters. Wait. Store `catering_loading_status` from the response and call `TrackerAPI` to store it.
7. **RETURN SUMMARY** — return the formatted summary block.

> Note: Unlike `aircraft_cabin_cleaning`, this agent has no explicit re-read/re-loop step after prerequisite resolution; each STEP 3–5 stores its own status inline before the next STEP runs. The final `TrackerAPI` persistence call occurs inside STEP 6.

#### sly_data contract

|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Direction           | Parameters                                                                                                                                                           |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `catering_loading_status`                                                                                                                                            |
| **From upstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `catering_loading_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `catering_loading_status` |
| **To downstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `catering_loading_status` |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|

> Note: `catering_loading_status` is included in all four allow blocks — it is what this network propagates to upstream, and it is also permitted in both downstream directions and from upstream. The `to_upstream` block lists only `catering_loading_status` because that is the new value this network produces.

#### Down-chain tools

```
["TrackerAPI", "catering_loading_operator", "/AirlineTurnaround/aircraft_disembark",
 "/AirlineTurnaround/aircraft_crew_exit", "/AirlineTurnaround/aircraft_baggage_unload"]
```

---

### 5.2 catering_loading_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_catering_loading.aircraft_catering_loading.catering_loading_operator`

Performs the catering loading action. It validates required parameters, checks that all three human-clearance prerequisites are satisfied, then sets `catering_loading_status = completed`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

#### Input parameters

|-----------------------------------|--------|:--------:|---------------------|
| Parameter                         | Type   | Required | Source priority     |
|-----------------------------------|--------|:--------:|---------------------|
| `flight_number`                   | string | Yes      | `args` -> `sly_data` |
| `aircraft_type`                   | string | Yes      | `args` -> `sly_data` |
| `flight_status`                   | string | No       | `args` -> `sly_data` |
| `gate_id`                         | string | Yes      | `args` -> `sly_data` |
| `passenger_disembarkation_status` | string | Yes      | `args` -> `sly_data` |
| `crew_exit_status`                | string | Yes      | `args` -> `sly_data` |
| `baggage_unload_status`           | string | Yes      | `args` -> `sly_data` |
|-----------------------------------|--------|:--------:|---------------------|

The HOCON `required` array for this tool lists six fields: `flight_number`, `aircraft_type`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`. `flight_status` is declared as a property but is not in `required`. If any required field is missing from both `args` and `sly_data`, the tool returns an error string immediately.

#### Loading logic

`catering_loading_status` is set to `completed` when **all three** of the following conditions are true (case-insensitive, after stripping whitespace):

|-----------------------------------|-------------------------|
| Field                             | Accepted values         |
|-----------------------------------|-------------------------|
| `passenger_disembarkation_status` | `completed`, `done`     |
| `crew_exit_status`                | `completed`, `exited`   |
| `baggage_unload_status`           | `completed`, `unloaded` |
|-----------------------------------|-------------------------|

If any condition fails, the tool returns `pending` (the initial value set at the top of `invoke`) without updating `sly_data`.

#### Output

- Writes `catering_loading_status` into `sly_data`
- Returns `catering_loading_status` string (`completed` or `pending`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_catering_loading.aircraft_catering_loading.TrackerAPI`

Manages shared turnaround state. Called at the start of the workflow (STEP 1) to read current values and again at the end of STEP 6 to persist the updated `catering_loading_status`.

This network's `TrackerAPI` declares the broadest parameter surface in the network — its `properties` block lists `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `ground_services_request_type`, `wheels_chocks_readiness_status`, `wheels_chocks_installation_status`, `gpu_readiness_status`, `acu_connection_status`, `gpu_connection_status`, `engines_stop_status`, `jetbridge_connection_status`, `door_opening_status`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, and `catering_loading_status`. The `required` array is empty, so any subset of these may be supplied per call.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` -> `sly_data['_tracker_config']` -> default config (lazy-initialized once per request).

---

## 6. External Tool Dependencies

These tools are not defined in this network. They are resolved at runtime from `registries/aaosa_basic.hocon`:

|----------------------------------------------|-----------------------------------|--------------------------------------------------------------------|
| Tool path                                    | Purpose                           | Condition triggering call                                          |
|----------------------------------------------|-----------------------------------|--------------------------------------------------------------------|
| `/AirlineTurnaround/aircraft_disembark`      | Complete passenger disembarkation | `passenger_disembarkation_status` does not contain `completed`     |
| `/AirlineTurnaround/aircraft_crew_exit`      | Complete crew exit                | `crew_exit_status` does not contain `completed` or `exited`        |
| `/AirlineTurnaround/aircraft_baggage_unload` | Complete baggage unloading        | `baggage_unload_status` does not contain `completed` or `unloaded` |
|----------------------------------------------|-----------------------------------|--------------------------------------------------------------------|

---

## 7. Sample Queries

```
# All prerequisites already confirmed
"The B747 aircraft of flight AF84 is on blocks at gate A1. Baggages have been unloaded.
All passengers have disembarked. The crew has exited the aircraft.
Load catering to the aircraft."

# Prerequisites not yet confirmed -- agent will resolve them
# (no explicit second sample query in the HOCON metadata)
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. Baggages have been unloaded. All passengers have disembarked. The crew has exited the aircraft. Load catering to the aircraft."

**Execution steps:**

1. STEP 1: `TrackerAPI` called -- reads: `flight_status=on blocks`, `passenger_disembarkation_status=completed`, `crew_exit_status=exited`, `baggage_unload_status=completed`
2. STEP 2: Flight status check passes (`on blocks` contains `block`)
3. STEPS 3-5: All prerequisites already satisfied: passengers off, crew off, baggage unloaded -- no external tool calls needed
4. STEP 6: `catering_loading_operator` called -- returns `catering_loading_status=completed`; `TrackerAPI` called again to persist
5. RETURN SUMMARY block returned

**Output:**

```
**************************************
* Summary of aircraft catering loading *
**************************************
** catering loading summary **:
** flight number **:                        AF84
** aircraft type **:                        B747
** gate id **:                              A1
** flight status **:                        on blocks
** passenger disembarkation status **:      completed
** crew exit status **:                     exited
** baggage unload status **:                completed
** catering loading status **:              completed
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
  "catering_loading_status": "completed"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Notes |
|-------|----------|-------|
| Typo in instructions: "Execute cateriung loading" | `aircraft_catering_loading.hocon` STEP 6 header | Cosmetic only; does not affect execution. |
| Agent `instructions` reads "Only use your tools to fulfill cabin cleaning tasks." | `aircraft_catering_loading.hocon` agent instructions (near the top) | Appears to be a copy-paste from `aircraft_cabin_cleaning`; should read "catering loading tasks". |

---

## 10. Extensibility Guidance

- Model intermediate statuses: `loading_started`, `loading_in_progress`, `loading_completed` (currently only `completed` or `pending` are returned by the operator)
- Back `TrackerAPI` with a persistent store for multi-session traceability
- Integrate catering inventory validation before the loading step
- Add meal count and galley position details to the operator for wide-body aircraft

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operations.
