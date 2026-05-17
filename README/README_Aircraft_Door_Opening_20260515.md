# Aircraft Door Opening
## Agentic AI Network – README

> **Configuration file:** `aircraft_door_opening.hocon`
> **Implementation file:** `aircraft_door_opening.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Open the aircraft door at the gate during turnaround, after verifying the aircraft is on blocks and the correct deplaning equipment is connected.

---

## 1. Overview

`aircraft_door_opening` is a foundational agentic network in the **AirlineTurnaround** system. It is called as an upstream dependency by several other networks — `aircraft_disembark`, `aircraft_baggage_unload`, `aircraft_crew_exit`, and `aircraft_crew_debrief` — whenever the door needs to be opened before those operations can proceed.

The network combines:

- An LLM-based orchestration agent (`door_opening_agent`) that interprets intent and drives the workflow
- One coded execution tool (`door_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Two external tool references (`aircraft_jetbridge_connect`, `aircraft_stairtruck_connect`) resolved from the shared registry `registries/aaosa_basic.hocon`

Compared to the networks it serves, this network has no `aircraft_door_opening` external dependency of its own — it is the door-opening primitive. A distinctive design aspect is its `door_operator`: the operator sets `door_opening_status = open` based solely on whether equipment is connected, with **no separate door-status input check**. Additionally, `jetbridge_connection_status` is intentionally excluded from `TrackerAPI` return fields, with explicit code documentation explaining the reasoning.

---

## 2. Repository Structure

```
aircraft_door_opening.hocon          # Agent network configuration
aircraft_door_opening.py             # Coded tool implementations (door_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_jetbridge_connect, aircraft_stairtruck_connect)
```

---

## 3. System Architecture

```
User / Caller  (or upstream network: aircraft_disembark, aircraft_baggage_unload, etc.)
   │
   ▼
door_opening_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                                       (Coded tool: read/write turnaround state via sly_data)
   │
   ├── door_operator                                    (Coded tool: open the aircraft door)
   │
   ├── /AirlineTurnaround/aircraft_jetbridge_connect    (External tool — jetway gates or unknown type)
   │
   └── /AirlineTurnaround/aircraft_stairtruck_connect   (External tool — stairtruck gates only)
```

### Design principles

- **Sequential fail-fast execution:** The orchestrator uses `CRITICAL: sequential executor` with `STEP` labels. Each prerequisite tool is called at most once; failure after a single attempt stops the workflow.
- **Equipment-type-aware routing:** The agent explicitly selects jetbridge or stairtruck based on `deplaning_equipment_type`. For unknown type, it defaults to calling jetbridge connect.
- **Explicit parameter passing for stairtruck:** When calling `aircraft_stairtruck_connect`, the agent is instructed to pass `acu_connection_status` and `gpu_connection_status` explicitly, with a `CRITICAL` warning that both must be `connected`.
- **Equipment-only door condition:** The `door_operator` opens the door based solely on equipment connection status — it does not check `door_opening_status` as an input. The initial value is `closed`; the output is `open`.
- **Intentional TrackerAPI exclusion:** `jetbridge_connection_status` is excluded from `RETURN_FIELDS` by design to prevent stale values from bleeding into downstream agents on stairtruck gates.

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

### 5.1 door_opening_agent (LLM Orchestrator)

The entry-point agent. It resolves prerequisites sequentially, enforces the on-blocks gate, connects the appropriate deplaning equipment if needed (one attempt only), opens the door, and returns the summary.

> Note: The agent is named `door_opening_agent` in the HOCON. The previous documentation referred to it as `aircraft_door_opening_agent`, which does not match the actual runtime tool name.

#### Input parameters

