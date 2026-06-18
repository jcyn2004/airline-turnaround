aircraft_ground_gpu_setup_agent# Aircraft Ground GPU Setup
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_gpu_setup.hocon`
> **Implementation file:** `aircraft_ground_gpu_setup.py`
> **Data file:** `aircraft_gate_selection/gate_equipments_base.csv` (shared with `aircraft_gate_selection` and `aircraft_ground_acu_setup`)
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Verify Ground Power Unit (GPU) readiness at an assigned gate for an incoming aircraft, by reading equipment availability from the gate inventory CSV. Returns `gpu_readiness_status` to the caller.

---

## 1. Overview

`aircraft_ground_gpu_setup` is the GPU counterpart to `aircraft_ground_acu_setup` — both are **leaf service networks** that verify equipment readiness by reading from `gate_equipments_base.csv`. This network is called exclusively by `aircraft_ground_gpu_connect` as its first step, before any safety-state checks are performed.

The network combines:

- An LLM-based orchestration agent (`gpu_agent`) that routes readiness vs. connection inquiries
- One active coded tool (`gpu_setup`) that reads GPU readiness from `gate_equipments_base.csv`
- A shared state manager (`TrackerAPI`) also implemented in Python
- One inactive coded class (`gpu_operator`) present in the Python file but **not registered in the HOCON tools list**

The active `gpu_setup` is the fully implemented version of the commented-out `gpu_setup` code that appears in `aircraft_ground_gpu_connect.py`. The key correction over that stub is the inclusion of both value translations: `'yes'` → `'ready'` **and** `'no'` → `'not ready'`.

---

## 2. Repository Structure

```
aircraft_ground_gpu_setup.hocon      # Agent network configuration
aircraft_ground_gpu_setup.py         # Coded tool implementations (gpu_setup, gpu_operator [inactive], TrackerAPI)
coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv   # Shared equipment inventory (read-only)
registries/aaosa_basic.hocon         # Shared registry (no external tools used)
```

---

## 3. System Architecture

```
aircraft_ground_gpu_connect   (Upstream caller)
   │
   ▼
gpu_agent  (LLM Orchestrator)
   │
   ├── gpu_setup       (Coded tool: read GPU readiness from gate_equipments_base.csv)
   │
   └── TrackerAPI      (Coded tool: read/write gpu_readiness_status via sly_data)
```

### Design principles

- **Data-driven readiness check:** `gpu_setup` reads the `ground_power_unit_readiness` column from the shared gate CSV for the given `gate_id`, translating `'yes'` → `'ready'` and `'no'` → `'not ready'`.
- **Read-only CSV access:** `gpu_setup` does not mutate the CSV — it only reads, the same as `acu_setup`.
- **Minimal scope:** The network tracks only three fields (`aircraft_type`, `gate_id`, `gpu_readiness_status`). TrackerAPI tracked fields and return fields are identical.
- **Leaf network:** No external tool dependencies. Resolves entirely from the CSV and sly_data.

---

## 4. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

> Note: The HOCON `llm_config` line includes a comment with previously tested alternatives (`gpt-4o`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`), consistent with the other ground service setup networks.

---

## 5. Components

### 5.1 gpu_agent (LLM Orchestrator)

The entry-point agent. It determines whether the inquiry is about GPU readiness or GPU connection, then routes accordingly.

#### Input parameters

| Parameter              | Type   | Required  | Description                               |
|------------------------|--------|:---------:|-------------------------------------------|
| `aircraft_type`        | string |    ✅     | Aircraft model/type                       |
| `flight_number`        | string |    ❌     | Flight number of the incoming aircraft    |
| `gate_id`              | string |    ✅     | Gate where the aircraft is assigned       |
| `gpu_readiness_status` | string |    ❌     | Current readiness status if already known |

#### Orchestration flow

The instructions use numbered-prose style. The flow is parallel to `aircraft_ground_acu_setup`, including an explicit TrackerAPI call step:

1. Read the inquiry — determine if it is about GPU readiness status or GPU connection.
2. If neither → stop and report not relevant.
3. If about **GPU readiness status**:
   - Call `gpu_setup` to read `gpu_readiness_status`.
   - Store the returned value.
   - Report its value back to user.
4. Call `TrackerAPI` and log all the available parameters.
   - Wait for its response.
   - Store all the available parameters.
5. Provide the GPU readiness summary.

> Note: Step 2 instructs the agent to "stop process here" when the inquiry is irrelevant, ensuring early exit on non-GPU inquiries.

#### sly_data contract

| Direction           | Parameters                                                                                  |
|---------------------|---------------------------------------------------------------------------------------------|
| **To upstream**     | `gpu_readiness_status`                                                                      |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`                                                 |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`                                                 |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `gpu_readiness_status`                         |

