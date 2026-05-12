# Aircraft Ground Wheelchocks Setup
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_wheelchocks_setup.hocon`
> **Implementation file:** `aircraft_ground_wheelchocks_setup.py`
> **Data file:** `aircraft_gate_selection/gate_equipments_base.csv` (shared with `aircraft_gate_selection`, `aircraft_ground_acu_setup`, `aircraft_ground_gpu_setup`)
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Verify wheel chocks readiness at an assigned gate for an incoming aircraft, by reading the `wheelchocks_readiness` column from the shared gate equipment inventory CSV. Returns `wheelchocks_readiness_status` to the caller.

---

## 1. Overview

`aircraft_ground_wheelchocks_setup` is the wheel chocks counterpart to `aircraft_ground_acu_setup` and `aircraft_ground_gpu_setup` — all three are **leaf service networks** that verify equipment readiness by reading from `gate_equipments_base.csv`. This network is called by:

- `aircraft_ground_wheelchocks_install` (step 2, before safety-state checks)
- `aircraft_ground_readiness` (step 4, as part of the combined readiness report)

The network combines:

- An LLM-based orchestration agent (`wheelchocks_agent`) that routes readiness vs. installation inquiries
- One active coded tool (`wheelchocks_setup`) that reads wheelchocks readiness from `gate_equipments_base.csv`
- A shared state manager (`TrackerAPI`) also implemented in Python
- One inactive coded class (`wheelchocks_operator`) present in the Python file but **not registered in the HOCON tools list**

Unlike `aircraft_ground_acu_setup` where the operator was commented out, and `aircraft_ground_gpu_setup` where it was also commented out, `wheelchocks_operator` here is **fully active Python code** — it just isn't wired up in the HOCON.

---

## 2. Repository Structure

```
aircraft_ground_wheelchocks_setup.hocon      # Agent network configuration
aircraft_ground_wheelchocks_setup.py         # Coded tool implementations (wheelchocks_setup, wheelchocks_operator [inactive], TrackerAPI)
coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv   # Shared equipment inventory (read-only)
registries/aaosa_basic.hocon                 # Shared registry (no external tools used)
```

---

## 3. System Architecture

```
aircraft_ground_wheelchocks_install   (Caller 1)
aircraft_ground_readiness             (Caller 2)
   │
   ▼
wheelchocks_agent  (LLM Orchestrator)
   │
   ├── wheelchocks_setup       (Coded tool: read wheelchocks readiness from gate_equipments_base.csv)
   │
   └── TrackerAPI              (Coded tool: read/write wheelchocks_readiness_status via sly_data)
