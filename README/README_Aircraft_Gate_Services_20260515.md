# Aircraft Gate Services
## Agentic AI Network – README

> **Configuration file:** `aircraft_gate_services.hocon`
> **Implementation file:** `aircraft_gate_services.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Aggregation router for gate-phase turnaround operations — routes to gate assignment (BRANCH A) or deplaning equipment connection (BRANCH B: jetbridge or stairtruck) based on inquiry intent.

---

## 1. Overview

`aircraft_gate_services` is one of the four aggregation networks called directly by `aircraft_turnaround_manager`. It handles the two gate-related steps in the turnaround sequence — STEP 3 (gate assignment) and STEP 9 (deplaning equipment connection). Each call executes exactly one branch determined by the primary intent of the inquiry.

The network combines:
- `gate_crew_agent` — a single LLM routing agent with two branches and two sub-paths in BRANCH B
- `TrackerAPI` — standard sly_data-first coded state manager
- Three external leaf networks resolved from `registries/aaosa_basic.hocon`

No prior documentation existed for this network; this README is built entirely from source.

---

## 2. Repository Structure

```
aircraft_gate_services.hocon     # Agent network configuration
aircraft_gate_services.py        # TrackerAPI implementation (sly_data-first)
registries/aaosa_basic.hocon     # Shared registry (leaf networks)
```

---

## 3. System Architecture

```
aircraft_turnaround_manager  (caller — STEPs 3 and 9)
   |
   v
