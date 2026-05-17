# Aircraft Jetbridge Connect
## Agentic AI Network – README

> **Configuration file:** `aircraft_jetbridge_connect.hocon`
> **Implementation file:** `aircraft_jetbridge_connect.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Connect the jetbridge to an aircraft at the gate during turnaround, after verifying that the ACU is connected, GPU is connected, and wheel chocks are installed.

---

## 1. Overview

`aircraft_jetbridge_connect` is an agentic network that orchestrates jetbridge connection for an aircraft in turnaround. Its prerequisite model is fundamentally different from what the previous documentation described — it does not check engines-stopped or on-blocks state directly, but instead requires three equipment-level prerequisites to be met first: ACU connected, GPU connected, and wheel chocks installed.

The network combines:

- An LLM-based orchestration agent (`jetbridge_connect_agent`) using the modern `CRITICAL: sequential executor` / `STEP` pattern
- One coded execution tool (`jetbridge_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Two external tool references (`aircraft_ground_acu_connect`, `aircraft_ground_gpu_connect`) resolved from the shared registry `registries/aaosa_basic.hocon`

---

## 2. Repository Structure

```
aircraft_jetbridge_connect.hocon    # Agent network configuration
aircraft_jetbridge_connect.py       # Coded tool implementations (jetbridge_operator, TrackerAPI)
registries/aaosa_basic.hocon        # Shared registry (aircraft_ground_acu_connect, aircraft_ground_gpu_connect)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
jetbridge_connect_agent  (LLM Orchestrator — STEP pattern)
   │
   ├── TrackerAPI                                         (Coded tool: read/write turnaround state via sly_data)
   │
   ├── jetbridge_operator                                 (Coded tool: connect jetbridge)
   │
   ├── /AirlineTurnaround/aircraft_ground_acu_connect     (External — if ACU not yet connected)
   │
   └── /AirlineTurnaround/aircraft_ground_gpu_connect     (External — if GPU not yet connected)
```

### Design principles

- **Equipment-level prerequisite gating:** Jetbridge connection requires ACU connected, GPU connected, and wheel chocks installed — not just on-blocks and engines stopped. This reflects the actual physical dependency: the jetbridge provides cabin access, which must be preceded by full ground power and stability.
- **Conditional active resolution:** If ACU or GPU are not connected, the agent resolves them via external networks. Wheelchocks are checked but not actively resolved — no external tool is in the toolset for wheelchocks.
- **Fail-fast on unresolved prerequisites:** After the external network calls, if any prerequisite is still not satisfied, the agent stops and reports which one failed.
- **STEP-pattern execution:** Uses the modern `CRITICAL: sequential executor` / `STEP` format for reliable LLM sequencing.
- **Operator checks ACU + GPU only:** `jetbridge_operator` validates `acu_connection_status` and `gpu_connection_status` — wheelchocks and flight_status are validated by the orchestrator, not the operator.

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

### 5.1 jetbridge_connect_agent (LLM Orchestrator)

The entry-point agent. It reads all parameters from TrackerAPI, validates flight status and equipment prerequisites, resolves ACU/GPU via external networks if needed, calls the jetbridge operator, persists the result, and returns the summary.

> Note: The agent is named `jetbridge_connect_agent` in the HOCON. The previous documentation referred to it as `aircraft_jetbridge_connect_agent`.

#### Input parameters

| Parameter                         | Type   | Required | Description                               |
|-----------------------------------|--------|:--------:|-------------------------------------------|
| `flight_number`                   | string |    ✅     | Flight identifier                         |
| `aircraft_type`                   | string |    ✅     | Aircraft model/type                       |
| `gate_id`                         | string |    ✅     | Gate where the aircraft is parked         |
| `flight_status`                   | string |    ✅     | Expected: contains `on blocks` or `on-blocks` |
| `acu_connection_status`           | string |    ✅     | Expected: contains `connected`            |
| `gpu_connection_status`           | string |    ✅     | Expected: contains `connected`            |
| `wheels_chocks_installation_status` | string |    ❌     | Expected: contains `installed`            |

#### Orchestration flow (STEP pattern)

**STEP 1 — Resolve prerequisites:**
Call `TrackerAPI` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`. Wait. Read back all values.

**STEP 2 — Verify flight status:**
`flight_status` must contain `'on blocks'` or `'on-blocks'`. If not → stop and report: `"Cannot connect jetbridge — aircraft is not yet on blocks."`

**STEP 3 — Ensure ACU, GPU, and wheelchocks are ready:**
If `acu_connection_status` contains `'connected'` AND `gpu_connection_status` contains `'connected'` AND `wheels_chocks_installation_status` contains `'installed'` → skip to STEP 4. Otherwise:
- Call `/AirlineTurnaround/aircraft_ground_acu_connect` if `acu_connection_status` is not `'connected'`.
- Call `/AirlineTurnaround/aircraft_ground_gpu_connect` if `gpu_connection_status` is not `'connected'`.
- Wait for responses. Extract and store statuses.
- If any prerequisite is still not satisfied after these calls → stop and report which prerequisite failed.

**STEP 4 — Connect jetbridge:**
Call `jetbridge_operator` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`. Wait. Extract `jetbridge_connection_status`. Call `TrackerAPI` to store it.

