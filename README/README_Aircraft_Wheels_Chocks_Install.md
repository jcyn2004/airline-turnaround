# Aircraft Ground Wheels Chocks Install
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_wheels_chocks_install.hocon`
> **Implementation file:** `aircraft_ground_wheels_chocks_install.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Install wheels chocks on an aircraft at the gate during turnaround, after first verifying wheels chocks readiness via a dedicated setup network, then confirming the aircraft is on blocks and engines are stopped.

---

## 1. Overview

`aircraft_ground_wheels_chocks_install` is the wheels chocks counterpart to `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect` in the **AirlineTurnaround** agentic system. All three networks share the same architectural pattern: a readiness gate checked via an external setup network, followed by safety-state prerequisite enforcement, before the actual installation/connection operator is called.

The network combines:

- An LLM-based orchestration agent (`aircraft_ground_wheels_chocks_install_agent`) that interprets intent and drives the workflow
- One coded execution tool (`wheels_chocks_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- One external tool reference (`/AirlineTurnaround/aircraft_ground_wheels_chocks_setup`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network is also the **provider of the `aircraft_ground_wheels_chocks_setup` external dependency** referenced by `aircraft_ground_readiness` — confirming that the setup network exists as a separate deployed unit, while this install network handles the actual installation action.

---

## 2. Repository Structure

```
aircraft_ground_wheels_chocks_install.hocon   # Agent network configuration
aircraft_ground_wheels_chocks_install.py      # Coded tool implementations (wheels_chocks_operator, TrackerAPI)
registries/aaosa_basic.hocon                  # Shared registry (/AirlineTurnaround/aircraft_ground_wheels_chocks_setup)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
aircraft_ground_wheels_chocks_install_agent  (LLM Orchestrator)
   │
   ├── /AirlineTurnaround/aircraft_ground_wheels_chocks_setup  (External tool: verify readiness — called FIRST)
   │
   ├── wheels_chocks_operator                                   (Coded tool: install wheels chocks)
   │
   └── TrackerAPI                                               (Coded tool: read/write turnaround state via sly_data)
```

### Design principles

- **Readiness gate — first:** Before any safety-state check, the orchestrator calls `aircraft_ground_wheels_chocks_setup` to confirm `wheels_chocks_readiness_status = 'ready'` or `'yes'`. If not confirmed, the workflow stops immediately.
- **Three-prerequisite enforcement:** After readiness is confirmed: `flight_status = on blocks`, `engines_stop_status = stopped`. All three must be satisfied.
- **Operator checks readiness only:** `wheels_chocks_operator` validates only `wheels_chocks_readiness_status` — safety prerequisites are enforced by the orchestrator.
- **sly_data-first for readiness:** `wheels_chocks_operator` reads `wheels_chocks_readiness_status` from `sly_data` first, then falls back to `args`.
- **Safer readiness guard:** The condition uses `'not' not in` (vs. `'no' not in` in GPU/ACU counterparts), correctly excluding `"not ready"` without risk of false positives from substrings.

---

## 4. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

> Note: The HOCON `llm_config` line includes a comment with previously tested model alternatives (`gpt-4o`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`), consistent with the other ground service networks.

---

## 5. Components

### 5.1 aircraft_ground_wheels_chocks_install_agent (LLM Orchestrator)

The entry-point agent. It first verifies wheels chocks readiness, then checks the two safety prerequisites, calls the operator, persists the result, and returns the summary.

#### Input parameters

| Parameter                           | Type   | Required | Description                             |
|-------------------------------------|--------|:--------:|-----------------------------------------|
| `aircraft_type`                     | string |    ✅     | Aircraft model/type                     |
| `flight_number`                     | string |    ❌     | Incoming flight number                  |
| `gate_id`                           | string |    ✅     | Gate where the aircraft is parked       |
| `flight_status`                     | string |    ❌     | Expected: `on blocks`                   |
| `engines_stop_status`               | string |    ❌     | Expected: `stopped`                     |
| `wheels_chocks_installation_status` | string |    ❌     | Current or previous installation status |
| `wheels_chocks_readiness_status`    | string |    ❌     | Readiness from setup network            |

> Note: Required parameters per the HOCON `function.parameters.required` schema are `["aircraft_type", "gate_id"]`. `flight_number` is declared in `properties` and flows through sly_data.

#### Orchestration flow

The instructions use older numbered-prose style, mirroring the ACU and GPU connect networks:

1. Read the inquiry — confirm it is about wheels chocks installation. If not → stop.
2. Call `/AirlineTurnaround/aircraft_ground_wheels_chocks_setup` with `aircraft_type` and `gate_id`. Store `wheels_chocks_readiness_status`. If not `ready` or `yes` → **stop and report not ready.**
3. With readiness confirmed, read `flight_status` and `engines_stop_status` from the inquiry.
4. If either prerequisite is unmet → call `TrackerAPI`. Store `engines_stop_status` and `flight_status`.
5. If still any prerequisite unmet → stop and report current statuses.
6. All three prerequisites confirmed → call `wheels_chocks_operator`. Save as `wheels_chocks_installation_status`. Report.
7. Call `TrackerAPI` — store `engines_stop_status`, `wheels_chocks_installation_status`, `wheels_chocks_readiness_status`, and `wheels_chocks_installation_status` again.
8. Return summary.

