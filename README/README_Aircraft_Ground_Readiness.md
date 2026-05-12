# Aircraft Ground Readiness
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_readiness.hocon`
> **Implementation file:** `aircraft_ground_readiness.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Check and report the combined readiness of all three ground service equipment types — ACU, GPU, and wheel chocks — at an assigned gate in a single call, by delegating to three dedicated setup networks.

---

## 1. Overview

`aircraft_ground_readiness` is a **readiness aggregator** in the **AirlineTurnaround** agentic system. It sits above the three individual setup networks (`aircraft_ground_acu_setup`, `aircraft_ground_gpu_setup`, `aircraft_ground_wheelchocks_setup`) and provides a single-call interface that always returns all three readiness statuses together.

The network combines:

- An LLM-based aggregation agent (`ground_readiness`) that calls all three setup networks in sequence
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references resolved from the shared registry `registries/aaosa_basic.hocon`

A notable design decision is documented directly in the HOCON via an inline comment block explaining the architectural evolution: the original instructions called each subsystem separately, requiring the upstream orchestrator to call this network three times (once per equipment type). The fix consolidated all three checks into a single call, restoring the abstraction boundary.

Two configuration values stand out as unique: `max_iterations = 3000` and `max_execution_seconds = 300` — significantly lower than the `40000` / `7200` values used by every other network in the system.

---

## 2. Repository Structure

```
aircraft_ground_readiness.hocon      # Agent network configuration
aircraft_ground_readiness.py         # TrackerAPI implementation (sly_data-first)
registries/aaosa_basic.hocon         # Shared registry (aircraft_ground_acu_setup, aircraft_ground_gpu_setup, aircraft_ground_wheelchocks_setup)
```

> Note: `aircraft_ground_wheelchocks_setup` is referenced as an external dependency but has not been observed in other network files. Its existence and implementation should be verified before deploying this network.

---

## 3. System Architecture

```
User / Caller  (or upstream orchestrator)
   │
   ▼
ground_readiness  (LLM Aggregation Agent)
   │
   ├── TrackerAPI                                           (Coded tool: sly_data-first state management)
   │
   ├── /AirlineTurnaround/aircraft_ground_acu_setup        (Step 2 — ACU readiness from CSV)
   │
   ├── /AirlineTurnaround/aircraft_ground_gpu_setup        (Step 3 — GPU readiness from CSV)
   │
   └── /AirlineTurnaround/aircraft_ground_wheelchocks_setup (Step 4 — wheelchocks readiness)
```

### Design principles

- **Complete-all semantics:** The agent is instructed to always execute all three readiness checks and return all three statuses — even if one or more returns `'not ready'`. It must not stop early on a failed check.
- **Single-call abstraction:** Upstream orchestrators receive all three statuses in one network invocation, hiding the three-step internal delegation.
- **Sequential with intermediate persistence:** Each setup network call is followed immediately by a `TrackerAPI` write, ensuring each status is persisted before the next check begins.
- **Tightly bounded execution:** Compared to every other network in the system, this network has a 13× lower iteration limit and 24× lower time limit, reflecting its narrow, predictable scope.

---

## 4. Runtime Configuration

|-------------------------|----------------|---------------------|
| Setting                 | Value          | System-wide typical |
|-------------------------|----------------|---------------------|
| LLM model               | `gpt-5.4-mini` | `gpt-5.4-mini`      |
| `max_iterations`        | **`3000`**     | `40000`             |
| `max_execution_seconds` | **`300`**      | `7200`              |
|-------------------------|----------------|---------------------|

> Note: These tight bounds reflect the intentional design scope of this network — three sequential tool calls with TrackerAPI logging between each. The bounds should be sufficient for this workflow but would fail if the network is extended with additional steps.

> Note: The `instructions_prefix` names **San Francisco International Airport** explicitly, consistent with `aircraft_gate_selection` and differentiating this network from most others which use a generic airport context.

---

## 5. Components

### 5.1 ground_readiness (LLM Aggregation Agent)

The entry-point agent. It validates inputs, calls each setup network in order, persists each result, and returns the combined summary.

#### Input parameters

