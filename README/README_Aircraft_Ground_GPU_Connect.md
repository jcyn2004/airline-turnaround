# Aircraft Ground GPU Connect
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_gpu_connect.hocon`
> **Implementation file:** `aircraft_ground_gpu_connect.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Connect a Ground Power Unit (GPU) to an aircraft at the gate during turnaround, after first verifying GPU readiness via a dedicated setup network, then confirming the aircraft is on blocks, engines are stopped, and wheel chocks are installed.

---

## 1. Overview

`aircraft_ground_gpu_connect` is the GPU counterpart to `aircraft_ground_acu_connect` in the **AirlineTurnaround** agentic system. The two networks are structurally identical, differing only in which ground unit is connected (GPU vs. ACU) and which setup network is called to verify readiness.

The network combines:

- An LLM-based orchestration agent (`gpu_agent`) that interprets intent and drives the workflow
- One coded execution tool (`gpu_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- One external tool reference (`/AirlineTurnaround/aircraft_ground_gpu_setup`) resolved from the shared registry `registries/aaosa_basic.hocon`

A commented-out `gpu_setup` class in the Python file represents the original inline GPU readiness-checking implementation (reading `ground_power_unit_readiness` from `gate_equipments_base.csv`), now superseded by the external network delegation.

---

## 2. Repository Structure

```
aircraft_ground_gpu_connect.hocon    # Agent network configuration
aircraft_ground_gpu_connect.py       # Coded tool implementations (gpu_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (/AirlineTurnaround/aircraft_ground_gpu_setup)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
gpu_agent  (LLM Orchestrator)
   │
   ├── /AirlineTurnaround/aircraft_ground_gpu_setup   (External tool: verify GPU readiness — called FIRST)
   │
   ├── gpu_operator                                    (Coded tool: connect GPU)
   │
   └── TrackerAPI                                      (Coded tool: read/write turnaround state via sly_data)
```

### Design principles

- **GPU readiness gate — first:** Before any safety-state check, the orchestrator calls `aircraft_ground_gpu_setup` to confirm `gpu_readiness_status = 'ready'` or `'yes'`. If not confirmed, the workflow stops immediately.
- **Four-prerequisite enforcement:** Only after GPU readiness is confirmed does the orchestrator check: `flight_status = on blocks`, `engines_stop_status = stopped`, `wheels_chocks_installation_status = installed`. All four must be satisfied.
- **Operator checks readiness only:** `gpu_operator` only validates `gpu_readiness_status` — the safety prerequisites are enforced exclusively by the orchestrator, mirroring the pattern in `aircraft_ground_acu_connect`.
- **sly_data-first for readiness:** `gpu_operator` reads `gpu_readiness_status` from `sly_data` first, then falls back to `args`.

---

## 4. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

> Note: The HOCON `llm_config` line includes a comment with previously tested alternatives (`gpt-4o`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`), consistent with the ACU network pair.

---

## 5. Components

### 5.1 gpu_agent (LLM Orchestrator)

The entry-point agent. It first verifies GPU readiness via an external network, then checks the three safety prerequisites, calls the operator, persists the result, and returns the summary.

#### Input parameters

| Parameter                           | Type   | Required  | Description                                                        |
|-------------------------------------|--------|:---------:|--------------------------------------------------------------------|
| `aircraft_type`                     | string |    ✅     | Aircraft model/type                                                |
| `gate_id`                           | string |    ✅     | Gate where the aircraft is parked                                  |
| `flight_status`                     | string |    ❌     | Expected: `on blocks`                                              |
| `engines_stop_status`               | string |    ❌     | Expected: `stopped`                                                |
| `wheels_chocks_installation_status` | string |    ❌     | Expected: `installed` (no underscore between "wheel" and "chocks") |
| `gpu_connection_status`             | string |    ❌     | Current or previous GPU connection status                          |
| `gpu_readiness_status`              | string |    ❌     | GPU readiness from setup network                                   |

> Note: `flight_number` is absent from the HOCON agent parameter schema, identical to `aircraft_ground_acu_connect`. It flows through sly_data but is not declared as an agent input.

#### Orchestration flow

The instructions use older numbered-prose style (not `CRITICAL: sequential executor` / `STEP`). The flow is a line-for-line mirror of `aircraft_ground_acu_connect`:

1. Read the inquiry — confirm it is about GPU connection. If not → stop.
2. Call `/AirlineTurnaround/aircraft_ground_gpu_setup` with `aircraft_type` and `gate_id`. Store `gpu_readiness_status`. If not `ready` or `yes` → **stop and report GPU not ready.**
3. With GPU readiness confirmed, read `flight_status`, `engines_stop_status`, `wheels_chocks_installation_status` from the inquiry.
4. If any safety prerequisite is unmet → call `TrackerAPI`. Store `engines_stop_status`, `wheels_chucks_installation_status` (typo), `flight_status`.
5. If still any prerequisite unmet OR `gpu_readiness_status` not `ready`/`yes` → stop and report current statuses.
6. All four prerequisites confirmed → call `gpu_operator`. Wait. Save result as `gpu_connection_status`. Report.
7. Call `TrackerAPI` — store all four status fields.
8. Return summary.

