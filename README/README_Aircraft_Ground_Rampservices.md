# Aircraft Ground Ramp Services
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_rampservices.hocon`
> **Implementation file:** `aircraft_ground_rampservices.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Execute all three ground ramp services in sequence — wheelchocks installation, ACU connection, and GPU connection — for an aircraft on blocks at the gate, after engines are stopped. Returns `wheels_chocks_installation_status`, `acu_connection_status`, and `gpu_connection_status` to the caller.

---

## 1. Overview

`aircraft_ground_rampservices` is a **ramp services orchestrator** in the **AirlineTurnaround** agentic system. It sits between `aircraft_ground_operation` (its upstream router) and the three individual ground service networks (`aircraft_ground_wheelchocks_install`, `aircraft_ground_acu_connect`, `aircraft_ground_gpu_connect`), bundling all three ramp operations into a single sequenced workflow.

The network combines:

- An LLM-based orchestration agent (`ground_rampservices`) that executes the three-step ramp sequence or dispatches a single task
- A shared state manager (`TrackerAPI`) implemented in Python

This network is called by `aircraft_ground_operation` at STEP 8 of the turnaround workflow, after ground readiness has been confirmed (STEP 4). It is a **mid-level orchestrator** — neither a leaf service nor a top-level manager. Its role is to abstract the three ramp operations behind a single call, so that upstream agents do not need to know the internals of each individual connection sub-network.

Two configuration values match `aircraft_ground_readiness` exactly: `max_iterations = 3000` and `max_execution_seconds = 300` — the tightest bounds in the system alongside that network, reflecting the narrow and predictable scope of the three-step ramp sequence.

---

## 2. Repository Structure

```
aircraft_ground_rampservices.hocon   # Agent network configuration
aircraft_ground_rampservices.py      # TrackerAPI implementation (sly_data-first)
registries/aaosa_basic.hocon         # Shared registry
```

---

## 3. System Architecture

```
aircraft_ground_operation  (Upstream caller — BRANCH B, STEP 8)
   │
   ▼
ground_rampservices  (LLM Orchestrator)
   │
   ├── TrackerAPI                                                (Coded tool: sly_data-first state management)
   │
   ├── /AirlineTurnaround/aircraft_ground_wheelchocks_install   (STEP 1 — Install wheelchocks)
   │
   ├── /AirlineTurnaround/aircraft_ground_acu_connect           (STEP 2 — Connect ACU)
   │
   └── /AirlineTurnaround/aircraft_ground_gpu_connect           (STEP 3 — Connect GPU)
```

### Design principles

- **Strict sequential execution:** Wheelchocks must be installed before ACU or GPU are connected — the HOCON instructions enforce this order explicitly with labeled STEP blocks and halt-on-failure guards.
- **Fail-fast per step:** If any step does not return the expected terminal status (`installed` or `connected`), execution stops immediately and the failure is reported. Subsequent steps are not attempted.
- **TrackerAPI persistence after each step:** After each of the three service calls, `TrackerAPI` is called to log the resulting status into `sly_data` before proceeding. This ensures state is durable across steps.
- **Dual-mode dispatch:** The agent detects whether the full three-step sequence is needed or only a single task is requested, and routes accordingly. Context detection is based on the presence of all three readiness status parameters or an explicit "execute ground ramp services" instruction.
- **Tightly bounded execution:** `max_iterations = 3000` and `max_execution_seconds = 300` — the same tight limits as `aircraft_ground_readiness`, reflecting three sequential tool calls with TrackerAPI logging between each.

---

## 4. Runtime Configuration

| Setting                 | Value          | System-wide typical |
|-------------------------|----------------|---------------------|
| LLM model               | `gpt-5.4-mini` | `gpt-5.4-mini`      |
| `max_iterations`        | **`3000`**     | `40000`             |
| `max_execution_seconds` | **`300`**      | `7200`              |