**RETURN SUMMARY.**

> Note: `wheels_chocks_installation_status` is checked in STEP 3's condition but there is **no external tool** to resolve it if it fails. The tools list (line 218) includes `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect` but no wheelchocks resolution tool. If chocks are not installed, the agent can only stop and report the failure — it cannot fix it automatically, unlike ACU and GPU.

> Note: `flight_status` is checked for `'on blocks'` or `'on-blocks'` in STEP 2 — the HOCON instruction accepts either the space-separated or hyphenated form.

#### sly_data contract

| Direction           | Parameters                                                                                                                                                                       |
|---------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `jetbridge_connection_status`                                                                                                                                                    |
| **To downstream**   | `jetbridge_connection_status`                                                                                                                                                    |
| **From upstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`, `jetbridge_connection_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `acu_connection_status`, `gpu_connection_status`, `wheels_chocks_installation_status`, `jetbridge_connection_status` |

> Note: Both `to_upstream` and `to_downstream` propagate only `jetbridge_connection_status`. All context flows in via `from_upstream`/`from_downstream`. This is the narrowest outbound sly_data in a multi-prerequisite network.

#### Down-chain tools

```
["TrackerAPI", "jetbridge_operator",
 "/AirlineTurnaround/aircraft_ground_acu_connect",
 "/AirlineTurnaround/aircraft_ground_gpu_connect"]
```

---

### 5.2 jetbridge_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_jetbridge_connect.aircraft_jetbridge_connect.jetbridge_operator`

Performs the jetbridge connection action. It validates all required parameters, checks both ACU and GPU connection statuses, then sets `jetbridge_connection_status = 'connected'`, writes to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

Initial value of `jetbridge_connection_status` is `'retracted'` (not `'pending'` as used in most other operators).

#### Input parameters

| Parameter               | Type   | Required | Source priority     |
|-------------------------|--------|:--------:|---------------------|
| `flight_number`         | string |    ✅     | `args` → `sly_data` |
| `aircraft_type`         | string |    ✅     | `args` → `sly_data` |
| `flight_status`         | string |    ❌     | `args` → `sly_data` |
| `gate_id`               | string |    ✅     | `args` → `sly_data` |
| `acu_connection_status` | string |    ✅     | `args` → `sly_data` |
| `gpu_connection_status` | string |    ✅     | `args` → `sly_data` |

> Note: The HOCON `required` list for `jetbridge_operator` is `["flight_number", "aircraft_type", "gate_id", "acu_connection_status", "gpu_connection_status"]` — `flight_status` is declared as a parameter but is **not** in the required list.

> Note: The operator does **not** check `wheels_chocks_installation_status`. The operator parameter schema does not include `wheels_chocks_installation_status` at all. Wheelchocks validation is entirely the orchestrator's responsibility.

#### Connection logic

`jetbridge_connection_status` is set to `'connected'` when **both** conditions are true (case-insensitive):

```
'connected' in acu_connection_status
AND
'connected' in gpu_connection_status
```

> Note: The `'connected' in` substring check means `'not connected'` would **also** satisfy the condition, since `'connected'` is a substring of `'not connected'`. Use exact matching (`acu_connection_status.strip().lower() == 'connected'`) for correctness.

#### Return behaviour

Unlike most other operators in the system (which have a `NameError` risk from uninitialized status variables), `jetbridge_operator` initialises `jetbridge_connection_status = 'retracted'` before the `if` block and returns `jetbridge_connection_status` unconditionally — so it returns `'retracted'` on failure. This avoids the `NameError` present in the ACU, GPU, and wheelchocks connect operators.

Line 175 assigns `message` again unconditionally after the `if` block:

```python
message = f"Flight {flight_number} ... status is {jetbridge_connection_status}."
```

This second assignment is dead code — `return jetbridge_connection_status` on line 178 returns the status value, not `message`. The commented-out `# return message` on line 177 shows the original intent was to return the log string (same bug as `aircraft_gpu_connect`), but the return was corrected to return `jetbridge_connection_status` directly. The second `message` assignment remains as an unused residue.

#### Output

