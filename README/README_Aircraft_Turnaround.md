# Aircraft Turnaround
## Agentic AI Network – README

> **Configuration file:** `aircraft_turnaround.hocon`
> **Implementation file:** `aircraft_turnaround.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Top-level orchestrator for the complete aircraft turnaround lifecycle — from landing clearance through fueling and final report — coordinating four aggregation sub-networks across 20 sequential steps.

---

## 1. Overview

`aircraft_turnaround` is the master orchestration network of the **AirlineTurnaround** agentic system. Every other network in the system ultimately serves this one. It receives a single user request ("execute the turnaround") and drives all 20 steps to completion, coordinating four aggregation sub-networks that themselves coordinate the individual service networks.

The network combines:

- `aircraft_turnaround_manager` — the LLM master orchestrator; entry point with detailed STEP-pattern instructions
- `TrackerAPI` — a uniquely designed implementation that returns a full **JSON string** rather than a tuple, tracks 30 fields, and has no `return_fields` concept — everything tracked is returned
- Four external aggregation networks that group related services

> **Important note on previous documentation:** The old doc described `aircraft_turnaround_agent` as the entry point and showed 17 individual service agents as direct children. The actual entry point is `aircraft_turnaround_manager`, and it calls only four aggregation networks. The old doc also listed fields like `landing_status`, `taxi_status`, `inspection_status`, `maintenance_status`, and `debrief_status` that do not exist. The model was listed as `gpt-4o`; the actual model is `gpt-5.4-mini`.

---

## 2. Repository Structure

```
aircraft_turnaround.hocon            # Agent network configuration (~880 lines, most detailed in system)
aircraft_turnaround.py               # TrackerAPI implementation (JSON-returning, 30 tracked fields)
registries/aaosa_basic.hocon         # Provides commondefs
```

---

## 3. System Architecture

```
User / Operations Control
   │
   ▼
aircraft_turnaround_manager  (LLM Master Orchestrator — 20-step STEP pattern)
   │
   ├── TrackerAPI                                        (Coded tool: JSON-returning full-state manager)
   │
   ├── /AirlineTurnaround/aircraft_crew_pilot            (Steps 1,2,5,6,7,10,11,13,14 — all crew & pilot tasks)
   │
   ├── /AirlineTurnaround/aircraft_gate_services         (Steps 3,9 — gate assignment + deplaning equipment)
   │
   ├── /AirlineTurnaround/aircraft_ground_operation      (Steps 4,8,12,18,19 — readiness, ramp, baggage, inspection, fueling)
   │
   └── /AirlineTurnaround/aircraft_cabin_services        (Steps 15,16,17 — cleaning, lavatory, catering)