> Note: These tight bounds reflect the intentional design scope of this network — three sequential tool calls with TrackerAPI logging between each. If additional ramp service steps are added, these values must be increased proportionally.

> Note: The `instructions_prefix` names **San Francisco International Airport** explicitly, consistent with `aircraft_ground_readiness` and `aircraft_gate_selection`.

---

## 5. Components

### 5.1 ground_rampservices (LLM Orchestrator)

The entry-point agent. It detects whether a full ramp sequence or single-task dispatch is needed, executes the appropriate flow, and returns the ramp services summary.

#### Input parameters

| Parameter                           | Type   | Required | Description                                   |
|-------------------------------------|--------|:--------:|-----------------------------------------------|
| `flight_number`                     | string |    ❌     | Flight number of the aircraft                 |
| `aircraft_type`                     | string |    ✅     | Aircraft model/type                           |
| `gate_id`                           | string |    ✅     | Gate assigned to the aircraft                 |
| `flight_status`                     | string |    ❌     | Current flight status (expected: `on blocks`) |
| `engines_stop_status`               | string |    ❌     | Engines stop status (expected: `stopped`)     |
| `wheels_chocks_readiness_status`    | string |    ❌     | Wheelchocks readiness (input to STEP 1)       |
| `acu_readiness_status`              | string |    ❌     | ACU readiness (input to STEP 2)               |
| `gpu_readiness_status`              | string |    ❌     | GPU readiness (input to STEP 3)               |
| `wheels_chocks_installation_status` | string |    ❌     | Wheelchocks installation result (output)      |
| `acu_connection_status`             | string |    ❌     | ACU connection result (output)                |
| `gpu_connection_status`             | string |    ❌     | GPU connection result (output)                |

#### Context detection

The agent uses two signals to decide between full-sequence and single-task mode:

- **Full sequence:** All three readiness status parameters are provided (`wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`), or the instruction contains `"execute ground ramp services"` or similar phrasing.
- **Single task:** The inquiry refers to only one of the three services explicitly.

#### Orchestration flow — full sequence

The instructions use explicit `STEP` labels with halt-on-failure guards:

1. **STEP 1 — Wheelchocks Installation**
   a. Call `/AirlineTurnaround/aircraft_ground_wheelchocks_install` with `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_readiness_status`.
   b. Wait for response. Store `wheels_chocks_installation_status`.
   c. If `wheels_chocks_installation_status` ≠ `'installed'` → **stop and report failure.**
   d. Call `TrackerAPI` to log `wheels_chocks_installation_status`.

2. **STEP 2 — ACU Connection**
   a. Call `/AirlineTurnaround/aircraft_ground_acu_connect` with `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`, `acu_readiness_status`.
   b. Wait for response. Store `acu_connection_status`.
   c. If `acu_connection_status` ≠ `'connected'` → **stop and report failure.**
   d. Call `TrackerAPI` to log `acu_connection_status`.

3. **STEP 3 — GPU Connection**
   a. Call `/AirlineTurnaround/aircraft_ground_gpu_connect` with `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`, `gpu_readiness_status`.
   b. Wait for response. Store `gpu_connection_status`.
   c. If `gpu_connection_status` ≠ `'connected'` → **stop and report failure.**
   d. Call `TrackerAPI` to log `gpu_connection_status`.

4. Return the ramp services summary (see §8).

#### Single-task dispatch

If only one task is requested, the agent calls only the relevant downstream network and reports that single result:

| Requested task      | Tool called                                              | Result stored                       |
|---------------------|----------------------------------------------------------|-------------------------------------|
| Wheelchocks only    | `/AirlineTurnaround/aircraft_ground_wheelchocks_install` | `wheels_chocks_installation_status` |
| ACU connection only | `/AirlineTurnaround/aircraft_ground_acu_connect`         | `acu_connection_status`             |
| GPU connection only | `/AirlineTurnaround/aircraft_ground_gpu_connect`         | `gpu_connection_status`             |
| None of the above   | — (not relevant)                                         | —                                   |

