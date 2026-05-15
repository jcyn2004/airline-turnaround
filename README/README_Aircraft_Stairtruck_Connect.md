# Aircraft Stairtruck Connect
## Agentic AI Network – README

> **Configuration file:** `aircraft_stairtruck_connect.hocon`
> **Implementation file:** `aircraft_stairtruck_connect.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Connect a stairtruck to an aircraft at the gate during turnaround, after verifying that ACU is connected, GPU is connected, and wheel chocks are installed.

---

## 1. Overview

`aircraft_stairtruck_connect` is the stairtruck counterpart to `aircraft_jetbridge_connect` in the **AirlineTurnaround** agentic system. The two networks are structurally identical — same prerequisite model (ACU + GPU + wheelchocks), same STEP-pattern orchestration, same operator logic — differing only in which deplaning equipment is connected and which output status field is set.

The class docstring in the Python file explicitly states: *"Mirrors jetbridge_operator but sets stairtruck_connection_status."*

The network combines:

- An LLM-based orchestration agent (`stairtruck_connect_agent`) using the `CRITICAL: sequential executor` / `STEP` pattern
- One coded execution tool (`stairtruck_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Two external tool references (`aircraft_ground_acu_connect`, `aircraft_ground_gpu_connect`) resolved from the shared registry `registries/aaosa_basic.hocon`

No prior production documentation was provided; this README is based entirely on the source files.

---

## 2. Repository Structure

```
aircraft_stairtruck_connect.hocon    # Agent network configuration
aircraft_stairtruck_connect.py       # Coded tool implementations (stairtruck_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_ground_acu_connect, aircraft_ground_gpu_connect)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
stairtruck_connect_agent  (LLM Orchestrator — STEP pattern)
   │
   ├── TrackerAPI                                        (Coded tool: read/write turnaround state via sly_data)
   │
   ├── stairtruck_operator                               (Coded tool: connect stairtruck)
   │
   ├── /AirlineTurnaround/aircraft_ground_acu_connect    (External — if ACU not yet connected)
   │
   └── /AirlineTurnaround/aircraft_ground_gpu_connect    (External — if GPU not yet connected)
```

### Design principles

Identical to `aircraft_jetbridge_connect`:

- **Equipment-level prerequisite gating:** ACU connected + GPU connected + wheel chocks installed, plus on-blocks flight status.
- **Conditional active resolution:** ACU and GPU resolved via external networks if unmet. Wheelchocks checked but not actively resolved (no external tool for it).
- **Fail-fast on unresolved prerequisites:** After external calls, if any prerequisite remains unmet, agent stops and reports.
- **STEP-pattern execution:** Reliable sequential LLM execution via `CRITICAL: sequential executor`.
- **Operator checks ACU + GPU only:** `stairtruck_operator` validates `acu_connection_status` and `gpu_connection_status`; wheelchocks and flight_status are validated by the orchestrator.

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

### 5.1 stairtruck_connect_agent (LLM Orchestrator)

The entry-point agent. It reads all parameters from TrackerAPI, validates flight status and equipment prerequisites, resolves ACU/GPU via external networks if needed, calls the stairtruck operator, persists the result, and returns the summary.

#### Input parameters

| Parameter                         | Type   | Required | Description                               |
|-----------------------------------|--------|:--------:|-------------------------------------------|
| `flight_number`                   | string |    ✅     | Flight identifier                         |
| `aircraft_type`                   | string |    ✅     | Aircraft model/type                       |
| `gate_id`                         | string |    ✅     | Gate where the aircraft is parked         |
| `flight_status`                   | string |    ✅     | Expected: contains `on blocks` or `block` |
| `acu_connection_status`           | string |    ✅     | Expected: contains `connected`            |
| `gpu_connection_status`           | string |    ✅     | Expected: contains `connected`            |
| `wheels_chocks_installation_status` | string |    ❌     | Expected: contains `installed`            |

> Note: The agent `function.description` says "I am in charge of connecting the **jetbridge** to the aircraft at the gate" — a copy-paste artifact from `aircraft_jetbridge_connect.hocon`. The actual function is stairtruck connection.

#### Orchestration flow (STEP pattern)

**STEP 1 — Resolve prerequisites:**
Call `TrackerAPI` with all seven parameters. Wait. Read back all values.

**STEP 2 — Verify flight status:**
`flight_status` must contain `'on blocks'` or `'block'`. If not → stop and report: `"Cannot connect stairtruck — aircraft is not yet on blocks."`

**STEP 3 — Ensure ACU, GPU, and wheelchocks are ready:**
If all three prerequisites confirmed → skip to STEP 4. Otherwise:
- Call `/AirlineTurnaround/aircraft_ground_acu_connect` if `acu_connection_status` not `'connected'`.
- Call `/AirlineTurnaround/aircraft_ground_gpu_connect` if `gpu_connection_status` not `'connected'`.
- Wait for responses. If any prerequisite still unmet → stop and report which failed.