```

> Note: The four aggregation networks are not themselves documented in the individual-network READMEs. They are intermediate layers that group the 20+ leaf service networks.

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

## 5. The 20-Step Turnaround Sequence

The instructions define 21 numbered items (STEP 0 through STEP 20) for incoming aircraft. Each step calls exactly one external network with named parameters and validates the response before proceeding.

|------|-------------------------------------------|------------------------------------|-------------------------------------------------------------------------------------|
| Step | Action                                    | Network called                     | Key output field                                                                    |
|------|-------------------------------------------|------------------------------------|-------------------------------------------------------------------------------------|
| 0    | Validate inputs                           | (none — extract from user message) | `flight_number`, `aircraft_type`, `aircraft_direction`                              |
| 1    | Request landing clearance                 | `aircraft_crew_pilot` BRANCH A     | `clearance_type`, `assigned_runway_id`                                              |
| 2    | Land the aircraft                         | `aircraft_crew_pilot` BRANCH B     | `flight_status = 'landed'`                                                          |
| 3    | Gate assignment                           | `aircraft_gate_services`           | `gate_id`, `deplaning_equipment_type`                                               |
| 4    | Ground services readiness                 | `aircraft_ground_operation`        | `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`      |
| 5    | Ground traffic clearance (taxi-in)        | `aircraft_crew_pilot` BRANCH C     | `ground_clearance_status`                                                           |
| 6    | Taxi to gate                              | `aircraft_crew_pilot` BRANCH D     | `flight_status = 'on blocks'`                                                       |
| 7    | Stop engines                              | `aircraft_crew_pilot` BRANCH E     | `engines_stop_status`                                                               |
| 8    | Ground ramp services (chocks + ACU + GPU) | `aircraft_ground_operation`        | `wheels_chocks_installation_status`, `acu_connection_status`, `gpu_connection_status` |
| 9    | Connect deplaning equipment               | `aircraft_gate_services`           | `jetbridge_connection_status` or `stairtruck_connection_status`                     |
| 10   | Open aircraft doors                       | `aircraft_crew_pilot` BRANCH G     | `door_opening_status`                                                               |
| 11   | Passenger disembarkation                  | `aircraft_crew_pilot` BRANCH H     | `passenger_disembarkation_status`                                                   |
| 12   | Baggage unloading                         | `aircraft_ground_operation`        | `baggage_unload_status`                                                             |
| 13   | Crew debrief                              | `aircraft_crew_pilot` BRANCH I     | `crew_debrief_status`                                                               |
| 14   | Crew exit                                 | `aircraft_crew_pilot` BRANCH F     | `crew_exit_status`                                                                  |
| 15   | Cabin cleaning                            | `aircraft_cabin_services`          | `cabin_cleaning_status`                                                             |
| 16   | Lavatory servicing                        | `aircraft_cabin_services`          | `lavatory_service_status`                                                           |
| 17.  | Catering loading                          | `aircraft_cabin_services`          | `catering_loading_status`                                                           |
| 18   | Inspection and maintenance                | `aircraft_ground_operation`        | `inspection_maintenance_status`                                                     |
| 19   | Fueling                                   | `aircraft_ground_operation`        | `fueling_status`                                                                    |
|------|-------------------------------------------|------------------------------------|-------------------------------------------------------------------------------------|
| 20   | Final report                              | (summary only)                     | Full turnaround report                                                              |
|------|-------------------------------------------|------------------------------------|-------------------------------------------------------------------------------------|

---

## 6. Components

### 6.1 aircraft_turnaround_manager (LLM Master Orchestrator)

The entry-point agent. It receives the initial user request and drives all 20 steps in strict sequential order.

> Note: The entry point is `aircraft_turnaround_manager`. The previous documentation called it `aircraft_turnaround_agent`.

#### Input parameters

|----------------------------|--------|:--------:|--------------------------------------------------------|
| Parameter                  | Type   | Required | Description                                            |
|----------------------------|--------|:--------:|--------------------------------------------------------|
| `flight_number`            | string |    ✅     | Flight identifier                                      |
| `aircraft_type`            | string |    ✅     | Aircraft model/type                                    |
| `aircraft_direction`       | string |    ✅     | `incoming` or `departing`                              |
| `flight_status`            | string |    ❌     | Current flight status                                  |
| `gate_id`                  | string |    ❌     | Assigned gate                                          |
| `deplaning_equipment_type` | string |    ❌     | `jetway` or `stairtruck`                               |
| `task_id`                  | string |    ❌     | Correlation token for sub-agent routing                |
| *(full schema)*            |        |          | 20+ additional fields tracking all turnaround statuses |
|----------------------------|--------|:--------:|--------------------------------------------------------|

> Note: `task_id` is a **correlation token** unique to this network. It is passed to `aircraft_crew_pilot` on each call so that the pilot sub-agent can route to the correct BRANCH (A through I). The description field explains the routing: `STEP_10_DOOR_OPENING → BRANCH G`, `STEP_11_PAX_DISEMBARKATION → BRANCH H`, `STEP_13_CREW_DEBRIEF → BRANCH I`.

#### CRITICAL EXECUTION RULES (verbatim from HOCON)

The instructions define 5 critical execution rules before the step sequence:

1. **Execute each STEP exactly once, in strict numbered order.** Never restart from STEP 1, even when TrackerAPI returns a full state snapshot — that snapshot means earlier steps succeeded.
2. **Do NOT call TrackerAPI spontaneously between steps.** Only call it when a specific STEP instructs it.
3. **Carry state forward from each step's response.** Do not re-derive state.
4. **Once a step produces a confirmed result, mark it done and move on.** Never re-execute.
5. **ONE TOOL CALL PER TURN — STRICTLY ENFORCED.** Every tool call must be issued alone. NEVER issue two tool calls in the same turn. *"Violating this rule causes the workflow to restart from STEP 1, which is a critical failure."*

These rules are the most detailed LLM execution constraints in any network in the system.

#### TOOL ROUTING CHEATSHEET

The instructions include an inline routing cheatsheet that overrides the LLM's model priors:

```
All crew tasks → /AirlineTurnaround/aircraft_crew_pilot
  STEP 1  — landing clearance       → BRANCH A
  STEP 2  — land aircraft           → BRANCH B
  STEP 5  — ground clearance        → BRANCH C
  STEP 6  — taxi to gate            → BRANCH D
  STEP 7  — stop engines            → BRANCH E
  STEP 10 — door opening            → BRANCH G (NOT aircraft_crew_cabin)
  STEP 11 — pax disembarkation      → BRANCH H (NOT aircraft_crew_cabin)
  STEP 13 — crew debrief            → BRANCH I (NOT aircraft_crew_cabin)
  STEP 14 — crew exit               → BRANCH F