| Parameter | Type | Required | Description |
|---|---|:---:|---|
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `gate_id` | string | ✅ | Gate assigned to the aircraft |
| `acu_readiness_status` | string | ❌ | ACU readiness (output) |
| `gpu_readiness_status` | string | ❌ | GPU readiness (output) |
| `wheelchocks_readiness_status` | string | ❌ | Wheel chocks readiness (output) |

#### Orchestration flow

The instructions use explicit `STEP` labels:

1. **STEP 1 — Validate inputs:** Confirm `aircraft_type` and `gate_id` are available. If missing → call `TrackerAPI` to retrieve. If still missing → ask user and wait.
2. **STEP 2 — Check ACU readiness:** Call `/AirlineTurnaround/aircraft_ground_acu_setup` with `aircraft_type`, `gate_id`. Wait. Store `acu_readiness_status`. Call `TrackerAPI` to log it.
3. **STEP 3 — Check GPU readiness:** Call `/AirlineTurnaround/aircraft_ground_gpu_setup` with `aircraft_type`, `gate_id`. Wait. Store `gpu_readiness_status`. Call `TrackerAPI` to log it.
4. **STEP 4 — Check wheelchocks readiness:** Call `/AirlineTurnaround/aircraft_ground_wheelchocks_setup` with `aircraft_type`, `gate_id`. Wait. Store `wheelchocks_readiness_status`. Call `TrackerAPI` to log it.
5. **STEP 5 — Return combined readiness report.**

> **NOTE in instructions:** "Always return ALL THREE statuses even if one or more is 'not ready'. Do not stop early if one status is 'not ready' — complete all three checks and report all results."

#### Design fix documented in HOCON

The HOCON contains an inline comment block at lines 125–130 explaining the architectural evolution:

> *"The original instructions called each readiness subsystem separately, which caused the turnaround orchestrator to call this agent three times (once per equipment). This forced the orchestrator to know the internals of this subsystem — a violation of abstraction. The fix: this agent always checks ALL THREE readiness statuses in one call and returns them together. The orchestrator only needs one call."*

This is one of the few places in the system where design rationale is explicitly documented in the HOCON.

#### sly_data contract

All four directions carry the same 5-field set — the most focused symmetric contract after the setup networks:

| Direction | Parameters |
|---|---|
| **To upstream** | `aircraft_type`, `gate_id`, `gpu_readiness_status`, `acu_readiness_status`, `wheelchocks_readiness_status` |
| **To downstream** | same 5 fields |
| **From upstream** | same 5 fields |
| **From downstream** | same 5 fields |

#### Down-chain tools

```
["TrackerAPI",
 "/AirlineTurnaround/aircraft_ground_acu_setup",
 "/AirlineTurnaround/aircraft_ground_gpu_setup",
 "/AirlineTurnaround/aircraft_ground_wheelchocks_setup"]
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

**Tracked fields:**
`acu_readiness_status`, `aircraft_type`, `gate_id`, `acu_readiness_status` *(duplicate)*, `gpu_readiness_status`, `wheelchocks_readiness_status`

**Return fields:** Identical to tracked fields (including the duplicate).

> Note: `acu_readiness_status` appears **twice** in both `FLIGHT_TURNAROUND_TRACKED_FIELDS` and `FLIGHT_TURNAROUND_RETURN_FIELDS` (lines 292–293 and 302–303 respectively). This is the same duplicate-field issue seen in `aircraft_ground_traffic` with `assigned_runway_id`. No runtime impact, but should be deduplicated.

> Note: The HOCON TrackerAPI definition correctly includes `"required": []` and has a clean, minimal parameter schema with no stale copy-paste artifacts — the most concise TrackerAPI schema in the system.

#### Commented-out alternative implementation

Lines 349–686 contain a fully commented-out duplicate of the entire active code (a second `TrackerAPI` class definition, configuration constants, and usage examples). This appears to be the old args-first implementation from an earlier version, preserved during refactoring. The commented block is identical in structure to the `_process_field` method commented out in `aircraft_ground_gpu_setup.py`. Safe to remove.

---

## 6. External Tool Dependencies

These tools are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path | Purpose | Step |
|---|---|---|
| `/AirlineTurnaround/aircraft_ground_acu_setup` | Check ACU readiness via CSV | Step 2 |
| `/AirlineTurnaround/aircraft_ground_gpu_setup` | Check GPU readiness via CSV | Step 3 |
| `/AirlineTurnaround/aircraft_ground_wheelchocks_setup` | Check wheelchocks readiness | Step 4 |

> Note: `aircraft_ground_wheelchocks_setup` has not appeared in any other network file reviewed so far. Verify its existence and implementation before deploying this network. If it does not exist, Step 4 will fail and `wheelchocks_readiness_status` will not be set.

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
4. `/AirlineTurnaround/aircraft_ground_wheelchocks_setup` called → `wheelchocks_readiness_status=ready`. `TrackerAPI` called (Step 4)
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
** wheelchocks readiness status   **: ready
```

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "gate_id": "A1",
  "acu_readiness_status": "ready",
  "gpu_readiness_status": "ready",
  "wheelchocks_readiness_status": "ready"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| `aircraft_ground_wheelchocks_setup` dependency not yet confirmed | `aircraft_ground_readiness.hocon` line 223 | **High** | This external network is referenced in Step 4 but has not appeared in any other reviewed file. If it does not exist, Step 4 will fail. Verify existence before deployment. |