**STEP 4 — Connect stairtruck:**
Call `stairtruck_operator` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`. Wait. Extract `stairtruck_connection_status`. Call `TrackerAPI` to store it.

**RETURN SUMMARY.**

> Note: Wheelchocks are in the STEP 3 prerequisite check but there is no external tool to resolve them. If chocks are not installed, the agent can only stop and report the failure — it cannot fix it automatically.

> Note: `'block'` in STEP 2 is an overly broad substring match — it accepts `"blocked"`, `"unblocked"`, etc. Same limitation as `aircraft_jetbridge_connect`.

#### sly_data contract

| Direction           | Parameters                                                                                                                                                                        |
|---------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `stairtruck_connection_status`                                                                                                                                                    |
| **To downstream**   | `stairtruck_connection_status`                                                                                                                                                    |
| **From upstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`, `stairtruck_connection_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`, `stairtruck_connection_status` |

> Note: Both outbound directions propagate only `stairtruck_connection_status` — identical narrow pattern to `aircraft_jetbridge_connect`.

#### Down-chain tools

```
["TrackerAPI", "stairtruck_operator",
 "/AirlineTurnaround/aircraft_ground_acu_connect",
 "/AirlineTurnaround/aircraft_ground_gpu_connect"]
```

---

### 5.2 stairtruck_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_stairtruck_connect.aircraft_stairtruck_connect.stairtruck_operator`

Connects the stairtruck. It validates all required parameters, checks both ACU and GPU connection statuses, then sets `stairtruck_connection_status = 'connected'`, writes to `sly_data`, and appends a timestamped log entry. Initial value is `'retracted'` (not `'pending'`).

The Python class docstring explicitly acknowledges its origin: *"Mirrors jetbridge_operator but sets stairtruck_connection_status."*

#### Input parameters

| Parameter               | Type   | Required | Source priority     |
|-------------------------|--------|:--------:|---------------------|
| `flight_number`         | string |    ✅     | `args` → `sly_data` |
| `aircraft_type`         | string |    ✅     | `args` → `sly_data` |
| `flight_status`         | string |    ✅     | `args` → `sly_data` |
| `gate_id`               | string |    ✅     | `args` → `sly_data` |
| `acu_connection_status` | string |    ✅     | `args` → `sly_data` |
| `gpu_connection_status` | string |    ✅     | `args` → `sly_data` |

#### Connection logic

`stairtruck_connection_status` is set to `'connected'` when **both** conditions are true (case-insensitive):

```
'connected' in acu_connection_status
AND
'connected' in gpu_connection_status
```

> Note: The `'connected' in` substring check means `'not connected'` would **also** satisfy the condition, since `'connected'` is a substring of `'not connected'`. Same critical issue as in `aircraft_jetbridge_connect`. Use exact matching for correctness.

#### Return behaviour

`stairtruck_connection_status` is initialised as `'retracted'` before the `if` block and returned unconditionally — so it returns `'retracted'` on failure rather than raising `NameError`. This is the correct safe pattern, consistent with `jetbridge_operator`.

Line 168 assigns `message` again unconditionally after the `if` block — dead code, since `return stairtruck_connection_status` (line 170) returns the status value. This is the same vestigial second assignment present in `aircraft_jetbridge_connect.py` (line 175), confirming the copy derivation.

#### Output

