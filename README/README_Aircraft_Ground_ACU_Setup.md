# Aircraft Ground ACU Setup
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_acu_setup.hocon`
> **Implementation file:** `aircraft_ground_acu_setup.py`
> **Data file:** `aircraft_gate_selection/gate_equipments_base.csv` (shared with `aircraft_gate_selection`)
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Verify ACU (Air Conditioning Unit) readiness at an assigned gate for an incoming aircraft, by reading equipment availability from the gate inventory CSV. Returns `acu_readiness_status` to the caller.

---

## 1. Overview

`aircraft_ground_acu_setup` is a **leaf service network** — the lowest-level dependency in the ACU sub-system. It is called exclusively by `aircraft_ground_acu_connect` as the first step in the ACU connection workflow, before any safety-state checks are performed.

The network combines:

- An LLM-based orchestration agent (`acu_agent`) that routes readiness vs. connection inquiries
- One active coded tool (`acu_setup`) that reads ACU readiness from `gate_equipments_base.csv`
- A shared state manager (`TrackerAPI`) also implemented in Python
- A second coded class (`acu_operator`) present in the Python file but **not registered in the HOCON tools list**

This network is one of only two in the system (with `aircraft_gate_selection`) that reads from a CSV file as its data source. It shares the same `gate_equipments_base.csv` file, reading the `air_conditioning_unit_readiness` column for the specific `gate_id` assigned to the aircraft.

---

## 2. Repository Structure

```
aircraft_ground_acu_setup.hocon      # Agent network configuration
aircraft_ground_acu_setup.py         # Coded tool implementations (acu_setup, acu_operator [inactive], TrackerAPI)
coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv   # Shared equipment inventory (read-only here)
registries/aaosa_basic.hocon         # Shared registry (no external tools used)
```

---

## 3. System Architecture

```
aircraft_ground_acu_connect   (Upstream caller)
   │
   ▼
acu_agent  (LLM Orchestrator)
   │
   ├── acu_setup       (Coded tool: read ACU readiness from gate_equipments_base.csv)
   │
   └── TrackerAPI      (Coded tool: read/write acu_readiness_status via sly_data)
```

### Design principles

- **Data-driven readiness check:** `acu_setup` reads the `air_conditioning_unit_readiness` column from the shared gate CSV for the given `gate_id`, translating `'yes'` → `'ready'` and `'no'` → `'not ready'`.
- **Read-only CSV access:** Unlike `deplaning_path_selector` in `aircraft_gate_selection`, `acu_setup` does **not** mutate the CSV — it only reads.
- **Minimal scope:** The network tracks only three fields (`aircraft_type`, `gate_id`, `acu_readiness_status`). TrackerAPI tracked fields and return fields are identical.
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

> Note: The HOCON `llm_config` line includes a comment with previously tested alternatives (`gpt-4o`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`), consistent with `aircraft_ground_acu_connect`.

---

## 5. Components

### 5.1 acu_agent (LLM Orchestrator)

The entry-point agent. It determines whether the inquiry is about ACU readiness or ACU connection, then routes accordingly.

#### Input parameters

| Parameter              | Type   | Required | Description                               |
|------------------------|--------|:--------:|-------------------------------------------|
| `aircraft_type`        | string |    ✅     | Aircraft model/type                       |
| `gate_id`              | string |    ✅     | Gate where the aircraft is assigned       |
| `acu_readiness_status` | string |    ❌     | Current readiness status if already known |

#### Orchestration flow

The instructions describe two distinct inquiry types handled by a single numbered-prose flow:

1. Read the inquiry — determine if it is about ACU readiness status or ACU connection.
2. If neither → stop and report not relevant.
3. If about **ACU readiness status** → call `acu_setup` to read `acu_readiness_status`. Store and report the result. Stop.
4. Call `TrackerAPI` — log all available parameters.
5. Return summary.

> Note: The instructions describe handling an "ACU connection" inquiry type (step 1), but no connection tool is registered in the HOCON `tools` array. Only `acu_setup` and `TrackerAPI` are available. If the agent receives an ACU connection inquiry, it has no tool to fulfill it and would either report an error or attempt to use `acu_setup` inappropriately.

