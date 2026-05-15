# Aircraft Ground ACU Connect
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_acu_connect.hocon`
> **Implementation file:** `aircraft_ground_acu_connect.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Connect an Air Conditioning Unit (ACU) to an aircraft at the gate during turnaround, after first verifying ACU readiness via a dedicated setup network, then confirming the aircraft is on blocks, engines are stopped, and wheel chocks are installed.

---

## 1. Overview

`aircraft_ground_acu_connect` is a more advanced variant of `aircraft_acu_connect` in the **AirlineTurnaround** agentic system. The key difference is the addition of a **fourth prerequisite** — `acu_readiness_status` — checked via a dedicated external network (`aircraft_ground_acu_setup`) before any safety-state checks are performed.

The network combines:

- An LLM-based orchestration agent (`acu_agent`) that interprets intent and drives the workflow
- One coded execution tool (`acu_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- One external tool reference (`/AirlineTurnaround/aircraft_ground_acu_setup`) resolved from the shared registry `registries/aaosa_basic.hocon`

A commented-out `acu_setup` class in the Python file represents the original inline readiness-checking implementation. This has been superseded by the external network delegation, though the code remains as a reference.

---

## 2. Repository Structure

```
aircraft_ground_acu_connect.hocon    # Agent network configuration
aircraft_ground_acu_connect.py       # Coded tool implementations (acu_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (/AirlineTurnaround/aircraft_ground_acu_setup)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
acu_agent  (LLM Orchestrator)
   │
   ├── /AirlineTurnaround/aircraft_ground_acu_setup   (External tool: verify ACU readiness — called FIRST)
   │
   ├── acu_operator                                    (Coded tool: connect ACU)
   │
   └── TrackerAPI                                      (Coded tool: read/write turnaround state via sly_data)
```

### Design principles

- **ACU readiness gate — first:** Before any safety-state check, the orchestrator calls `aircraft_ground_acu_setup` to confirm `acu_readiness_status = 'ready'` or `'yes'`. If not confirmed, the workflow stops immediately.
- **Four-prerequisite enforcement:** Only after ACU readiness is confirmed does the orchestrator check: `flight_status = on blocks`, `engines_stop_status = stopped`, `wheels_chocks_installation_status = installed`. All four must be satisfied before `acu_operator` is called.
- **Operator checks readiness only:** Unlike `aircraft_acu_connect`, `acu_operator` here does not re-check engines or chocks — it only validates `acu_readiness_status`. The safety prerequisites are enforced exclusively by the orchestrator.
- **sly_data-first for readiness:** `acu_operator` reads `acu_readiness_status` from `sly_data` first, then falls back to `args`.
- **Structured output:** The agent returns a formatted summary including all four prerequisite statuses.

---

## 4. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

> Note: The HOCON `llm_config` line includes a comment showing previously tested alternatives (`gpt-4o`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`), making this one of the few networks where model selection history is visible.

---

## 5. Components

### 5.1 acu_agent (LLM Orchestrator)

The entry-point agent. It first verifies ACU readiness via an external network, then checks the three safety prerequisites, calls the operator, persists the result, and returns the summary.

#### Input parameters

| Parameter                         | Type   | Required | Description                                                              |
|-----------------------------------|--------|:--------:|--------------------------------------------------------------------------|
| `aircraft_type`                   | string |    ✅     | Aircraft model/type                                                      |
| `gate_id`                         | string |    ✅     | Gate where the aircraft is parked                                        |
| `flight_status`                   | string |    ❌     | Expected: `on blocks`                                                    |
| `engines_stop_status`             | string |    ❌     | Expected: `stopped`                                                      |
| `wheels_chocks_installation_status` | string |    ❌     | Expected: `installed` (note: no underscore between "wheel" and "chocks") |
| `acu_connection_status`           | string |    ❌     | Current or previous ACU connection status                                |
| `acu_readiness_status`            | string |    ❌     | ACU readiness from setup network                                         |

> Note: `flight_number` is absent from the HOCON agent parameter schema (it is not in the `properties` object or `required` array), though it flows through sly_data and is tracked by `TrackerAPI`.

#### Orchestration flow

The instructions use older numbered-prose style (not `CRITICAL: sequential executor` / `STEP`):

