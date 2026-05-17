# Aircraft Ground Wheels Chocks Setup
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_wheels_chocks_setup.hocon`
> **Implementation file:** `aircraft_ground_wheels_chocks_setup.py`
> **Data file:** `aircraft_gate_selection/gate_equipments_base.csv` (shared with `aircraft_gate_selection`, `aircraft_ground_acu_setup`, `aircraft_ground_gpu_setup`)
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Verify wheels chocks readiness at an assigned gate for an incoming aircraft, by reading the `wheelchocks_readiness` column from the shared gate equipment inventory CSV. Returns `wheels_chocks_readiness_status` to the caller.

---

## 1. Overview

`aircraft_ground_wheels_chocks_setup` is the wheels chocks counterpart to `aircraft_ground_acu_setup` and `aircraft_ground_gpu_setup` — all three are **leaf service networks** that verify equipment readiness by reading from `gate_equipments_base.csv`. This network is called by:

- `aircraft_ground_wheels_chocks_install` (step 2, before safety-state checks)
- `aircraft_ground_readiness` (step 4, as part of the combined readiness report)

The network combines:

- An LLM-based orchestration agent (`wheels_chocks_agent`) that handles wheels chocks readiness inquiries
- One active coded tool (`wheels_chocks_setup`) that reads wheels chocks readiness from `gate_equipments_base.csv`
- A shared state manager (`TrackerAPI`) also implemented in Python

The HOCON registers exactly three tools: `wheels_chocks_agent`, `wheels_chocks_setup`, and `TrackerAPI`. No operator class is registered in this HOCON.

---

## 2. Repository Structure

```
aircraft_ground_wheels_chocks_setup.hocon      # Agent network configuration
aircraft_ground_wheels_chocks_setup.py         # Coded tool implementations (wheels_chocks_setup, TrackerAPI)
coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv   # Shared equipment inventory (read-only)
registries/aaosa_basic.hocon                   # Shared registry (no external tools used)
```

---

## 3. System Architecture

```
aircraft_ground_wheels_chocks_install   (Caller 1)
aircraft_ground_readiness               (Caller 2)
   │
   ▼
wheels_chocks_agent  (LLM Orchestrator)
   │
   ├── wheels_chocks_setup     (Coded tool: read wheels chocks readiness from gate_equipments_base.csv)
   │
   └── TrackerAPI              (Coded tool: read/write wheels_chocks_readiness_status via sly_data)