`flight_number`, `aircraft_type`, and `gate_id` are carried in the three input-bearing directions (from_upstream, to_downstream, from_downstream). `gpu_readiness_status` is the network's produced output: it flows out via `to_upstream` and is returned via `from_downstream`. `flight_status` is not part of the contract for this readiness-only setup network.

#### Down-chain tools

```
["gpu_setup", "TrackerAPI"]
```

---

### 5.2 gpu_setup (Coded Tool — Active)

**Class:** `AirlineTurnaround.aircraft_ground_gpu_setup.aircraft_ground_gpu_setup.gpu_setup`

Reads GPU readiness from `gate_equipments_base.csv`. It filters by `gate_id`, reads the `ground_power_unit_readiness` column, translates the raw value to a human-readable status, writes it to `sly_data`, and returns it.

#### Input parameters

| Parameter              | Type   | Required  | Source priority     |
|------------------------|--------|:---------:|---------------------|
| `aircraft_type`        | string |    ✅     | `args` → `sly_data` |
| `flight_number`        | string |    ❌     | `args` → `sly_data` |
| `gate_id`              | string |    ✅     | `args` → `sly_data` |
| `gpu_readiness_status` | string |    ❌     | `args` → `sly_data` |

#### Readiness lookup logic

1. Read `gate_equipments_base.csv` from the hardcoded path:
   `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"`
2. Filter rows where `gate_id == gate_id` (no filter on `aircraft_type` — same limitation as `acu_setup`)
3. Read `ground_power_unit_readiness` from the first matching row
4. Translate:
   - `'yes'` → `'ready'`
   - `'no'` → `'not ready'`
   - Any other value → returned as-is
5. Write `gpu_readiness_status` to `sly_data`
6. Return `gpu_readiness_status`

> Note: This is a complete and correct implementation. The commented-out `gpu_setup` in `aircraft_ground_gpu_connect.py` was missing the `'no'` → `'not ready'` translation (line 113–114 here vs. absent there). This active implementation is the canonical version.

If no row matches `gate_id`, `gpu_readiness_status.values[0]` on line 105 will raise `IndexError` — the same risk present in `acu_setup`.

#### CSV data reference

In the current `gate_equipments_base.csv`, every row has `ground_power_unit_readiness = 'yes'` for all B747 entries (both jetway and stairtruck gates). This means `gpu_setup` will return `'ready'` for any valid gate assigned to a B747 in the current baseline.

#### Output

- Writes `gpu_readiness_status` into `sly_data`
- Returns `gpu_readiness_status` string (`'ready'`, `'not ready'`, or `'pending'`)
- `file_path_log` is defined but **never used** — no log entry is written (same as `acu_setup`)

---

### 5.3 gpu_operator (Coded Tool — Inactive / Not Registered)

**Class:** `AirlineTurnaround.aircraft_ground_gpu_setup.aircraft_ground_gpu_setup.gpu_operator` *(not registered)*

A GPU connection operator is present in the Python file (lines 125–222) but is **not listed in the HOCON tools array**. It is therefore unreachable at runtime.

The logic reads `aircraft_type`, `gate_id`, and `gpu_readiness_status` (using `args`-first, unlike the active `gpu_operator` in `aircraft_ground_gpu_connect.py` which uses `sly_data`-first), then sets `gpu_connection_status = 'connected'` if `gpu_readiness_status` contains `'ready'` or `'available'`.

Notable differences from the active `gpu_operator` in `aircraft_ground_gpu_connect.py`:

| Aspect                                 | This inactive version                              | Active version (in `gpu_connect`) |                                |
|----------------------------------------|----------------------------------------------------|-----------------------------------|--------------------------------|
| `gpu_readiness_status` lookup priority | `args` → `sly_data`                                | `sly_data` → `args`               |                                |
| Readiness condition                    | `('ready' in ...) \                                | ('available' in ...)`             | same + `'no' not in ...` guard |
| `NameError` risk                       | Yes — same uninitialized `gpu_connection_status`   | Yes                               |                                |
| Comment on line 142                    | `# acu_connection_status = 'pending'` (wrong name) | same residue                      |                                |

This class appears to be the earlier version of the GPU operator, preserved here before the `sly_data`-first priority and `'no' not in` guard were added to the active version. Safe to remove.

---

### 5.4 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_gpu_setup.aircraft_ground_gpu_setup.TrackerAPI`

Manages the minimal shared state for this network.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

The default configuration for this network is identical to `aircraft_ground_acu_setup` in structure (3 fields, tracked = return):

**Tracked fields:**
`aircraft_type`, `gpu_readiness_status`, `gate_id`

**Return fields:**
`aircraft_type`, `gpu_readiness_status`, `gate_id`

> Note: Tracked fields and return fields are identical — consistent with `aircraft_ground_acu_setup` and `aircraft_gate_selection`.