> Note: Step 6a says "call your tools to connect GPU" without naming `gpu_operator` explicitly.

> Note: Steps 4 and 7 both reference `wheels_chucks_installation_status` (double typo: "chucks" and no underscore). The Python implementation correctly uses `wheels_chocks_installation_status`.

#### sly_data contract

| Direction           | Parameters                                                                                                                                                              |
|---------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**     | `gpu_connection_status`, `gpu_readiness_status`                                                                                                                         |
| **To downstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheels_chocks_installation_status`, `gpu_connection_status`, `gpu_readiness_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheels_chocks_installation_status`, `gpu_connection_status`, `gpu_readiness_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheels_chocks_installation_status`, `gpu_connection_status`, `gpu_readiness_status` |

> Note: The sly_data blocks use `wheels_chocks_installation_status` (no underscore). The Python `FLIGHT_TURNAROUND_TRACKED_FIELDS` uses `wheels_chocks_installation_status` (with underscore). These are different field names and will not resolve to the same sly_data key — the same mismatch documented in `aircraft_ground_acu_connect`.

> Note: Both `gpu_connection_status` and `gpu_readiness_status` propagate upstream — the same broader outbound pattern as `aircraft_ground_acu_connect`.

#### Down-chain tools

```
["gpu_operator", "/AirlineTurnaround/aircraft_ground_gpu_setup", "TrackerAPI"]
```

---

### 5.2 gpu_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_gpu_connect.aircraft_ground_gpu_connect.gpu_operator`

Connects the GPU. It validates `aircraft_type` and `gate_id`, then checks `gpu_readiness_status` only. If readiness is confirmed, sets `gpu_connection_status = 'connected'`, writes to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

#### Input parameters

| Parameter              | Type   | Required  | Source priority                          |
|------------------------|--------|:---------:|------------------------------------------|
| `aircraft_type`        | string |    ✅     | `args` → `sly_data`                      |
| `gate_id`              | string |    ✅     | `args` → `sly_data`                      |
| `gpu_readiness_status` | string |    ✅     | **`sly_data` → `args`** (sly_data-first) |

#### Connection logic

`gpu_connection_status` is set to `'connected'` when (case-insensitive):

```
('ready' in gpu_readiness_status AND 'no' not in gpu_readiness_status)
OR 'available' in gpu_readiness_status
```

> Note: This condition is identical to `aircraft_ground_acu_connect`'s `acu_operator`. Both share the same `'no' not in` guard risk — any string containing the substring `'no'` (e.g. `'unknown'`) would be rejected. The `'available' in` OR branch also accepts `'not available'` since `'available'` is a substring of both.

#### Comparison with `aircraft_ground_acu_connect`'s `acu_operator`

The `gpu_operator` in this network uses the same compound condition as `aircraft_ground_acu_connect`'s `acu_operator` (including the `'no' not in` guard), while the standalone `aircraft_ground_acu_setup`'s `acu_operator` (inactive class) uses a simpler `('ready' in ...) | ('available' in ...)` without the guard. This inconsistency across the three operator variants means the same readiness string may be accepted by one and rejected by another depending on which network is involved.

#### Critical code bug — `NameError` on failed readiness check (line 215)

```python
if (readiness condition):
    gpu_connection_status = 'connected'   # only assigned here
    message = f"..."
    ...

return gpu_connection_status   # NameError if condition was False
```

If `gpu_readiness_status` fails the condition, `gpu_connection_status` is never assigned and `return gpu_connection_status` raises `NameError`. The operator has no fallback return path.

Line 141 shows the fix was intentionally disabled: `# acu_connection_status = 'pending'` — notably still saying `acu_connection_status` (a copy-paste residue from the ACU counterpart) rather than `gpu_connection_status`. This confirms the class was derived from the ACU operator without fully renaming all references.

#### Output