#### sly_data contract

| Direction           | Parameters                                                                                                                                                                                                                                                   |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `flight_number`, `aircraft_type`, `gate_id`, `gpu_connection_status`, `acu_connection_status`, `wheels_chocks_installation_status`                                                                                                                           |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `gpu_connection_status`, `acu_connection_status`, `wheels_chocks_installation_status`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `gpu_connection_status`, `acu_connection_status`, `wheels_chocks_installation_status`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `gpu_connection_status`, `acu_connection_status`, `wheels_chocks_installation_status`                                                                                                                           |

> Note: The asymmetry between upstream/downstream is intentional. The three readiness statuses (`wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`) and safety prerequisites (`flight_status`, `engines_stop_status`) flow inward from upstream and downstream to this network, but are **not propagated back upstream** — only the three terminal results (`*_installation_status`, `*_connection_status`) are returned upward.

> Note: `flight_status` and `engines_stop_status` flow to downstream networks (needed by `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect` for their safety-prerequisite checks) but are not returned to upstream — this network consumes them, it does not produce them.

#### Down-chain tools

```
["TrackerAPI",
 "/AirlineTurnaround/aircraft_ground_acu_connect",
 "/AirlineTurnaround/aircraft_ground_gpu_connect",
 "/AirlineTurnaround/aircraft_ground_wheelchocks_install"]
```

---

### 5.2 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_rampservices.aircraft_ground_rampservices.TrackerAPI`

Standard `sly_data`-first implementation. Called three times during the full-sequence workflow — once after each ramp service step to persist the resulting status into `sly_data`.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

**Tracked fields:**
`aircraft_type`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`

**Return fields:**
`aircraft_type`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`

> Note: Tracked fields and return fields are identical — consistent with the pattern used by `aircraft_ground_acu_setup`, `aircraft_ground_gpu_setup`, and `aircraft_ground_readiness`.

> Note: `flight_number` is tracked in the HOCON TrackerAPI parameter schema but is **absent from `FLIGHT_TURNAROUND_TRACKED_FIELDS`** in the Python implementation. It will not be read from or written to `sly_data` by TrackerAPI, though it flows through the agent's sly_data allow blocks.

> Note: The readiness status fields (`wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`) and safety prerequisite fields (`flight_status`, `engines_stop_status`) are **not tracked by TrackerAPI**. They are consumed by downstream networks but not persisted by this network's state manager.

---

## 6. External Tool Dependencies

These tools are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path                                                | Purpose                                 | Step   |
|----------------------------------------------------------|-----------------------------------------|--------|
| `/AirlineTurnaround/aircraft_ground_wheelchocks_install` | Install wheelchocks, verify `installed` | STEP 1 |
| `/AirlineTurnaround/aircraft_ground_acu_connect`         | Connect ACU, verify `connected`         | STEP 2 |
| `/AirlineTurnaround/aircraft_ground_gpu_connect`         | Connect GPU, verify `connected`         | STEP 3 |

Each downstream network handles its own internal readiness verification before executing the physical connection or installation — this network does not pre-check readiness directly; it passes the readiness status values along and trusts the sub-networks to enforce their own prerequisites.

---

## 7. Sample Queries

```
"Flight AF84 is on blocks at gate A1 and the wheelchocks are ready. The B747 aircraft's engines
are stopped. Install wheelchocks."

"Flight AF84 is on blocks at gate A1 and the acu is ready. The B747 aircraft's engines are stopped
and wheelchocks have been installed. Connect acu."

"Flight AF84 is on blocks at gate A1 and the gpu is ready. The B747 aircraft's engines are stopped
and wheelchocks have been installed. Connect gpu."
```

---

## 8. Example Execution Trace

**Input (called from `aircraft_ground_operation`, BRANCH B):**
> `flight_number=AF84, aircraft_type=B747, gate_id=A1, flight_status=on blocks, engines_stop_status=stopped, wheels_chocks_readiness_status=ready, acu_readiness_status=ready, gpu_readiness_status=ready`

