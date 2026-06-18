# Aircraft Ground Ramp Services
## Agentic AI Network – README

> **Configuration file:** `aircraft_aircraft_ground_rampservices.hocon`
> **Implementation file:** `aircraft_aircraft_ground_rampservices.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Execute all three ground ramp services in sequence — wheels chocks installation, ACU connection, and GPU connection — for an aircraft on blocks at the gate, after engines are stopped. Returns `wheels_chocks_installation_status`, `acu_connection_status`, and `gpu_connection_status` to the caller.

---

## 1. Overview

`aircraft_aircraft_ground_rampservices` is a **ramp services orchestrator** in the **AirlineTurnaround** agentic system. It sits between `aircraft_ground_operation` (its upstream router) and the three individual ground service networks (`aircraft_ground_wheels_chocks_install`, `aircraft_ground_acu_connect`, `aircraft_ground_gpu_connect`), bundling all three ramp operations into a single sequenced workflow.

The network combines:

- An LLM-based orchestration agent (`aircraft_ground_rampservices`) that executes the three-step ramp sequence or dispatches a single task
- A shared state manager (`TrackerAPI`) implemented in Python

This network is called by `aircraft_ground_operation` at STEP 8 of the turnaround workflow, after ground readiness has been confirmed (STEP 4). It is a **mid-level orchestrator** — neither a leaf service nor a top-level manager. Its role is to abstract the three ramp operations behind a single call, so that upstream agents do not need to know the internals of each individual connection sub-network.

Two configuration values are set to the system-wide typical bounds: `max_iterations = 50000` and `max_execution_seconds = 7200` — providing ample headroom for the three sequential sub-network calls with TrackerAPI logging between each.

---

## 2. Repository Structure

```
aircraft_aircraft_ground_rampservices.hocon   # Agent network configuration
aircraft_aircraft_ground_rampservices.py      # TrackerAPI implementation (sly_data-first)
registries/aaosa_basic.hocon         # Shared registry
```

---

## 3. System Architecture

```
aircraft_ground_operation  (Upstream caller — BRANCH B, STEP 8)
   │
   ▼
aircraft_ground_rampservices  (LLM Orchestrator)
   │
   ├── TrackerAPI                                                  (Coded tool: sly_data-first state management)
   │
   ├── /AirlineTurnaround/aircraft_ground_wheels_chocks_install   (STEP 1 — Install wheels chocks)
   │
   ├── /AirlineTurnaround/aircraft_ground_acu_connect             (STEP 2 — Connect ACU)
   │
   └── /AirlineTurnaround/aircraft_ground_gpu_connect             (STEP 3 — Connect GPU)