1. Read the inquiry — confirm it is about ACU connection. If not → stop.
2. Call `/AirlineTurnaround/aircraft_ground_acu_setup` with `aircraft_type` and `gate_id`. Wait. Store `acu_readiness_status`. If not explicitly `ready` or `yes` → **stop and report ACU not ready.**
3. With ACU readiness confirmed, read from the inquiry: `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status`.
4. If any of the three safety prerequisites are unmet → call `TrackerAPI`. Wait. Store `engines_stop_status`, `wheels_chucks_installation_status` (typo — see Known Issues), `flight_status`.
5. If still any prerequisite unmet OR `acu_readiness_status` not `ready`/`yes` → stop and report current statuses.
6. All four prerequisites confirmed → call `acu_operator`. Wait. Save result as `acu_connection_status`. Report.
7. Call `TrackerAPI` — store all four status fields.
8. Return summary.

> Note: Step 4 is only entered when prerequisites are unmet (step 3 checked the inquiry, not sly_data). The TrackerAPI read in step 4 therefore serves as the primary sly_data lookup for missing values, not a re-check after a prior confirmation.

> Note: Step 6a says "call your tools to connect ACU" without naming `acu_operator` explicitly. The agent must select the correct tool from its toolset autonomously.

#### sly_data contract

| Direction           | Parameters                                                                                                                                                              |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `acu_connection_status`, `acu_readiness_status`                                                                                                                         |
| **To downstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheels_chocks_installation_status`, `acu_connection_status`, `acu_readiness_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheels_chocks_installation_status`, `acu_connection_status`, `acu_readiness_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheels_chocks_installation_status`, `acu_connection_status`, `acu_readiness_status` |

> Note: The sly_data blocks use `wheels_chocks_installation_status` (no underscore between "wheel" and "chocks"). The Python `FLIGHT_TURNAROUND_TRACKED_FIELDS` uses `wheels_chocks_installation_status` (with underscore). These are different field names. Values stored under one name will not be found when the other name is looked up.

> Note: `to_upstream` propagates both `acu_connection_status` and `acu_readiness_status` — broader than most other networks that propagate only the primary output status.

#### Down-chain tools

```
["acu_operator", "/AirlineTurnaround/aircraft_ground_acu_setup", "TrackerAPI"]
```

---

### 5.2 acu_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_acu_connect.aircraft_ground_acu_connect.acu_operator`

Connects the ACU. It validates `aircraft_type` and `gate_id`, then checks `acu_readiness_status` only. If readiness is confirmed, sets `acu_connection_status = 'connected'`, writes to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

#### Input parameters

| Parameter              | Type   | Required | Source priority                          |
|------------------------|--------|:--------:|------------------------------------------|
| `aircraft_type`        | string |    ✅     | `args` → `sly_data`                      |
| `gate_id`              | string |    ✅     | `args` → `sly_data`                      |
| `acu_readiness_status` | string |    ✅     | **`sly_data` → `args`** (sly_data-first) |

Unlike all other operators in the system, `acu_operator` does **not** check `engines_stop_status`, `wheels_chocks_installation_status`, or `flight_status`. Safety prerequisites are enforced by the orchestrator. The operator only validates ACU readiness.

#### Connection logic

`acu_connection_status` is set to `'connected'` when (case-insensitive):

```
('ready' in acu_readiness_status AND 'no' not in acu_readiness_status)
OR 'available' in acu_readiness_status
```

> Note: The `'no' not in` guard is intended to exclude values like `"not ready"`, but it would also exclude any string that happens to contain the substring `"no"` — including `"unknown"`. The `'available' in` OR branch accepts values like `"available"` or `"not available"` alike (since `'available'` is a substring of both). For production use, exact-match comparisons are safer.

#### Critical code bug — `NameError` on failed readiness check (line 215)

```python
if (readiness condition):
    acu_connection_status = 'connected'   # only assigned here
    message = f"..."
    ...

return acu_connection_status   # NameError if condition was False
```

If `acu_readiness_status` fails the condition, `acu_connection_status` is never assigned and `return acu_connection_status` raises `NameError`. The operator has no fallback return path. Fix: initialize `acu_connection_status = 'pending'` before the `if` block.

#### Output