```

### Design principles

- **Data-driven readiness check:** `wheelchocks_setup` reads the `wheelchocks_readiness` column from the shared gate CSV for the given `gate_id`, translating `'yes'` → `'ready'` and `'no'` → `'not ready'`.
- **Read-only CSV access:** `wheelchocks_setup` does not mutate the CSV.
- **Minimal scope:** 3-field TrackerAPI with tracked fields = return fields.
- **Leaf network:** No external tool dependencies.
- **Complete translations:** Both `'yes'` → `'ready'` and `'no'` → `'not ready'` are implemented — unlike the commented-out stubs in `aircraft_ground_gpu_connect.py` and `aircraft_ground_wheelchocks_install.py` which only translated `'yes'`.

---

## 4. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

> Note: The HOCON `llm_config` line includes a comment with previously tested model alternatives, consistent with the other ground service setup networks.

---

## 5. Components

### 5.1 wheelchocks_agent (LLM Orchestrator)

The entry-point agent. It determines whether the inquiry is about wheelchocks readiness or wheelchocks installation, then routes accordingly.

> Note: The instructions say "When user submit inquiry about GPU" (line 117) — a copy-paste from `aircraft_ground_gpu_setup`. Should read "about wheelchocks". This is a documentation-only error with no runtime impact.

#### Input parameters

| Parameter | Type | Required | Description |
|---|---|:---:|---|
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `gate_id` | string | ✅ | Gate where the aircraft is assigned |
| `wheelchocks_readiness_status` | string | ❌ | Current readiness status if already known |

#### Orchestration flow

The instructions mirror `aircraft_ground_acu_setup` and `aircraft_ground_gpu_setup` exactly in structure, with the same flow-logic ambiguity:

1. Read the inquiry — determine if it is about wheelchocks readiness or installation.
2. If neither → stop and report not relevant.
3. If about **wheelchocks readiness status** → call `wheelchocks_setup`. Store and report `wheelchocks_readiness_status`. **Stop.**
4. Return the wheelchocks connection status summary.

> Note: Step 3c says "stop process here", making step 4 (summary) unreachable on the standard path — the same ambiguity present in the ACU and GPU setup networks. The summary in step 4 would only display if the LLM does not follow the stop instruction.

> Note: The summary template in step 4 shows `wheels_chucks_readiness_status` (with `wheels_` prefix and "chucks" typo) — but the actual field name throughout the rest of the network is `wheelchocks_readiness_status`. This label mismatch means the summary will display the wrong placeholder.

#### sly_data contract

All four directions carry the same 3-field set — fully symmetric, matching `aircraft_ground_acu_setup` and `aircraft_ground_gpu_setup`:

| Direction | Parameters |
|---|---|
| **To upstream** | `aircraft_type`, `gate_id`, `wheelchocks_readiness_status` |
| **To downstream** | same 3 fields |
| **From upstream** | same 3 fields |
| **From downstream** | same 3 fields |

#### Down-chain tools

```
["wheelchocks_setup", "TrackerAPI"]
```

---

### 5.2 wheelchocks_setup (Coded Tool — Active)

**Class:** `AirlineTurnaround.aircraft_ground_wheelchocks_setup.aircraft_ground_wheelchocks_setup.wheelchocks_setup`

Reads wheelchocks readiness from `gate_equipments_base.csv`. Filters by `gate_id`, reads the `wheelchocks_readiness` column, applies both value translations, writes to `sly_data`, and returns.

#### Input parameters

| Parameter | Type | Required | Source priority |
|---|---|:---:|---|
| `aircraft_type` | string | ✅ | `args` → `sly_data` |
| `gate_id` | string | ✅ | `args` → `sly_data` |

#### Readiness lookup logic

1. Read `gate_equipments_base.csv` from:
   `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"`
2. Filter rows where `gate_id == gate_id` (no filter on `aircraft_type`)
3. Read `wheelchocks_readiness` from the first matching row
4. Translate:
   - `'yes'` → `'ready'`
   - `'no'` → `'not ready'`
   - Any other value → returned as-is
5. Write `wheelchocks_readiness_status` to `sly_data`
6. Return `wheelchocks_readiness_status`

> Note: Both `'yes'` → `'ready'` AND `'no'` → `'not ready'` translations are present (lines 111–115). This makes `wheelchocks_setup` the **most complete** of the three setup implementations — `aircraft_ground_acu_setup`'s `acu_setup` also has both, while `aircraft_ground_gpu_setup`'s `gpu_setup` only has `'yes'` → `'ready'`.

If no row matches `gate_id`, `wheelchocks_readiness_status.values[0]` (line 105) will raise `IndexError` — same risk as the ACU and GPU setup operators.

#### Print banner copy-paste artifacts

Lines 103 and 106 print `"ACU READINESS STATUS 1"` and `"ACU READINESS STATUS 2"` inside the `WHEELCHOCKS READINESS STATUS CHECK` block — identical to the same error in the commented-out `wheelchocks_setup` in `aircraft_ground_wheelchocks_install.py`. Should read `"WHEELCHOCKS READINESS STATUS 1/2"`.

#### Output

- Writes `wheelchocks_readiness_status` into `sly_data`
- Returns `wheelchocks_readiness_status` string (`'ready'`, `'not ready'`, or `'pending'`)
- `file_path_log` is defined on line 48 but **never used** — no log entry is written, consistent with `acu_setup` and `gpu_setup`

---

### 5.3 wheelchocks_operator (Coded Tool — Active Python, Not Registered)

**Class:** `AirlineTurnaround.aircraft_ground_wheelchocks_setup.aircraft_ground_wheelchocks_setup.wheelchocks_operator` *(not in HOCON tools list)*

A fully active (non-commented) wheelchocks installation operator is present in the Python file (lines 126–221) but **not listed in the HOCON tools array**. It is therefore unreachable at runtime from this network.

Unlike the inactive operators in `aircraft_ground_acu_setup` and `aircraft_ground_gpu_setup` (which were commented out), this class is **fully compiled and importable** — only its absence from the HOCON prevents it from being called.

#### Installation logic

The operator checks `flight_status` (not `wheelchocks_readiness_status`) as its installation condition:

```python
if gate_id and aircraft_type and "on" in flight_status and "blocks" in flight_status:
    wheelchocks_installation_status = 'installed'
```

