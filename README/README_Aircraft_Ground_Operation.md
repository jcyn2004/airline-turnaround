# Aircraft Ground Operation
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_operation.hocon`
> **Implementation file:** `aircraft_ground_operation.py` *(not uploaded — see section 5.2)*
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Pure pass-through router for all ground operations — receives an `instruction` field from `aircraft_turnaround_manager` and routes verbatim to one of three sub-networks: ground readiness, ground ramp services, or ground servicing.

---

## 1. Overview

`aircraft_ground_operation` is one of the four aggregation networks called directly by `aircraft_turnaround_manager`. It handles five of the twenty turnaround steps (STEPs 4, 8, 12, 18, 19) and is the busiest aggregation network in terms of call frequency.

Unlike `aircraft_cabin_services` or `aircraft_gate_services` (which have their own TrackerAPI call logic), this network is designed as a **pure pass-through router**. Its instructions explicitly prohibit any response transformation: the sub-agent response must be returned verbatim to the caller. TrackerAPI is listed in the tools but the instructions never direct the agent to call it — state management is delegated entirely to the downstream sub-networks.

The network combines:
- `ground_operation_agent` — a single LLM pass-through routing agent with three branches
- `TrackerAPI` — registered but not called by agent instructions (see section 5.2)
- Three external sub-networks

No Python implementation file was uploaded. The TrackerAPI class path references `AirlineTurnaround.aircraft_ground_operation.aircraft_ground_operation.TrackerAPI`; its tracked fields are documented from the HOCON schema only.

---

## 2. Repository Structure

```
aircraft_ground_operation.hocon    # Agent network configuration
aircraft_ground_operation.py       # TrackerAPI implementation (not uploaded)
registries/aaosa_basic.hocon       # Shared registry (sub-networks)
```

---

## 3. System Architecture

```
aircraft_turnaround_manager  (caller — STEPs 4, 8, 12, 18, 19)
   │
   ▼
ground_operation_agent  (LLM Pass-Through Router — instruction-field routing)
   │
   ├── TrackerAPI                                        (Registered but not called by instructions)
   │
   ├── /AirlineTurnaround/aircraft_ground_readiness      (BRANCH A — STEPs 4: readiness check)
   │
   ├── /AirlineTurnaround/aircraft_ground_rampservices   (BRANCH B — STEP 8: wheelchocks, ACU, GPU)
   │
   └── /AirlineTurnaround/aircraft_ground_servicing      (BRANCH C — STEPs 12, 18, 19: baggage, inspection, fueling)
                │
                ├── Internal BRANCH A: baggage unload    (instruction contains 'unload'/'baggage')
                ├── Internal BRANCH B: inspection/maint  (instruction contains 'inspection'/'maintenance')
                └── Internal BRANCH C: fueling           (instruction contains 'fuel'/'fueling'/'refuel')
