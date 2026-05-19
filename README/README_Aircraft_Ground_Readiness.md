# Aircraft Ground Readiness
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_readiness.hocon`
> **Implementation file:** `aircraft_ground_readiness.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Check and report the combined readiness of all three ground service equipment types — ACU, GPU, and wheel chocks — at an assigned gate in a single call, by delegating to three dedicated setup networks.

---

## 1. Overview

`aircraft_ground_readiness` is a **readiness aggregator** in the **AirlineTurnaround** agentic system. It sits above the three individual setup networks (`aircraft_ground_acu_setup`, `aircraft_ground_gpu_setup`, `aircraft_ground_wheels_chocks_setup`) and provides a single-call interface that always returns all three readiness statuses together.

The network combines:

- An LLM-based aggregation agent (`ground_readiness`) that calls all three setup networks in sequence
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references resolved from the shared registry `registries/aaosa_basic.hocon`

A notable design decision is that the agent instructions explicitly require that all three readiness checks always run together in a single call — restoring the abstraction boundary that would otherwise force the upstream orchestrator to call this network three times (once per equipment type).

Configuration values are aligned with the system-wide standard: `max_iterations = 50000` and `max_execution_seconds = 7200`, consistent with the other networks in the system.

---

## 2. Repository Structure

```
registries/AirlineTurnaround/aircraft_ground_readiness.hocon                                  # Agent network configuration
coded_tools/AirlineTurnaround/aircraft_ground_readiness/aircraft_ground_readiness.py          # TrackerAPI implementation (sly_data-first)
registries/aaosa_basic.hocon                                                                  # Shared registry (aircraft_ground_acu_setup, aircraft_ground_gpu_setup, aircraft_ground_wheels_chocks_setup)
```

---

## 3. System Architecture

```
User / Caller  (or upstream orchestrator)
   │
   ▼
ground_readiness  (LLM Aggregation Agent)
   │
   ├── TrackerAPI                                              (Coded tool: sly_data-first state management)
   │
   ├── /AirlineTurnaround/aircraft_ground_acu_setup           (Step 2 — ACU readiness from CSV)
   │
   ├── /AirlineTurnaround/aircraft_ground_gpu_setup           (Step 3 — GPU readiness from CSV)
   │
   └── /AirlineTurnaround/aircraft_ground_wheels_chocks_setup (Step 4 — wheels chocks readiness)
```

### Design principles

- **Complete-all semantics:** The agent is instructed to always execute all three readiness checks and return all three statuses — even if one or more returns `'not ready'`. It must not stop early on a failed check.
- **Single-call abstraction:** Upstream orchestrators receive all three statuses in one network invocation, hiding the three-step internal delegation.
- **Sequential with intermediate persistence:** Each setup network call is followed immediately by a `TrackerAPI` write, ensuring each status is persisted before the next check begins.
- **Error-resilient progression:** Per NOTE 2 in the instructions, if any step returns an error string, the error is recorded as the status value and execution continues to the next step. The agent never aborts early.

---

## 4. Runtime Configuration

|-------------------------|----------------|---------------------|
| Setting                 | Value          | System-wide typical |
|-------------------------|----------------|---------------------|
| LLM model               | `gpt-5.4-mini` | `gpt-5.4-mini`      |
| `max_iterations`        | `50000`        | `40000`             |
| `max_execution_seconds` | `7200`         | `7200`              |
|-------------------------|----------------|---------------------|

> Note: The `instructions_prefix` names **San Francisco International Airport** explicitly, consistent with `aircraft_gate_selection` and differentiating this network from most others which use a generic airport context.

---

## 5. Components

### 5.1 ground_readiness (LLM Aggregation Agent)

The entry-point agent. It validates inputs, calls each setup network in order, persists each result, and returns the combined summary.

#### Input parameters

| Parameter                        | Type   | Required | Description                            |
|----------------------------------|--------|:--------:|----------------------------------------|
| `aircraft_type`                  | string |    ✅     | Aircraft model/type                    |
| `gate_id`                        | string |    ✅     | Gate assigned to the aircraft          |
| `flight_number`                  | string |    ❌     | Flight number of the incoming aircraft |
| `acu_readiness_status`           | string |    ❌     | ACU readiness (output)                 |
| `gpu_readiness_status`           | string |    ❌     | GPU readiness (output)                 |
| `wheels_chocks_readiness_status` | string |    ❌     | Wheel chocks readiness (output)        |

#### Orchestration flow

The instructions use explicit `STEP` labels:

1. **STEP 1 — Validate inputs:** Confirm `aircraft_type` and `gate_id` are available. If missing → call `TrackerAPI` to retrieve. If still missing → ask user and wait.
2. **STEP 2 — Check ACU readiness:** Call `/AirlineTurnaround/aircraft_ground_acu_setup` with `aircraft_type`, `gate_id`. Wait. Store `acu_readiness_status`. Call `TrackerAPI` to log it.
3. **STEP 3 — Check GPU readiness:** Call `/AirlineTurnaround/aircraft_ground_gpu_setup` with `aircraft_type`, `gate_id`. Wait. Store `gpu_readiness_status`. Call `TrackerAPI` to log it.
4. **STEP 4 — Check wheels chocks readiness:** Call `/AirlineTurnaround/aircraft_ground_wheels_chocks_setup` with `aircraft_type`, `gate_id`. Wait. Store `wheels_chocks_readiness_status`. Call `TrackerAPI` to log it.
5. **STEP 5 — Return combined readiness report.**

> **NOTE 1 in instructions:** "Always return ALL THREE statuses even if one or more is 'not ready'. Do not stop early if one status is 'not ready' — complete all three checks and report all results."

