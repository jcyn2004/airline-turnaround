# Aircraft Ground Wheelchocks Install
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_wheelchocks_Install.hocon` *(note mixed-case filename)*
> **Implementation file:** `aircraft_ground_wheelchocks_install.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Install wheel chocks on an aircraft at the gate during turnaround, after first verifying wheelchocks readiness via a dedicated setup network, then confirming the aircraft is on blocks and engines are stopped.

---

## 1. Overview

`aircraft_ground_wheelchocks_install` is the wheel chocks counterpart to `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect` in the **AirlineTurnaround** agentic system. All three networks share the same architectural pattern: a readiness gate checked via an external setup network, followed by safety-state prerequisite enforcement, before the actual installation/connection operator is called.

The network combines:

- An LLM-based orchestration agent (`wheelchocks_agent`) that interprets intent and drives the workflow
- One coded execution tool (`wheelchocks_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- One external tool reference (`/AirlineTurnaround/aircraft_ground_wheelchocks_setup`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network is also the **provider of the `aircraft_ground_wheelchocks_setup` external dependency** referenced by `aircraft_ground_readiness` — confirming that the setup network exists as a separate deployed unit, while this install network handles the actual installation action.

A commented-out `wheelchocks_setup` class in the Python file represents the original inline readiness-check implementation, now superseded by the external `aircraft_ground_wheelchocks_setup` network. A commented line in the HOCON (line 210) shows that `aircraft_engines_stop` and `aircraft_chocks_install` were considered as tools and subsequently removed.

---

## 2. Repository Structure

```
aircraft_ground_wheelchocks_Install.hocon   # Agent network configuration (mixed-case filename)
aircraft_ground_wheelchocks_install.py      # Coded tool implementations (wheelchocks_operator, TrackerAPI)
registries/aaosa_basic.hocon                # Shared registry (/AirlineTurnaround/aircraft_ground_wheelchocks_setup)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
wheelchocks_agent  (LLM Orchestrator)
   │
   ├── /AirlineTurnaround/aircraft_ground_wheelchocks_setup  (External tool: verify readiness — called FIRST)
   │
   ├── wheelchocks_operator                                   (Coded tool: install wheel chocks)
   │
   └── TrackerAPI                                             (Coded tool: read/write turnaround state via sly_data)
```

### Design principles

- **Readiness gate — first:** Before any safety-state check, the orchestrator calls `aircraft_ground_wheelchocks_setup` to confirm `wheelchocks_readiness_status = 'ready'` or `'yes'`. If not confirmed, the workflow stops immediately.
- **Three-prerequisite enforcement:** After readiness is confirmed: `flight_status = on blocks`, `engines_stop_status = stopped`. All three must be satisfied.
- **Operator checks readiness only:** `wheelchocks_operator` validates only `wheelchocks_readiness_status` — safety prerequisites are enforced by the orchestrator.
- **sly_data-first for readiness:** `wheelchocks_operator` reads `wheelchocks_readiness_status` from `sly_data` first, then falls back to `args`.
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

> Note: The HOCON `llm_config` line includes a comment with previously tested model alternatives, consistent with the other ground service networks.

---

## 5. Components

### 5.1 wheelchocks_agent (LLM Orchestrator)

The entry-point agent. It first verifies wheelchocks readiness, then checks the two safety prerequisites, calls the operator, persists the result, and returns the summary.

#### Input parameters

| Parameter | Type | Required | Description |
|---|---|:---:|---|
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `gate_id` | string | ✅ | Gate where the aircraft is parked |
| `flight_status` | string | ❌ | Expected: `on blocks` |
| `engines_stop_status` | string | ❌ | Expected: `stopped` |
| `wheelchocks_installation_status` | string | ❌ | Current or previous installation status |
| `wheelchocks_readiness_status` | string | ❌ | Readiness from setup network |

> Note: `flight_number` is absent from the HOCON agent parameter schema (`properties` and `required`), identical to `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect`. It flows through sly_data but is not declared as an agent input.

#### Orchestration flow

The instructions use older numbered-prose style, mirroring the ACU and GPU connect networks:

1. Read the inquiry — confirm it is about wheelchocks installation. If not → stop.
2. Call `/AirlineTurnaround/aircraft_ground_wheelchocks_setup` with `aircraft_type` and `gate_id`. Store `wheelchocks_readiness_status`. If not `ready` or `yes` → **stop and report not ready.**
3. With readiness confirmed, read `flight_status` and `engines_stop_status` from the inquiry.
4. If either prerequisite is unmet → call `TrackerAPI`. Store `engines_stop_status` and `flight_status`.
5. If still any prerequisite unmet → stop and report current statuses.
6. All three prerequisites confirmed → call `wheelchocks_operator`. Save as `wheelchocks_installation_status`. Report.
7. Call `TrackerAPI` — store `engines_stop_status`, `wheels_chucks_installation_status` (typo), `wheelchocks_readiness_status`, `wheelchocks_installation_status`.
8. Return summary.

> Note: Step 7 stores `wheels_chucks_installation_status` (double typo: "chucks" and `wheels_` prefix). The Python tracked fields use `wheelchocks_installation_status` (no `wheels_` prefix, no `chucks`). These are different sly_data keys.

> Note: The summary template in step 8 shows `wheels_chocks_installation_status` (with `wheels_` prefix and correct `chocks` spelling) — yet another variant, making three different spellings of the same concept across this network's instructions alone.

#### sly_data contract

| Direction | Parameters |
|---|---|
| **To upstream** | `wheelchocks_installation_status`, `wheelchocks_readiness_status` |
| **To downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheelchocks_installation_status`, `wheelchocks_readiness_status` |
| **From upstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheelchocks_installation_status`, `wheelchocks_readiness_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `wheelchocks_installation_status`, `wheelchocks_readiness_status` |

> Note: Both `wheelchocks_installation_status` and `wheelchocks_readiness_status` propagate upstream — matching the pattern of `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect`.

#### Down-chain tools

```
["wheelchocks_operator", "/AirlineTurnaround/aircraft_ground_wheelchocks_setup", "TrackerAPI"]
```

> Note: Line 210 in the HOCON contains a commented-out alternative tools line:
> `# "/AirlineTurnaround/aircraft_engines_stop","/AirlineTurnaround/aircraft_chocks_install",`
> This shows the earlier design considered delegating to those networks for prerequisite resolution. The current design checks prerequisites internally and stops on failure rather than delegating.

---

### 5.2 wheelchocks_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_wheelchocks_install.aircraft_ground_wheelchocks_install.wheelchocks_operator`

Performs the wheelchocks installation. It validates `aircraft_type` and `gate_id`, then checks `wheelchocks_readiness_status` only. If readiness is confirmed, sets `wheelchocks_installation_status = 'installed'`, writes to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

#### Input parameters

| Parameter | Type | Required | Source priority |
|---|---|:---:|---|
| `aircraft_type` | string | ✅ | `args` → `sly_data` |
| `gate_id` | string | ✅ | `args` → `sly_data` |
| `wheelchocks_readiness_status` | string | ✅ | **`sly_data` → `args`** (sly_data-first) |

> Note: The operator's docstring says `args: an empty dictionary (not used)` — an outdated copy, since `args` is clearly used for `aircraft_type`, `gate_id`, and `wheelchocks_readiness_status` fallback. Identical stale docstring seen in other operators.

> Note: Lines 179–187 contain a commented-out `args`-first version of the `wheelchocks_readiness_status` lookup. The active version on lines 189–198 uses `sly_data`-first. The commented block is the superseded implementation.

#### Installation logic

`wheelchocks_installation_status` is set to `'installed'` when (case-insensitive):

```
('ready' in wheelchocks_readiness_status AND 'not' not in wheelchocks_readiness_status)
OR 'available' in wheelchocks_readiness_status
```

> Note: This network uses `'not' not in` as the exclusion guard rather than `'no' not in` (used in the GPU and ACU connect networks). This is a safer guard — it correctly excludes `"not ready"` without the false-positive risk that `'no' not in` would have for strings like `"unknown"`.

> Note: The `'available' in` OR branch still accepts `"not available"` since `'available'` is a substring. Use exact matching for robustness.

#### Critical code bug — `NameError` on failed readiness check (line 224)

```python
if (readiness condition):
    wheelchocks_installation_status = 'installed'   # only assigned here
    ...

return wheelchocks_installation_status   # NameError if condition was False
```

If `wheelchocks_readiness_status` fails the condition check, `wheelchocks_installation_status` is never assigned and `return wheelchocks_installation_status` raises `NameError`. The same bug exists in `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect`. Fix: add `wheelchocks_installation_status = 'pending'` before the `if` block.

#### Output

- Writes `wheelchocks_installation_status = 'installed'` into `sly_data` on success
- Returns `wheelchocks_installation_status` (`'installed'`) — or raises `NameError` on failure
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_wheelchocks_install.aircraft_ground_wheelchocks_install.TrackerAPI`

Standard sly_data-first implementation. Called in step 4 to read missing prerequisite statuses, and again in step 7 after the operator to persist all status fields.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

**Tracked fields:**
`aircraft_type`, `engines_stop_status`, `flight_number`, `flight_status`, `gate_id`, `wheelchocks_installation_status`

**Return fields:**
`engines_stop_status`, `flight_status`, `wheelchocks_installation_status`

> Note: `wheelchocks_readiness_status` is **not tracked** by Python `FLIGHT_TURNAROUND_TRACKED_FIELDS`, despite appearing in the HOCON sly_data allow blocks, the operator's required inputs, and the HOCON TrackerAPI schema. TrackerAPI will not persist or return it. If the orchestrator calls TrackerAPI to log `wheelchocks_readiness_status` (step 7), that value will be silently dropped.

> Note: The HOCON TrackerAPI definition correctly includes `"required": []`.

> Note: The HOCON TrackerAPI description references `"wheels_chucks_installation_status"` (double typo) — stale copy-paste artifact, not tracked.

---

## 6. External Tool Dependencies

| Tool path | Purpose | When called |
|---|---|---|
| `/AirlineTurnaround/aircraft_ground_wheelchocks_setup` | Verify wheelchocks readiness at the gate | Step 2 — before any safety-state check; unconditional |

---

## 7. Commented-Out Code — `wheelchocks_setup` Class

Lines 30–120 contain a fully commented-out `wheelchocks_setup` class — the original inline readiness implementation. It reads `wheelchocks_readiness` from `gate_equipments_base.csv` and translates `'yes'` → `'ready'`. This is the code that would power `aircraft_ground_wheelchocks_setup` (the external setup network).

Notable: the debug print banners inside the commented block say `"ACU READINESS STATUS 1"` and `"ACU READINESS STATUS 2"` (lines 103, 106) — copy-paste artifacts from `aircraft_ground_acu_connect.py`. The operational logic is correct (reads `wheelchocks_readiness` column) but the print labels are wrong.

Also notable: unlike `aircraft_ground_acu_setup`'s `acu_setup`, the commented-out `wheelchocks_setup` here does **not** translate `'no'` → `'not ready'` — only `'yes'` → `'ready'` is present (line 111–112). This matches the gap previously noted in the commented-out `gpu_setup` in `aircraft_ground_gpu_connect.py`.

---

## 8. Sample Queries

```
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The engines are stopped and wheelchocks are ready. Install the wheelchocks."
```

---

## 9. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. The engines are stopped and wheelchocks are ready. Install the wheelchocks."

**Execution steps:**

1. `/AirlineTurnaround/aircraft_ground_wheelchocks_setup` called (step 2) — returns `wheelchocks_readiness_status=ready`
2. Readiness confirmed ✅
3. Prerequisites read: `flight_status=on blocks`, `engines_stop_status=stopped`
4. All three prerequisites met ✅ (step 5 check passes)
5. `wheelchocks_operator` called — returns `wheelchocks_installation_status=installed`
6. `TrackerAPI` called (step 7) — persists status fields
7. Summary returned

**Output:**

```
*******************************************
* Summary of aircraft wheelchocks install *
*******************************************
** flight status **:                          on blocks
** engines stop status **:                    stopped
** wheels chocks installation status **:      installed
** wheelchocks readiness status **:           ready
```

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "engines_stop_status": "stopped",
  "wheelchocks_readiness_status": "ready",
  "wheelchocks_installation_status": "installed"
}
```

---

## 10. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| **`NameError` on failed readiness check** | `aircraft_ground_wheelchocks_install.py` line 224 | **Critical** | `wheelchocks_installation_status` only assigned inside the `if` block. `return wheelchocks_installation_status` raises `NameError` if condition fails. Fix: add `wheelchocks_installation_status = 'pending'` before the `if` block. |
| `wheelchocks_readiness_status` not in Python `FLIGHT_TURNAROUND_TRACKED_FIELDS` | `aircraft_ground_wheelchocks_install.py` lines 512–519 | **High** | Field is used by the operator, appears in sly_data allow blocks, and is in the HOCON TrackerAPI schema, but TrackerAPI will silently drop it. Add to tracked fields. |
| Three different spellings of installation field name | `aircraft_ground_wheelchocks_Install.hocon` steps 7 and 8 | Medium | Step 7 stores `wheels_chucks_installation_status` (wheels_ prefix + chucks). Step 8 summary shows `wheels_chocks_installation_status` (wheels_ prefix + chocks). Python tracked fields use `wheelchocks_installation_status` (no wheels_ prefix). All three are different sly_data keys. |
| `'available' in` OR branch accepts `"not available"` | `aircraft_ground_wheelchocks_install.py` line 206 | Medium | `'available' in "not available"` is `True`. Use exact matching: `wheelchocks_readiness_status.strip().lower() in ('ready', 'yes', 'available')`. |
| Commented-out `wheelchocks_setup` banner says `"ACU READINESS STATUS"` | `aircraft_ground_wheelchocks_install.py` lines 103, 106 | Low | Copy-paste from `aircraft_ground_acu_connect.py`. Should read `"WHEELCHOCKS READINESS STATUS"`. |
| Commented-out `wheelchocks_setup` missing `'no'` → `'not ready'` translation | `aircraft_ground_wheelchocks_install.py` line 111 | Low | Only `'yes'` → `'ready'` is present. Consistent gap with the commented `gpu_setup` in `aircraft_ground_gpu_connect.py`. |
| HOCON filename uses mixed case | File: `aircraft_ground_wheelchocks_Install.hocon` | Low | Capital `I` in `Install`. All other HOCON files in the system use all-lowercase filenames. May cause case-sensitive import failures on Linux. |
| `flight_number` absent from agent parameter schema | `aircraft_ground_wheelchocks_Install.hocon` | Low | Same gap as `aircraft_ground_acu_connect` and `aircraft_ground_gpu_connect`. |
| Commented-out args-first lookup for `wheelchocks_readiness_status` | `aircraft_ground_wheelchocks_install.py` lines 179–187 | Low | Superseded implementation. Safe to remove. |
| HOCON TrackerAPI description references stale fields | `aircraft_ground_wheelchocks_Install.hocon` line 255 | Low | `"wheels_chucks_installation_status"` — double typo, not tracked. |

---

## 11. Relationship to Other Networks

This network completes the trio of readiness-gated installation/connection networks:

| Aspect | `aircraft_ground_acu_connect` | `aircraft_ground_gpu_connect` | `aircraft_ground_wheelchocks_install` |
|---|---|---|---|
| Unit installed/connected | ACU | GPU | Wheel chocks |
| Setup network called | `aircraft_ground_acu_setup` | `aircraft_ground_gpu_setup` | `aircraft_ground_wheelchocks_setup` |
| Operator checks | readiness only | readiness only | readiness only |
| Output status | `acu_connection_status` = `'connected'` | `gpu_connection_status` = `'connected'` | `wheelchocks_installation_status` = `'installed'` |
| `NameError` bug | Yes | Yes | Yes |
| Readiness exclusion guard | `'no' not in` | `'no' not in` | **`'not' not in`** (safer) |
| Commented-out setup class | Yes (`acu_setup`) | Yes (`gpu_setup`) | Yes (`wheelchocks_setup`) |
| Setup `'no'`→`'not ready'` in inline | Yes | No (omitted) | No (omitted) |

The `aircraft_ground_wheelchocks_setup` external network referenced here is also the dependency called by `aircraft_ground_readiness` in Step 4 (checking wheelchocks readiness as part of the combined ground services readiness report).

---

## 12. Extensibility Guidance

- Fix the `NameError` immediately: `wheelchocks_installation_status = 'pending'` before the `if` block
- Add `wheelchocks_readiness_status` to `FLIGHT_TURNAROUND_TRACKED_FIELDS` and `FLIGHT_TURNAROUND_RETURN_FIELDS`
- Standardize the installation field name to `wheelchocks_installation_status` throughout instructions, summary template, and Python tracked fields — eliminating the three-spelling inconsistency
- Replace the `'available' in` OR branch with exact matching
- Rename the HOCON file to `aircraft_ground_wheelchocks_install.hocon` (all lowercase) to prevent case-sensitivity issues on Linux
- Remove the commented-out `wheelchocks_setup` class and the commented-out args-first lookup

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