> Note: Step 4 (TrackerAPI call) and step 5 (return summary) are reached only for ACU readiness inquiries that proceed past step 3c. The flow from step 3c says "stop process here", so steps 4 and 5 would only be reached if the orchestrator does not strictly follow that instruction.

#### sly_data contract

| Direction           | Parameters                                         |
|---------------------|----------------------------------------------------|
| **To upstream**     | `aircraft_type`, `gate_id`, `acu_readiness_status` |
| **To downstream**   | `aircraft_type`, `gate_id`, `acu_readiness_status` |
| **From upstream**   | `aircraft_type`, `gate_id`, `acu_readiness_status` |
| **From downstream** | `aircraft_type`, `gate_id`, `acu_readiness_status` |

> Note: All four sly_data directions carry the same three fields. This is the most symmetric sly_data contract in the system. `flight_number` and `flight_status` are absent — this network operates on gate identity only.

#### Down-chain tools

```
["acu_setup", "TrackerAPI"]
```

---

### 5.2 acu_setup (Coded Tool — Active)

**Class:** `AirlineTurnaround.aircraft_ground_acu_setup.aircraft_ground_acu_setup.acu_setup`

Reads ACU readiness from `gate_equipments_base.csv`. It filters by `gate_id`, reads the `air_conditioning_unit_readiness` column, translates the raw value to a human-readable status, writes it to `sly_data`, and returns it.

#### Input parameters

| Parameter       | Type   | Required | Source priority     |
|-----------------|--------|:--------:|---------------------|
| `aircraft_type` | string |    ✅     | `args` → `sly_data` |
| `gate_id`       | string |    ✅     | `args` → `sly_data` |

#### Readiness lookup logic

1. Read `gate_equipments_base.csv` from the hardcoded path:
   `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"`
2. Filter rows where `gate_id == gate_id` (no filter on `aircraft_type` — see Known Issues)
3. Read `air_conditioning_unit_readiness` from the first matching row
4. Translate:
   - `'yes'` → `'ready'`
   - `'no'` → `'not ready'`
   - Any other value → returned as-is
5. Write `acu_readiness_status` to `sly_data`
6. Return `acu_readiness_status`

If no row matches `gate_id`, pandas will return an empty Series. `acu_readiness_status.values[0]` on line 105 will raise `IndexError`.

If both `gate_id` and `aircraft_type` are `None`, the CSV read is skipped and `acu_readiness_status = 'pending'` is returned. However, given both are required parameters and missing ones return an error earlier, this path is unreachable in normal execution.

#### CSV data reference

In the current `gate_equipments_base.csv`, every row has `air_conditioning_unit_readiness = 'yes'` for all B747 entries (both jetway and stairtruck). This means `acu_setup` will return `'ready'` for any valid gate assigned to a B747.

#### Output

- Writes `acu_readiness_status` into `sly_data`
- Returns `acu_readiness_status` string (`'ready'`, `'not ready'`, or `'pending'`)
- Appends a timestamped log entry to `test_debug/airlineturnaround.txt` (via `file_path_log` — though the actual `open()` write call is not present in this operator; only `file_path_log` is defined)

> Note: `file_path_log` is defined on line 48 but never used — there is no `open(file_path_log, ...)` write in `acu_setup`. Unlike all other operators in the system, this one does not write a log entry.

---

### 5.3 acu_operator (Coded Tool — Inactive / Not Registered)

**Class:** `AirlineTurnaround.aircraft_ground_acu_setup.aircraft_ground_acu_setup.acu_operator`

An ACU connection operator is present in the Python file (lines 125–223) but is **not listed in the HOCON tools array**. It is therefore unreachable by the agent at runtime.

The logic reads `aircraft_type`, `gate_id`, and `acu_readiness_status`, then sets `acu_connection_status = 'connected'` if `acu_readiness_status` contains `'ready'` or `'available'`. It has the same `NameError` risk as the operator in `aircraft_ground_acu_connect.py` — `acu_connection_status` is only assigned inside the `if` block, and `return acu_connection_status` on line 217 is unconditional.

Additionally, line 142 shows `# acu_connection_status = 'pending'` commented out — this was the intended fix for the `NameError` and was deliberately disabled, leaving the bug in place.