- Writes `acu_connection_status = 'connected'` into `sly_data` on success
- Returns `acu_connection_status` (`'connected'`) — or raises `NameError` on failure
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_acu_connect.aircraft_ground_acu_connect.TrackerAPI`

Manages shared turnaround state. Called in step 4 to read missing prerequisite statuses, and again in step 7 after the operator to persist all status fields.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `acu_connection_status`, `acu_readiness_status`, `engines_stop_status`, `flight_number`, `flight_status`, `gate_id`, `wheels_chocks_installation_status`

**Return fields:**
`acu_connection_status`, `acu_readiness_status`, `engines_stop_status`, `flight_status`, `wheels_chocks_installation_status`

> Note: The Python `TrackerAPI` tracked/return fields use `wheels_chocks_installation_status` (with underscore). The HOCON sly_data blocks and TrackerAPI schema use `wheels_chocks_installation_status` (no underscore). These are different field names and will not resolve to the same sly_data key. Values written by the orchestrator under `wheels_chocks_installation_status` will not be found by `TrackerAPI` when it looks for `wheels_chocks_installation_status`.

> Note: The HOCON `TrackerAPI` description references `"wheels_chucks_installation_status"` (double typo: missing underscore AND "chucks"). The Python uses the correct `wheels_chocks_installation_status`.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

| Tool path                                      | Purpose                                    | When called                                                   |
|------------------------------------------------|--------------------------------------------|---------------------------------------------------------------|
| `/AirlineTurnaround/aircraft_ground_acu_setup` | Verify ACU readiness at the specified gate | Step 2 — before any safety-state check; call is unconditional |

---

## 7. Commented-Out Code — `acu_setup` Class

Lines 30–121 of the Python file contain a fully commented-out `acu_setup` class that was the original inline ACU readiness implementation. It read `air_conditioning_unit_readiness` from `gate_equipments_base.csv` for the given `gate_id`, and translated `'yes'` to `'ready'`. This logic has been extracted into the external `aircraft_ground_acu_setup` network. The commented code remains as a reference and can be safely removed from production.

---

## 8. Sample Queries

```
# All prerequisites already met
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The engines are stopped and wheels chocks have been installed and the ACU is ready.
Connect the ACU."
```

---

## 9. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. The engines are stopped and wheels chocks have been installed and the ACU is ready. Connect the ACU."

**Execution steps:**

1. `/AirlineTurnaround/aircraft_ground_acu_setup` called (step 2) — returns `acu_readiness_status=ready`
2. ACU readiness confirmed ✅
3. Prerequisites read from inquiry: `flight_status=on blocks`, `engines_stop_status=stopped`, `wheels_chocks_installation_status=installed`
4. All four prerequisites met ✅ (step 5 check passes)
5. `acu_operator` called — returns `acu_connection_status=connected`
6. `TrackerAPI` called (step 7) — persists all status fields
7. Summary returned

**Output:**

```
***********************************
* Summary of aircraft acu connect *
***********************************
** flight status **:                          on blocks
** engines stop status **:                    stopped
** wheels chocks installation status **:      installed
** acu readiness status **:                   ready
** acu connection status **:                  connected
```

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "engines_stop_status": "stopped",
  "wheels_chocks_installation_status": "installed",
  "acu_readiness_status": "ready",
  "acu_connection_status": "connected"
}
```

---

## 10. Known Issues and Maintenance Notes

| Issue   | Location          |   Severity   | Notes |
|---------|-------------------|:------------:|-------|
|         |                   | **Critical** |       |


---

## 11. Relationship to `aircraft_acu_connect`

This network extends `aircraft_acu_connect` with one additional prerequisite and a different operator design:

| Aspect                   | `aircraft_acu_connect`                       | `aircraft_ground_acu_connect`                               |
|--------------------------|----------------------------------------------|-------------------------------------------------------------|
| Prerequisites            | on blocks, engines stopped, chocks installed | + ACU readiness (via external network)                      |
| Readiness check          | None                                         | `/AirlineTurnaround/aircraft_ground_acu_setup` called first |
| Operator checks          | engines stopped + chocks installed           | ACU readiness only                                          |
| Safety gate              | Operator enforces engines + chocks           | Orchestrator enforces all four; operator is readiness-only  |
| `flight_number` required | Yes                                          | No (absent from schema; flows via sly_data)                 |

---

## 12. Extensibility Guidance

- Replace the compound readiness condition with exact-value matching: `acu_readiness_status.strip().lower() in ('ready', 'yes', 'available')`
- Upgrade to the `CRITICAL: sequential executor` / `STEP` pattern for more reliable LLM execution

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