> **NOTE 2 in instructions:** "Always proceed through ALL THREE steps regardless of the result from any individual step. If a step returns an error string, record the error as the status value and continue to the next step. Never abort early."

#### sly_data contract

| Direction           | Parameters                                                                                                                       |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`                                                 |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`                                                                                      |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`                                                                                      |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`    |

> Note: `from_upstream` carries the additional `flight_number` field, allowing flight context to flow into this network from the orchestrator.

#### Down-chain tools

```
["TrackerAPI",
 "/AirlineTurnaround/aircraft_ground_acu_setup",
 "/AirlineTurnaround/aircraft_ground_gpu_setup",
 "/AirlineTurnaround/aircraft_ground_wheels_chocks_setup"]
```

---

### 5.2 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_readiness.aircraft_ground_readiness.TrackerAPI`

Standard `sly_data`-first implementation. Called three times during the workflow — once after each equipment readiness check to persist the returned status — and potentially once in Step 1 to retrieve missing inputs.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

**Tracked fields (`FLIGHT_TURNAROUND_TRACKED_FIELDS`):**
`acu_readiness_status`, `aircraft_type`, `flight_number`, `gate_id`, `gpu_readiness_status`, `wheels_chocks_readiness_status`

**Return fields (`FLIGHT_TURNAROUND_RETURN_FIELDS`):** Identical to tracked fields.

#### TrackerAPI parameter schema

The HOCON TrackerAPI definition has a clean, minimal parameter schema with `"required": []` and the following properties: `aircraft_type`, `gate_id`, `wheels_chocks_readiness_status`, `gpu_readiness_status`, `acu_readiness_status`, `flight_number`.

---

## 6. External Tool Dependencies

These tools are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path                                                | Purpose                          | Step   |
|----------------------------------------------------------|----------------------------------|--------|
| `/AirlineTurnaround/aircraft_ground_acu_setup`           | Check ACU readiness via CSV      | Step 2 |
| `/AirlineTurnaround/aircraft_ground_gpu_setup`           | Check GPU readiness via CSV      | Step 3 |
| `/AirlineTurnaround/aircraft_ground_wheels_chocks_setup` | Check wheels chocks readiness    | Step 4 |

---

## 7. Sample Queries

```
"The B747 of flight AF84 has been assigned gate A1. Report the readiness of ground services at the gate."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 of flight AF84 has been assigned gate A1. Report the readiness of ground services at the gate."

**Execution steps:**

1. Inputs validated: `aircraft_type=B747`, `gate_id=A1` ✅ (Step 1)
2. `/AirlineTurnaround/aircraft_ground_acu_setup` called → `acu_readiness_status=ready`. `TrackerAPI` called (Step 2)
3. `/AirlineTurnaround/aircraft_ground_gpu_setup` called → `gpu_readiness_status=ready`. `TrackerAPI` called (Step 3)
4. `/AirlineTurnaround/aircraft_ground_wheels_chocks_setup` called → `wheels_chocks_readiness_status=ready`. `TrackerAPI` called (Step 4)
5. Summary returned (Step 5)

**Output:**

```
***************************************
* Ground services readiness summary   *
***************************************
** aircraft type                  **: B747
** gate id                        **: A1
** ACU readiness status           **: ready
** GPU readiness status           **: ready
** wheels chocks readiness status **: ready
```

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "gate_id": "A1",
  "acu_readiness_status": "ready",
  "gpu_readiness_status": "ready",
  "wheels_chocks_readiness_status": "ready"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue                                                            | Location                                              | Severity | Notes                                                                                                                                                                                     |
|------------------------------------------------------------------|-------------------------------------------------------|:--------:|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Interactive user-wait in Step 1                                  | `aircraft_ground_readiness.hocon` Step 1 instructions |   Low    | "If still missing, ask the user and wait" — same automated-context risk as `aircraft_engines_stop`.                                                                                       |

---

## 10. Relationship to Other Networks

`aircraft_ground_readiness` sits at the top of the equipment readiness sub-system:

```
aircraft_gate_selection             ─── writes availability  →  gate_equipments_base.csv
                                                                   │
aircraft_ground_acu_setup           ←── reads ACU readiness  ────┤
aircraft_ground_gpu_setup           ←── reads GPU readiness  ────┤
aircraft_ground_wheels_chocks_setup ← reads chocks readiness ────┘
         │
         └── aircraft_ground_readiness  ─── aggregates all three, single call interface
```

| Network                               | Role                                                                            |
|---------------------------------------|---------------------------------------------------------------------------------|
| `aircraft_ground_acu_setup`           | Leaf — reads `air_conditioning_unit_readiness` from CSV                         |
| `aircraft_ground_gpu_setup`           | Leaf — reads `ground_power_unit_readiness` from CSV                             |
| `aircraft_ground_wheels_chocks_setup` | Leaf — reads `wheels_chocks_readiness` from CSV                                 |
| `aircraft_ground_readiness`           | Aggregator — calls all three, returns combined result                           |
| `aircraft_ground_acu_connect`         | Consumer — calls `aircraft_ground_acu_setup` directly (not via this aggregator) |
| `aircraft_ground_gpu_connect`         | Consumer — calls `aircraft_ground_gpu_setup` directly (not via this aggregator) |

---

## 11. Extensibility Guidance

- The three setup networks (`aircraft_ground_acu_setup`, `aircraft_ground_gpu_setup`, `aircraft_ground_wheels_chocks_setup`) follow a common CSV-reading pattern. New equipment readiness checks can be added by implementing a similar leaf network and registering it both in `aaosa_basic.hocon` and in the `tools` list of the `ground_readiness` agent.

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