#### sly_data contract

| Direction           | Parameters                                                                                                                                                 |
|---------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `wheels_chocks_installation_status`                                                                                                                        |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`                                                                        |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`, `wheels_chocks_readiness_status`                                      |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `wheels_chocks_readiness_status`                                                                              |

> Note: Both `wheels_chocks_installation_status` and `wheels_chocks_readiness_status` propagate upstream — matching the pattern of `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect`.

#### Down-chain tools

```
["wheels_chocks_operator", "/AirlineTurnaround/aircraft_ground_wheels_chocks_setup", "TrackerAPI"]
```

---

### 5.2 wheels_chocks_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_wheels_chocks_install.aircraft_ground_wheels_chocks_install.wheels_chocks_operator`

Performs the wheels chocks installation. It validates `flight_number`, `aircraft_type`, and `gate_id`, then checks `wheels_chocks_readiness_status` only. If readiness is confirmed, sets `wheels_chocks_installation_status = 'installed'`, writes to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`. If the readiness condition is not met, `wheels_chocks_installation_status` retains its default value of `'pending'`.

#### Input parameters (HOCON schema)

| Parameter                           | Type   | Required (HOCON) | Source priority (Python)                 |
|-------------------------------------|--------|:----------------:|------------------------------------------|
| `aircraft_type`                     | string |        ✅         | `args` → `sly_data`                      |
| `flight_number`                     | string |        ❌         | `args` → `sly_data`                      |
| `flight_status`                     | string |        ❌         | (declared, not used by operator code)    |
| `gate_id`                           | string |        ✅         | `args` → `sly_data`                      |
| `wheels_chocks_installation_status` | string |        ❌         | (declared, not used by operator code)    |
| `wheels_chocks_readiness_status`    | string |        ❌         | **`sly_data` → `args`** (sly_data-first) |

> Note: The HOCON declares only `["aircraft_type", "gate_id"]` as required, but the Python implementation also requires `flight_number` and `wheels_chocks_readiness_status` at runtime — returning an error string if either is missing.

> Note: The operator's docstring says `args: an empty dictionary (not used)` — an outdated copy, since `args` is clearly used for `flight_number`, `aircraft_type`, `gate_id`, and `wheels_chocks_readiness_status` fallback. Identical stale docstring seen in other operators.

#### Installation logic

`wheels_chocks_installation_status` is set to `'installed'` when (case-insensitive):

```
('ready' in wheels_chocks_readiness_status AND 'not' not in wheels_chocks_readiness_status)
OR 'available' in wheels_chocks_readiness_status
```

> Note: This network uses `'not' not in` as the exclusion guard rather than `'no' not in` (used in the GPU and ACU connect networks). This is a safer guard — it correctly excludes `"not ready"` without the false-positive risk that `'no' not in` would have for strings like `"unknown"`.

> Note: The `'available' in` OR branch still accepts `"not available"` since `'available'` is a substring. Use exact matching for robustness.

#### Default `'pending'` initialization (NameError prevention)

```python
wheels_chocks_installation_status = 'pending'   # initialized before the if block
...
if (readiness condition):
    wheels_chocks_installation_status = 'installed'
    ...
