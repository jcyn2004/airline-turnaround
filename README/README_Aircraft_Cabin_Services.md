# Aircraft Cabin Services
## Agentic AI Network – README

> **Configuration file:** `aircraft_cabin_services.hocon`
> **Implementation file:** `aircraft_cabin_services.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Aggregation router for aircraft cabin services — receives an `instruction` field from `aircraft_turnaround_manager` and routes to one of three leaf service networks: cabin cleaning, lavatory service, or catering loading.

---

## 1. Overview

`aircraft_cabin_services` is an aggregation network — one of the four intermediate networks called directly by `aircraft_turnaround_manager`. Unlike the individual service networks it wraps, this network itself contains no coded execution logic. Its sole role is to interpret an `instruction` routing field and delegate to the appropriate leaf network.

The network is called three times during the turnaround sequence (STEPS 15, 16, 17), with a different `instruction` value each time:
- STEP 15: `instruction='Clean the aircraft cabin.'`
- STEP 16: `instruction='Service the aircraft lavatory.'`
- STEP 17: `instruction='Load catering supplies.'`

The network combines:
- `cabin_services` — single LLM routing agent; interprets `instruction` and delegates
- `TrackerAPI` — coded state manager (with a notable class path anomaly)
- Three external leaf networks resolved from `registries/aaosa_basic.hocon`

No prior documentation existed for this network; this README is based entirely on the source files.

---

## 2. Repository Structure

```
aircraft_cabin_services.hocon    # Agent network configuration
aircraft_cabin_services.py       # TrackerAPI implementation (args-first, 7 tracked fields)
registries/aaosa_basic.hocon     # Shared registry (leaf service networks)
```

---

## 3. System Architecture

```
aircraft_turnaround_manager  (caller — STEPS 15, 16, 17)
   │
   ▼
cabin_services  (LLM Router — instruction-based routing)
   │
   ├── TrackerAPI                                       (Coded tool: read/write cabin service statuses)
   │
   ├── /AirlineTurnaround/aircraft_cabin_cleaning       (Routed to when instruction contains 'clean')
   │
   ├── /AirlineTurnaround/aircraft_lavatory_service     (Routed to when instruction contains 'lavatory')
   │
   └── /AirlineTurnaround/aircraft_catering_loading     (Routed to when instruction contains 'catering')