```

### Design principles

- **Strict sequential execution:** The three steps run in a fixed order — wheels chocks installation first, then ACU connection, then GPU connection. The HOCON instructions enforce this order explicitly with labeled STEP blocks.
- **Unconditional progression:** The instructions explicitly direct the agent to execute ALL three steps unconditionally. Status fields in args may be null — this is expected and normal. The agent does NOT check or validate prior-step completion before calling the next sub-agent and does NOT stop between steps.
- **TrackerAPI persistence after each step:** After each of the three service calls, `TrackerAPI` is called to log the resulting status into `sly_data` before proceeding. This ensures state is durable across steps.
- **Dual-mode dispatch:** The agent detects whether the full three-step sequence is needed or only a single task is requested, and routes accordingly. Context detection is based on the presence of all three readiness status parameters or an explicit "execute ground ramp services" instruction.
- **Standard execution bounds:** `max_iterations = 50000` and `max_execution_seconds = 7200` — system-wide typical limits, accommodating three sequential tool calls with TrackerAPI logging between each.

---

## 4. Runtime Configuration

| Setting                 | Value          | System-wide typical |
|-------------------------|----------------|---------------------|
| LLM model               | `gpt-5.4-mini` | `gpt-5.4-mini`      |
| `max_iterations`        | **`50000`**    | `40000`             |
| `max_execution_seconds` | **`7200`**     | `7200`              |

> Note: These bounds align with the system-wide typical envelope and provide ample headroom for three sequential sub-network calls with TrackerAPI logging between each.

> Note: The `instructions_prefix` names **San Francisco International Airport** explicitly, consistent with `aircraft_ground_readiness` and `aircraft_gate_selection`.

---

## 5. Components

### 5.1 aircraft_ground_rampservices (LLM Orchestrator)

The entry-point agent. It detects whether a full ramp sequence or single-task dispatch is needed, executes the appropriate flow, and returns the ramp services summary.

#### Input parameters

| Parameter                           | Type   | Required | Description                                   |
|-------------------------------------|--------|:--------:|-----------------------------------------------|
| `flight_number`                     | string |    ❌     | Flight number of the aircraft                 |
| `aircraft_type`                     | string |    ✅     | Aircraft model/type                           |
| `gate_id`                           | string |    ✅     | Gate assigned to the aircraft                 |
| `flight_status`                     | string |    ❌     | Current flight status (expected: `on blocks`) |
| `engines_stop_status`               | string |    ❌     | Engines stop status (expected: `stopped`)     |
| `wheels_chocks_readiness_status`    | string |    ❌     | Wheels chocks readiness (input to STEP 1)     |
| `acu_readiness_status`              | string |    ❌     | ACU readiness (input to STEP 2)               |
| `gpu_readiness_status`              | string |    ❌     | GPU readiness (input to STEP 3)               |
| `wheels_chocks_installation_status` | string |    ❌     | Wheels chocks installation result (output)    |
| `acu_connection_status`             | string |    ❌     | ACU connection result (output)                |
| `gpu_connection_status`             | string |    ❌     | GPU connection result (output)                |

#### Context detection

The agent uses two signals to decide between full-sequence and single-task mode:

- **Full sequence:** All three readiness status parameters are provided (`wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`), or the instruction contains `"execute ground ramp services"` or similar phrasing.
- **Single task:** The inquiry refers to only one of the three services explicitly.

#### Orchestration flow — full sequence

The instructions use explicit `STEP` labels and direct unconditional progression through all three steps:

1. **STEP 1 — Wheels Chocks Installation**
   a. Call `/AirlineTurnaround/aircraft_ground_wheels_chocks_install` with `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_readiness_status`.
   b. Wait for response. Store `wheels_chocks_installation_status`.
   c. Call `TrackerAPI` to log `wheels_chocks_installation_status`.
   d. **Proceed immediately to STEP 2 regardless of `wheels_chocks_installation_status` value.**

2. **STEP 2 — ACU Connection**
   a. Call `/AirlineTurnaround/aircraft_ground_acu_connect` with `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`, `acu_readiness_status`.
   b. Wait for response. Store `acu_connection_status`.
   c. Call `TrackerAPI` to log `acu_connection_status`.
   d. **Proceed immediately to STEP 3 regardless of `acu_connection_status` value.**

3. **STEP 3 — GPU Connection**
   a. Call `/AirlineTurnaround/aircraft_ground_gpu_connect` with `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`, `gpu_readiness_status`.
   b. Wait for response. Store `gpu_connection_status`.
   c. Call `TrackerAPI` to log `gpu_connection_status`.
   d. Proceed to RETURN SUMMARY.

4. Return the ramp services summary (see §8).

#### Single-task dispatch

If only one task is requested, the agent calls only the relevant downstream network and reports that single result:

| Requested task      | Tool called                                                | Result stored                       |
|---------------------|------------------------------------------------------------|-------------------------------------|
| Wheels chocks only  | `/AirlineTurnaround/aircraft_ground_wheels_chocks_install` | `wheels_chocks_installation_status` |
| ACU connection only | `/AirlineTurnaround/aircraft_ground_acu_connect`           | `acu_connection_status`             |
| GPU connection only | `/AirlineTurnaround/aircraft_ground_gpu_connect`           | `gpu_connection_status`             |
| None of the above   | — (not relevant)                                           | —                                   |

#### sly_data contract

| Direction           | Parameters                                                                                                                                                                                                                                                   |
|---------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `wheels_chocks_installation_status`, `acu_connection_status`, `gpu_connection_status`                                                                                                                          |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`, `wheels_chocks_installation_status`     |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`                                          |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `wheels_chocks_installation_status`, `acu_connection_status`, `gpu_connection_status`                                                                             |

> Note: The asymmetry between upstream/downstream is intentional. The three readiness statuses (`wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`) and safety prerequisites (`flight_status`, `engines_stop_status`) flow inward from upstream and downstream to this network, but are **not propagated back upstream** — only the three terminal results (`*_installation_status`, `*_connection_status`) are returned upward.

> Note: `flight_status` and `engines_stop_status` flow to downstream networks (needed by `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect` for their safety-prerequisite checks) but are not returned to upstream — this network consumes them, it does not produce them.

#### Down-chain tools

```
["TrackerAPI",
 "/AirlineTurnaround/aircraft_ground_acu_connect",
 "/AirlineTurnaround/aircraft_ground_gpu_connect",
 "/AirlineTurnaround/aircraft_ground_wheels_chocks_install"]