This is **different from the active `wheelchocks_operator` in `aircraft_ground_wheelchocks_install.py`**, which checks `wheelchocks_readiness_status`. This version is more similar to `aircraft_chocks_install`'s `wheels_chocks_operator` (the simpler standalone network), while the `aircraft_ground_wheelchocks_install` version follows the readiness-gate pattern.

#### `NameError` risk (line 217)

`wheelchocks_installation_status` is only assigned inside the `if` block. If `flight_status` does not contain `'on'` and `'blocks'`, the variable is never assigned and `return wheelchocks_installation_status` raises `NameError`. The same bug is present in the active `wheelchocks_operator` in `aircraft_ground_wheelchocks_install.py`.

---

### 5.4 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_wheelchocks_setup.aircraft_ground_wheelchocks_setup.TrackerAPI`

Minimal 3-field configuration, consistent with `aircraft_ground_acu_setup` and `aircraft_ground_gpu_setup`.

**Tracked fields:** `aircraft_type`, `gate_id`, `wheelchocks_readiness_status`

**Return fields:** `aircraft_type`, `gate_id`, `wheelchocks_readiness_status`

Tracked = return fields, consistent with all three setup networks and `aircraft_gate_selection`.

> Note: The HOCON TrackerAPI description references `"engines_stop_status"` and `"wheels_chucks_installation_status"` — stale copy-paste artifacts not tracked by this network.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. Data Source — gate_equipments_base.csv

`wheelchocks_setup` reads the **same CSV file** as `aircraft_gate_selection`, `aircraft_ground_acu_setup`, and `aircraft_ground_gpu_setup`, located at:

```
Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"
```

The relevant column is `wheelchocks_readiness`. In the current baseline CSV:

- All B747 jetway entries (gates A1–A40): `wheelchocks_readiness = 'yes'`
- All B747 stairtruck entries (gates B1–B20): `wheelchocks_readiness = 'yes'`

Every valid B747 gate assignment will return `wheelchocks_readiness_status = 'ready'` in the current data. `wheelchocks_setup` is read-only — it does not mutate the CSV.

---

## 7. External Tool Dependencies

This network has no external tool dependencies. The `registries/aaosa_basic.hocon` include is present but no external tools appear in the agent's `tools` array.

---

## 8. Sample Queries

```
"The B747 aircraft of flight AF84 has been assigned gate A1. Report wheelchocks readiness at the gate."
```

---

## 9. Example Execution Trace

**Input (called from `aircraft_ground_wheelchocks_install` or `aircraft_ground_readiness`):**
> `aircraft_type = B747, gate_id = A1`

**Execution steps:**

1. Inquiry classified as readiness check (step 3)
2. `wheelchocks_setup` called — reads `gate_equipments_base.csv`, finds gate A1, reads `wheelchocks_readiness = 'yes'`, translates to `'ready'`
3. `wheelchocks_readiness_status = 'ready'` written to `sly_data`, returned to orchestrator
4. Summary returned to upstream caller

**Output:**

```
*********************************************
* Summary of aircraft wheelchocks readiness *
*********************************************
** aircraft_type **:                   B747
** gate_id **:                         A1
** wheels chucks readiness status **:  ready
```

