# Aircraft Gate Services
## Agentic AI Network – README

> **Configuration file:** `aircraft_gate_services.hocon` (uploaded as `aircraft_gate_services__1_.hocon`)
> **Implementation file:** `aircraft_gate_services.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Aggregation router for gate-phase turnaround operations — routes to gate assignment (BRANCH A) or deplaning equipment connection (BRANCH B: jetbridge or stairtruck) based on an `instruction` field.

---

## 1. Overview

`aircraft_gate_services` is one of the four aggregation networks called directly by `aircraft_turnaround_manager`. It handles the two gate-related steps in the turnaround sequence — STEP 3 (gate assignment) and STEP 9 (deplaning equipment connection). Each call executes exactly one branch determined by an `instruction` field or a gate_id presence check.

The network combines:
- `gate_crew_agent` — a single LLM routing agent with two branches and three sub-paths
- `TrackerAPI` — standard sly_data-first coded state manager
- Three external leaf networks resolved from `registries/aaosa_basic.hocon`

No prior documentation existed for this network; this README is built entirely from source.

> **Note on filename:** The uploaded HOCON file is named `aircraft_gate_services__1_.hocon` (with `__1_` suffix). This is likely a versioning or download artifact. The actual deployed filename in the registry is `aircraft_gate_services.hocon`.

> **Note on task title:** The task prompt requested `README_Aircraft_Ground_Traffic.md` — this appears to be an error. The uploaded files are for `aircraft_gate_services`. This README is correctly titled for the gate services network.

---

## 2. Repository Structure

```
aircraft_gate_services.hocon     # Agent network configuration
aircraft_gate_services.py        # TrackerAPI implementation (sly_data-first, 21 tracked fields)
registries/aaosa_basic.hocon     # Shared registry (leaf networks)
```

---

## 3. System Architecture

```
aircraft_turnaround_manager  (caller — STEPs 3 and 9)
   │
   ▼
gate_crew_agent  (LLM Router — instruction-field-first routing)
   │
   ├── TrackerAPI                                        (Coded tool: sly_data-first state management)
   │
   ├── /AirlineTurnaround/aircraft_gate_selection        (BRANCH A — gate assignment)
   │
   ├── /AirlineTurnaround/aircraft_jetbridge_connect     (BRANCH B STEP 2A — jetway gates)
   │
   └── /AirlineTurnaround/aircraft_stairtruck_connect    (BRANCH B STEP 2B — stairtruck gates)