```

---

### 5.2 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_aircraft_ground_rampservices.aircraft_aircraft_ground_rampservices.TrackerAPI`

Standard `sly_data`-first implementation. Called three times during the full-sequence workflow — once after each ramp service step to persist the resulting status into `sly_data`.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

**Tracked fields:**
`aircraft_type`, `flight_number`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`

**Return fields:**
`aircraft_type`, `flight_number`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`

> Note: Tracked fields and return fields are identical — consistent with the pattern used by `aircraft_ground_acu_setup`, `aircraft_ground_gpu_setup`, and `aircraft_ground_readiness`.

> Note: The readiness status fields (`wheels_chocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`) are exposed in the HOCON TrackerAPI parameter schema but are **not present in `FLIGHT_TURNAROUND_TRACKED_FIELDS`** in the Python implementation. They will not be read from or written to `sly_data` by TrackerAPI, though they flow through the agent's sly_data allow blocks. The safety-prerequisite fields (`flight_status`, `engines_stop_status`) are also not tracked by TrackerAPI — they are consumed by downstream networks but not persisted by this network's state manager.

---

## 6. External Tool Dependencies

These tools are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path                                                  | Purpose                                   | Step   |
|------------------------------------------------------------|-------------------------------------------|--------|
| `/AirlineTurnaround/aircraft_ground_wheels_chocks_install` | Install wheels chocks, verify `installed` | STEP 1 |
| `/AirlineTurnaround/aircraft_ground_acu_connect`           | Connect ACU, verify `connected`           | STEP 2 |
| `/AirlineTurnaround/aircraft_ground_gpu_connect`           | Connect GPU, verify `connected`           | STEP 3 |

Each downstream network handles its own internal readiness verification before executing the physical connection or installation — this network does not pre-check readiness directly; it passes the readiness status values along and trusts the sub-networks to enforce their own prerequisites.

---

## 7. Sample Queries

```
"Flight AF84 is on blocks at gate A1 and the wheels chocks are ready. The B747 aircraft's engines
are stopped. Install wheels chocks."

"Flight AF84 is on blocks at gate A1 and the acu is ready. The B747 aircraft's engines are stopped
and wheels chocks have been installed. Connect acu."

"Flight AF84 is on blocks at gate A1 and the gpu is ready. The B747 aircraft's engines are stopped
and wheels chocks have been installed. Connect gpu."
```

---

## 8. Example Execution Trace

**Input (called from `aircraft_ground_operation`, BRANCH B):**
> `flight_number=AF84, aircraft_type=B747, gate_id=A1, flight_status=on blocks, engines_stop_status=stopped, wheels_chocks_readiness_status=ready, acu_readiness_status=ready, gpu_readiness_status=ready`

**Execution steps:**