```

### Design principles

- **Instruction-field routing:** The `instruction` parameter determines which branch executes. This is a direct parallel to the `aircraft_ground_servicing` dispatch pattern.
- **Args-unwrapping guard:** The agent instructions begin with an explicit FORMAT A / FORMAT B detection block to handle both direct named-pair calls and args-wrapped calls from the master orchestrator.
- **Stop-after-branch:** Each branch (steps 3, 4, 5) ends with `stop process here` — only one service executes per call.
- **Context forwarding:** The three human-clearance status fields (`passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`) are passed by the caller but are not tracked by this network's TrackerAPI — they flow through to the leaf networks via sly_data from the caller's sly_data context.

---

## 4. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `3000`         |
| `max_execution_seconds` | `300`          |
|-------------------------|----------------|


> Note: These limits are significantly lower than every other network in the system, which uses `max_iterations: 40000` and `max_execution_seconds: 7200`. The cabin services network is expected to complete quickly — it makes one delegated call and returns a summary.

---

## 5. Components

### 5.1 cabin_services (LLM Router)

The single entry-point agent. It parses the `instruction` field, routes to the correct leaf network, calls TrackerAPI to persist the result, and returns a formatted summary.

> Note: The agent is named `cabin_services` in the HOCON. It has no `function.parameters` wrapper — the `parameters` block is defined directly under `function` alongside `description`, which is the correct neuro-san schema structure.

#### Input parameters

|-----------------------------------|--------|:--------:|--------------------------------------------|
| Parameter                         | Type   | Required | Description                                |
|-----------------------------------|--------|:--------:|--------------------------------------------|
| `aircraft_type`                   | string |    ✅     | Aircraft model/type                        |
| `gate_id`                         | string |    ✅     | Gate where the aircraft is parked          |
| `flight_number`                   | string |    ❌     | Flight identifier                          |
| `flight_status`                   | string |    ❌     | Flight status                              |
| `passenger_disembarkation_status` | string |    ❌     | Must be `completed` before service         |
| `crew_exit_status`                | string |    ❌     | Must be `completed` before service         |
| `baggage_unload_status`           | string |    ❌     | Baggage unload state                       |
| `instruction`                     | string |    ❌     | **Routing discriminant** (see table below) |
| `cabin_cleaning_status`           | string |    ❌     | Set by leaf network                        |
| `lavatory_service_status`         | string |    ❌     | Set by leaf network                        |
| `catering_loading_status`         | string |    ❌     | Set by leaf network                        |
|-----------------------------------|--------|:--------:|--------------------------------------------|

#### Instruction routing

|------------------------|---------------------------|------------------------------------------------|
| `instruction` contains | Branch executed           | Leaf network called                            |
|------------------------|---------------------------|------------------------------------------------|
| `'clean'`              | Step 3 — cabin cleaning   | `/AirlineTurnaround/aircraft_cabin_cleaning`   |
| `'lavatory'`           | Step 4 — lavatory service | `/AirlineTurnaround/aircraft_lavatory_service` |
| `'catering'`           | Step 5 — catering loading | `/AirlineTurnaround/aircraft_catering_loading` |
|------------------------|---------------------------|------------------------------------------------|

> Note: The routing is substring-matching on the `instruction` field, not exact-match. If no matching instruction is present, the agent falls back to the aaosa `Determine`/`Fulfill` protocol — it asks each down-chain tool whether it can handle the inquiry.

#### Parameter format guard (CRITICAL block)

The instructions include an explicit unwrapping guard at the top:
```
FORMAT A (correct): {"flight_number": "AF84", "aircraft_type": "B747", ..., "instruction": "..."}
FORMAT B (wrapped): {"args": [{"flight_number": "AF84", ..., "instruction": "..."}]}
```
If FORMAT B is received, the agent must extract the inner object from `args[0]` before routing. This mirrors the same guard in `aircraft_turnaround_manager`'s step instructions (STEPS 15–17).

#### Orchestration flow per branch

Each branch follows the same 5-substep pattern:
1. Call the relevant leaf network.
2. Wait for the response.
3. Call `TrackerAPI` — store all available parameters.
4. Return the formatted summary.
5. Stop.

#### Summary formats

**Cabin cleaning:**
```
**************************************
* Summary of aircraft cabin cleaning *
**************************************
** cabin cleaning summary **:
** flight number **: [flight_number]
** aircraft type **: [aircraft_type]
** flight status **: [flight_status]
** gate id **: [gate_id]
** cabin cleaning status **: [cabin_cleaning_status]
```

**Lavatory service:**
```
****************************************
* Summary of aircraft lavatory service *
****************************************
** flight_number **: [flight_number]
** aircraft_type **: [aircraft_type]
** flight_status **: [flight_status]
** gate_id **: [gate_id]
** lavatory service status **: [lavatory_service_status]
```

**Catering loading:**
```
****************************************
* Summary of aircraft catering loading *
****************************************
** flight number **: [flight_number]
** aircraft type **: [aircraft_type]
** flight status **: [flight_status]
** gate id **: [gate_id]
** catering loading service summary **: [catering_loading_status]
```

> Note: The cabin cleaning summary includes a `** cabin cleaning summary **:` header line not present in the other two. The lavatory service summary uses underscore-delimited field names (`flight_number`, `aircraft_type`) while cabin cleaning and catering use space-delimited (`flight number`, `aircraft type`). These are style inconsistencies across the three branches.

#### sly_data contract

All four directions carry the same 7-field set:

| Direction           | Fields                                                                                                                                      |
|---------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| All four directions | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `catering_loading_status`, `cabin_cleaning_status`, `lavatory_service_status` |

> Note: `passenger_disembarkation_status`, `crew_exit_status`, and `baggage_unload_status` are in the agent parameter schema but are **absent from all four sly_data allow blocks**. These prerequisite status fields must be passed by the caller as explicit named parameters — they will not flow through sly_data from this network.

#### Down-chain tools

```
["/AirlineTurnaround/aircraft_lavatory_service",
 "/AirlineTurnaround/aircraft_cabin_cleaning",
 "/AirlineTurnaround/aircraft_catering_loading",
 "TrackerAPI"]
```

---

### 5.2 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_rampservices.aircraft_ground_rampservices.TrackerAPI`