```

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

### 5.1 gate_crew_agent (LLM Router)

The single entry-point agent. It checks the `instruction` field first, then falls back to inquiry text to determine which branch executes.

> Note: The agent description contains a typo: `"I am responsibke for gate assignment"` — should be `"responsible"`.

#### Input parameters

| ----------------------------------- | -------= | :--------: | ----------------------------------------------------------- |
| Parameter                           | Type     | Required   | Description                                                 |
| ----------------------------------- | -------= | :--------: | ----------------------------------------------------------- |
| `aircraft_type`                     | string   | ✅          | Aircraft model/type                                         |
| `flight_number`                     | string   | ✅          | Flight identifier                                           |
| `flight_status`                     | string   | ❌          | Current flight status                                       |
| `gate_id`                           | string   | ❌          | Assigned gate (null triggers BRANCH A)                      |
| `instruction`                       | string   | ❌          | **Primary routing discriminant**                            |
| `deplaning_equipment_type`          | string   | ❌          | `jetway` or `stairtruck` — required for BRANCH B routing    |
| `acu_connection_status`             | string   | ❌          | Required by STEP 2A/2B                                      |
| `gpu_connection_status`             | string   | ❌          | Required by STEP 2A/2B                                      |
| `wheels_chocks_installation_status`   | string   | ❌          | Required by STEP 2A/2B                                      |
| `jetbridge_connection_status`       | string   | ❌          | Output of STEP 2A                                           |
| `stairtruck_connection_status`      | string   | ❌          | Output of STEP 2B                                           |
| `deplaning_equipment_id`            | string   | ❌          | Equipment identifier at gate                                |
| ----------------------------------- | -------= | :--------: | ----------------------------------------------------------- |

#### Routing logic

The agent reads the `instruction` field **before** reading the inquiry text:

| Condition                                                  | Branch triggered                               |
|------------------------------------------------------------|------------------------------------------------|
| `instruction` absent/null AND `gate_id` is null            | **BRANCH A**                                   |
| `instruction` contains `'assign'`, `'gate'`, or `'select'` | **BRANCH A**                                   |
| `gate_id` already set in args                              | Skip to **BRANCH B**                           |
| `instruction` contains `'jetbridge'` or `'jet bridge'`     | **BRANCH B → STEP 2A**                         |
| `instruction` contains `'stairtruck'` or `'stair'`         | **BRANCH B → STEP 2B**                         |
| `instruction` contains `'connect'` or `'deplaning'`        | **BRANCH B** (equipment type determines 2A/2B) |
| Inquiry asks to connect jetbridge or stairtruck            | **BRANCH B**                                   |

---

#### BRANCH A — Gate assignment

**Trigger:** Called as STEP 3 by `aircraft_turnaround_manager` with no `instruction` and no `gate_id`.

**STEP 1 — Execute gate assignment:**
Call `/AirlineTurnaround/aircraft_gate_selection` with `flight_number`, `aircraft_type`. Wait. Extract: `gate_id`, `deplaning_equipment_type`, `deplaning_equipment_id`, `deplaning_equipment_readiness_time`, `deplaning_equipment_score`. Call `TrackerAPI` to store `gate_id` and `deplaning_equipment_type`.

> Note: The instruction says to extract `deplaning_equipment_readiness_time` and `deplaning_equipment_score` but these fields are not in the Python `FLIGHT_TURNAROUND_TRACKED_FIELDS` and are not tracked by TrackerAPI. They appear in the summary template but will not be persisted in sly_data.

**STEP 2 — RETURN SUMMARY:**
```
**************************************
* Summary of aircraft gate selection *
**************************************
** flight number                      **: [flight_number]
** aircraft type                      **: [aircraft_type]
** gate id                            **: [gate_id]
** deplaning equipment type           **: [deplaning_equipment_type]
** deplaning equipment id             **: [deplaning_equipment_id]
** deplaning equipment readiness time **: [deplaning_equipment_readiness_time]
** deplaning equipment score          **: [deplaning_equipment_score]
```

---

#### BRANCH B — Jetbridge or stairtruck connection

**Trigger:** Called as STEP 9 by `aircraft_turnaround_manager` with `instruction='Connect the jetbridge.'` or `instruction='Connect the stairtruck.'`.

**STEP 1 — Determine deplaning equipment type (from args, NOT TrackerAPI):**

The instructions include a documented rationale for avoiding TrackerAPI here:
> *"CRITICAL: Read deplaning_equipment_type DIRECTLY from the incoming args. Do NOT call TrackerAPI to resolve this — TrackerAPI may not yet have the value and will return null, causing incorrect routing. The manager always passes deplaning_equipment_type as a named parameter."*

Resolution order:
1. If `deplaning_equipment_type` (from args) contains `'jetway'` or `'jetbridge'` → STEP 2A
2. If `deplaning_equipment_type` (from args) contains `'stairtruck'` or `'stair'` → STEP 2B
3. If null/absent, check `instruction`: `'jetbridge'` → STEP 2A, `'stairtruck'` → STEP 2B
4. Otherwise → default to STEP 2A (jetbridge)

**STEP 2A — Connect jetbridge (jetway gate):**
Call `/AirlineTurnaround/aircraft_jetbridge_connect` with: `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`. Single isolated call. Extract `jetbridge_connection_status`. Call `TrackerAPI` to store it.

**STEP 2B — Connect stairtruck (stairtruck gate):**
Call `/AirlineTurnaround/aircraft_stairtruck_connect` with the same parameter set. Extract `stairtruck_connection_status`. Call `TrackerAPI` to store it.

**RETURN SUMMARY A (jetbridge):**
```
***********************************
* Summary of jetbridge connection *
***********************************
** flight_status                  **: [flight_status]
** acu_connection_status          **: [acu_connection_status]
** gpu_connection_status          **: [gpu_connection_status]
** wheelchocks installation status**: [wheels_chocks_installation_status]
** jetbridge_connection_status    **: [jetbridge_connection_status]
```

**RETURN SUMMARY B (stairtruck):**
```
************************************
* Summary of stairtruck connection *
************************************
** flight_status                  **: [flight_status]
** acu_connection_status          **: [acu_connection_status]
** gpu_connection_status          **: [gpu_connection_status]
** wheelchocks installation status**: [wheels_chocks_installation_status]
** stairtruck_connection_status   **: [stairtruck_connection_status]
```

---

#### sly_data contract

All four directions carry the same 17-field set:

`flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `door_opening_status`, `passenger_disembarkation_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `deplaning_equipment_id`, `gpu_connection_status`, `gpu_readiness_status`, `acu_connection_status`, `acu_readiness_status`, `wheels_chocks_readiness_status`, `wheels_chocks_installation_status`

> Note: `gpu_readiness_status` and `wheels_chocks_installation_status` are in the sly_data allow blocks but **absent from `FLIGHT_TURNAROUND_TRACKED_FIELDS`** in Python. They propagate through sly_data channels between networks but TrackerAPI will not track or echo them.

> Note: `task_id` is **not** in the sly_data allow blocks — unlike `aircraft_crew_pilot` which threads `task_id` through all directions. This network does not use the correlation token pattern.

#### Down-chain tools

```
["/AirlineTurnaround/aircraft_gate_selection",
 "/AirlineTurnaround/aircraft_jetbridge_connect",
 "/AirlineTurnaround/aircraft_stairtruck_connect",
 "TrackerAPI"]