```

> Note: BRANCH C passes `instruction` through to `aircraft_ground_servicing` unchanged, which performs a second level of instruction-based routing to its own internal branches A/B/C. This creates a two-level instruction routing chain: `aircraft_turnaround_manager` → `aircraft_ground_operation` → `aircraft_ground_servicing` → leaf network.

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

### 5.1 ground_operation_agent (LLM Pass-Through Router)

The single entry-point agent. Its defining design principle, stated explicitly in the instructions, is zero transformation of sub-agent responses.

> *"CRITICAL: You are a pass-through router. Read the instruction field FIRST, route to exactly ONE sub-agent, pass ALL received parameters through unchanged, wait for the response, and return it verbatim to the caller. Do NOT transform, summarise, or re-interpret the sub-agent response. Do NOT call more than one sub-agent per invocation."*

#### Input parameters

|-----------------------------------|--------|:--------:|--------------------------------------------|
| Parameter                         | Type   | Required | Description                                |
|-----------------------------------|--------|:--------:|--------------------------------------------|
| `aircraft_type`                   | string | ✅       | Aircraft model/type                        |
| `flight_number`                   | string | ❌       | Flight identifier                          |
| `flight_status`                   | string | ❌       | Current flight status                      |
| `gate_id`                         | string | ❌       | Gate identifier                            |
| `engines_stop_status`             | string | ❌       | Required for BRANCH B                      |
| `wheelchocks_readiness_status`    | string | ❌       | Required for BRANCH B                      |
| `acu_readiness_status`            | string | ❌       | Required for BRANCH B                      |
| `gpu_readiness_status`            | string | ❌       | Required for BRANCH B                      |
| `wheelchocks_installation_status` | string | ❌       | Output of BRANCH B                         |
| `acu_connection_status`           | string | ❌       | Output of BRANCH B                         |
| `gpu_connection_status`           | string | ❌       | Output of BRANCH B                         |
| `jetbridge_connection_status`     | string | ❌       | Required for BRANCH C                      |
| `stairtruck_connection_status`    | string | ❌       | Required for BRANCH C                      |
| `deplaning_equipment_type`        | string | ❌       | Required for BRANCH C                      |
| `door_opening_status`             | string | ❌       | Required for BRANCH C                      |
| `passenger_disembarkation_status` | string | ❌       | Required for BRANCH C                      |
| `crew_exit_status`                | string | ❌       | Required for BRANCH C                      |
| `baggage_unload_status`           | string | ❌       | Output of BRANCH C (baggage path)          |
| `inspection_maintenance_status`   | string | ❌       | Output of BRANCH C (inspection path)       |
| `fueling_status`                  | string | ❌       | Output of BRANCH C (fueling path)          |
| `instruction`                     | string | ❌       | **Routing discriminant** — see table below |
|-----------------------------------|--------|:--------:|--------------------------------------------|

#### Instruction routing table

|------------------------------------------------------------------------------------------------|--------------|--------------------------------|--------------------|
| `instruction` contains                                                                         | Branch       | Sub-network called             | Turnaround step(s) |
|------------------------------------------------------------------------------------------------|--------------|--------------------------------|--------------------|
| `'readiness'` or `'check'`                                                                     | **BRANCH A** | `aircraft_ground_readiness`    | STEP 4             |
| `'ramp'`, `'wheelchocks'`, `'install'`, `'connect acu'`, `'connect gpu'`, or `'ramp services'` | **BRANCH B** | `aircraft_ground_rampservices` | STEP 8             |
| `'unload'`, `'baggage'`, `'inspection'`, `'maintenance'`, `'fuel'`, `'fueling'`, or `'refuel'` | **BRANCH C** | `aircraft_ground_servicing`    | STEPs 12, 18, 19   |
|------------------------------------------------------------------------------------------------|--------------|--------------------------------|--------------------|

> Note: BRANCH C instructions that arrive here (`'unload'`, `'inspection'`, `'fuel'`, etc.) are passed through unchanged to `aircraft_ground_servicing`, which uses these same keywords for its own internal branch routing. The instruction value is the carrier signal for two consecutive routing decisions.

> Note: The keyword `'check'` in BRANCH A would also match `'check readiness'`, `'check engines'`, `'check door'`, or any instruction containing the word "check". This is a broader match than intended if callers ever send instructions like `'check connection status'`.

#### Turnaround step mapping (called by `aircraft_turnaround_manager`)

|-----------------|-----------------------------------------|---------------|
| Turnaround STEP | `instruction` value passed              | Branch routed |
|-----------------|-----------------------------------------|---------------|
| STEP 4          | `'Check ground services readiness.'`    | BRANCH A      |
| STEP 8          | `'Execute ground ramp services.'`       | BRANCH B      |
| STEP 12         | `'Unload baggage from the aircraft.'`   | BRANCH C      |
| STEP 18         | `'Perform inspection and maintenance.'` | BRANCH C      |
| STEP 19         | `'Fuel the aircraft.'`                  | BRANCH C      |
|-----------------|-----------------------------------------|---------------|

---

#### BRANCH A — Ground readiness check (STEP 4)

**STEP 1:** Call `/AirlineTurnaround/aircraft_ground_readiness` with `aircraft_type`, `gate_id`. Wait. Extract `acu_readiness_status`, `gpu_readiness_status`, `wheelchocks_readiness_status`. **Return sub-agent response verbatim.**

---

#### BRANCH B — Ground ramp services (STEP 8)

**STEP 1:** Call `/AirlineTurnaround/aircraft_ground_rampservices` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheelchocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`. Wait. Extract `wheelchocks_installation_status`, `acu_connection_status`, `gpu_connection_status`. **Return sub-agent response verbatim.**

> Note: `aircraft_ground_rampservices` is a sub-network not individually documented in the README series so far. It handles wheelchocks installation, ACU connection, and GPU connection as a single consolidated ramp service operation.

---

#### BRANCH C — Ground servicing (STEPs 12, 18, 19)

**STEP 1:** Call `/AirlineTurnaround/aircraft_ground_servicing` with the full parameter set including `instruction` (passed through unchanged). Wait. Extract `baggage_unload_status` OR `inspection_maintenance_status` OR `fueling_status` (whichever applies to the instruction). **Return sub-agent response verbatim.**

> Note: BRANCH C is the only branch that passes `instruction` as a named parameter to its sub-network. BRANCHes A and B pass it only implicitly through sly_data via allow blocks.