- Writes `stairtruck_connection_status = 'connected'` into `sly_data` on success; not updated on failure
- Returns `stairtruck_connection_status` string (`'connected'` or `'retracted'`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt` on success only

> Note: The HOCON `stairtruck_operator` description says "This agent connects **jetbridge** to the aircraft" — copy-paste from `aircraft_jetbridge_connect.hocon`. The function is stairtruck connection.

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_stairtruck_connect.aircraft_stairtruck_connect.TrackerAPI`

Standard sly_data-first implementation. Called in STEP 1 to read all available parameters, and again in STEP 4 after the operator to persist `stairtruck_connection_status`.

#### Configuration

**Tracked fields:**
`aircraft_type`, `acu_connection_status`, `flight_number`, `flight_status`, `gate_id`, `gpu_connection_status`, `stairtruck_connection_status`

**Return fields:**
`acu_connection_status`, `flight_status`, `gpu_connection_status`, `stairtruck_connection_status`

> Note: `wheels_chocks_installation_status` is in the HOCON sly_data allow blocks and HOCON TrackerAPI parameter schema, but is **not in `FLIGHT_TURNAROUND_TRACKED_FIELDS`**. TrackerAPI will not persist or return this field — identical gap to `aircraft_jetbridge_connect`.

> Note: `flight_number`, `aircraft_type`, and `gate_id` are tracked but not returned.

> Note: The HOCON TrackerAPI schema includes both `jetbridge_connection_status` AND `stairtruck_connection_status` (line 318, 322). `aircraft_jetbridge_connect`'s TrackerAPI only included `jetbridge_connection_status`. This wider schema is appropriate for a TrackerAPI that may be shared with door-opening networks.

> Note: The HOCON TrackerAPI description has `"statusengines_stop_status"` — the concatenated copy-paste artifact also present in `aircraft_jetbridge_connect`.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

| Tool path                                        | Purpose     | Condition triggering call                         |
|--------------------------------------------------|-------------|---------------------------------------------------|
| `/AirlineTurnaround/aircraft_ground_acu_connect` | Connect ACU | STEP 3: `acu_connection_status` not `'connected'` |
| `/AirlineTurnaround/aircraft_ground_gpu_connect` | Connect GPU | STEP 3: `gpu_connection_status` not `'connected'` |

> Note: No external tool exists for `wheels_chocks_installation_status`. If chocks are not installed, the agent can only stop and report.

---

## 7. Sample Queries

```
# All prerequisites confirmed
"Flight AF84 is on blocks at gate A1. ACU and GPU are connected to this B747,
and wheelchocks have been installed. Connect the stairtruck."

# Prerequisites not yet confirmed — agent will attempt to resolve ACU/GPU
"Flight AF84 is on blocks at gate A1. Connect the stairtruck."
```

---

## 8. Example Execution Trace

**Input:**
> "Flight AF84 is on blocks at gate A1. ACU and GPU are connected to this B747, and wheelchocks have been installed. Connect the stairtruck."

**Execution steps:**

1. `TrackerAPI` called (STEP 1) — reads: `flight_status=on blocks`, `acu_connection_status=connected`, `gpu_connection_status=connected`, `wheels_chocks_installation_status=installed`
2. `flight_status` check: contains `'on blocks'` ✅ (STEP 2)
3. All three prerequisites confirmed ✅ → skip to STEP 4 (STEP 3)
4. `stairtruck_operator` called — returns `stairtruck_connection_status=connected`
5. `TrackerAPI` called — stores `stairtruck_connection_status=connected`
6. Summary returned

**Output:**

```
*******************************************
* Summary of aircraft stairtruck connect  *
*******************************************
** flight_status                   **: on blocks
** acu connection status           **: connected
** gpu connection status           **: connected
** wheelchocks installation status **: installed
** stairtruck connection status    **: connected
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "acu_connection_status": "connected",
  "gpu_connection_status": "connected",
  "wheels_chocks_installation_status": "installed",
  "stairtruck_connection_status": "connected"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue                                                                     | Location                                       | Severity | Notes                                                                                                                                                                                                                                  |
|---------------------------------------------------------------------------|------------------------------------------------|:--------:|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| No external tool to resolve wheelchocks                                   | `aircraft_stairtruck_connect.hocon` line 218   |  Medium  | STEP 3 checks wheelchocks but no resolution tool is registered. Same gap as `aircraft_jetbridge_connect`.                                                                                                                              |
| Agent description says "connecting the **jetbridge**"                     | `aircraft_stairtruck_connect.hocon` line 93    |   Low    | Copy-paste from `aircraft_jetbridge_connect.hocon`. Should say "stairtruck".                                                                                                                                                           |
| `stairtruck_operator` description says "connects **jetbridge**"           | `aircraft_stairtruck_connect.hocon` line 225   |   Low    | Same copy-paste. Should say "stairtruck".                                                                                                                                                                                              |
| Redundant second `message` assignment (dead code)                         | `aircraft_stairtruck_connect.py` line 168      |   Low    | Assigned after the `if` block but never used — `return stairtruck_connection_status` follows immediately. Same dead code as jetbridge (line 175).                                                                                      |

---

## 10. Comparison with `aircraft_jetbridge_connect`

| Aspect                                              | `aircraft_jetbridge_connect`  | `aircraft_stairtruck_connect`                                               |
|-----------------------------------------------------|-------------------------------|-----------------------------------------------------------------------------|
| Entry agent name                                    | `jetbridge_connect_agent`     | `stairtruck_connect_agent`                                                  |
| Operator name                                       | `jetbridge_operator`          | `stairtruck_operator`                                                       |
| Output status field                                 | `jetbridge_connection_status` | `stairtruck_connection_status`                                              |
| Initial status value                                | `'retracted'`                 | `'retracted'`                                                               |
| `'connected' in` substring bug                      | Yes                           | Yes                                                                         |
| Redundant `message` assignment                      | Yes (line 175)                | Yes (line 168)                                                              |
| `wheels_chocks_installation_status` not tracked       | Yes                           | Yes                                                                         |
| TrackerAPI schema includes both bridge/truck fields | No (only jetbridge)           | Yes (both `jetbridge_connection_status` and `stairtruck_connection_status`) |
| Agent description copy-paste                        | No                            | Yes ("connecting the jetbridge")                                            |
| Operator description copy-paste                     | No                            | Yes ("connects jetbridge")                                                  |
| Class docstring documents mirror relationship       | No                            | Yes ("Mirrors jetbridge_operator...")                                       |

The TrackerAPI HOCON schema difference is the one structurally meaningful distinction: `aircraft_stairtruck_connect`'s TrackerAPI exposes both `jetbridge_connection_status` and `stairtruck_connection_status`, which makes it appropriate for use in contexts where both connection types need to be visible in state.

---

## 11. Extensibility Guidance

- Add `wheels_chocks_installation_status` to `FLIGHT_TURNAROUND_TRACKED_FIELDS` and `RETURN_FIELDS`
- Consider adding `/AirlineTurnaround/aircraft_ground_wheelchocks_install` to the tools list for complete prerequisite resolution

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
