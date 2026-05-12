# Aircraft GPU Connect
## Agentic AI Network – README

> **Configuration file:** `aircraft_gpu_connect.hocon`
> **Implementation file:** `aircraft_gpu_connect.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Connect a Ground Power Unit (GPU) to an aircraft at the gate during turnaround, after verifying that engines are stopped and wheel chocks are installed.

---

## 1. Overview

`aircraft_gpu_connect` is an agentic network that orchestrates GPU connection for an aircraft in turnaround. It is part of the broader **AirlineTurnaround** agentic system and is a structural counterpart to `aircraft_acu_connect` — both require the same two safety prerequisites (engines stopped, chocks installed) before connecting power or conditioning equipment.

The network combines:

- An LLM-based orchestration agent (`gpu_connect_agent`) that interprets intent and drives the workflow
- One coded execution tool (`gpu_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Two external tool references (`aircraft_engines_stop`, `aircraft_chocks_install`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network uses older numbered-prose orchestration instructions (no `CRITICAL: sequential executor` / `STEP` pattern), and contains several code-level issues that require attention — most critically, `gpu_operator` returns the log message string rather than the status value on success.

---

## 2. Repository Structure

```
aircraft_gpu_connect.hocon           # Agent network configuration
aircraft_gpu_connect.py              # Coded tool implementations (gpu_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_engines_stop, aircraft_chocks_install)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
gpu_connect_agent  (LLM Orchestrator)
   │
   ├── gpu_operator                                      (Coded tool: connect GPU)
   │
   ├── /AirlineTurnaround/aircraft_engines_stop          (External tool — if engines not stopped)
   │
   ├── /AirlineTurnaround/aircraft_chocks_install        (External tool — if chocks not installed)
   │
   └── TrackerAPI                                        (Coded tool: read/write turnaround state via sly_data)
```

### Design principles

- **Dual safety prerequisite gating:** GPU connection requires both `engines_stop_status` (stopped/done) AND `wheels_chocks_installation_status` (installed/done). If either is unmet, the agent delegates to external networks to resolve before proceeding.
- **Active prerequisite resolution:** Unlike fail-fast networks, this agent calls external tools and loops back to re-check after each resolution attempt.
- **Tool-first execution:** The LLM orchestrates; GPU connection is performed by `gpu_operator`.
- **sly_data as shared state:** `gpu_connection_status` flows to both upstream and downstream networks.

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

### 5.1 gpu_connect_agent (LLM Orchestrator)

The entry-point agent. It reads prerequisite statuses, delegates resolution to external tools as needed, calls `gpu_operator`, persists the result, and returns the summary.

> Note: The agent is named `gpu_connect_agent` in the HOCON. The previous documentation referred to it as `aircraft_gpu_connect_agent`, which does not match the actual runtime tool name.

#### Input parameters

| Parameter | Type | Required | Description |
|---|---|:---:|---|
| `flight_number` | string | ✅ | Flight identifier |
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `flight_status` | string | ✅ | Flight status (expected: `on blocks`) |
| `gate_id` | string | ✅ | Gate where the aircraft is parked |
| `engines_stop_status` | string | ❌ | Expected: `stopped` |
| `wheels_chocks_installation_status` | string | ❌ | Expected: `installed` |

> Note: `gpu_connection_status` does not appear in the HOCON agent parameter schema but flows through sly_data.

#### Orchestration flow

The instructions use older numbered-prose style, not the `CRITICAL: sequential executor` / `STEP` pattern:

1. Read the inquiry — determine `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`.
2. Call `TrackerAPI` — store all three statuses (using field name `wheels_chucks_installation_status` — note the typo in the instructions).
3. If all three conditions met (`on blocks`, `stopped`, `installed`) → skip to step 6.
4. If any condition is unmet → call the relevant external tool(s) to resolve. Wait for responses. Return to step 2.
5. Call `TrackerAPI` again — re-read `engines_stop_status` and `wheels_chocks_installation_status`.
6. All conditions met → call `gpu_operator`. Wait. Save result as `gpu_connection_status`.
7. Call `TrackerAPI` to log all available parameters.
8. Return summary.

> Note: Step 6b in the instructions says "save it as `acu_connection_status`" — a copy-paste error from `aircraft_acu_connect`. The correct field is `gpu_connection_status`.

> Note: Step 5 is a redundant TrackerAPI call placed between steps 3 and 6 — the same pattern seen in `aircraft_engines_stop`. If step 3 confirmed all prerequisites, step 5 re-confirms before calling the operator, adding no functional value on the normal path.

#### sly_data contract

| Direction | Parameters |
|---|---|
| **To upstream** | `gpu_connection_status` |
| **To downstream** | `gpu_connection_status` |
| **From upstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheels_chocks_installation_status`, `gpu_connection_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheels_chocks_installation_status`, `gpu_connection_status` |

> Note: Both `to_upstream` and `to_downstream` carry only `gpu_connection_status`. The full context set flows in both `from` directions but not outbound — the same pattern as `aircraft_acu_connect`.

#### Down-chain tools

```
["gpu_operator", "/AirlineTurnaround/aircraft_engines_stop",
 "/AirlineTurnaround/aircraft_chocks_install", "TrackerAPI"]
```

---

### 5.2 gpu_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_gpu_connect.aircraft_gpu_connect.gpu_operator`

Performs the GPU connection action. It validates all required parameters, checks both safety prerequisites, then sets `gpu_connection_status = 'Connected'` (capital C), writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

#### Input parameters

| Parameter | Type | Required | Source priority |
|---|---|:---:|---|
| `flight_number` | string | ✅ | `args` → `sly_data` |
| `aircraft_type` | string | ✅ | `args` → `sly_data` |
| `flight_status` | string | ✅ | `args` → `sly_data` |
| `gate_id` | string | ✅ | `args` → `sly_data` |
| `engines_stop_status` | string | ✅ | `args` → `sly_data` |
| `wheels_chocks_installation_status` | string | ✅ | `args` → `sly_data` |

All six parameters are hard-required. If any is missing from both `args` and `sly_data`, the tool returns an error string immediately.

#### Connection logic

`gpu_connection_status` is set to `'Connected'` (capital C) when **both** of the following conditions are true (case-insensitive):

| Field | Accepted values |
|---|---|
| `engines_stop_status` | `stopped`, `done` |
| `wheels_chocks_installation_status` | `installed`, `done` |

#### Critical code bugs

**Bug 1 — Wrong return value on success (line 190):**

```python
sly_data["gpu_connection_status"] = gpu_connection_status   # sets 'Connected'
return message   # returns the log string, NOT gpu_connection_status
```

The operator writes `'Connected'` to `sly_data` correctly but returns `message` — the timestamped log string (e.g. `"Flight AF84 ... has gpu installed. Its gpu installation status is Connected."`) — rather than `gpu_connection_status`. The calling agent receives the log string, not the status value. This can cause `VALIDATION` checks in the orchestrator (if any) to fail, and will pollute the summary with a raw log line.

**Bug 2 — `NameError` on failed prerequisites (line 190):**

```python
if ((conditions)):
    gpu_connection_status = 'Connected'
    message = f"..."   # message only assigned inside the if block
    ...

return message   # NameError if conditions were False — message was never assigned
```

If `engines_stop_status` or `wheels_chocks_installation_status` fail the condition check, the `if` block is skipped and `message` is never assigned. `return message` on line 190 will raise a `NameError: name 'message' is not defined`. The operator has no fallback return path for the failure case.

**Bug 3 — Status casing inconsistency:**

`gpu_connection_status = 'Connected'` uses an uppercase first letter. All other operators in the system use all-lowercase status values (`completed`, `stopped`, `installed`, etc.). Downstream agents checking for `'connected'` (lowercase) will not match.

#### Output (when bugs are resolved)

- Writes `gpu_connection_status = 'Connected'` into `sly_data`
- Currently returns `message` (log string) instead of `gpu_connection_status` — see Bug 1
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_gpu_connect.aircraft_gpu_connect.TrackerAPI`

Manages shared turnaround state. Called in step 2 to read prerequisites, in step 5 as a re-check guard, and in step 7 to persist all available parameters after GPU connection.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `engines_stop_status`, `flight_number`, `flight_status`, `gate_id`, `gpu_connection_status`, `wheels_chocks_installation_status`

**Return fields:**
`flight_status`, `engines_stop_status`, `gpu_connection_status`, `wheels_chocks_installation_status`

> Note: The HOCON `TrackerAPI` description references `"wheels_chucks_installation_status"` (typo: `chucks`) twice — once in the description text and implicitly through parameter naming. The Python implementation correctly uses `wheels_chocks_installation_status`. This is the same inconsistency present in the orchestrator instructions.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

These tools are not defined in this network. They are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path | Purpose | Condition triggering call |
|---|---|---|
| `/AirlineTurnaround/aircraft_engines_stop` | Stop aircraft engines | `engines_stop_status` not `stopped` |
| `/AirlineTurnaround/aircraft_chocks_install` | Install wheel chocks | `wheels_chocks_installation_status` not `installed` |

---

## 7. Sample Queries

```
# All prerequisites already met
"The B747 aircraft of flight AF84 is on blocks at gate A1.
Engines are stopped and wheels chocks are installed. Connect the GPU."

# Prerequisites not yet confirmed — agent will resolve them
"The B747 aircraft of flight AF84 is on blocks at gate A1. Connect the GPU."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. Engines are stopped and wheels chocks are installed. Connect the GPU."

**Execution steps:**

1. `TrackerAPI` called (step 2) — reads: `flight_status=on blocks`, `engines_stop_status=stopped`, `wheels_chocks_installation_status=installed`
2. All prerequisites met ✅ (step 3)
3. `gpu_operator` called — writes `gpu_connection_status=Connected` to sly_data; **currently returns log string** (step 6)
4. `TrackerAPI` called (step 7) — persists `gpu_connection_status=Connected`
5. Summary returned

**Output:**

```
***********************************
* Summary of aircraft gpu connect *
***********************************
** flight status **:                         on blocks
** engines stop status **:                   stopped
** wheels chucks installation status **:     installed
** gpu connection status  **:                Connected
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "engines_stop_status": "stopped",
  "wheels_chocks_installation_status": "installed",
  "gpu_connection_status": "Connected"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| Agent name mismatch with prior documentation | `aircraft_gpu_connect.hocon` line 90 | Low | Agent is `gpu_connect_agent`, not `aircraft_gpu_connect_agent`. |
| **`gpu_operator` returns log string on success** | `aircraft_gpu_connect.py` line 190 | **Critical** | `return message` returns the log string, not `gpu_connection_status`. The calling agent receives a raw log line. Fix: change to `return gpu_connection_status`. |
| **`NameError` on prerequisite failure** | `aircraft_gpu_connect.py` line 190 | **Critical** | `message` is only assigned inside the `if` block. If prerequisites fail, `return message` will raise `NameError`. Fix: add `return gpu_connection_status` (which holds `'pending'`) before the `if`, or add an `else` branch. |
| `gpu_connection_status = 'Connected'` (capital C) | `aircraft_gpu_connect.py` line 175 | Medium | All other operators return lowercase status values. Downstream agents checking for `'connected'` will not match. Fix: `'connected'`. |
| Step 6b says "save as `acu_connection_status`" | `aircraft_gpu_connect.hocon` line 146 | Low | Copy-paste from `aircraft_acu_connect`. Should read `gpu_connection_status`. |
| `wheels_chucks_installation_status` typo in instructions | `aircraft_gpu_connect.hocon` lines 135, 138, 143, 155 | Low | Consistent use of `chucks` instead of `chocks` throughout the orchestrator instruction text. Python correctly uses `wheels_chocks_installation_status`. |
| Redundant TrackerAPI call in step 5 | `aircraft_gpu_connect.hocon` line 141 | Low | Same pattern as `aircraft_engines_stop` — the re-check adds no value when step 3 already confirmed prerequisites. |
| Summary header says "gpu connect" but step 8 label says "fueling status report" | `aircraft_gpu_connect.hocon` line 149 | Low | "Provide the fueling status report summary" — copy-paste from `aircraft_fueling`. Should read "gpu connect status report summary". |
| Hardcoded log path comment | `aircraft_gpu_connect.py` line 67 | Low | Commented-out absolute path remains; active path uses `Path.cwd()`. |

---

## 10. Extensibility Guidance

- **Fix Bug 1 immediately:** Change `return message` to `return gpu_connection_status` on line 190
- **Fix Bug 2 immediately:** Initialize `message = ''` before the `if` block, or add `return gpu_connection_status` as the else path
- **Fix Bug 3:** Change `'Connected'` to `'connected'` (lowercase) for consistency with the system-wide status value convention
- Upgrade to the `CRITICAL: sequential executor` / `STEP` pattern used in more recent networks for more reliable LLM execution
- Fix the `wheels_chucks_installation_status` typo in the orchestrator instructions
- Remove the redundant step 5 TrackerAPI call

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation electrical or safety-critical systems.