gate_crew_agent  (LLM Router — primary-intent routing)
   |
   |-- TrackerAPI                                        (Coded tool: sly_data-first state management)
   |
   |-- /AirlineTurnaround/aircraft_gate_selection        (BRANCH A — gate assignment)
   |
   |-- /AirlineTurnaround/aircraft_jetbridge_connect     (BRANCH B STEP 2A — jetway gates)
   |
   `-- /AirlineTurnaround/aircraft_stairtruck_connect    (BRANCH B STEP 2B — stairtruck gates)
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

The single entry-point agent. It reads the full inquiry and matches PRIMARY INTENT to determine which branch executes.

#### Input parameters

| ----------------------------------- | -------= | :--------: | ----------------------------------------------------------- |
| Parameter                           | Type     | Required   | Description                                                 |
| ----------------------------------- | -------= | :--------: | ----------------------------------------------------------- |
| `aircraft_type`                     | string   | YES        | Aircraft model/type                                         |
| `flight_number`                     | string   | YES        | Flight identifier                                           |
| `flight_status`                     | string   | NO         | Current flight status                                       |
| `gate_id`                           | string   | NO         | Assigned gate                                               |
| `assigned_runway_id`                | string   | NO         | Runway assigned by clearance                                |
| `door_opening_status`               | string   | NO         | Door opening status                                         |
| `passenger_disembarkation_status`   | string   | NO         | Passenger disembarkation status                             |
| `deplaning_equipment_type`          | string   | NO         | `jetway` or `stairtruck` — drives BRANCH B sub-path         |
| `deplaning_equipment_id`            | string   | NO         | Equipment identifier at gate                                |
| `deplaning_equipment_readiness_time`| string   | NO         | Time to ready deplaning equipment                           |
| `deplaning_equipment_score`         | string   | NO         | Deterministic score for deplaning equipment                 |
| `acu_connection_status`             | string   | NO         | Required by STEP 2A/2B                                      |
| `gpu_connection_status`             | string   | NO         | Required by STEP 2A/2B                                      |
| `wheels_chocks_installation_status` | string   | NO         | Required by STEP 2A/2B                                      |
| `jetbridge_connection_status`       | string   | NO         | Output of STEP 2A                                           |
| `stairtruck_connection_status`      | string   | NO         | Output of STEP 2B                                           |
| ----------------------------------- | -------= | :--------: | ----------------------------------------------------------- |

#### Routing logic

The agent reads the full inquiry and matches PRIMARY INTENT:

| Condition                                                                                              | Branch triggered                               |
|--------------------------------------------------------------------------------------------------------|------------------------------------------------|
| Inquiry asks to assign a gate, select a gate, or find a parking gate                                   | **BRANCH A**                                   |
| Inquiry asks to connect the jetbridge / instruction contains "Connect the jetbridge"                   | **BRANCH B -> STEP 2A**                        |
| Inquiry asks to connect the stairtruck / instruction contains "Connect the stairtruck"                 | **BRANCH B -> STEP 2B**                        |
| Instruction is "Connect the deplaning equipment."                                                      | **BRANCH B** (equipment type determines 2A/2B) |
| Inquiry not about gate assignment or jetbridge/stairtruck connection                                   | Reply not relevant and stop                    |

---

#### BRANCH A — Gate assignment

**Trigger:** Inquiry asks to assign a gate, select a gate, or find a parking gate. Called as STEP 3 by `aircraft_turnaround_manager`.

**STEP 1 — Execute gate assignment:**
Call `/AirlineTurnaround/aircraft_gate_selection` with `flight_number`, `aircraft_type`. Wait. Extract: `gate_id`, `deplaning_equipment_type`, `deplaning_equipment_id`, `deplaning_equipment_readiness_time`, `deplaning_equipment_score`. Call `TrackerAPI` to store `gate_id` and `deplaning_equipment_type`.

> Note: The instruction tells the LLM to extract `deplaning_equipment_readiness_time` and `deplaning_equipment_score` for the summary, but these fields are not explicitly stored back to TrackerAPI in STEP 1 (only `gate_id` and `deplaning_equipment_type` are). They are however listed in the sly_data allow blocks for cross-network propagation.

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

**Trigger:** Inquiry asks to connect the jetbridge or stairtruck, or the instruction contains "Connect the jetbridge" / "Connect the stairtruck", or the instruction is "Connect the deplaning equipment." Called as STEP 9 by `aircraft_turnaround_manager`.

**STEP 1 — Determine deplaning equipment type (via TrackerAPI):**

The HOCON instructs the agent to read `deplaning_equipment_type` from sly_data via `TrackerAPI`:

> *"Read deplaning_equipment_type from sly_data via TrackerAPI."*

Resolution order:
1. If `deplaning_equipment_type` contains `'jetway'` or `'jetbridge'` -> STEP 2A
2. If `deplaning_equipment_type` contains `'stairtruck'` or `'stair'` -> STEP 2B
3. If `deplaning_equipment_type` is not available -> reply that the information is unavailable.

**STEP 2A — Connect jetbridge (jetway gate):**
Call `/AirlineTurnaround/aircraft_jetbridge_connect` with: `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`. Extract `jetbridge_connection_status`. Call `TrackerAPI` to store it. Go to RETURN SUMMARY A.

**STEP 2B — Connect stairtruck (stairtruck gate):**
Call `/AirlineTurnaround/aircraft_stairtruck_connect` with the same parameter set. Extract `stairtruck_connection_status`. Call `TrackerAPI` to store it. Go to RETURN SUMMARY B.

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

All four directions (`to_upstream`, `to_downstream`, `from_upstream`, `from_downstream`) carry the same 19-field set:

`flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `door_opening_status`, `passenger_disembarkation_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `deplaning_equipment_id`, `deplaning_equipment_readiness_time`, `deplaning_equipment_score`, `gpu_connection_status`, `gpu_readiness_status`, `acu_connection_status`, `acu_readiness_status`, `wheels_chocks_readiness_status`, `wheels_chocks_installation_status`

> Note: The `from_downstream` block in the HOCON has a duplicated `deplaning_equipment_type` key — it appears twice in that block. This is a benign duplication.

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

Standard sly_data-first implementation. Called in BRANCH A STEP 1 after gate selection, in BRANCH B STEP 1 to resolve `deplaning_equipment_type`, and in BRANCH B STEP 2A or 2B after equipment connection.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### HOCON parameter schema (16 fields exposed to the LLM)

`flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `assigned_runway_id`, `door_opening_status`, `passenger_disembarkation_status`, `jetbridge_connection_status`, `deplaning_equipment_id`, `deplaning_equipment_type`, `deplaning_equipment_readiness_time`, `deplaning_equipment_score`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`, `stairtruck_connection_status`

> Note: The HOCON TrackerAPI description mentions `engines_stop_status` and `wheels chucks installation status` (with the double-`c` typo `chucks`), but `engines_stop_status` is **not** in the TrackerAPI parameter schema — the description references a field the LLM cannot pass through TrackerAPI in this network.

> Note: `gpu_readiness_status`, `acu_readiness_status`, `wheels_chocks_readiness_status` appear in the sly_data allow blocks but are **not** in the TrackerAPI parameter schema. They propagate through sly_data channels between networks but cannot be explicitly tracked via TrackerAPI in this network.

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

# STEP 9 — jet bridge connection (BRANCH B)
"Flight AF84 is on blocks at gate A1. ACU and GPU are connected to this B747,
and wheelchocks have been installed. Connect the jet bridge."
```

