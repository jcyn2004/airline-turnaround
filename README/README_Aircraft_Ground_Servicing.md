# Aircraft Ground Servicing
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_servicing.hocon`
> **Implementation file:** `aircraft_ground_servicing.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Route a ground servicing request to one of three service branches — baggage unloading, inspection/maintenance, or fueling — based on an explicit `instruction` field, then execute the selected service via its dedicated external network.

---

## 1. Overview

`aircraft_ground_servicing` is a **branch-routing dispatcher** in the **AirlineTurnaround** agentic system. Unlike most other networks that execute a single service, this network reads an `instruction` field and routes to exactly one of three downstream service networks per invocation. It acts as a unified entry point for the three turnaround services most dependent on human-clearance prerequisites.

The network combines:

- An LLM-based routing agent (`aircraft_ground_servicing_agent`) that reads the `instruction` field, selects the correct branch, and executes it
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_baggage_unload`, `aircraft_inspection_maintenance`, `aircraft_fueling`) resolved from the shared registry `registries/aaosa_basic.hocon`

A critical architectural distinction is the TrackerAPI implementation in this network: it uses **`args`-first** resolution (not `sly_data`-first), with an explicit docstring explaining the rationale. This is the only TrackerAPI in the system with this priority order and the only one with documented design reasoning for its field resolution strategy.

---

## 2. Repository Structure

```
aircraft_ground_servicing.hocon      # Agent network configuration
aircraft_ground_servicing.py         # TrackerAPI implementation (args-first)
registries/aaosa_basic.hocon         # Shared registry (aircraft_baggage_unload, aircraft_inspection_maintenance, aircraft_fueling)
```

---

## 3. System Architecture

```
User / Caller  (or upstream orchestrator)
   │  instruction = 'baggage' | 'inspection' | 'fuel'
   ▼
aircraft_ground_servicing_agent  (LLM Branch Router)
   │
   ├── TrackerAPI                                          (Coded tool: args-first state management)
   │
   ├── /AirlineTurnaround/aircraft_baggage_unload          (Branch A — baggage/unload)
   │
   ├── /AirlineTurnaround/aircraft_inspection_maintenance  (Branch B — inspection/maintenance)
   │
   └── /AirlineTurnaround/aircraft_fueling                 (Branch C — fuel/fueling/refuel)
```

### Design principles

- **Instruction-based routing:** The `instruction` parameter is the routing key. The agent reads it first and selects exactly one branch. If no branch matches, the agent reports not relevant.
- **Branch isolation:** Each branch executes its steps independently. Once a branch is matched, the agent is explicitly instructed not to evaluate or execute steps from other branches.
- **Validation-before-reporting:** All three branches include a `VALIDATION` step requiring the returned status to contain a specific value before success is declared. The agent must not fabricate completion.
- **TrackerAPI called last in each branch:** Unlike most orchestrators that call TrackerAPI first, the instructions for all three branches call the external service network first, then call TrackerAPI to persist the result. Branch A adds a `CRITICAL: Do NOT call TrackerAPI before executing` warning.
- **args-first TrackerAPI:** This network's `TrackerAPI` resolves `args` before `sly_data`, with documented rationale — new values from the current operation must overwrite prior accumulated state.

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

### 5.1 aircraft_ground_servicing_agent (LLM Branch Router)

The entry-point agent. It reads the `instruction` field, matches it to a branch, and executes that branch's single service step plus validation and summary.

#### Input parameters

| Parameter                         | Type   | Required | Description                                                                                             |
|-----------------------------------|--------|:--------:|---------------------------------------------------------------------------------------------------------|
| `flight_number`                   | string |    ✅     | Flight identifier                                                                                       |
| `aircraft_type`                   | string |    ✅     | Aircraft model/type                                                                                     |
| `flight_status`                   | string |    ✅     | Flight status                                                                                           |
| `gate_id`                         | string |    ❌     | Gate where the aircraft is parked                                                                       |
| `instruction`                     | string |    ❌     | Routing key: `'baggage'`/`'unload'`, `'inspection'`/`'maintenance'`, or `'fuel'`/`'fueling'`/`'refuel'` |
| `jetbridge_connection_status`     | string |    ❌     | For Branch A                                                                                            |
| `stairtruck_connection_status`    | string |    ❌     | For Branch A                                                                                            |
| `door_opening_status`             | string |    ❌     | For Branch A                                                                                            |
| `passenger_disembarkation_status` | string |    ❌     | For Branches B and C                                                                                    |
| `crew_exit_status`                | string |    ❌     | For Branches B and C                                                                                    |
| `baggage_unload_status`           | string |    ❌     | For Branches B and C                                                                                    |
| `inspection_maintenance_status`   | string |    ❌     | For Branch B output                                                                                     |
| `fueling_status`                  | string |    ❌     | For Branch C output                                                                                     |

> Note: `clearance_type` appears once in the HOCON agent parameter schema. No duplication is present.

#### Branch routing logic

| `instruction` contains               | Branch       | External network called                              |
|--------------------------------------|--------------|------------------------------------------------------|
| `'baggage'` or `'unload'`            | **Branch A** | `/AirlineTurnaround/aircraft_baggage_unload`         |
| `'inspection'` or `'maintenance'`    | **Branch B** | `/AirlineTurnaround/aircraft_inspection_maintenance` |
| `'fuel'`, `'fueling'`, or `'refuel'` | **Branch C** | `/AirlineTurnaround/aircraft_fueling`                |
| No match                             | —            | Agent replies not relevant and stops                 |

Branch A has highest routing priority and is checked first. If `instruction` contains `'baggage'` or `'unload'`, Branch A MUST execute regardless of other content in `instruction`.

#### Branch A — Baggage Unloading

1. `CRITICAL: Do NOT call TrackerAPI first.` Read all prerequisite values directly from incoming args.
2. Call `/AirlineTurnaround/aircraft_baggage_unload` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status`. Wait.
3. **VALIDATION:** `baggage_unload_status` must contain `'completed'` or `'unloaded'`. If not → report failure.
4. Call `TrackerAPI` to store `baggage_unload_status`.
5. Return summary.