---

#### sly_data contract

All four directions carry the same 20-field set:

`flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheelchocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`, `wheelchocks_installation_status`, `acu_connection_status`, `gpu_connection_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `door_opening_status`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `inspection_maintenance_status`, `fueling_status`

> Note: `instruction` is in the agent parameter schema but **absent from all four sly_data allow blocks**. It must always be passed as an explicit named parameter by the caller — it will not flow through sly_data automatically. This is correct by design for an instruction-routing network.

> Note: `task_id` is absent from all sly_data allow blocks — this network does not use the correlation token pattern used by `aircraft_crew_pilot`.

> Note: `assigned_runway_id` and `assigned_runway_length` are absent from the sly_data allow blocks despite being in `aircraft_crew_pilot`'s contract. These fields will not propagate through this network.

#### Down-chain tools

```
["TrackerAPI",
 "/AirlineTurnaround/aircraft_ground_readiness",
 "/AirlineTurnaround/aircraft_ground_rampservices",
 "/AirlineTurnaround/aircraft_ground_servicing"]
```

---

### 5.2 TrackerAPI (Registered but Not Instructed to Call)

**Class:** `AirlineTurnaround.aircraft_ground_operation.aircraft_ground_operation.TrackerAPI`

TrackerAPI is listed in the tools array (line 373) and its HOCON schema is fully defined, but **no branch in the instructions ever directs the agent to call it**. All three branches make exactly one external sub-network call and return the response verbatim — there is no TrackerAPI read or write step.

This is unique among all aggregation networks: `aircraft_cabin_services` calls TrackerAPI after each service, `aircraft_gate_services` calls TrackerAPI after each connection. `aircraft_ground_operation` delegates state persistence entirely to its downstream sub-networks.

> Note: No Python implementation file was uploaded for this network. The TrackerAPI class path is `AirlineTurnaround.aircraft_ground_operation.aircraft_ground_operation.TrackerAPI`. The fields below are inferred from the HOCON schema only.

#### HOCON schema fields (inferred tracked fields)

`flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheelchocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`, `wheelchocks_installation_status`, `acu_connection_status`, `gpu_connection_status`, `door_opening_status`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `inspection_maintenance_status`, `fueling_status`

> Note: The HOCON TrackerAPI schema correctly includes `"required": []`.

> Note: The TrackerAPI description is a single generic line: "I am the flight tracker in charge of logging parameters during aircraft turnaround." No copy-paste typos or stale field references.

---

## 6. External Sub-Network Dependencies

|---------------------------------------------------|----------|------------------|-------------------------------------------------------------------------------------|
| Sub-network path                                  | Branch   | Turnaround steps | Output fields                                                                       |
|---------------------------------------------------|----------|------------------|-------------------------------------------------------------------------------------|
| `/AirlineTurnaround/aircraft_ground_readiness`    | BRANCH A | STEP 4           | `acu_readiness_status`, `gpu_readiness_status`, `wheelchocks_readiness_status`      |
| `/AirlineTurnaround/aircraft_ground_rampservices` | BRANCH B | STEP 8           | `wheelchocks_installation_status`, `acu_connection_status`, `gpu_connection_status` |
| `/AirlineTurnaround/aircraft_ground_servicing`    | BRANCH C | STEPs 12, 18, 19 | `baggage_unload_status` / `inspection_maintenance_status` / `fueling_status`        |
|---------------------------------------------------|----------|------------------|-------------------------------------------------------------------------------------|

> Note: `aircraft_ground_rampservices` is a sub-network not yet individually documented in the README series. It consolidates wheelchocks installation, ACU connection, and GPU connection into a single ramp operation call.

---

## 7. Sample Queries

```
# STEP 4 — readiness check (BRANCH A)
"The B747 of flight AF84 has been assigned gate A21.
 Report the readiness of ground services at the gate."

# Called by aircraft_turnaround_manager STEP 4:
{"aircraft_type": "B747", "gate_id": "A21",
 "instruction": "Check ground services readiness."}

# STEP 8 — ramp services (BRANCH B)
"Flight AF84 is on blocks at gate A21. Engines are stopped.
 Wheelchocks, ACU and GPU are ready. Execute ground ramp services."

# STEP 12 — baggage unload (BRANCH C)
"The B747 aircraft of flight AF84 is on blocks at gate A21.
 The plane has been connected to the jetbridge. The aircraft door is open.
 Unload baggage."

# STEP 18 — inspection/maintenance (BRANCH C)
"Passengers have disembarked. Crew has exited. Perform inspection and maintenance."