return wheels_chocks_installation_status
```

The Python code initializes `wheels_chocks_installation_status = 'pending'` at the start of `invoke()` (before the readiness check), so the return statement is always safe. This differs from the `NameError`-prone pattern in `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect`, where the variable is only assigned inside the conditional block.

#### Output

- Writes `wheels_chocks_installation_status = 'installed'` into `sly_data` on success
- Returns `wheels_chocks_installation_status` (`'installed'` on success, `'pending'` on failed readiness)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt` on success

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_wheels_chocks_install.aircraft_ground_wheels_chocks_install.TrackerAPI`

Standard sly_data-first implementation. Called in step 4 to read missing prerequisite statuses, and again in step 7 after the operator to persist all status fields.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

**Tracked fields (`FLIGHT_TURNAROUND_TRACKED_FIELDS`):**
`aircraft_type`, `engines_stop_status`, `flight_number`, `flight_status`, `gate_id`, `wheels_chocks_readiness_status`, `wheels_chocks_installation_status`

**Return fields (`FLIGHT_TURNAROUND_RETURN_FIELDS`):**
`engines_stop_status`, `flight_status`, `wheels_chocks_readiness_status`, `wheels_chocks_installation_status`

> Note: Both `wheels_chocks_readiness_status` and `wheels_chocks_installation_status` are tracked and returned — consistent with the HOCON sly_data allow blocks and the operator's required inputs.

> Note: The HOCON TrackerAPI `function.parameters` schema also declares `jetbridge_connection_status` and `door_opening_status` as accepted properties (with `"required": []`), even though those fields are not in the Python `FLIGHT_TURNAROUND_TRACKED_FIELDS` and will not be persisted by this TrackerAPI instance.

---

## 6. External Tool Dependencies

| Tool path                                                | Purpose                                    | When called                                           |
|----------------------------------------------------------|--------------------------------------------|-------------------------------------------------------|
| `/AirlineTurnaround/aircraft_ground_wheels_chocks_setup` | Verify wheels chocks readiness at the gate | Step 2 — before any safety-state check; unconditional |

---

## 7. Implementation Notes

The Python file `aircraft_ground_wheels_chocks_install.py` contains only active code — there is no commented-out `wheels_chocks_setup` class in the current implementation. The readiness check is fully delegated to the external `aircraft_ground_wheels_chocks_setup` network, which lives in its own HOCON (`aircraft_ground_wheels_chocks_setup.hocon`) and Python file.

The HOCON file's `tools` list for `aircraft_ground_wheels_chocks_install_agent` contains only the three active down-chain references: `wheels_chocks_operator`, `/AirlineTurnaround/aircraft_ground_wheels_chocks_setup`, and `TrackerAPI`.

---

## 8. Sample Queries

```
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The engines are stopped and wheels chocks are ready. Install the wheels chocks."
```

---

## 9. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. The engines are stopped and wheels chocks are ready. Install the wheels chocks."

**Execution steps:**

1. `/AirlineTurnaround/aircraft_ground_wheels_chocks_setup` called (step 2) — returns `wheels_chocks_readiness_status=ready`
2. Readiness confirmed ✅
3. Prerequisites read: `flight_status=on blocks`, `engines_stop_status=stopped`
4. All three prerequisites met ✅ (step 5 check passes)
5. `wheels_chocks_operator` called — returns `wheels_chocks_installation_status=installed`
6. `TrackerAPI` called (step 7) — persists status fields
7. Summary returned

**Output:**

```
*********************************************
* Summary of aircraft wheels chocks install *
*********************************************
** flight status **:                          on blocks
** engines stop status **:                    stopped
** wheels chocks installation status **:      installed
** wheels chocks readiness status **:         ready
```

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "engines_stop_status": "stopped",
  "wheels_chocks_readiness_status": "ready",
  "wheels_chocks_installation_status": "installed"
}
```

---

## 10. Known Issues and Maintenance Notes

| Issue                                                | Location                                                    |   Severity   | Notes                                                                                                                                                |
|------------------------------------------------------|-------------------------------------------------------------|:------------:|------------------------------------------------------------------------------------------------------------------------------------------------------|
| `'available' in` OR branch accepts `"not available"` | `aircraft_ground_wheels_chocks_install.py` line 119         |    Medium    | `'available' in "not available"` is `True`. Use exact matching: `wheels_chocks_readiness_status.strip().lower() in ('ready', 'yes', 'available')`.   |
| HOCON `required` vs. Python runtime requirements     | `aircraft_ground_wheels_chocks_install.hocon` line 248      |     Low      | The operator HOCON declares only `["aircraft_type", "gate_id"]` as required, but the Python also enforces `flight_number` and readiness at runtime.  |

---

## 11. Relationship to Other Networks

This network completes the trio of readiness-gated installation/connection networks:

| Aspect                               | `aircraft_ground_acu_connect`           | `aircraft_ground_gpu_connect`           | `aircraft_ground_wheels_chocks_install`             |
|--------------------------------------|-----------------------------------------|-----------------------------------------|-----------------------------------------------------|
| Unit installed/connected             | ACU                                     | GPU                                     | Wheels chocks                                       |
| Setup network called                 | `aircraft_ground_acu_setup`             | `aircraft_ground_gpu_setup`             | `aircraft_ground_wheels_chocks_setup`               |
| Operator checks                      | readiness only                          | readiness only                          | readiness only                                      |
| Output status                        | `acu_connection_status` = `'connected'` | `gpu_connection_status` = `'connected'` | `wheels_chocks_installation_status` = `'installed'` |
| `NameError` bug                      | Yes                                     | Yes                                     | **No** (initialized to `'pending'`)                 |
| Readiness exclusion guard            | `'no' not in`                           | `'no' not in`                           | **`'not' not in`** (safer)                          |

The `aircraft_ground_wheels_chocks_setup` external network referenced here is also the dependency called by `aircraft_ground_readiness` (checking wheels chocks readiness as part of the combined ground services readiness report).

---

## 12. Extensibility Guidance

- Replace the `'available' in` OR branch with exact matching to avoid false positives on `"not available"`
- Align the HOCON `required` list for `wheels_chocks_operator` with the Python runtime requirements (add `flight_number` and `wheels_chocks_readiness_status`)
- Propagate the `'pending'` default-initialization pattern back to the ACU and GPU connect operators to fix their `NameError` bug

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
