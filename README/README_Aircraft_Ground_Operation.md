# Aircraft Ground Operation
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_operation.hocon`
> **Implementation file:** none (no Python implementation file is registered for this network)
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Pure pass-through router for all ground operations — receives an `instruction` field from `aircraft_turnaround_manager` and routes verbatim to one of three sub-networks: ground readiness, ground ramp services, or ground servicing.

---

## 1. Overview

`aircraft_ground_operation` is one of the four aggregation networks called directly by `aircraft_turnaround_manager`. It handles five of the twenty turnaround steps (STEPs 4, 8, 12, 18, 19) and is the busiest aggregation network in terms of call frequency.

Unlike `aircraft_cabin_services` or `aircraft_gate_services` (which have their own TrackerAPI call logic), this network is designed as a **pure pass-through router**. Its instructions explicitly prohibit any response transformation: the sub-agent response must be returned verbatim to the caller. There is **no TrackerAPI registered** in this network — state management is delegated entirely to the downstream sub-networks.

The network combines:
- `ground_operation_agent` — a single LLM pass-through routing agent with three branches
- Three external sub-networks (no TrackerAPI; the tools array contains only the three sub-network paths)

No Python implementation file is referenced by this network. The HOCON declares only the orchestrator agent and three external sub-network tools.

---

## 2. Repository Structure

```
aircraft_ground_operation.hocon    # Agent network configuration
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
| `aircraft_type`                   | string |    YES   | Aircraft model/type                        |
| `flight_number`                   | string |    NO    | Flight identifier                          |
| `flight_status`                   | string |    NO    | Current flight status                      |
| `gate_id`                         | string |    NO    | Gate identifier                            |
| `engines_stop_status`             | string |    NO    | Required for BRANCH B                      |
| `wheels_chocks_readiness_status`    | string |    NO    | Required for BRANCH B                      |
| `acu_readiness_status`            | string |    NO    | Required for BRANCH B                      |
| `gpu_readiness_status`            | string |    NO    | Required for BRANCH B                      |
| `wheels_chocks_installation_status` | string |    NO    | Output of BRANCH B                         |
| `acu_connection_status`           | string |    NO    | Output of BRANCH B                         |
| `gpu_connection_status`           | string |    NO    | Output of BRANCH B                         |
| `jetbridge_connection_status`     | string |    NO    | Required for BRANCH C                      |
| `stairtruck_connection_status`    | string |    NO    | Required for BRANCH C                      |
| `deplaning_equipment_type`        | string |    NO    | Required for BRANCH C                      |
| `door_opening_status`             | string |    NO    | Required for BRANCH C                      |
| `passenger_disembarkation_status` | string |    NO    | Required for BRANCH C                      |
| `crew_exit_status`                | string |    NO    | Required for BRANCH C                      |
| `baggage_unload_status`           | string |    NO    | Output of BRANCH C (baggage path)          |
| `inspection_maintenance_status`   | string |    NO    | Output of BRANCH C (inspection path)       |
| `fueling_status`                  | string |    NO    | Output of BRANCH C (fueling path)          |
| `instruction`                     | string |    NO    | **Routing discriminant** — see table below |
|-----------------------------------|--------|:--------:|--------------------------------------------|

#### Instruction routing table

|------------------------------------------------------------------------------------------------|--------------|--------------------------------|--------------------|
| `instruction` contains                                                                         | Branch       | Sub-network called             | Turnaround step(s) |
|------------------------------------------------------------------------------------------------|--------------|--------------------------------|--------------------|
| `'readiness'` or `'check'`                                                                     | **BRANCH A** | `aircraft_ground_readiness`    | STEP 4             |
| `'ramp'`, `'install'`, `'connect acu'`, `'connect gpu'`, `'ramp services'`, `'execute ground ramp'`, or `'perform ground ramp'` | **BRANCH B** | `aircraft_ground_rampservices` | STEP 8             |
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