**Execution steps:**

1. Context detected as full sequence (all three readiness statuses provided) ✅
2. `/AirlineTurnaround/aircraft_ground_wheelchocks_install` called → `wheels_chocks_installation_status=installed`. `TrackerAPI` called (STEP 1)
3. `/AirlineTurnaround/aircraft_ground_acu_connect` called → `acu_connection_status=connected`. `TrackerAPI` called (STEP 2)
4. `/AirlineTurnaround/aircraft_ground_gpu_connect` called → `gpu_connection_status=connected`. `TrackerAPI` called (STEP 3)
5. Summary returned (STEP 4)

**Output:**

```
***************************************
* Ground ramp services summary        *
***************************************
** flight number                  **: AF84
** aircraft type                  **: B747
** gate id                        **: A1
** wheelchocks installation status**: installed
** acu connection status          **: connected
** gpu connection status          **: connected
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "gate_id": "A1",
  "wheels_chocks_installation_status": "installed",
  "acu_connection_status": "connected",
  "gpu_connection_status": "connected"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue                                                                           | Location                                          | Severity | Notes                                                                                                                                                                                     |
|---------------------------------------------------------------------------------|---------------------------------------------------|:--------:|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Single-task dispatch does not call TrackerAPI                                   | `aircraft_ground_rampservices.hocon` instructions |   Low    | The single-task dispatch path reports the result but does not explicitly direct a TrackerAPI log call, unlike the full-sequence path where TrackerAPI is called after each step.          |
| Context detection relies on keyword matching for "execute ground ramp services" | `aircraft_ground_rampservices.hocon` instructions |   Low    | The full-sequence trigger includes an instruction string match. If upstream callers use different phrasing, the agent may fall into single-task dispatch mode instead of full sequence.   |

---

## 10. Relationship to Other Networks

`aircraft_ground_rampservices` is the BRANCH B target of `aircraft_ground_operation`, and itself orchestrates three leaf-level connection networks:

```
aircraft_ground_operation
   │
   └── BRANCH B ──► aircraft_ground_rampservices  (this network)
                         │
                         ├── STEP 1 ──► aircraft_ground_wheelchocks_install
                         │
                         ├── STEP 2 ──► aircraft_ground_acu_connect
                         │                    └── aircraft_ground_acu_setup (readiness check)
                         │
                         └── STEP 3 ──► aircraft_ground_gpu_connect
                                              └── aircraft_ground_gpu_setup (readiness check)
```

| Network                               | Role relative to this network                                                     |
|---------------------------------------|-----------------------------------------------------------------------------------|
| `aircraft_ground_operation`           | Upstream router — calls this network at BRANCH B (STEP 8)                         |
| `aircraft_ground_wheelchocks_install` | Downstream leaf — executes wheelchocks installation (STEP 1)                      |
| `aircraft_ground_acu_connect`         | Downstream mid-level — verifies ACU readiness, then connects (STEP 2)             |
| `aircraft_ground_gpu_connect`         | Downstream mid-level — verifies GPU readiness, then connects (STEP 3)             |
| `aircraft_ground_acu_setup`           | Indirect dependency — called internally by `aircraft_ground_acu_connect`          |
| `aircraft_ground_gpu_setup`           | Indirect dependency — called internally by `aircraft_ground_gpu_connect`          |
| `aircraft_ground_readiness`           | Sibling — called at BRANCH A (STEP 4); provides readiness inputs for this network |

---

## 11. Extensibility Guidance

- Consider adding a TrackerAPI call in the single-task dispatch path to match the persistence behavior of the full-sequence path.
- If the context-detection keyword matching for full-sequence mode proves fragile, replace with an explicit boolean parameter (e.g. `execute_full_sequence: true`) passed by `aircraft_ground_operation`.

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