> Note: The HOCON TrackerAPI description references `"wheels_chucks_installation_status"` and `"engines_stop_status"` — stale copy-paste artifacts. Neither is tracked by this network.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`. The HOCON schema also exposes `flight_number`, `flight_status`, and several turnaround status fields in the `parameters` object, none of which are tracked by the Python default config.

---

## 6. Data Source — gate_equipments_base.csv

`gpu_setup` reads the **same CSV file** as `aircraft_gate_selection`'s `deplaning_path_selector` and `aircraft_ground_acu_setup`'s `acu_setup`, located at:

```
Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"
```

The relevant column is `ground_power_unit_readiness`. In the current baseline CSV:

- All B747 jetway entries (gates A1–A40): `ground_power_unit_readiness = 'yes'`
- All B747 stairtruck entries (gates B1–B20): `ground_power_unit_readiness = 'yes'`

Every valid B747 gate assignment will return `gpu_readiness_status = 'ready'` in the current data. `gpu_setup` is read-only — it does not mutate the CSV.

---

## 7. External Tool Dependencies

This network has no external tool dependencies. The `registries/aaosa_basic.hocon` include is present but no external tools appear in the agent's `tools` array.

---

## 8. Sample Queries

```
"The B747 aircraft of flight AF84 has been assigned gate A1. Report GPU readiness at the gate."
```

---

## 9. Example Execution Trace

**Input (called from `aircraft_ground_gpu_connect`):**
> `aircraft_type = B747, gate_id = A1`

**Execution steps:**

1. Inquiry classified as readiness check (step 3)
2. `gpu_setup` called — reads `gate_equipments_base.csv`, finds gate A1, reads `ground_power_unit_readiness = 'yes'`, translates to `'ready'`
3. `gpu_readiness_status = 'ready'` written to `sly_data`, returned to orchestrator
4. `TrackerAPI` called — logs available parameters
5. Summary returned to upstream caller

**Output:**

```
*************************************
* Summary of aircraft gpu readiness *
*************************************
** aircraft_type **:       B747
** gate id **:             A1
** gpu readiness status **: ready
```

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "gate_id": "A1",
  "gpu_readiness_status": "ready"
}
```

---

## 10. Known Issues and Maintenance Notes

| Issue                                            | Location                                 | Severity | Notes                                                                                                                                                                    |
|--------------------------------------------------|------------------------------------------|:--------:|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `IndexError` if `gate_id` not in CSV             | `aircraft_ground_gpu_setup.py` line 105  |  Medium  | `gpu_readiness_status.values[0]` raises `IndexError` if no rows match `gate_id`. No guard. Same issue as `acu_setup`.                                                    |
| `gpu_setup` does not filter by `aircraft_type`   | `aircraft_ground_gpu_setup.py` line 98   |  Medium  | DataFrame filtered only by `gate_id`. If a gate serves multiple aircraft types with different GPU readiness, the wrong row could be returned. Same issue as `acu_setup`. |

---

## 11. Relationship to Other Networks

```
aircraft_gate_selection          ─── writes → gate_equipments_base.csv (availability)
aircraft_ground_acu_setup        ─── reads  → gate_equipments_base.csv (air_conditioning_unit_readiness)
aircraft_ground_gpu_setup        ─── reads  → gate_equipments_base.csv (ground_power_unit_readiness)
aircraft_ground_acu_connect      ─── calls  → aircraft_ground_acu_setup
aircraft_ground_gpu_connect      ─── calls  → aircraft_ground_gpu_setup
```

### Comparison: `aircraft_ground_gpu_setup` vs. `aircraft_ground_acu_setup`

| Aspect                                 | `aircraft_ground_acu_setup`         | `aircraft_ground_gpu_setup`                                 |            |                          |
|----------------------------------------|-------------------------------------|-------------------------------------------------------------|------------|--------------------------|
| CSV column read                        | `air_conditioning_unit_readiness`   | `ground_power_unit_readiness`                               |            |                          |
| Active coded tool                      | `acu_setup`                         | `gpu_setup`                                                 |            |                          |
| `'yes'` → `'ready'` translation        | Yes                                 | Yes                                                         |            |                          |
| `'no'` → `'not ready'` translation     | Yes                                 | Yes                                                         |            |                          |
| Inactive operator class                | `acu_operator`                      | `gpu_operator`                                              |            |                          |
| Inactive operator readiness condition  | `'ready' \                          | 'available'`                                                | `'ready' \ | 'available'` (identical) |
| Instructions: explicit TrackerAPI call | Yes (step 4)                        | Yes (step 4)                                                |            |                          |
| TrackerAPI HOCON description artifact  | `wheels_chucks_installation_status` | `wheels_chucks_installation_status` + `engines_stop_status` |            |                          |

---

## 12. Extensibility Guidance

- Add `IndexError` guard: if no row matches `gate_id`, return an informative error string rather than crashing
- Add `aircraft_type` as a filter condition in the CSV lookup for correctness with multi-type gates
- Make the CSV path configurable via a constructor parameter or shared constant rather than a hardcoded cross-module reference

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation electrical or safety-critical systems.