Ground operation tasks → /AirlineTurnaround/aircraft_ground_operation
  STEP 4  — ground readiness        → instruction='Check ground services readiness.'
  STEP 8  — ramp services           → instruction='Execute ground ramp services.'
  STEP 12 — baggage unload          → instruction='Unload baggage from the aircraft.'
  STEP 18 — inspection/maint        → instruction='Perform inspection and maintenance.'
  STEP 19 — fueling                 → instruction='Fuel the aircraft.'
```

#### Per-step validation and retry

Most steps include explicit validation and retry logic. Notable examples:

- **STEP 2** validates the response summary header — `'* Summary of aircraft landing *'` is valid; `'* Summary of air traffic clearance *'` means wrong branch was returned and mandates an immediate retry.
- **STEP 6** requires reading `flight_status` directly from the response, explicitly NOT from TrackerAPI or sly_data.
- **STEP 9** requires storing only the relevant connection status in TrackerAPI — not both `jetbridge_connection_status` and `stairtruck_connection_status`.
- **STEP 12** has the most aggressive isolation instructions: "If you find yourself about to invoke STEP_1_LANDING_CLEARANCE or any other agent while aircraft_ground_operation has not yet responded, you are violating this rule — cancel that call and wait."

#### Inline parameter format examples (STEPS 15–19)

Several steps include explicit CORRECT/INCORRECT call format examples:
```
CORRECT:   {"flight_number": "AF84", "aircraft_type": "B747", ..., "instruction": "Clean the aircraft cabin."}
INCORRECT: {"args": [{"flight_number": "AF84", ..., "instruction": "Clean the aircraft cabin."}]}
```

#### sly_data contract

The sly_data allow blocks propagate 30 fields in all four directions — the largest in the system:

`air_conditioning_unit_connection_status`, `air_conditioning_unit_readiness_status`, `aircraft_direction`, `aircraft_type`, `assigned_runway_id`, `assigned_runway_length`, `baggage_unload_status`, `cabin_cleaning_status`, `catering_loading_status`, `clearance_type`, `crew_debrief_status`, `crew_exit_status`, `deplaning_equipment_type`, `door_opening_status`, `engines_stop_status`, `flight_number`, `flight_status`, `fueling_status`, `gate_id`, `ground_power_unit_connection_status`, `ground_power_unit_readiness_status`, `ground_clearance_status`, `ground_clearance_type`, `inspection_maintenance_status`, `jetbridge_connection_status`, `lavatory_service_status`, `passenger_disembarkation_status`, `wheels_chocks_installation_status`, `wheels_chocks_readiness_status`, `acu_connection_status`, `acu_readiness_status`, `gpu_connection_status`, `gpu_readiness_status`, `task_id`

> Note: The sly_data allow blocks use both `air_conditioning_unit_connection_status` / `air_conditioning_unit_readiness_status` (long-form names from older networks) and `acu_connection_status` / `acu_readiness_status` (short-form). These are different field names that represent the same concepts in different sub-networks.

#### Down-chain tools

```
["TrackerAPI",
 "/AirlineTurnaround/aircraft_cabin_services",
 "/AirlineTurnaround/aircraft_crew_pilot",
 "/AirlineTurnaround/aircraft_gate_services",
 "/AirlineTurnaround/aircraft_ground_operation"]