**STEP 1:** Call `/AirlineTurnaround/aircraft_ground_readiness` with `flight_number`, `aircraft_type`, `gate_id`. Wait. Extract `acu_readiness_status`, `gpu_readiness_status`, `wheels_chocks_readiness_status`. **Return sub-agent response verbatim.**

---

#### BRANCH B — Ground ramp services (STEP 8)

**STEP 1:** Call `/AirlineTurnaround/aircraft_ground_rampservices` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`. Wait. Extract `wheels_chocks_installation_status`, `acu_connection_status`, `gpu_connection_status`. **Return sub-agent response verbatim.**

> Note: `aircraft_ground_rampservices` is a sub-network not individually documented in the README series so far. It handles wheelchocks installation, ACU connection, and GPU connection as a single consolidated ramp service operation.

---

#### BRANCH C — Ground servicing (STEPs 12, 18, 19)

**STEP 1:** Call `/AirlineTurnaround/aircraft_ground_servicing` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `door_opening_status`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, and `instruction` (passed through unchanged). Wait. Extract `baggage_unload_status` OR `inspection_maintenance_status` OR `fueling_status` (whichever applies to the instruction). **Return sub-agent response verbatim.**

> Note: BRANCH C is the only branch that passes `instruction` as a named parameter to its sub-network. BRANCHes A and B pass it only implicitly through sly_data via allow blocks.

---

#### sly_data contract

| Direction           | Parameters |
|---------------------|------------|
| **To upstream**     | `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`, `wheels_chocks_installation_status`, `acu_connection_status`, `gpu_connection_status`, `baggage_unload_status`, `inspection_maintenance_status`, `fueling_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `inspection_maintenance_status` |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `inspection_maintenance_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`, `wheels_chocks_installation_status`, `acu_connection_status`, `gpu_connection_status`, `baggage_unload_status`, `inspection_maintenance_status`, `fueling_status` |

> Note: `instruction` is in the agent parameter schema but **absent from all four sly_data allow blocks**. It must always be passed as an explicit named parameter by the caller — it will not flow through sly_data automatically. This is correct by design for an instruction-routing network.

> Note: `task_id` is absent from all sly_data allow blocks — this network does not use the correlation token pattern used by `aircraft_crew_pilot`.

> Note: `assigned_runway_id` and `assigned_runway_length` are absent from the sly_data allow blocks despite being in `aircraft_crew_pilot`'s contract. These fields will not propagate through this network.

#### Down-chain tools

```
["/AirlineTurnaround/aircraft_ground_readiness",
 "/AirlineTurnaround/aircraft_ground_rampservices",
 "/AirlineTurnaround/aircraft_ground_servicing"]
```

---

### 5.2 No TrackerAPI registered

This network does **not** register a TrackerAPI tool. The orchestrator agent's `tools` list contains only the three external sub-network paths (`aircraft_ground_readiness`, `aircraft_ground_rampservices`, `aircraft_ground_servicing`). No TrackerAPI class is referenced and no Python implementation file is associated with this HOCON.

This is unique among the aggregation networks: `aircraft_cabin_services` calls TrackerAPI after each service, `aircraft_gate_services` calls TrackerAPI after each connection. `aircraft_ground_operation` delegates state persistence entirely to its downstream sub-networks, and does not even register a TrackerAPI stub.

> Note: Because there is no TrackerAPI in this network, none of the orchestrator-level fields are tracked locally; any tracking happens inside the downstream leaf networks.

---

## 6. External Sub-Network Dependencies

|---------------------------------------------------|----------|------------------|-------------------------------------------------------------------------------------|
| Sub-network path                                  | Branch   | Turnaround steps | Output fields                                                                       |
|---------------------------------------------------|----------|------------------|-------------------------------------------------------------------------------------|
| `/AirlineTurnaround/aircraft_ground_readiness`    | BRANCH A | STEP 4           | `acu_readiness_status`, `gpu_readiness_status`, `wheels_chocks_readiness_status`      |
| `/AirlineTurnaround/aircraft_ground_rampservices` | BRANCH B | STEP 8           | `wheels_chocks_installation_status`, `acu_connection_status`, `gpu_connection_status` |
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
"The B747 aircraft of flight AF84 is on blocks at gate A21.
 Passengers have disembarked. Crew has exited.
 Perform inspection and maintenance."