1. Context detected as full sequence (all three readiness statuses provided) ✅
2. `/AirlineTurnaround/aircraft_ground_wheels_chocks_install` called → `wheels_chocks_installation_status=installed`. `TrackerAPI` called (STEP 1)
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
** wheels chocks installation status**: installed
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

| Issue                                                                           | Location                                          | Severity | Notes                                                                                                                                                                                  |
|---------------------------------------------------------------------------------|---------------------------------------------------|:--------:|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Unconditional progression through all three steps                               | `aircraft_aircraft_ground_rampservices.hocon` instructions |  Medium  | The instructions direct the agent to proceed through STEP 2 and STEP 3 regardless of the prior step's status value. A failure in STEP 1 will not halt subsequent attempts.             |
| STEP 1 call target contains a stray space in the instructions                   | `aircraft_aircraft_ground_rampservices.hocon` (STEP 1)     |  Medium  | The STEP 1 directive reads `aircraft_ground_wheels chocks_install` (with a space) while the registered tool name is `aircraft_ground_wheels_chocks_install`. LLM tolerance varies.     |
| Single-task dispatch does not call TrackerAPI                                   | `aircraft_aircraft_ground_rampservices.hocon` instructions |   Low    | The single-task dispatch path reports the result but does not explicitly direct a TrackerAPI log call, unlike the full-sequence path where TrackerAPI is called after each step.       |
| Context detection relies on keyword matching for "execute ground ramp services" | `aircraft_aircraft_ground_rampservices.hocon` instructions |   Low    | The full-sequence trigger includes an instruction string match. If upstream callers use different phrasing, the agent may fall into single-task dispatch mode instead of full sequence.|

---

## 10. Relationship to Other Networks

`aircraft_aircraft_ground_rampservices` is the BRANCH B target of `aircraft_ground_operation`, and itself orchestrates three leaf-level connection networks:

```
aircraft_ground_operation
   │
   └── BRANCH B ──► aircraft_aircraft_ground_rampservices  (this network)
                         │
                         ├── STEP 1 ──► aircraft_ground_wheels_chocks_install
                         │
                         ├── STEP 2 ──► aircraft_ground_acu_connect
                         │                    └── aircraft_ground_acu_setup (readiness check)
                         │
                         └── STEP 3 ──► aircraft_ground_gpu_connect
                                              └── aircraft_ground_gpu_setup (readiness check)
```

| Network                                 | Role relative to this network                                                     |
|-----------------------------------------|-----------------------------------------------------------------------------------|
| `aircraft_ground_operation`             | Upstream router — calls this network at BRANCH B (STEP 8)                         |
| `aircraft_ground_wheels_chocks_install` | Downstream leaf — executes wheels chocks installation (STEP 1)                    |
| `aircraft_ground_acu_connect`           | Downstream mid-level — verifies ACU readiness, then connects (STEP 2)             |
| `aircraft_ground_gpu_connect`           | Downstream mid-level — verifies GPU readiness, then connects (STEP 3)             |
| `aircraft_ground_acu_setup`             | Indirect dependency — called internally by `aircraft_ground_acu_connect`          |
| `aircraft_ground_gpu_setup`             | Indirect dependency — called internally by `aircraft_ground_gpu_connect`          |
| `aircraft_ground_readiness`             | Sibling — called at BRANCH A (STEP 4); provides readiness inputs for this network |

---

## 11. Extensibility Guidance

- Consider adding a TrackerAPI call in the single-task dispatch path to match the persistence behavior of the full-sequence path.
- Fix the stray space in the STEP 1 call target (`aircraft_ground_wheels chocks_install` → `aircraft_ground_wheels_chocks_install`) to avoid LLM resolution ambiguity.
- If unconditional progression through failed steps is undesirable, replace the current "proceed regardless" directives with explicit halt-on-failure guards keyed on terminal statuses (`installed`, `connected`).
- If the context-detection keyword matching for full-sequence mode proves fragile, replace with an explicit boolean parameter (e.g. `execute_full_sequence: true`) passed by `aircraft_ground_operation`.

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