#### Branch B — Inspection and Maintenance

1. Call `/AirlineTurnaround/aircraft_inspection_maintenance` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`. Wait.
2. **VALIDATION:** `inspection_maintenance_status` must contain `'completed'`. If not → report failure.
3. Call `TrackerAPI` to store `inspection_maintenance_status`.
4. Return summary.

#### Branch C — Fueling

1. Call `/AirlineTurnaround/aircraft_fueling` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`. Wait.
2. **VALIDATION:** `fueling_status` must contain `'completed'`. If not → report failure with raw response.
3. Call `TrackerAPI` to store `fueling_status`.
4. Return summary (with note: "IMPORTANT: Use this exact template").

#### sly_data contract

| Direction           | Parameters |
|---------------------|------------|
| **To upstream**     | `baggage_unload_status`, `inspection_maintenance_status`, `fueling_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `inspection_maintenance_status` |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `inspection_maintenance_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `baggage_unload_status`, `inspection_maintenance_status`, `fueling_status` |

#### Down-chain tools

```
["/AirlineTurnaround/aircraft_baggage_unload",
 "/AirlineTurnaround/aircraft_inspection_maintenance",
 "/AirlineTurnaround/aircraft_fueling",
 "TrackerAPI"]
```

---

### 5.2 TrackerAPI (Coded Tool) — Args-First Implementation

**Class:** `AirlineTurnaround.aircraft_ground_servicing.aircraft_ground_servicing.TrackerAPI`

This is the **only TrackerAPI in the system that uses `args`-first resolution**. All other TrackerAPI instances prefer `sly_data`. The docstring explains the design decision:

> *"args carries the current operation's output (e.g. fueling_status from the fueling agent). sly_data carries prior state. If we always preferred sly_data, a completed inspection from STEP 18 would silently block the fueling write in STEP 19, causing the agent to return the wrong branch summary."*

#### Data resolution priority

1. **`args[field]`** — authoritative for writes; always wins. Value is immediately written to `sly_data`.
2. **`sly_data[field]`** — read existing state when `args` has no value for the field.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

This is the **inverse** of the standard priority used by all other TrackerAPI implementations in the system.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is the broadest TrackerAPI config in the system:

**Tracked fields (22):**
`flight_number`, `aircraft_type`, `flight_status`, `ground_clearance_type`, `gate_id`, `assigned_runway_id`, `assigned_runway_length`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`, `aircraft_direction`, `clearance_type`, `engines_stop_status`, `door_opening_status`, `jetbridge_connection_status`, `passenger_disembarkation_status`, `crew_exit_status`, `baggage_unload_status`, `inspection_maintenance_status`, `fueling_status`, `stairtruck_connection_status`, `deplaning_equipment_type`

**Return fields:** Identical to tracked fields (all 22 returned).

> Note: `inspection_maintenance_status` is tracked and returned by the Python TrackerAPI and is also exposed by the HOCON `TrackerAPI` parameters schema.

> Note: `stairtruck_connection_status` and `deplaning_equipment_type` are present both in the sly_data allow blocks and in `FLIGHT_TURNAROUND_TRACKED_FIELDS` / `FLIGHT_TURNAROUND_RETURN_FIELDS`. TrackerAPI tracks and returns them.

> Note: The HOCON `TrackerAPI` description still references the legacy field name `"wheels_chocks_installation_status"`, while the schema and Python tracker use `wheels_chocks_readiness_status`. The description string is stale and should be aligned.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

These tools are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path                                            | Branch | Trigger keywords                  |
|------------------------------------------------------|--------|-----------------------------------|
| `/AirlineTurnaround/aircraft_baggage_unload`         | A      | `'baggage'`, `'unload'`           |
| `/AirlineTurnaround/aircraft_inspection_maintenance` | B      | `'inspection'`, `'maintenance'`   |
| `/AirlineTurnaround/aircraft_fueling`                | C      | `'fuel'`, `'fueling'`, `'refuel'` |

---

## 7. Sample Queries

```
# Branch A
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The plane has been connected to the jetbridge. The aircraft door is open.
Unload baggages."

# Branch B
"The B747 aircraft of flight AF84 is on blocks at gate A1.
Baggages have been unloaded. All passengers have disembarked.
The crew has exited the aircraft. Perform inspection and maintenance."

# Branch C
"The B747 aircraft of flight AF84 is on blocks at gate A1.
Baggages have been unloaded. All passengers have disembarked.
The crew has exited the aircraft. Perform the fueling of the aircraft."
```

---

## 8. Example Execution Trace (Branch C — Fueling)

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. Baggages have been unloaded. All passengers have disembarked. The crew has exited the aircraft. Perform the fueling of the aircraft."

**Execution steps:**

1. `instruction` matched to Branch C (`'fuel'`/`'fueling'` detected)
2. `/AirlineTurnaround/aircraft_fueling` called with all parameters
3. Validation: `fueling_status=completed` ✅
4. `TrackerAPI` called — stores `fueling_status=completed`
5. Summary returned

**Output:**

```
*******************************
* Summary of aircraft fueling *
*******************************
** flight status                    **: on blocks
** passenger disembarkation status  **: completed
** crew exit status                 **: exited
** baggage unload status            **: completed
** fueling status summary           **: completed
```

---

## 9. Known Issues and Maintenance Notes

| Issue       | Location    | Severity | Notes    |
|-------------|-------------|:--------:|----------|
|             |             |          |          |

---

## 10. Relationship to Other Networks

`aircraft_ground_servicing` acts as a single-call interface for three networks that could otherwise be called independently:

| Direct call                                     | Via `aircraft_ground_servicing` |
|-------------------------------------------------|---------------------------------|
| Call `aircraft_baggage_unload` directly         | Pass `instruction='baggage'`    |
| Call `aircraft_inspection_maintenance` directly | Pass `instruction='inspection'` |
| Call `aircraft_fueling` directly                | Pass `instruction='fuel'`       |

The primary value-add is the shared TrackerAPI with 22-field coverage, the instruction-routing dispatch, and the standardized validation + summary templates for all three services. Upstream orchestrators that need to trigger multiple services in sequence can call this network multiple times with different `instruction` values.

---

## 11. Key Architectural Differences from Other Networks

| Aspect                      | `aircraft_ground_servicing`          | Typical network                           |
|-----------------------------|--------------------------------------|-------------------------------------------|
| TrackerAPI field resolution | `args`-first (write always wins)     | `sly_data`-first (accumulated state wins) |
| Number of external services | 3 (routed by `instruction`)          | 1                                         |
| TrackerAPI called           | After service execution              | Before and after                          |
| Branch A: TrackerAPI timing | Explicitly deferred to after service | Called at step 1                          |
| Tracked field count         | 22 (broadest non-master set)         | 3–8                                       |
| TrackerAPI tracked = return | Yes                                  | Varies                                    |

---

## 12. Extensibility Guidance

- Add Branch D, E, etc. for additional services (cabin cleaning, catering loading, crew exit) by following the same BRANCH → STEP → VALIDATION → RETURN SUMMARY pattern

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational control systems.