# STEP 19 — fueling (BRANCH C)
"The B747 aircraft of flight AF84 is on blocks at gate A21.
 Passengers have disembarked. Crew has exited.
 Perform fueling."
```

---

## 8. Known Issues and Maintenance Notes

| Issue                                                                  | Location                                        | Severity | Notes                                                                                                                                                                                                                                                                                                                                 |
|------------------------------------------------------------------------|-------------------------------------------------|:--------:|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `instruction` absent from all sly_data allow blocks                    | `aircraft_ground_operation.hocon` lines 309–406 |  Medium  | Callers must always pass `instruction` as an explicit named parameter. It will not flow through sly_data from a prior call. This is correct for a routing network but differs from patterns in `aircraft_cabin_services` and `aircraft_gate_services`.                                                                                |
| No local state tracking                                                | `aircraft_ground_operation.hocon` tools array (line 408) |   Info   | No TrackerAPI is registered for this network. All persistence is delegated to downstream sub-networks.                                                                                                                                                                                                                                |
| `'check'` keyword in BRANCH A is overly broad                          | `aircraft_ground_operation.hocon` line 229      |   Low    | Matches any instruction containing `'check'`, not just ground readiness checks. Could misroute `'check connection status'` or similar.                                                                                                                                                                                                |
| `flight_number` declared twice in agent parameters                     | `aircraft_ground_operation.hocon` lines 111–122 |   Low    | `flight_number` is defined twice (lines 111–114 and 119–122) in the parameters block. JSON/HOCON last-wins semantics make this harmless but it is duplicated content.                                                                                                                                                                 |
| ~~BRANCH B output fields dropped from `to_upstream`~~ **FIXED**        | `aircraft_ground_operation.hocon` `allow.to_upstream` | Resolved | `wheels_chocks_installation_status`, `acu_connection_status`, and `gpu_connection_status` were extracted from the BRANCH B sub-agent response per the agent instructions but were missing from the `to_upstream` sly_data allow-list, so they never reached `aircraft_turnaround_manager`. This previously forced STEP 8 to call `aircraft_ground_rampservices` directly, bypassing this network, since its own `to_upstream` block correctly exposed those fields. The allow-list has been corrected to include all three fields, and STEP 8 now routes through `aircraft_ground_operation` like the other ground-operation steps. |

---

## 9. Comparison with Sibling Aggregation Networks

|-----------------------------------|--------------------------------------------------------------------|---------------------------------|-----------------------------|
| Aspect                            | `aircraft_ground_operation`                                        | `aircraft_cabin_services`       | `aircraft_gate_services`    |
|-----------------------------------|--------------------------------------------------------------------|---------------------------------|-----------------------------|
| Entry agent name                  | `ground_operation_agent`                                           | `cabin_services`                | `gate_crew_agent`           |
| Number of branches                | 3 (readiness / ramp / servicing)                                   | 3 (clean / lavatory / catering) | 2+2 sub-paths               |
| TrackerAPI registered             | **No — not in tools array at all**                                 | Yes — called after each service | Yes — called after each connection |
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

The `instruction` string must contain keywords that satisfy both routing layers. `'Unload baggage from the aircraft.'` works because `'unload'` matches BRANCH C here AND `'baggage'` / `'unload'` matches BRANCH A inside `aircraft_ground_servicing`. The instructions for this network explicitly note: *"Pass the instruction field through unchanged so aircraft_ground_servicing can route to the correct internal branch."*

---

## 11. Extensibility Guidance

- Add `instruction` to the sly_data allow blocks if it should persist across calls (currently requires explicit passing every time)
- Fix the `'check'` keyword match to require `'readiness'` specifically, or use `'check readiness'` as the compound trigger
- Remove the duplicate `flight_number` parameter declaration in the agent parameters block
- If local tracking is ever needed, a TrackerAPI tool can be added to the `tools` array alongside the three sub-network paths

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