```

---

### 5.2 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_gate_services.aircraft_gate_services.TrackerAPI`

Standard sly_data-first implementation. Called in BRANCH A STEP 1 after gate selection, and in BRANCH B STEP 2A or 2B after equipment connection.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration (21 tracked fields = 21 return fields)

`acu_readiness_status`, `aircraft_direction`, `aircraft_type`, `assigned_runway_id`, `assigned_runway_length`, `clearance_type`, `door_opening_status`, `flight_number`, `flight_status`, `gate_id`, `ground_clearance_status`, `ground_clearance_type`, `jetbridge_connection_status`, `passenger_disembarkation_status`, `wheels_chocks_readiness_status`, `engines_stop_status`, `deplaning_equipment_type`, `deplaning_equipment_id`, `gpu_connection_status`, `acu_connection_status`, `stairtruck_connection_status`

> Note: Tracked fields and return fields are identical — TrackerAPI returns everything it tracks.

> Note: `gpu_readiness_status` is in the HOCON TrackerAPI parameter schema (exposed to the LLM) and in the sly_data allow blocks, but **absent from Python `FLIGHT_TURNAROUND_TRACKED_FIELDS`**. The LLM can pass it, it will be ignored by TrackerAPI, and it won't be returned.

> Note: `wheels_chocks_installation_status` is in the sly_data allow blocks and the HOCON TrackerAPI schema but **absent from Python tracked fields** — same gap.

> Note: The HOCON TrackerAPI description contains `"wheels_chucks_installation_status"` — the double-`c` copy-paste typo seen in multiple other networks.

> Note: `"required": []` is correctly defined.

---

## 6. External Tool Dependencies