- Writes `jetbridge_connection_status = 'connected'` into `sly_data` on success; `sly_data` is not updated on failure
- Returns `jetbridge_connection_status` string (`'connected'` or `'retracted'`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt` on success only

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_jetbridge_connect.aircraft_jetbridge_connect.TrackerAPI`

Standard sly_data-first implementation. Called in STEP 1 to read all available parameters, and again in STEP 4 after the operator to persist `jetbridge_connection_status`.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

**Tracked fields:**
`aircraft_type`, `acu_connection_status`, `flight_number`, `flight_status`, `gate_id`, `gpu_connection_status`, `jetbridge_connection_status`

**Return fields:**
`acu_connection_status`, `flight_status`, `gpu_connection_status`, `jetbridge_connection_status`

> Note: `wheels_chocks_installation_status` is in the HOCON sly_data allow blocks and HOCON TrackerAPI parameter schema, but is **not in `FLIGHT_TURNAROUND_TRACKED_FIELDS`**. TrackerAPI will not persist or return this field. If an upstream caller passes `wheels_chocks_installation_status` via sly_data, it will flow through the allow blocks but TrackerAPI cannot log or echo it.

> Note: `flight_number`, `aircraft_type`, and `gate_id` are tracked but not returned — they are persisted to sly_data but not echoed back in the return tuple.

> Note: The HOCON TrackerAPI description contains the phrase `"I check engines stop status as status engines_stop_status."` — a copy-paste artifact where `status` precedes `engines_stop_status`. Neither this field nor `engines_stop_status` is tracked by this network (though `engines_stop_status` is declared in the TrackerAPI parameter schema).

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

> Note: The HOCON TrackerAPI parameter schema also declares `ground_services_request_type`, `wheels_chocks_readiness_status`, `gpu_readiness_status`, `engines_stop_status`, and `door_opening_status`, none of which are used by this network's flow.

---

## 6. External Tool Dependencies

These tools are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path                                        | Purpose                 | Condition triggering call                              |
|--------------------------------------------------|-------------------------|--------------------------------------------------------|
| `/AirlineTurnaround/aircraft_ground_acu_connect` | Connect ACU to aircraft | `acu_connection_status` does not contain `'connected'` |
| `/AirlineTurnaround/aircraft_ground_gpu_connect` | Connect GPU to aircraft | `gpu_connection_status` does not contain `'connected'` |

> Note: There is no external tool to resolve `wheels_chocks_installation_status`. If chocks are not installed when STEP 3 runs, the only outcome is a stop-and-report failure. The caller (or a higher-level orchestrator) must ensure chocks are installed before calling this network.

---

## 7. Sample Queries

```
# All prerequisites confirmed
"Flight AF84 is on blocks at gate A1. ACU and GPU are connected to this B747,
and wheelchocks have been installed. Connect the jet bridge."

# Prerequisites not yet confirmed — agent will attempt to resolve ACU/GPU
"Flight AF84 is on blocks at gate A1. Connect the jet bridge."
```

---

## 8. Example Execution Trace

**Input:**
> "Flight AF84 is on blocks at gate A1. ACU and GPU are connected to this B747, and wheelchocks have been installed. Connect the jet bridge."

**Execution steps:**

1. `TrackerAPI` called (STEP 1) — reads: `flight_status=on blocks`, `acu_connection_status=connected`, `gpu_connection_status=connected`, `wheels_chocks_installation_status=installed`
2. `flight_status` check: contains `'on blocks'` ✅ (STEP 2)
3. All three prerequisites confirmed ✅ → skip to STEP 4 (STEP 3)
4. `jetbridge_operator` called — returns `jetbridge_connection_status=connected`
5. `TrackerAPI` called — stores `jetbridge_connection_status=connected`
6. Summary returned

**Output:**

```
*****************************************
* Summary of aircraft jetbridge connect *
*****************************************
** flight_status                   **: on blocks
** acu connection status           **: connected
** gpu connection status           **: connected
** wheelchocks installation status **: installed
** jetbridge connection status     **: connected
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
  "jetbridge_connection_status": "connected"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue                                                         | Location                                      | Severity | Notes                                                                                                                                                                                                                                                                                            |
|---------------------------------------------------------------|-----------------------------------------------|:--------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| No external tool to resolve `wheels_chocks_installation_status` | `aircraft_jetbridge_connect.hocon` line 218   |  Medium  | STEP 3 checks wheelchocks but no wheelchocks connect/install tool is in the tools list. A chocks failure can only produce a stop-and-report, not automated resolution. Consider adding `/AirlineTurnaround/aircraft_ground_wheelchocks_install` to the tools list.                               |

---

## 10. Prerequisites — Comparison with Prior Documentation

| Prerequisite           | Old documentation  | Actual implementation                             |
|------------------------|--------------------|---------------------------------------------------|
| Aircraft on blocks     | ✅ Required        | ✅ Required (STEP 2)                              |
| Engines stopped        | ✅ Required        | ❌ Not checked anywhere                           |
| ACU connected          | ❌ Not mentioned   | ✅ Required (STEP 3) — resolved via external tool |
| GPU connected          | ❌ Not mentioned   | ✅ Required (STEP 3) — resolved via external tool |
| Wheel chocks installed | ❌ Not mentioned   | ✅ Checked (STEP 3) — but not resolvable via tool |

The prerequisite shift reflects the actual physical logic of jetbridge deployment: you want to confirm the aircraft has stable ground power and is mechanically secured before extending the bridge.

---

## 11. Extensibility Guidance

- Add `/AirlineTurnaround/aircraft_ground_wheelchocks_install` to the tools list so STEP 3 can resolve all three prerequisites, not just two

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