> Note: The class path references `aircraft_ground_rampservices` — a module that is **not part of this network**. This appears to be a copy-paste artifact from `aircraft_ground_operation` or a related ramp services network. The Python file `aircraft_cabin_services.py` contains a `TrackerAPI` class that would be the expected implementation, but the HOCON wires a class from a different module entirely.

The TrackerAPI in `aircraft_cabin_services.py` uses **args-first** resolution — checking `args` before `sly_data` — making it one of the older-generation implementations in the system. Most other networks use sly_data-first.

#### Data resolution priority (args-first)

1. **`args[field]`** — if present, writes to `sly_data` and returns value.
2. **`sly_data[field]`** — used only when `args` has no value.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

**Tracked fields:**
`flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `catering_loading_status`, `cabin_cleaning_status`, `lavatory_service_status`

**Return fields:** Identical to tracked fields (all 7 returned).

> Note: The TrackerAPI HOCON schema exposes only 5 fields (`aircraft_type`, `gate_id`, `wheels_chocks_installation_status`, `gpu_connection_status`, `acu_connection_status`) — a minimal and mismatched schema. None of the three cabin service status fields appear in the HOCON TrackerAPI schema, yet they are what this network primarily needs to track. The Python config is correct; the HOCON schema is stale.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

|------------------------------------------------|------------------------|-------------------------------------|
| Tool path                                      | Purpose                | Instruction trigger                 |
|------------------------------------------------|------------------------|-------------------------------------|
| `/AirlineTurnaround/aircraft_cabin_cleaning`   | Perform cabin cleaning | `instruction` contains `'clean'`    |
| `/AirlineTurnaround/aircraft_lavatory_service` | Service lavatories     | `instruction` contains `'lavatory'` |
| `/AirlineTurnaround/aircraft_catering_loading` | Load catering          | `instruction` contains `'catering'` |
|------------------------------------------------|------------------------|-------------------------------------|

---

## 7. Sample Queries

```
# Used directly
"The B747 aircraft of flight AF84 is on blocks at gate A1.
Baggages have been unloaded. All passengers have disembarked.
The crew has exited the aircraft. Perform aircraft cabin cleaning."

# As called by aircraft_turnaround_manager STEP 15
{flight_number, aircraft_type, flight_status, gate_id,
 passenger_disembarkation_status, crew_exit_status,
 baggage_unload_status, instruction='Clean the aircraft cabin.'}
```

---

## 8. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|-------|----------|:--------:|-------|
|       |          |          |       |

---

## 9. Comparison with `aircraft_ground_servicing` (Parallel Pattern)

`aircraft_cabin_services` and `aircraft_ground_servicing` use the same instruction-routing pattern:

|-----------------------------|-------------------------------|-------------------------------------------------------------------|
| Aspect                      | `aircraft_cabin_services`     | `aircraft_ground_servicing`                                       |
|-----------------------------|-------------------------------|-------------------------------------------------------------------|
| Routing discriminant        | `instruction` field           | `instruction` field                                               |
| Number of branches          | 3 (clean, lavatory, catering) | 3 (baggage, inspection, fueling)                                  |
| Format guard                | Yes (FORMAT A / FORMAT B)     | Yes                                                               |
| External tool networks      | Cabin services leaf networks  | Ground services leaf networks                                     |
| TrackerAPI resolution       | Args-first                    | Args-first (sly_data-first documented but args-first in practice) |
| Execution limits            | 3,000 / 300s                  | 40,000 / 7,200s                                                   |
| HOCON TrackerAPI class path | Wrong module                  | Correct module                                                    |
|-----------------------------|-------------------------------|-------------------------------------------------------------------|

---

## 10. Extensibility Guidance

- Fix the TrackerAPI class path to `AirlineTurnaround.aircraft_cabin_services.aircraft_cabin_services.TrackerAPI`
- Update the HOCON TrackerAPI schema to expose the three cabin service status fields and remove the irrelevant ramp service fields
- Add `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status` to all four sly_data allow blocks
- Remove the ~140-line commented-out `execute_aircraft_landing` block from the Python file
- Remove the three iterations of commented-out ground readiness instructions from the HOCON
- Consider increasing `max_iterations` to 40000 and `max_execution_seconds` to 7200 to match other networks

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