This operator appears to be a vestigial copy from `aircraft_ground_acu_connect.py` that was never wired up to this network's HOCON. It could be activated by adding it to the `tools` array, which would enable this network to handle both readiness checks and ACU connection in a single network. Currently it serves no function.

---

### 5.4 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_acu_setup.aircraft_ground_acu_setup.TrackerAPI`

Manages the minimal shared state for this network. Called in step 4 to persist `acu_readiness_status` after the readiness check.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

The default configuration for this network is the most minimal TrackerAPI in the system alongside `aircraft_engines_stop` and `aircraft_chocks_install`:

**Tracked fields:**
`aircraft_type`, `acu_readiness_status`, `gate_id`

**Return fields:**
`aircraft_type`, `acu_readiness_status`, `gate_id`

> Note: Tracked fields and return fields are identical — the same pattern as `aircraft_gate_selection`. All tracked fields are returned.

> Note: The HOCON TrackerAPI description references `"wheels_chucks_installation_status"` — a stale copy-paste artifact. Neither that field nor any other turnaround status field is tracked by this network.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. Data Source — gate_equipments_base.csv

`acu_setup` reads the **same CSV file** used by `aircraft_gate_selection`'s `deplaning_path_selector`, located at:

```
Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"
```

The relevant column is `air_conditioning_unit_readiness`. In the current baseline CSV:

- All B747 jetway entries (gates A1–A40): `air_conditioning_unit_readiness = 'yes'`
- All B747 stairtruck entries (gates B1–B20): `air_conditioning_unit_readiness = 'yes'`

This means every valid B747 gate assignment will return `acu_readiness_status = 'ready'` in the current data.

> Note: Unlike `deplaning_path_selector`, `acu_setup` does **not** mutate the CSV. It is read-only.

> Note: Because both networks share the same file, any availability changes made by `deplaning_path_selector` (setting selected units to `availability = 'no'`) do not affect ACU readiness lookups — the `air_conditioning_unit_readiness` column is independent.

---

## 7. External Tool Dependencies

This network has no external tool dependencies. The `registries/aaosa_basic.hocon` include is present but no external tools appear in the agent's `tools` array.

---

## 8. Sample Queries

```
"The B747 aircraft of flight AF84 has been assigned gate A1. Report ACU readiness at the gate."
```

---

## 9. Example Execution Trace

**Input (called from `aircraft_ground_acu_connect`):**
> `aircraft_type = B747, gate_id = A1`

**Execution steps:**

1. Inquiry classified as readiness check (step 3)
2. `acu_setup` called — reads `gate_equipments_base.csv`, finds gate A1, reads `air_conditioning_unit_readiness = 'yes'`, translates to `'ready'`
3. `acu_readiness_status = 'ready'` written to `sly_data`, returned to orchestrator
4. `TrackerAPI` called (step 4) — persists `acu_readiness_status`
5. Summary returned to upstream caller

**Output:**

```
*************************************
* Summary of aircraft acu readiness *
*************************************
** aircraft type **:       B747
** gate id **:             A1
** acu readiness status **: ready
```

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "gate_id": "A1",
  "acu_readiness_status": "ready"
}
```

---

## 10. Known Issues and Maintenance Notes

| Issue      | Location |           Severity          | Notes      |
|------------|----------|:---------------------------:|------------|
|            |          |            Medium           |            |
|            |          |            Medium           |            |
|            |          |             Low             |            |

---

## 11. Relationship to Other Networks

```
aircraft_gate_selection         ─── writes → gate_equipments_base.csv (availability)
aircraft_ground_acu_setup       ─── reads  → gate_equipments_base.csv (air_conditioning_unit_readiness)
aircraft_ground_acu_connect     ─── calls  → aircraft_ground_acu_setup (step 2, before safety checks)
```

`aircraft_ground_acu_setup` is called by `aircraft_ground_acu_connect` as a dependency, and itself calls `acu_setup` which reads from the file that `aircraft_gate_selection` manages. The two CSV operations are independent of each other (different columns), but they share the same physical file.

---

## 12. Extensibility Guidance

- 

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