```

---

### 6.2 TrackerAPI (Coded Tool — Master Version)

**Class:** `AirlineTurnaround.aircraft_turnaround.aircraft_turnaround.TrackerAPI`

This TrackerAPI is significantly different from all other TrackerAPI implementations in the system. It is the most capable version, designed specifically for the full-turnaround context.

#### Key differences from all other TrackerAPI implementations

|----------------------------|--------------------------------------------------------|-------------------------------------------|
| Aspect                     | All other TrackerAPIs                                  | This TrackerAPI                           |
|----------------------------|--------------------------------------------------------|-------------------------------------------|
| Return type                | `Tuple[Optional[str], ...]`                            | `str` (JSON-encoded dict)                 |
| Return fields config       | `TrackerConfig` has `tracked_fields` + `return_fields` | `TrackerConfig` has `tracked_fields` only |
| What is returned           | Only fields in `return_fields`                         | **All tracked fields, every time**        |
| Field selection by caller  | By position in tuple                                   | By key in returned JSON dict              |
| null handling              | Missing fields absent from return                      | Missing fields included as `null`         |
| `_build_return_tuple`      | Yes                                                    | No — replaced by `_build_return_json`     |
| `print()` alongside logger | No                                                     | Yes — `print()` on every read/write       |
|----------------------------|--------------------------------------------------------|-------------------------------------------|

The design rationale is documented in the class docstring: *"Consuming agents are responsible for reading whichever keys are relevant to their own task from the returned dict. No field selection is needed on the TrackerAPI side."*

#### TrackerConfig simplification

The `TrackerConfig` dataclass in this file has **only** `tracked_fields` — no `return_fields`. The `__post_init__` validation checks only that `tracked_fields` is not empty. This is a structural change from all other TrackerConfig instances which require both fields.

#### Default tracked fields (30 fields)

`acu_connection_status`, `acu_readiness_status`, `aircraft_direction`, `aircraft_landing_report`, `aircraft_type`, `assigned_runway_id`, `assigned_runway_length`, `baggage_unload_status`, `cabin_cleaning_status`, `catering_loading_status`, `clearance_type`, `crew_debrief_status`, `crew_exit_status`, `deplaning_equipment_type`, `door_opening_status`, `engines_stop_status`, `flight_number`, `flight_status`, `fueling_status`, `gate_id`, `gpu_connection_status`, `gpu_readiness_status`, `ground_clearance_status`, `ground_clearance_type`, `inspection_maintenance_status`, `jetbridge_connection_status`, `lavatory_service_status`, `stairtruck_connection_status`, `passenger_disembarkation_status`, `wheels_chocks_installation_status`, `wheels_chocks_readiness_status`

> Note: The HOCON TrackerAPI schema has `"required":` with no value assignment (line 875) — a syntax issue. Should be `"required": []`. Unlike other networks, the HOCON TrackerAPI `parameters` block also has no closing `"required"` key at all.

> Note: `crew_exit_status` appears as a **quoted** key in the HOCON TrackerAPI schema (line 854: `"crew_exit_status": {...}`). This is **correctly quoted** here — unlike `aircraft_inspection_maintenance`, `aircraft_lavatory_service`, and `aircraft_traffic_controller` where it appeared unquoted.

---

## 7. Sample Query

```
"The B747 aircraft of flight AF84 is incoming. Execute the turnaround process."
```

---

## 8. Example Final Report (STEP 20 output)

```
============================================
*  AIRCRAFT TURNAROUND COMPLETE REPORT     *
============================================
** Flight Number        **: AF84
** Aircraft Type        **: B747
** Aircraft Direction   **: incoming
** Gate ID              **: A5
** Assigned Runway      **: 19R
** Clearance Type       **: CLEARED_FOR_LANDING
** Flight Status        **: on blocks
** Engines Stop         **: stopped
** Wheelchocks Readiness**: ready
** Wheelchocks Install  **: installed
** ACU Readiness        **: ready
** ACU Connection       **: connected
** GPU Readiness        **: ready
** GPU Connection       **: connected
** Jetbridge            **: connected
** Stairtruck           **: not applicable
** Door Opening         **: open
** Pax Disembarkation   **: completed
** Baggage Unload       **: completed
** Crew Debrief         **: completed
** Crew Exit            **: completed
** Cabin Cleaning       **: completed
** Lavatory Service     **: completed
** Catering Loading     **: completed
** Inspection/Maint     **: completed
** Fueling              **: completed
============================================
```

---

## 9. Known Issues and Maintenance Notes

|--------------------------------------------------------------------------------|----------------------------------------|:--------:|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| Issue                                                                          | Location                               | Severity | Notes                                                                                                                                                  |
|--------------------------------------------------------------------------------|----------------------------------------|:--------:|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| Prior documentation listed wrong model, wrong agent hierarchy, invented fields | Prior documentation                    |    —     | See section 1. `landing_status`, `taxi_status`, `inspection_status`, `maintenance_status`, `debrief_status` do not exist.                              |
| `air_conditioning_unit_*` vs `acu_*` field name duality                        | sly_data allow blocks                  |  Medium  | Both long-form and short-form names for ACU fields appear in the sly_data contract. Sub-networks use different naming conventions.                     |
| STEP 9 TrackerAPI write must be selective                                      | `aircraft_turnaround.hocon` STEP 9     |   Info   | Instructions explicitly warn: do NOT write both connection status fields simultaneously. Passing the wrong field persists a false `'connected'` value. |
| STEP 2 response header validation                                              | `aircraft_turnaround.hocon` STEP 2     |   Info   | Summary header check is a robust protection against the pilot sub-agent returning the wrong branch.                                                    |
|--------------------------------------------------------------------------------|----------------------------------------|:--------:|--------------------------------------------------------------------------------------------------------------------------------------------------------|

---

## 10. Architectural Position — System Entry Point

`aircraft_turnaround` is the root of the AirlineTurnaround agentic system. The network dependency graph for incoming aircraft is:

```
aircraft_turnaround
├── aircraft_crew_pilot (STEPS 1,2,5,6,7,10,11,13,14)
│   ├── aircraft_traffic_controller (STEP 1 — clearance)
│   ├── aircraft_landing           (STEP 2 — land)
│   ├── aircraft_ground_traffic    (STEP 5 — ground clearance)
│   ├── aircraft_taxiing           (STEP 6 — taxi to gate)
│   ├── aircraft_engines_stop      (STEP 7)
│   ├── aircraft_door_opening      (STEP 10)
│   ├── aircraft_disembark         (STEP 11)
│   ├── aircraft_crew_debrief      (STEP 13)
│   └── aircraft_crew_exit         (STEP 14)
├── aircraft_gate_services (STEPS 3,9)
│   ├── aircraft_gate_selection    (STEP 3)
│   ├── aircraft_jetbridge_connect (STEP 9 — if jetway)
│   └── aircraft_stairtruck_connect (STEP 9 — if stairtruck)
├── aircraft_ground_operation (STEPS 4,8,12,18,19)
│   ├── aircraft_ground_readiness  (STEP 4)
│   ├── aircraft_ground_acu_connect/gpu_connect/wheelchocks_install (STEP 8)
│   ├── aircraft_baggage_unload    (STEP 12)
│   ├── aircraft_inspection_maintenance (STEP 18)
│   └── aircraft_fueling           (STEP 19)
└── aircraft_cabin_services (STEPS 15,16,17)
    ├── aircraft_cabin_cleaning    (STEP 15)
    ├── aircraft_lavatory_service  (STEP 16)
    └── aircraft_catering_loading  (STEP 17)
```

---

## 11. Extensibility Guidance

- Add a departing aircraft step sequence (the instructions cover only `incoming` aircraft — a departing branch needs to be written)
- Standardise `air_conditioning_unit_*` → `acu_*` and `ground_power_unit_*` → `gpu_*` field names across all sly_data allow blocks
- As the root orchestrator, any new service network added to the system must be registered under one of the four aggregation networks (`aircraft_crew_pilot`, `aircraft_gate_services`, `aircraft_ground_operation`, `aircraft_cabin_services`) — or a new aggregation network must be created if the category is new

---

## 12. Compliance Notice

This network models simulated aircraft turnaround workflows and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical control systems.
