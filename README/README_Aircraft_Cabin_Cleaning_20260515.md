# Aircraft Cabin Cleaning
## Agentic AI Network – README

> **Configuration file:** `aircraft_cabin_cleaning.hocon`
> **Implementation file:** `aircraft_cabin_cleaning.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Clean the aircraft cabin at the gate during turnaround, after verifying that passengers have disembarked, crew has exited, and baggage has been unloaded.

---

## 1. Overview

`aircraft_cabin_cleaning` is an agentic network that orchestrates cabin cleaning for an arriving aircraft. It is part of the broader **AirlineTurnaround** agentic system.

The network combines:

- An LLM-based orchestration agent (`cabin_cleaning_agent`) that interprets intent and drives the workflow
- One coded execution tool (`cabin_cleaning_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_disembark`, `aircraft_crew_exit`, `aircraft_baggage_unload`) resolved from the shared registry `registries/aaosa_basic.hocon`

A key characteristic of this network compared to equipment-focused turnaround agents is that its prerequisites are **human-clearance gates** — the cabin cannot be cleaned until passengers have left, crew has exited, and hold baggage has been cleared. The orchestrator enforces all three sequentially and will call external networks to resolve any unmet prerequisite before proceeding.

---

## 2. Repository Structure

```
aircraft_cabin_cleaning.hocon        # Agent network configuration
aircraft_cabin_cleaning.py           # Coded tool implementations (cabin_cleaning_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_disembark, aircraft_crew_exit, aircraft_baggage_unload)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
cabin_cleaning_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                                   (Coded tool: read/write turnaround state via sly_data)
   │
   ├── cabin_cleaning_operator                      (Coded tool: perform cabin cleaning)
   │
   ├── /AirlineTurnaround/aircraft_disembark        (External tool — if passengers not yet off)
   │
   ├── /AirlineTurnaround/aircraft_crew_exit        (External tool — if crew not yet off)
   │
   └── /AirlineTurnaround/aircraft_baggage_unload   (External tool — if baggage not yet unloaded)
```

### Design principles

- **Sequential prerequisite enforcement:** The orchestrator explicitly steps through flight status, passenger disembarkation, crew exit, and baggage unload in order before calling the cleaning operator. The instruction set uses `CRITICAL: sequential executor` language to reinforce this with the LLM.
- **Active prerequisite resolution:** If any of the three human-clearance prerequisites is unmet, the agent calls the corresponding external turnaround network to resolve it rather than simply aborting.
- **Tool-first execution:** All operational actions are performed by coded or external tools; the LLM orchestrates, not executes.
- **sly_data as shared state:** `TrackerAPI` and `cabin_cleaning_operator` exchange state through the `sly_data` mechanism — parameters flow between tools without re-passing through the LLM.
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

### 5.1 cabin_cleaning_agent (LLM Orchestrator)

The entry-point agent. It parses the user inquiry, enforces all human-clearance prerequisites, delegates resolution to external networks as needed, executes cleaning, and returns the final summary.

#### Input parameters

|-----------------------------------|--------|:--------:|-----------------------------------------------------------|
| Parameter                         | Type   | Required | Description                                               |
|-----------------------------------|--------|:--------:|-----------------------------------------------------------|
| `flight_number`                   | string | ✅       | Flight identifier                                         |
| `aircraft_type`                   | string | ✅       | Aircraft model/type                                       |
| `gate_id`                         | string | ✅       | Gate where the aircraft is parked                         |
| `flight_status`                   | string | ❌       | Flight status (expected: contains `on blocks` or `block`) |
| `passenger_disembarkation_status` | string | ❌       | Expected: contains `completed`                            |
| `crew_exit_status`                | string | ❌       | Expected: contains `completed` or `exited`                |
| `baggage_unload_status`           | string | ❌       | Expected: contains `completed` or `unloaded`              |
| `cabin_cleaning_status`           | string | ❌       | Current or previous cleaning status                       |
|-----------------------------------|--------|:--------:|-----------------------------------------------------------|

> Note: `flight_status` is absent from the HOCON `required` array even though the orchestrator instructions treat it as a hard gate (STEP 2). `gate_id` is declared required at the agent level and is also required by the operator.

#### Orchestration flow

The orchestrator uses explicit numbered steps in its instruction set and is instructed to execute them strictly in sequence. The HOCON defines six numbered steps followed by a `RETURN SUMMARY` block:

1. **STEP 1 — Collect parameters** — read from inquiry and call `TrackerAPI` to store all available values and read back any missing ones from `sly_data`.
2. **STEP 2 — Verify flight status** — `flight_status` must contain `on blocks` or `block`. If not, report and stop.
3. **STEP 3 — Verify passenger disembarkation** — if `passenger_disembarkation_status` does not contain `completed`, call `/AirlineTurnaround/aircraft_disembark` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`. Store `passenger_disembarkation_status`.
4. **STEP 4 — Verify crew exit** — if `crew_exit_status` does not contain `completed` or `exited`, call `/AirlineTurnaround/aircraft_crew_exit` with the same four parameters. Store `crew_exit_status`.
5. **STEP 5 — Verify baggage unload** — if `baggage_unload_status` does not contain `completed` or `unloaded`, call `/AirlineTurnaround/aircraft_baggage_unload` with the same four parameters. Store `baggage_unload_status`.
6. **STEP 6 — Execute cabin cleaning** — call `cabin_cleaning_operator` with all seven operational parameters. Store `cabin_cleaning_status`, then call `TrackerAPI` to persist it.
7. **RETURN SUMMARY** — return the formatted summary block.