| Tool path                                        | Branch           | Purpose                                       |
|--------------------------------------------------|------------------|-----------------------------------------------|
| `/AirlineTurnaround/aircraft_gate_selection`     | BRANCH A         | Assign gate and determine deplaning equipment |
| `/AirlineTurnaround/aircraft_jetbridge_connect`  | BRANCH B STEP 2A | Connect jetbridge at jetway gates             |
| `/AirlineTurnaround/aircraft_stairtruck_connect` | BRANCH B STEP 2B | Connect stairtruck at stairtruck gates        |

---

## 7. Sample Queries

```
# STEP 3 — gate assignment (BRANCH A)
"Assign a gate for the parking flight AF84 which is a B747."

# STEP 9 — jetbridge connection (BRANCH B via instruction)
{"flight_number": "AF84", "aircraft_type": "B747", "flight_status": "on blocks",
 "gate_id": "A1", "acu_connection_status": "connected",
 "gpu_connection_status": "connected",
 "wheels_chocks_installation_status": "installed",
 "deplaning_equipment_type": "jetway",
 "instruction": "Connect the jetbridge."}

# STEP 9 — stairtruck connection (BRANCH B via instruction)
"Flight AF84 is on blocks at gate A1. ACU and GPU are connected to this B747,
and wheelchocks have been installed. Connect the stairtruck."
```

---

## 8. Example Execution Traces

### STEP 3 — Gate assignment

**Input:** `{"flight_number": "AF84", "aircraft_type": "B747"}`

1. `instruction` absent and `gate_id` null → BRANCH A
2. `aircraft_gate_selection` called → returns `gate_id=A5`, `deplaning_equipment_type=jetway`, `deplaning_equipment_id=JB-A5`, `deplaning_equipment_score=0.42`
3. `TrackerAPI` stores `gate_id` and `deplaning_equipment_type`
4. Summary returned

### STEP 9 — Jetbridge connection

**Input:** Full parameter set with `instruction='Connect the jetbridge.'`

1. `instruction` contains `'jetbridge'` → BRANCH B
2. `deplaning_equipment_type='jetway'` from args → STEP 2A
3. `aircraft_jetbridge_connect` called → returns `jetbridge_connection_status=connected`
4. `TrackerAPI` stores `jetbridge_connection_status`
5. RETURN SUMMARY A returned

---

## 9. Known Issues and Maintenance Notes

| Issue                                                                                          | Location                                       | Severity | Notes                                                                                                                                                                                |
|------------------------------------------------------------------------------------------------|------------------------------------------------|:--------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| HOCON filename has `__1_` suffix                                                               | filename                                       |   Low    | `aircraft_gate_services__1_.hocon` suggests a versioning/download artifact. Deployed filename should be `aircraft_gate_services.hocon`.                                              |


---

## 10. Comparison with Sibling Aggregation Networks

`aircraft_gate_services` is one of four aggregation networks under `aircraft_turnaround_manager`. Here's how it compares to the others:

| Aspect                | `aircraft_gate_services`                              | `aircraft_cabin_services`   | `aircraft_ground_operation`                    |
|-----------------------|-------------------------------------------------------|-----------------------------|------------------------------------------------|
| Entry agent name      | `gate_crew_agent`                                     | `cabin_services`            | *(not yet documented)*                         |
| Routing discriminant  | `instruction` + `gate_id` presence                    | `instruction`               | `instruction`                                  |
| Number of branches    | 2 (A: assignment; B: connection with 2A/2B sub-paths) | 3 (clean/lavatory/catering) | 3+ (readiness/ramp/baggage/inspection/fueling) |
| TrackerAPI avoidance  | Yes — BRANCH B STEP 1                                 | No                          | Yes — multiple steps                           |
| Tracked fields        | 21                                                    | 7                           | *(not yet documented)*                         |
| Execution limits      | 40,000 / 7,200s                                       | 3,000 / 300s                | 40,000 / 7,200s                                |
| TrackerAPI class path | Correct                                               | Wrong module                | *(not yet documented)*                         |

---

## 11. Extensibility Guidance

- 

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