*(Note: the summary label "wheels chucks readiness status" is the typo from step 4; the actual sly_data key returned is `wheelchocks_readiness_status`)*

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "gate_id": "A1",
  "wheelchocks_readiness_status": "ready"
}
```

---

## 10. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| `wheelchocks_operator` active but not registered in HOCON | `aircraft_ground_wheelchocks_setup.py` lines 126–221 / HOCON tools list | High | Unlike the commented-out operators in ACU and GPU setup files, this class is fully active Python code. Either register it in HOCON (after fixing the `NameError`) or note explicitly that it is intentionally unused. |
| **`NameError` in `wheelchocks_operator`** | `aircraft_ground_wheelchocks_setup.py` line 217 | **Critical** (if activated) | `wheelchocks_installation_status` only assigned inside the `if` block. `return wheelchocks_installation_status` raises `NameError` if `flight_status` doesn't contain `'on blocks'`. |
| `wheelchocks_operator` uses `flight_status` condition (vs. readiness) | `aircraft_ground_wheelchocks_setup.py` line 199 | Medium | This operator installs chocks when `'on' in flight_status AND 'blocks' in flight_status`. The active operator in `aircraft_ground_wheelchocks_install.py` uses `wheelchocks_readiness_status`. Two different installation logics for the same action. |
| Print banner says `"ACU READINESS STATUS 1/2"` | `aircraft_ground_wheelchocks_setup.py` lines 103, 106 | Low | Copy-paste from `aircraft_ground_acu_connect.py`. Should read `"WHEELCHOCKS READINESS STATUS 1/2"`. |
| Summary template uses `wheels_chucks_readiness_status` | `aircraft_ground_wheelchocks_setup.hocon` line 130 | Low | Double typo (`wheels_` prefix + "chucks"). The actual field is `wheelchocks_readiness_status`. The summary will display `[wheels_chucks_readiness_status]` as a literal placeholder if this field name is not matched. |
| Instructions say "submit inquiry about GPU" | `aircraft_ground_wheelchocks_setup.hocon` line 117 | Low | Copy-paste from `aircraft_ground_gpu_setup.hocon`. Should say "about wheelchocks". |
| `wheelchocks_setup` does not filter by `aircraft_type` | `aircraft_ground_wheelchocks_setup.py` line 98 | Low | CSV filtered only by `gate_id`. Multi-type gate scenarios could return wrong readiness. |
| `IndexError` if `gate_id` not in CSV | `aircraft_ground_wheelchocks_setup.py` line 105 | Medium | `wheelchocks_readiness_status.values[0]` raises `IndexError` if no rows match. No guard. Same risk as ACU and GPU setup. |
| `file_path_log` defined but never used | `aircraft_ground_wheelchocks_setup.py` line 48 | Low | Log path defined but no write call in `wheelchocks_setup`. Consistent with `acu_setup` and `gpu_setup`. |
| HOCON TrackerAPI description references stale fields | `aircraft_ground_wheelchocks_setup.hocon` lines 202–203 | Low | `engines_stop_status` and `wheels_chucks_installation_status` referenced; neither is tracked. |

---

## 11. Relationship to Other Networks

`aircraft_ground_wheelchocks_setup` is the third and final leaf in the ground equipment readiness sub-system:

```
gate_equipments_base.csv
   │
   ├── aircraft_gate_selection          (reads + writes: availability)
   ├── aircraft_ground_acu_setup        (reads: air_conditioning_unit_readiness)
   ├── aircraft_ground_gpu_setup        (reads: ground_power_unit_readiness)
   └── aircraft_ground_wheelchocks_setup (reads: wheelchocks_readiness)

Callers of aircraft_ground_wheelchocks_setup:
   ├── aircraft_ground_wheelchocks_install  (step 2 — readiness gate before installation)
   └── aircraft_ground_readiness            (step 4 — combined readiness report)
```

### Comparison: three setup networks

| Aspect | `aircraft_ground_acu_setup` | `aircraft_ground_gpu_setup` | `aircraft_ground_wheelchocks_setup` |
|---|---|---|---|
| CSV column read | `air_conditioning_unit_readiness` | `ground_power_unit_readiness` | `wheelchocks_readiness` |
| `'yes'` → `'ready'` | Yes | Yes | Yes |
| `'no'` → `'not ready'` | Yes | Yes | Yes |
| Inactive operator | `acu_operator` (commented out) | `gpu_operator` (commented out) | `wheelchocks_operator` (**active**, not registered) |
| Inactive operator condition | readiness-based | readiness-based | **flight_status-based** (different logic) |
| Instructions "about GPU" copy-paste | No | No | **Yes** (line 117) |
| Print banner copy-paste | No | No | **Yes** (ACU READINESS STATUS 1/2) |
| Summary label typo | No | No | **Yes** (`wheels_chucks_readiness_status`) |
| HOCON TrackerAPI description | Stale fields | Stale fields | Stale fields |
| `file_path_log` unused | Yes | Yes | Yes |

---

## 12. Extensibility Guidance

- Fix the `IndexError` guard: if no row matches `gate_id`, return an informative error string
- Add `aircraft_type` as a filter condition in the CSV lookup for multi-type gate correctness
- Add a log write to `wheelchocks_setup` (consistent with other operators)
- Decide whether to activate `wheelchocks_operator` (add to HOCON tools array, fix `NameError`) or remove it as dead code
- Fix the three copy-paste artifacts from GPU and ACU setups: instructions text ("about GPU"), print banners ("ACU READINESS STATUS"), summary label ("wheels_chucks_readiness_status")
- Make the CSV path configurable rather than hardcoded to the `aircraft_gate_selection` directory

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