#### sly_data contract

|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Direction           | Parameters                                                                                                                                                            |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `cabin_cleaning_status`, `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `cabin_cleaning_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `cabin_cleaning_status` |
| **To downstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `cabin_cleaning_status` |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------|

> Note: All four `allow` blocks declare the same eight sly_data fields, each listed once.

#### Down-chain tools

```
["TrackerAPI", "cabin_cleaning_operator", "/AirlineTurnaround/aircraft_disembark",
 "/AirlineTurnaround/aircraft_crew_exit", "/AirlineTurnaround/aircraft_baggage_unload"]
```

---

### 5.2 cabin_cleaning_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_cabin_cleaning.aircraft_cabin_cleaning.cabin_cleaning_operator`

Performs the cabin cleaning action. It validates all required parameters, checks that all three human-clearance prerequisites are satisfied, then sets `cabin_cleaning_status = completed`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

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

All seven parameters are hard-required by the operator at runtime (the HOCON `required` array only declares `flight_number`, `aircraft_type`, `gate_id`, but the Python coded tool enforces all seven). If any is missing from both `args` and `sly_data`, the tool returns an error string immediately.

#### Cleaning logic

`cabin_cleaning_status` is set to `completed` when **all three** of the following conditions are true (case-insensitive, after stripping whitespace):

|-----------------------------------|-------------------------|
| Field                             | Accepted values         |
|-----------------------------------|-------------------------|
| `passenger_disembarkation_status` | `completed`, `done`     |
| `crew_exit_status`                | `completed`, `exited`   |
| `baggage_unload_status`           | `completed`, `unloaded` |
|-----------------------------------|-------------------------|

If any condition fails, the tool returns `pending` (the initial value set at the top of `invoke`) without updating `sly_data`.

#### Output

- Writes `cabin_cleaning_status` into `sly_data`
- Returns `cabin_cleaning_status` string (`completed` or `pending`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_cabin_cleaning.aircraft_cabin_cleaning.TrackerAPI`

Manages shared turnaround state. Called at the start of the workflow to read current values, and again after `cabin_cleaning_operator` to persist the updated status. The `TrackerAPI` HOCON declares the seven cabin-cleaning-relevant parameters (`aircraft_type`, `flight_number`, `flight_status`, `baggage_unload_status`, `cabin_cleaning_status`, `crew_exit_status`, `passenger_disembarkation_status`) with `required: []` — values flow primarily through `sly_data`.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `baggage_unload_status`, `cabin_cleaning_status`, `crew_exit_status`, `flight_number`, `flight_status`, `passenger_disembarkation_status`

> Note: `gate_id` is absent from `FLIGHT_TURNAROUND_TRACKED_FIELDS` even though it is required by `cabin_cleaning_operator`. It will not be persisted or returned by TrackerAPI in the default configuration.

**Return fields:**
`cabin_cleaning_status` (only)

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
Perform aircraft cabin cleaning and provide a summary report."

# Prerequisites not yet confirmed — agent will resolve them
"The B747 aircraft of flight AF84 is on blocks at gate A1.
Perform aircraft cabin cleaning and provide a summary report."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. Baggages have been unloaded. All passengers have disembarked. The crew has exited the aircraft. Perform aircraft cabin cleaning and provide a summary report."

**Execution steps:**

1. `TrackerAPI` called — reads: `flight_status=on blocks`, `passenger_disembarkation_status=completed`, `crew_exit_status=exited`, `baggage_unload_status=completed`
2. Flight status check: on blocks ✅
3. Passenger disembarkation check: completed ✅
4. Crew exit check: exited ✅
5. Baggage unload check: completed ✅
6. `cabin_cleaning_operator` called — returns `cabin_cleaning_status=completed`
7. `TrackerAPI` called again — persists `cabin_cleaning_status=completed`
8. Summary returned

**Output:**

```
**************************************
* Summary of aircraft cabin cleaning *
**************************************
** cabin cleaning summary **:
** flight number **:                        AF84
** aircraft type **:                        B747
** gate id **:                              A1
** flight status **:                        on blocks
** passenger disembarkation status **:      completed
** crew exit status **:                     exited
** baggage unload status **:                completed
** cabin cleaning status **:                completed
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
  "cabin_cleaning_status": "completed"
}
```

---

## 9. Known Issues and Maintenance Notes

|-------|----------|-------|
| Issue | Location | Notes |
|-------|----------|-------|
|       |          |       |
|-------|----------|-------|

---

## 10. Extensibility Guidance

- Add zone-based cleaning tracking (galley, lavatories, cabin zones) for wide-body aircraft
- Model intermediate statuses: `cleaning_started`, `cleaning_in_progress`, `cleaning_completed` (currently only `completed` or `pending` are returned by the operator)
- Back `TrackerAPI` with a persistent store for multi-session traceability and audit logs
- Add concurrency controls when multiple turnaround networks update the same flight record simultaneously
- Integrate crew scheduling or cleaning team allocation systems
- Add SLA monitoring for cleaning turnaround time

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operations.