|-----------------------------------|--------|:--------:|-------------------------------------------------------------------------------------------------------|
| Parameter                         | Type   | Required | Description                                                                                           |
|-----------------------------------|--------|:--------:|-------------------------------------------------------------------------------------------------------|
| `flight_number`                   | string | ✅       | Flight identifier                                                                                     |
| `aircraft_type`                   | string | ✅       | Aircraft model/type                                                                                   |
| `gate_id`                         | string | ✅       | Gate where the aircraft is parked                                                                     |
| `flight_status`                   | string | ✅       | Flight status (expected: contains `on blocks` or `block`)                                             |
| `jetbridge_connection_status`     | string | ❌       | Jetbridge state — null on stairtruck gates                                                            |
| `stairtruck_connection_status`    | string | ❌       | Stairtruck state — null on jetway gates                                                               |
| `deplaning_equipment_type`        | string | ❌       | Equipment type: `jetway`/`jetbridge` or `stairtruck`/`stair`                                          |
| `door_opening_status`             | string | ❌       | Current door state                                                                                    |
| `acu_connection_status`           | string | ❌       | Required when calling stairtruck connect internally                                                   |
| `gpu_connection_status`           | string | ❌       | Required when calling stairtruck connect internally                                                   |
| `wheels_chocks_installation_status` | string | ❌       | Passed to stairtruck connect                                                                          |
|-----------------------------------|--------|:--------:|-------------------------------------------------------------------------------------------------------|

#### Orchestration flow

1. **STEP 1 — Resolve prerequisites:** Call `TrackerAPI` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`. Read back all values.
2. **STEP 2 — Verify flight status:** `flight_status` must contain `on blocks` or `block`. If not → stop and report `"Aircraft is not yet on blocks. Door cannot be opened."`
3. **STEP 3 — Ensure deplaning equipment is connected (ONE call if needed):**
   - `jetway`/`jetbridge` → require `jetbridge_connection_status` contains `connected`. If not → call `/AirlineTurnaround/aircraft_jetbridge_connect` once. Store result via `TrackerAPI`. If still not connected → stop.
   - `stairtruck`/`stair` → require `stairtruck_connection_status` contains `connected`. If not → call `/AirlineTurnaround/aircraft_stairtruck_connect` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`. **CRITICAL: `acu_connection_status` and `gpu_connection_status` must both be `connected`.** Store result via `TrackerAPI`. If still not connected → stop.
   - Unknown type → accept either connection status. If neither connected → call `/AirlineTurnaround/aircraft_jetbridge_connect` as default. Store result via `TrackerAPI`.
4. **STEP 4 — Open the door:**
   - Confirm correct equipment connection status is `connected` before proceeding.
   - If `deplaning_equipment_type` contains `stairtruck`/`stair` → pass `stairtruck_connection_status='connected'`, do **NOT** pass `jetbridge_connection_status`.
   - Call `door_operator` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`. Extract `door_opening_status`. Store via `TrackerAPI`.
5. **RETURN SUMMARY.**

> Note: The instructions include a safety re-check at the top of Step 4: if the required connection is not confirmed as `connected`, the agent loops back to Step 3 rather than proceeding. This is the only network in the system with an explicit step-level loop-back instruction embedded within a sequential executor pattern.

#### sly_data contract

| Direction | Parameters |
|---|---|
| **To upstream** | `door_opening_status`, `jetbridge_connection_status` |
| **To downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `door_opening_status` |
| **From upstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `door_opening_status` |

> Note: `to_downstream` carries all 8 fields including `stairtruck_connection_status` and `deplaning_equipment_type`, ensuring downstream networks receiving this network's output via sly_data have full equipment context propagated to them.

> Note: `to_upstream` propagates `jetbridge_connection_status` even though this value is intentionally excluded from `TrackerAPI` return fields. The value reaches upstream through the sly_data allow block, not through the TrackerAPI response.

#### Down-chain tools

```
["TrackerAPI", "door_operator", "/AirlineTurnaround/aircraft_jetbridge_connect",
 "/AirlineTurnaround/aircraft_stairtruck_connect"]
```

---

### 5.2 door_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_door_opening.aircraft_door_opening.door_operator`

Performs the door opening action. It validates required parameters, evaluates whether at least one piece of deplaning equipment is connected, then sets `door_opening_status = open`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

> Note: The operator's docstring lists `acu_connection_status`, `gpu_connection_status`, and `wheels_chocks_installation status` as sly_data keys. None of these are actually read by the operator logic — the docstring is a copy from an earlier template and does not reflect the actual implementation.

#### Input parameters

| Parameter | Type | Required | Source priority |
|---|---|:---:|---|
| `flight_number` | string | ✅ | `args` → `sly_data` |
| `aircraft_type` | string | ✅ | `args` → `sly_data` |
| `gate_id` | string | ✅ | `args` → `sly_data` |
| `flight_status` | string | ❌ | `args` → `sly_data` |
| `jetbridge_connection_status` | string | ❌ | `args` → `sly_data` |
| `stairtruck_connection_status` | string | ❌ | `args` → `sly_data` |
| `door_opening_status` | string | ❌ | `args` → `sly_data` |