```

### Design principles

- **Data-driven readiness check:** `wheels_chocks_setup` reads the `wheelchocks_readiness` column from the shared gate CSV for the given `gate_id`, translating `'yes'` → `'ready'` and `'no'` → `'not ready'`.
- **Read-only CSV access:** `wheels_chocks_setup` does not mutate the CSV.
- **4-field TrackerAPI:** Tracked fields = return fields (`aircraft_type`, `flight_number`, `gate_id`, `wheels_chocks_readiness_status`).
- **Leaf network:** No external tool dependencies.
- **Complete translations:** Both `'yes'` → `'ready'` and `'no'` → `'not ready'` are implemented — unlike the commented-out stubs in `aircraft_ground_gpu_connect.py` and `aircraft_ground_wheels_chocks_install.py` which only translated `'yes'`.

---

## 4. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

> Note: The HOCON `llm_config` line includes a comment with previously tested model alternatives (`gpt-4o`, `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`), consistent with the other ground service setup networks.

---

## 5. Components

### 5.1 wheels_chocks_agent (LLM Orchestrator)

The entry-point agent. It handles inquiries about wheels chocks readiness and ground services readiness checks. The agent is configured to be **ALWAYS relevant** for wheels chocks readiness or any ground services readiness check that includes wheels chocks, and never refuses based on missing or null status fields.

#### Input parameters

| Parameter                        | Type   | Required | Description                               |
|----------------------------------|--------|:--------:|-------------------------------------------|
| `aircraft_type`                  | string |    ✅     | Aircraft model/type                       |
| `flight_number`                  | string |    ❌     | Flight number of the incoming aircraft    |
| `gate_id`                        | string |    ✅     | Gate where the aircraft is parked         |
| `wheels_chocks_readiness_status` | string |    ❌     | Current readiness status if already known |

#### Orchestration flow

1. Read the inquiry — any inquiry about ground services readiness, wheels chocks readiness status, or wheels chocks installation/connection is relevant.
2. Only reply not relevant if the inquiry is entirely unrelated to wheels chocks or ground services.
3. If about **wheels chocks readiness status** → call `wheels_chocks_setup`, store the returned `wheels_chocks_readiness_status`, and report its value back to user.
4. Call `TrackerAPI` and log all available parameters.
5. Provide the wheels chocks readiness status summary.

#### sly_data contract

All four directions carry the same 4-field set — fully symmetric:

| Direction           | Parameters                                                                       |
|---------------------|----------------------------------------------------------------------------------|
| **To upstream**     | `aircraft_type`, `flight_number`, `gate_id`, `wheels_chocks_readiness_status`    |
| **To downstream**   | same 4 fields                                                                    |
| **From upstream**   | same 4 fields                                                                    |
| **From downstream** | same 4 fields                                                                    |

#### Down-chain tools

```
["wheels_chocks_setup", "TrackerAPI"]
```

---

### 5.2 wheels_chocks_setup (Coded Tool — Active)

**Class:** `AirlineTurnaround.aircraft_ground_wheels_chocks_setup.aircraft_ground_wheels_chocks_setup.wheels_chocks_setup`

Reads wheels chocks readiness from `gate_equipments_base.csv`. Filters by `gate_id`, reads the `wheelchocks_readiness` column, applies both value translations, writes to `sly_data`, and returns.

#### Input parameters

| Parameter                        | Type   | Required | Source priority     |
|----------------------------------|--------|:--------:|---------------------|
| `aircraft_type`                  | string |    ✅     | `args` → `sly_data` |
| `flight_number`                  | string |    ❌     | `args` → `sly_data` |
| `gate_id`                        | string |    ✅     | `args` → `sly_data` |
| `wheels_chocks_readiness_status` | string |    ❌     | `args` → `sly_data` |

#### Readiness lookup logic

1. Read `gate_equipments_base.csv` from:
   `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"`
2. Filter rows where `gate_id == gate_id` (no filter on `aircraft_type`)
3. Read `wheelchocks_readiness` from the first matching row
4. Translate:
   - `'yes'` → `'ready'`
   - `'no'` → `'not ready'`
   - Any other value → returned as-is
5. Write `wheels_chocks_readiness_status` to `sly_data`
6. Return `wheels_chocks_readiness_status`

> Note: Both `'yes'` → `'ready'` AND `'no'` → `'not ready'` translations are present. This makes `wheels_chocks_setup` the **most complete** of the three setup implementations — `aircraft_ground_acu_setup`'s `acu_setup` also has both, while `aircraft_ground_gpu_setup`'s `gpu_setup` only has `'yes'` → `'ready'`.

If no row matches `gate_id`, `wheels_chocks_readiness_status.values[0]` will raise `IndexError` — same risk as the ACU and GPU setup operators.

#### Output