- Writes `gpu_connection_status = 'connected'` into `sly_data` on success
- Returns `gpu_connection_status` (`'connected'`) — or raises `NameError` on failure
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_gpu_connect.aircraft_ground_gpu_connect.TrackerAPI`

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
`aircraft_type`, `gpu_connection_status`, `gpu_readiness_status`, `engines_stop_status`, `flight_number`, `flight_status`, `gate_id`, `wheels_chocks_installation_status`

**Return fields:**
`gpu_connection_status`, `gpu_readiness_status`, `engines_stop_status`, `flight_status`, `wheels_chocks_installation_status`

> Note: The Python tracked/return fields use `wheels_chocks_installation_status` (with underscore). The HOCON sly_data blocks and TrackerAPI schema use `wheels_chocks_installation_status` (no underscore). These are different sly_data keys — the same field name mismatch documented in `aircraft_ground_acu_connect`.

> Note: The HOCON `TrackerAPI` description references `"wheels_chucks_installation_status"` (double typo). Neither that field nor the correct spelling is returned by TrackerAPI in this network (only `wheels_chocks_installation_status` is in `RETURN_FIELDS`, and the HOCON schema parameter is `wheels_chocks_installation_status`).

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

| Tool path                                      | Purpose                                    | When called                                                   |
|------------------------------------------------|--------------------------------------------|---------------------------------------------------------------|
| `/AirlineTurnaround/aircraft_ground_gpu_setup` | Verify GPU readiness at the specified gate | Step 2 — before any safety-state check; call is unconditional |

---

## 7. Commented-Out Code — `gpu_setup` Class

Lines 30–121 of the Python file contain a fully commented-out `gpu_setup` class that was the original inline GPU readiness implementation. It is a direct mirror of the commented-out `acu_setup` in `aircraft_ground_acu_connect.py`, differing only in:

- Column read: `ground_power_unit_readiness` (vs. `air_conditioning_unit_readiness` for ACU)
- Print banner text: `GPU READINESS` (vs. `ACU READINESS`)
- Translated status: `'yes'` → `'ready'` (same), but **no `'no'` → `'not ready'` translation** (ACU setup translated both; GPU setup only translated `'yes'`)

This logic has been extracted into the external `aircraft_ground_gpu_setup` network. The commented code can be safely removed from production.

---

## 8. Sample Queries

```
# All prerequisites already met
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The engines are stopped and wheels chocks have been installed and the GPU is ready.
Connect the GPU."
```

---

## 9. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. The engines are stopped and wheels chocks have been installed and the GPU is ready. Connect the GPU."

**Execution steps:**

1. `/AirlineTurnaround/aircraft_ground_gpu_setup` called (step 2) — returns `gpu_readiness_status=ready`
2. GPU readiness confirmed ✅
3. Prerequisites read from inquiry: `flight_status=on blocks`, `engines_stop_status=stopped`, `wheels_chocks_installation_status=installed`
4. All four prerequisites met ✅ (step 5 check passes)
5. `gpu_operator` called — returns `gpu_connection_status=connected`
6. `TrackerAPI` called (step 7) — persists all status fields
7. Summary returned

**Output:**

```
***********************************
* Summary of aircraft gpu connect *
***********************************
** flight status **:                          on blocks
** engines stop status **:                    stopped
** wheels chocks installation status **:      installed
** gpu readiness status **:                   ready
** gpu connection status **:                  connected
```

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "engines_stop_status": "stopped",
  "wheels_chocks_installation_status": "installed",
  "gpu_readiness_status": "ready",
  "gpu_connection_status": "connected"
}
```

---

## 10. Known Issues and Maintenance Notes

| Issue         | Location |   Severity   | Notes  |
|---------------|----------|:------------:|--------|
|               |          |    Medium    |        |

---

## 11. Relationship to Other Networks

This network is the GPU counterpart to `aircraft_ground_acu_connect`, and follows the same dependency pattern:

```
aircraft_ground_gpu_setup     ──→  verifies GPU readiness (reads gate_equipments_base.csv)
aircraft_ground_gpu_connect   ──→  connects GPU (calls gpu_setup network first)
```

| Aspect                            | `aircraft_ground_acu_connect`                  | `aircraft_ground_gpu_connect`                  |           |
|-----------------------------------|------------------------------------------------|------------------------------------------------|-----------|
| Unit connected                    | ACU (Air Conditioning)                         | GPU (Ground Power)                             |           |
| Setup network called              | `/AirlineTurnaround/aircraft_ground_acu_setup` | `/AirlineTurnaround/aircraft_ground_gpu_setup` |           |
| CSV column read (in setup)        | `air_conditioning_unit_readiness`              | `ground_power_unit_readiness`                  |           |
| Operator readiness condition      | `'ready' ... 'no' not in ... \                 | 'available'`                                   | identical |
| `NameError` bug                   | Yes                                            | Yes                                            |           |
| Residual ACU reference in comment | N/A                                            | Yes (line 141: `acu_connection_status`)        |           |
| `'no'` → `'not ready'` in setup   | Yes (acu_setup)                                | No (commented-out gpu_setup omits it)          |           |

---

## 12. Extensibility Guidance

- Replace the compound readiness condition with exact-value matching: `gpu_readiness_status.strip().lower() in ('ready', 'yes', 'available')`
- Upgrade to the `CRITICAL: sequential executor` / `STEP` pattern for more reliable LLM execution
- Standardize the readiness condition across all GPU/ACU operator variants for consistent behavior

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation electrical or safety-critical systems.