# STEP 19 — fueling (BRANCH C)
"Passengers have disembarked. Crew has exited. Perform fueling."
```

---

## 8. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| TrackerAPI registered but never called by instructions | `aircraft_ground_operation.hocon` line 373 | Medium | All three branches return sub-agent response verbatim without calling TrackerAPI. State persistence is delegated to downstream sub-networks. This is intentional by design but means the local TrackerAPI never runs. Consider removing it from the tools list to avoid confusion, or document the delegation intent more explicitly. |
| `instruction` absent from all sly_data allow blocks | `aircraft_ground_operation.hocon` lines 273–369 | Medium | Callers must always pass `instruction` as an explicit named parameter. It will not flow through sly_data from a prior call. This is correct for a routing network but differs from patterns in `aircraft_cabin_services` and `aircraft_gate_services`. |
| Python implementation file not uploaded | — | Info | TrackerAPI class path is known; tracked fields inferred from HOCON schema only. |
| `'check'` keyword in BRANCH A is overly broad | `aircraft_ground_operation.hocon` line 212 | Low | Matches any instruction containing `'check'`, not just ground readiness checks. Could misroute `'check connection status'` or similar. |
| `aircraft_ground_rampservices` sub-network not individually documented | — | Info | This is the only sub-network in the turnaround system without a README in this series so far. |
| No verbatim-return enforcement for TrackerAPI | `aircraft_ground_operation.hocon` instructions | Low | The instructions say to return sub-agent responses verbatim, but don't explicitly forbid spontaneous TrackerAPI calls. An LLM may occasionally call TrackerAPI between the sub-agent call and the return. |

---

## 9. Comparison with Sibling Aggregation Networks

|-----------------------------------|--------------------------------------------------------------------|---------------------------------|-----------------------------|
| Aspect                            | `aircraft_ground_operation`                                        | `aircraft_cabin_services`       | `aircraft_gate_services`    |
|-----------------------------------|--------------------------------------------------------------------|---------------------------------|-----------------------------|
| Entry agent name                  | `ground_operation_agent`                                           | `cabin_services`                | `gate_crew_agent`           |
| Number of branches                | 3 (readiness / ramp / servicing)                                   | 3 (clean / lavatory / catering) | 2+2 sub-paths               |
| TrackerAPI called in instructions | **No — registered but never invoked**                              | Yes — after each service        | Yes — after each connection |
| Response handling                 | **Verbatim pass-through**                                          | Summary template per branch     | Summary template per branch |
| Two-level routing chain           | Yes — BRANCH C passes `instruction` to `aircraft_ground_servicing` | No                              | No                          |
| Execution limits                  | 40,000 / 7,200s                                                    | 3,000 / 300s                    | 40,000 / 7,200s             |
| Python file uploaded              | No                                                                 | Yes                             | Yes                         |
|-----------------------------------|--------------------------------------------------------------------|---------------------------------|-----------------------------|

---

## 10. Two-Level Instruction Routing Chain

This network introduces the only two-level instruction routing chain in the system. When `aircraft_turnaround_manager` calls STEP 12 (baggage) or STEP 18 (inspection) or STEP 19 (fueling), the `instruction` value flows through three layers:

```
aircraft_turnaround_manager
  instruction='Unload baggage from the aircraft.'
    │
    ▼
ground_operation_agent  (BRANCH C match: 'unload')
  passes instruction='Unload baggage from the aircraft.' unchanged
    │
    ▼
aircraft_ground_servicing  (internal BRANCH A match: 'unload'/'baggage')
    │
    ▼
/AirlineTurnaround/aircraft_baggage_unload  (leaf network)
```

The `instruction` string must contain keywords that satisfy both routing layers. `'Unload baggage from the aircraft.'` works because `'unload'` matches BRANCH C here AND `'baggage'` / `'unload'` matches BRANCH A inside `aircraft_ground_servicing`. The instructions for this network explicitly note: *"Pass the instruction field through unchanged so aircraft_ground_servicing can route to the correct internal branch (A/B/C)."*

---

## 11. Extensibility Guidance

- If TrackerAPI is intended to be called (e.g. to persist state at the aggregation level), add explicit TrackerAPI call steps to each branch's instructions
- If TrackerAPI is never intended to be called here, consider removing it from the tools list to prevent unintended spontaneous calls by the LLM
- Add `instruction` to the sly_data allow blocks if it should persist across calls (currently requires explicit passing every time)
- Fix the `'check'` keyword match to require `'readiness'` specifically, or use `'check readiness'` as the compound trigger
- `aircraft_ground_rampservices` should be documented as part of this README series

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