---

## 8. Example Execution Traces

### STEP 3 — Gate assignment

**Input:** `{"flight_number": "AF84", "aircraft_type": "B747"}`

1. Inquiry asks to assign a gate -> BRANCH A
2. `aircraft_gate_selection` called -> returns `gate_id=A5`, `deplaning_equipment_type=jetway`, `deplaning_equipment_id=JB-A5`, `deplaning_equipment_score=0.42`
3. `TrackerAPI` stores `gate_id` and `deplaning_equipment_type`
4. Summary returned

### STEP 9 — Jetbridge connection

**Input:** Inquiry "Connect the jet bridge." with full parameter set

1. Inquiry asks to connect the jetbridge -> BRANCH B
2. `deplaning_equipment_type` read via TrackerAPI -> contains `'jetway'` -> STEP 2A
3. `aircraft_jetbridge_connect` called -> returns `jetbridge_connection_status=connected`
4. `TrackerAPI` stores `jetbridge_connection_status`
5. RETURN SUMMARY A returned

---

## 9. Known Issues and Maintenance Notes

| Issue                                                                                          | Location                                       | Severity | Notes                                                                                                                                                                                |
|------------------------------------------------------------------------------------------------|------------------------------------------------|:--------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| TrackerAPI description references `engines_stop_status` but field is not in parameter schema   | TrackerAPI `function.description`              |   Low    | The description mentions checking engines stop status, but `engines_stop_status` is not declared in the TrackerAPI properties list.                                                  |
| `wheels chucks` typo in TrackerAPI description                                                 | TrackerAPI `function.description`              |   Low    | Description text reads "wheels chucks installation status" (double-`c`). The parameter key is correctly `wheels_chocks_installation_status`.                                          |
| Duplicate `deplaning_equipment_type` key in `from_downstream` sly_data allow block             | `from_downstream.sly_data`                     |   Low    | Field appears twice in the same dict; benign duplication.                                                                                                                            |


---

## 10. Comparison with Sibling Aggregation Networks

`aircraft_gate_services` is one of four aggregation networks under `aircraft_turnaround_manager`. Here's how it compares to the others:

| Aspect                | `aircraft_gate_services`                              | `aircraft_cabin_services`   | `aircraft_ground_operation`                    |
|-----------------------|-------------------------------------------------------|-----------------------------|------------------------------------------------|
| Entry agent name      | `gate_crew_agent`                                     | `cabin_services`            | *(not yet documented)*                         |
| Routing discriminant  | Primary intent of inquiry                             | `instruction`               | `instruction`                                  |
| Number of branches    | 2 (A: assignment; B: connection with 2A/2B sub-paths) | 3 (clean/lavatory/catering) | 3+ (readiness/ramp/baggage/inspection/fueling) |
| TrackerAPI usage      | Yes — used to resolve `deplaning_equipment_type`      | No                          | Yes — multiple steps                           |
| HOCON tracked fields  | 16                                                    | 7                           | *(not yet documented)*                         |
| Execution limits      | 40,000 / 7,200s                                       | 3,000 / 300s                | 40,000 / 7,200s                                |
| TrackerAPI class path | Correct                                               | Wrong module                | *(not yet documented)*                         |

---

## 11. Extensibility Guidance

- 

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