- Writes `wheels_chocks_readiness_status` into `sly_data`
- Returns `wheels_chocks_readiness_status` string (`'ready'`, `'not ready'`, or `'pending'`)

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_wheels_chocks_setup.aircraft_ground_wheels_chocks_setup.TrackerAPI`

4-field configuration, consistent with `aircraft_ground_acu_setup` and `aircraft_ground_gpu_setup`.

**Tracked fields:** `aircraft_type`, `flight_number`, `gate_id`, `wheels_chocks_readiness_status`

**Return fields:** `aircraft_type`, `flight_number`, `gate_id`, `wheels_chocks_readiness_status`

Tracked = return fields, consistent with all three setup networks and `aircraft_gate_selection`.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. Data Source — gate_equipments_base.csv

`wheels_chocks_setup` reads the **same CSV file** as `aircraft_gate_selection`, `aircraft_ground_acu_setup`, and `aircraft_ground_gpu_setup`, located at:

```
Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"
```

The relevant column is `wheelchocks_readiness`. In the current baseline CSV:

- All B747 jetway entries (gates A1–A40): `wheelchocks_readiness = 'yes'`
- All B747 stairtruck entries (gates B1–B20): `wheelchocks_readiness = 'yes'`

Every valid B747 gate assignment will return `wheels_chocks_readiness_status = 'ready'` in the current data. `wheels_chocks_setup` is read-only — it does not mutate the CSV.

---

## 7. External Tool Dependencies

This network has no external tool dependencies. The `registries/aaosa_basic.hocon` include is present but no external tools appear in the agent's `tools` array.

---

## 8. Sample Queries

```
"The B747 aircraft of flight AF84 has been assigned gate A1. Report wheels chocks readiness at the gate."
```

---

## 9. Example Execution Trace

**Input (called from `aircraft_ground_wheels_chocks_install` or `aircraft_ground_readiness`):**
> `aircraft_type = B747, flight_number = AF84, gate_id = A1`

**Execution steps:**

1. Inquiry classified as wheels chocks readiness check
2. `wheels_chocks_setup` called — reads `gate_equipments_base.csv`, finds gate A1, reads `wheelchocks_readiness = 'yes'`, translates to `'ready'`
3. `wheels_chocks_readiness_status = 'ready'` written to `sly_data`, returned to orchestrator
4. `TrackerAPI` logs all available parameters
5. Summary returned to upstream caller

**Output:**

```
***********************************************
* Summary of aircraft wheels chocks readiness *
***********************************************
** aircraft_type **:                   B747
** flight_number **:                   AF84
** gate_id **:                         A1
** wheels chocks readiness status **:  ready
```

**JSON equivalent:**

```json
{
  "aircraft_type": "B747",
  "flight_number": "AF84",
  "gate_id": "A1",
  "wheels_chocks_readiness_status": "ready"
}
```

---

## 10. Known Issues and Maintenance Notes

| Issue                                                                 | Location                                                                |           Severity          | Notes                                                                                                                                                                                                                                                 |
|-----------------------------------------------------------------------|-------------------------------------------------------------------------|:---------------------------:|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `wheels_chocks_setup` does not filter by `aircraft_type`              | `aircraft_ground_wheels_chocks_setup.py`                                |             Low             | CSV filtered only by `gate_id`. Multi-type gate scenarios could return wrong readiness.                                                                                                                                                               |
| `IndexError` if `gate_id` not in CSV                                  | `aircraft_ground_wheels_chocks_setup.py`                                |            Medium           | `wheels_chocks_readiness_status.values[0]` raises `IndexError` if no rows match. No guard. Same risk as ACU and GPU setup.                                                                                                                              |



---

## 11. Relationship to Other Networks

`aircraft_ground_wheels_chocks_setup` is the third and final leaf in the ground equipment readiness sub-system:

```
gate_equipments_base.csv
   │
   ├── aircraft_gate_selection             (reads + writes: availability)
   ├── aircraft_ground_acu_setup           (reads: air_conditioning_unit_readiness)
   ├── aircraft_ground_gpu_setup           (reads: ground_power_unit_readiness)
   └── aircraft_ground_wheels_chocks_setup (reads: wheelchocks_readiness)

Callers of aircraft_ground_wheels_chocks_setup:
   ├── aircraft_ground_wheels_chocks_install  (step 2 — readiness gate before installation)
   └── aircraft_ground_readiness              (step 4 — combined readiness report)
```

### Comparison: three setup networks

| Aspect                              | `aircraft_ground_acu_setup`       | `aircraft_ground_gpu_setup`    | `aircraft_ground_wheels_chocks_setup`               |
|-------------------------------------|-----------------------------------|--------------------------------|-----------------------------------------------------|
| CSV column read                     | `air_conditioning_unit_readiness` | `ground_power_unit_readiness`  | `wheelchocks_readiness`                             |
| `'yes'` → `'ready'`                 | Yes                               | Yes                            | Yes                                                 |
| `'no'` → `'not ready'`              | Yes                               | Yes                            | Yes                                                 |
| Operator class in HOCON             | No (commented out)                | No (commented out)             | No (not registered)                                 |
| TrackerAPI field count              | 3                                 | 3                              | 4 (includes `flight_number`)                        |

---

## 12. Extensibility Guidance

- Fix the `IndexError` guard: if no row matches `gate_id`, return an informative error string
- Add `aircraft_type` as a filter condition in the CSV lookup for multi-type gate correctness
- Make the CSV path configurable rather than hardcoded to the `aircraft_gate_selection` directory

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