#### Door opening logic

The operator evaluates `equipment_connected` as:

```
jetbridge_connection_status contains 'connected'
OR
stairtruck_connection_status contains 'connected'
```

`door_opening_status` is set to `open` when `equipment_connected` is `True`. The operator does not check `door_opening_status` as an input — it makes no distinction between a door that was already open and one that needs to be opened. Initial value is `closed`; if equipment is not connected, the tool returns an error string and `closed` is never replaced.

#### Output

- Writes `door_opening_status = 'open'` into `sly_data` on success
- Returns `door_opening_status` string (`open` or `closed`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_door_opening.aircraft_door_opening.TrackerAPI`

Manages shared turnaround state. Called in Step 1 to read current values, after equipment connection to store the result, and after `door_operator` to persist `door_opening_status`.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `deplaning_equipment_type`, `door_opening_status`, `flight_number`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`

> Note: `gate_id` is included in tracked fields here — unlike `aircraft_disembark` and `aircraft_cabin_cleaning` where it was absent. This is a notable improvement in this network's TrackerAPI configuration.

**Return fields:**
`deplaning_equipment_type`, `door_opening_status`, `flight_status`, `stairtruck_connection_status`

> Note: `jetbridge_connection_status` is **intentionally excluded** from `RETURN_FIELDS`. The code includes an explicit explanatory comment:
> *"jetbridge_connection_status is intentionally excluded from RETURN_FIELDS. The door opening agent does not need to echo it back — the turnaround manager already holds it from STEP 9. Returning it here caused stale sly_data values to bleed into the door opening summary and mislead downstream agents on stairtruck gates (where jetbridge was never connected)."*
> This is the only network in the system with a documented intentional field exclusion from TrackerAPI return fields.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`, resolving the omission seen in `aircraft_crew_debrief`, `aircraft_crew_exit`, and `aircraft_disembark`.

---

## 6. External Tool Dependencies

These tools are not defined in this network. They are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path | Purpose | Condition triggering call |
|---|---|---|
| `/AirlineTurnaround/aircraft_jetbridge_connect` | Connect jetbridge | Equipment not connected on jetway gate, or unknown type with neither connected |
| `/AirlineTurnaround/aircraft_stairtruck_connect` | Connect stairtruck | Equipment not connected on stairtruck gate |

---

## 7. Sample Queries

```
# All prerequisites already met
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The jetbridge is connected to the plane. Open the aircraft door."

# Prerequisites not yet confirmed — agent will resolve them (one attempt each)
"The B747 aircraft of flight AF84 is on blocks at gate A1. Open the aircraft door."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. The jetbridge is connected to the plane. Open the aircraft door."

**Execution steps:**

1. `TrackerAPI` called (Step 1) — reads: `flight_status=on blocks`, `jetbridge_connection_status=connected`
2. Flight status check: on blocks ✅ (Step 2)
3. Equipment check: jetbridge connected ✅ (Step 3, no external call needed)
4. `door_operator` called — returns `door_opening_status=open` (Step 4)
5. `TrackerAPI` called — persists `door_opening_status=open`
6. Summary returned

**Output:**

```
************************************
* Summary of aircraft door opening *
************************************
** flight status                   **: on blocks
** deplaning equipment type        **: jetway
** jetbridge connection status     **: connected
** stairtruck connection status    **: null
** door opening status             **: open
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "deplaning_equipment_type": "jetway",
  "jetbridge_connection_status": "connected",
  "stairtruck_connection_status": null,
  "door_opening_status": "open"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Notes |
|---|---|---|
| `door_operator` does not check if door is already open | `aircraft_door_opening.py` | The operator always sets `door_opening_status = open` if equipment is connected, with no check for whether it was already open. This is safe but means calling the operator on an already-open door produces the same result as on a closed one. |

---

## 10. Extensibility Guidance

- Add an idempotency check in `door_operator`: if `door_opening_status` is already `open` in `sly_data`, skip the operation and return immediately
- Clean up `door_operator` docstring to accurately reflect the parameters it actually reads
- Consider adding `door_opening_status` as an input check (skip to Step 4 return if already `open`), reducing unnecessary `door_operator` calls when called from downstream networks that already confirmed the door open

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
