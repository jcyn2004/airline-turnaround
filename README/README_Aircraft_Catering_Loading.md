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

- An LLM-based orchestration agent (`Catering_loading_agent`) that interprets intent and drives the workflow
- One coded execution tool (`catering_loading_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_disembark`, `aircraft_crew_exit`, `aircraft_baggage_unload`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network shares the same human-clearance prerequisite pattern as `aircraft_cabin_cleaning`: catering cannot be loaded until the cabin is clear of passengers, crew, and hold baggage. Unlike the cabin cleaning network, this network does not use explicit numbered sequential steps in its LLM instructions — it uses a more traditional conditional flow.

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
   │
   ▼
Catering_loading_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                                   (Coded tool: read/write turnaround state via sly_data)
   │
   ├── catering_loading_operator                    (Coded tool: perform catering loading)
   │
   ├── /AirlineTurnaround/aircraft_disembark        (External tool — if passengers not yet off)
   │
   ├── /AirlineTurnaround/aircraft_crew_exit        (External tool — if crew not yet off)
   │
   └── /AirlineTurnaround/aircraft_baggage_unload   (External tool — if baggage not yet unloaded)
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

### 5.1 Catering_loading_agent (LLM Orchestrator)

The entry-point agent. It parses the user inquiry, enforces human-clearance prerequisites, delegates resolution to external networks as needed, executes catering loading, and returns the final summary.

> Note: The agent name in the HOCON is `Catering_loading_agent` (capital C, underscore). This differs from the all-lowercase snake_case convention used in all other networks in this system (e.g. `cabin_cleaning_agent`, `baggage_unload_agent`). The effective tool name at runtime follows whatever the HOCON declares.

#### Input parameters

|-----------------------------------|--------|:--------:|-------------------------------------------------------------|
| Parameter                         | Type   | Required | Description                                                 |
|-----------------------------------|--------|:--------:|-------------------------------------------------------------|
| `gate_id`                         | string | ✅       | Gate where the aircraft is parked                           |
| `passenger_disembarkation_status` | string | ✅       | Expected: contains `completed`                              |
| `crew_exit_status`                | string | ✅       | Expected: contains `completed` or `exited`                  |
| `baggage_unload_status`           | string | ✅       | Expected: contains `completed` or `unloaded`                |
| `flight_number`                   | string | ❌       | Flight identifier                                           |
| `aircraft_type`                   | string | ❌       | Aircraft model/type                                         |
| `flight_status`                   | string | ❌       | Flight status (expected: contains `on blocks` or `at gate`) |
|-----------------------------------|--------|:--------:|-------------------------------------------------------------|

> Note: The HOCON `required` array includes `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, and `baggage_unload_status`, but not `flight_number`, `aircraft_type`, or `flight_status` — even though all seven are required by `catering_loading_operator`. The three omitted fields are expected to be available from `sly_data`.

#### Orchestration flow

1. Determine which of the following are provided: `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `gate_id`, `flight_status`, `flight_number`, `aircraft_type`.
2. Call `TrackerAPI` — read and store all available parameters.
3. If all three clearance statuses are satisfied (`passenger_disembarkation_status` contains `completed`, `crew_exit_status` contains `completed`, `baggage_unload_status` contains `completed`) → skip to step 6.
4. If any prerequisite is unmet, call the relevant external tool(s) to resolve them. Wait for all responses.
5. Call `TrackerAPI` again — re-read and store all statuses. If any prerequisite is still unmet, return to step 3.
6. Call `catering_loading_operator` with all parameters. Capture result as `catering_loading_status`.
7. Call `TrackerAPI` to persist `catering_loading_status` and refresh all parameters.
8. Return the formatted summary block.

> Note: Step 4 in the orchestrator instructions calls "your tools" without specifying which ones — the LLM is expected to select the appropriate external tools from its toolset based on which prerequisites are missing. This is less explicit than the step-by-step approach used in `aircraft_cabin_cleaning`.

#### sly_data contract

|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| Direction           | Parameters                                                                                                                                   |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `catering_loading_status`                                                                                                                    |
| **From upstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |
| **To downstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------|

> Note: `catering_loading_status` is propagated upstream only. It is not included in `to_downstream`, `from_upstream`, or `from_downstream`. This means downstream networks cannot receive the catering status via sly_data from this network unless they pull it independently.

#### Down-chain tools

```
["TrackerAPI", "catering_loading_operator", "/AirlineTurnaround/aircraft_disembark",
 "/AirlineTurnaround/aircraft_crew_exit", "/AirlineTurnaround/aircraft_baggage_unload"]
```

---

### 5.2 catering_loading_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_catering_loading.aircraft_catering_loading.catering_loading_operator`

Performs the catering loading action. It validates all required parameters, checks that all three human-clearance prerequisites are satisfied, then sets `catering_loading_status = completed`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

#### Input parameters

|-----------------------------------|--------|:--------:|---------------------|
| Parameter                         | Type   | Required | Source priority     |
|-----------------------------------|--------|:--------:|---------------------|
| `flight_number`                   | string | ✅       | `args` → `sly_data` |
| `aircraft_type`                   | string | ✅       | `args` → `sly_data` |
| `flight_status`                   | string | ✅       | `args` → `sly_data` |
| `gate_id`                         | string | ✅       | `args` → `sly_data` |
| `passenger_disembarkation_status` | string | ✅       | `args` → `sly_data` |
| `crew_exit_status`                | string | ✅       | `args` → `sly_data` |
| `baggage_unload_status`           | string | ✅       | `args` → `sly_data` |
|-----------------------------------|--------|:--------:|---------------------|

All seven parameters are hard-required. If any is missing from both `args` and `sly_data`, the tool returns an error string immediately.

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

Manages shared turnaround state. Called at the start of the workflow to read current values, again after prerequisite resolution, and again after `catering_loading_operator` to persist the updated status.

This network's `TrackerAPI` is notable for having the most comprehensive default **return fields** of any network in the system — it returns `aircraft_type`, `baggage_unload_status`, `catering_loading_status`, `crew_exit_status`, `flight_number`, `flight_status`, and `gate_id`, giving the orchestrator a full context snapshot on each call.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `baggage_unload_status`, `catering_loading_status`, `crew_exit_status`, `flight_number`, `flight_status`, `gate_id`, `passenger_disembarkation_status`

**Return fields:**
`aircraft_type`, `baggage_unload_status`, `catering_loading_status`, `crew_exit_status`, `flight_number`, `flight_status`, `gate_id`

> Note: `passenger_disembarkation_status` is tracked but not returned. The orchestrator must rely on the value already present in `sly_data` or passed through `args` after the initial `TrackerAPI` call.

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

# Prerequisites not yet confirmed — agent will resolve them
# (no explicit second sample query in the HOCON metadata)
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. Baggages have been unloaded. All passengers have disembarked. The crew has exited the aircraft. Load catering to the aircraft."

**Execution steps:**

1. `TrackerAPI` called — reads: `flight_status=on blocks`, `passenger_disembarkation_status=completed`, `crew_exit_status=exited`, `baggage_unload_status=completed`
2. All prerequisites satisfied: passengers off ✅, crew off ✅, baggage unloaded ✅
3. `catering_loading_operator` called — returns `catering_loading_status=completed`
4. `TrackerAPI` called again — persists `catering_loading_status=completed`
5. Summary returned

**Output:**

```
****************************************
* Summary of aircraft catering loading *
****************************************
** flight number **:                        AF84
** aircraft type **:                        B747
** flight status **:                        on blocks
** gate id **:                              A1
** crew exit status **:                     exited
** passenger disembarkation status **:      completed
** baggage unload status **:                completed
** catering loading service summary **:     completed
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
|       |          |       |

---

## 10. Extensibility Guidance

- Model intermediate statuses: `loading_started`, `loading_in_progress`, `loading_completed` (currently only `completed` or `pending` are returned by the operator)
- Back `TrackerAPI` with a persistent store for multi-session traceability
- Integrate catering inventory validation before the loading step
- Add meal count and galley position details to the operator for wide-body aircraft

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operations.