| `acu_readiness_status` duplicated in tracked/return fields | `aircraft_ground_readiness.py` lines 292–293, 302–303 | Low | Listed twice in both `FLIGHT_TURNAROUND_TRACKED_FIELDS` and `FLIGHT_TURNAROUND_RETURN_FIELDS`. No runtime impact but results in the field being returned twice in the tuple. Deduplicate. |
| Commented-out duplicate `TrackerAPI` (~338 lines) | `aircraft_ground_readiness.py` lines 349–686 | Low | Entire alternative implementation preserved from refactoring. Safe to remove. |
| `max_iterations=3000` and `max_execution_seconds=300` | `aircraft_ground_readiness.hocon` lines 15–16 | Info | Tightest bounds in the system — by design for this network's narrow scope. If additional steps are added to the workflow, these values must be increased. |
| Interactive user-wait in Step 1 | `aircraft_ground_readiness.hocon` Step 1 instructions | Low | "If still missing, ask the user and wait" — same automated-context risk as `aircraft_engines_stop`. |

---

## 10. Relationship to Other Networks

`aircraft_ground_readiness` sits at the top of the equipment readiness sub-system:

```
aircraft_gate_selection          ─── writes availability  →  gate_equipments_base.csv
                                                               │
aircraft_ground_acu_setup        ←── reads ACU readiness  ───┤
aircraft_ground_gpu_setup        ←── reads GPU readiness  ───┤
aircraft_ground_wheelchocks_setup ← reads chocks readiness ──┘
         │
         └── aircraft_ground_readiness  ─── aggregates all three, single call interface
```

| Network | Role |
|---|---|
| `aircraft_ground_acu_setup` | Leaf — reads `air_conditioning_unit_readiness` from CSV |
| `aircraft_ground_gpu_setup` | Leaf — reads `ground_power_unit_readiness` from CSV |
| `aircraft_ground_wheelchocks_setup` | Leaf — reads `wheelchocks_readiness` from CSV (unconfirmed) |
| `aircraft_ground_readiness` | Aggregator — calls all three, returns combined result |
| `aircraft_ground_acu_connect` | Consumer — calls `aircraft_ground_acu_setup` directly (not via this aggregator) |
| `aircraft_ground_gpu_connect` | Consumer — calls `aircraft_ground_gpu_setup` directly (not via this aggregator) |

---

## 11. Extensibility Guidance

- Verify and implement `aircraft_ground_wheelchocks_setup` (the `wheelchocks_readiness` column in `gate_equipments_base.csv` exists and contains `'yes'`/`'no'` values — the setup network simply needs to be built following the same pattern as `aircraft_ground_acu_setup`)
- Deduplicate `acu_readiness_status` in `FLIGHT_TURNAROUND_TRACKED_FIELDS` and `RETURN_FIELDS`
- Remove the commented-out duplicate `TrackerAPI` implementation (~338 lines)
- If extending this network with additional equipment types, increase `max_iterations` and `max_execution_seconds` proportionally (roughly 3000/300 per equipment check pair based on the current values)

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
