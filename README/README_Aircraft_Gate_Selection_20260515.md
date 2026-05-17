# Aircraft Gate Selection
## Agentic AI Network – README

> **Configuration file:** `aircraft_gate_selection.hocon`
> **Implementation file:** `aircraft_gate_selection.py`
> **Data file:** `gate_equipments_base.csv`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Assign a gate and select the best available deplaning equipment (jetway or stairtruck) for an incoming aircraft, based on aircraft type, equipment readiness, and availability.

---

## 1. Overview

`aircraft_gate_selection` is the most architecturally distinctive network in the **AirlineTurnaround** agentic system. Unlike all other networks, which perform binary status checks against operational state, this network executes a **data-driven scoring and selection algorithm** using a real CSV equipment inventory file. The result — a `gate_id`, equipment type, equipment ID, readiness time, and score — is then propagated downstream to networks such as `aircraft_disembark`, `aircraft_crew_exit`, and `aircraft_baggage_unload` that require both gate identity and deplaning equipment type.

The network combines:

- An LLM-based orchestration agent (`gate_selection_agent`) that interprets the inquiry and drives a two-step workflow
- One coded execution tool (`deplaning_path_selector`) that implements the selection algorithm in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- A CSV reference data file (`gate_equipments_base.csv`) that contains the equipment inventory

Several sub-agents (`jetway_agent`, `stairtruck_agent`, `jetway_park_agent`, `stairtruck_park_agent`) appear as commented-out stubs in both the HOCON and Python — they represent an earlier, more decomposed architecture that has been superseded by the current unified `deplaning_path_selector`.

---

## 2. Repository Structure

```
aircraft_gate_selection.hocon        # Agent network configuration
aircraft_gate_selection.py           # Coded tool implementations (deplaning_path_selector, TrackerAPI)
gate_equipments_base.csv             # Equipment inventory with readiness scores (mutable — updated on each selection)
registries/aaosa_basic.hocon         # Shared registry (no external tools used)
```

> Note: This network includes `registries/aaosa_basic.hocon`, the same shared registry used by all other networks in the system.

---

## 3. System Architecture

```
User / Caller
   │
   ▼
gate_selection_agent  (LLM Orchestrator)
   │
   ├── deplaning_path_selector    (Coded tool: CSV-based gate + equipment selection)
   │
   └── TrackerAPI                 (Coded tool: read/write turnaround state via sly_data)
```

### Design principles

- **Data-driven selection:** Gate and equipment assignment is driven by a CSV inventory file scored on readiness time. The algorithm selects the available unit with the lowest `readiness` value (fastest to deploy) across both jetway and stairtruck candidates, then compares the best of each type.
- **Score formula:** `score = 1 / (1 + readiness)` — higher score means lower readiness time, i.e. faster availability. Pre-computed scores are stored in the CSV but recalculated at runtime.
- **Stateful CSV mutation:** After selection, the chosen unit's `availability` is set to `no` and the CSV is written back to disk. This is the **only network in the system** that modifies a persistent data file as part of its operation.
- **Minimal orchestration:** The workflow is just two steps — retrieve identity parameters, call selector, store results.
- **Airport-specific configuration:** The HOCON `instructions_prefix` names San Francisco International Airport explicitly, unlike all other networks which use a generic airport context.

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

### 5.1 gate_selection_agent (LLM Orchestrator)

The entry-point agent. It resolves the required identity parameters, calls `deplaning_path_selector`, stores the results, and returns the summary.

> Note: The agent is named `gate_selection_agent` in the HOCON. The previous documentation referred to it as `aircraft_gate_selection_agent`, which does not match the actual runtime tool name.

#### Input parameters

|-----------------|--------|:--------:|----------------------------------------------|
| Parameter       | Type   | Required | Description                                  |
|-----------------|--------|:--------:|----------------------------------------------|
| `flight_number` | string | ✅       | Flight identifier                            |
| `aircraft_type` | string | ✅       | Aircraft model/type — used to filter the CSV |
| `gate_id`       | string | ❌       | Pre-existing gate assignment (if any)        |
|-----------------|--------|:--------:|----------------------------------------------|

> Note: `aircraft_direction` and `gate_selection_status` appear in the previous documentation but do not exist anywhere in the HOCON schema, Python implementation, or CSV. They should be removed from any external documentation or integration contracts.

#### Orchestration flow

1. **STEP 1 — Resolve flight_number and aircraft_type:** Read from inquiry or sly_data. If either is missing, call `TrackerAPI` to retrieve. If still missing → stop and report `"Cannot assign gate — flight_number and aircraft_type are required."`
2. **STEP 2 — Select gate and deplaning path:** Call `deplaning_path_selector` with `flight_number`, `aircraft_type`. Extract: `gate_id`, `deplaning_equipment_type`, `deplaning_equipment_id`, `deplaning_equipment_readiness_time`, `deplaning_equipment_score`. Call `TrackerAPI` to store `gate_id` and `deplaning_equipment_type`.
3. **RETURN SUMMARY.**

#### sly_data contract

|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Direction         | Parameters                                                                                                                                                          |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **To upstream**   | `gate_id`, `flight_number`, `aircraft_type`, `deplaning_equipment_type`, `deplaning_equipment_id`, `deplaning_equipment_score`, `deplaning_equipment_readiness_time` |
| **From upstream** | `gate_id`, `flight_number`, `aircraft_type`, `deplaning_equipment_type`, `deplaning_equipment_id`, `deplaning_equipment_score`, `deplaning_equipment_readiness_time` |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|

> Note: This network has no `to_downstream` or `from_downstream` sly_data blocks — it is intended as an early-stage upstream network that feeds context to the rest of the turnaround pipeline. `deplaning_equipment_readiness_time` is returned by `deplaning_path_selector`, shown in the summary, and included in both the `to_upstream` and `from_upstream` sly_data blocks.

#### Down-chain tools

```
["deplaning_path_selector", "TrackerAPI"]
```

---

### 5.2 deplaning_path_selector (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_gate_selection.aircraft_gate_selection.deplaning_path_selector`

The core selection tool. It reads `gate_equipments_base.csv`, filters by `aircraft_type`, scores all available units, selects the best jetway and best stairtruck independently, then picks whichever has the lowest readiness time overall. The selected unit's `availability` is set to `no` and the CSV is written back to disk.

> Note: The class path uses the `AirlineTurnaround.` root prefix, consistent with all other coded tools in the system.

#### Constructor

Unlike all other coded tools in the system (which have no constructor and receive configuration through `args`/`sly_data`), `deplaning_path_selector` has an explicit `__init__` with two configurable paths:

|-----------------------|-------------------------------------------------------------------------------------------------------------|
| Parameter             | Default                                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------------------|
| `equipments_csv_path` | `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"` |
| `log_path`            | `Path.cwd() / "test_debug" / "airlineturnaround.txt"`                                                       |
|-----------------------|-------------------------------------------------------------------------------------------------------------|

#### Input parameters

|-----------------|--------|:--------:|---------------------|
| Parameter       | Type   | Required | Source priority     |
|-----------------|--------|:--------:|---------------------|
| `aircraft_type` | string | ✅       | `args` → `sly_data` |
|-----------------|--------|:--------:|---------------------|

Only `aircraft_type` is actually read. `flight_number`, `gate_id`, and equipment fields in the HOCON schema are not used by the operator logic.

#### Selection algorithm

1. Load `gate_equipments_base.csv` as a DataFrame
2. Filter rows where `aircraft_type == aircraft_type`
3. Compute `score = 1 / (1 + readiness)` for all rows
4. Among rows where `type == 'jetway'` and `availability == 'yes'` → select row with minimum `readiness` → `jetway_dict`
5. Among rows where `type == 'stairtruck'` and `availability == 'yes'` → select row with minimum `readiness` → `stairtruck_dict`
6. Compare `jetway_dict` and `stairtruck_dict` by `readiness` → pick the lower one as `gate_dict`
7. Write `gate_id`, `deplaning_equipment_id`, `deplaning_equipment_type`, `deplaning_equipment_readiness_time`, `deplaning_equipment_score` into `sly_data`
8. **Set `availability = 'no'` for selected unit and write CSV back to disk**
9. Return `gate_dict`

If no entries exist for the given `aircraft_type`, raises `ValueError`. If no available jetway or stairtruck is found (all `availability == 'no'`), raises `ValueError`.

#### Output

- Writes 5 fields into `sly_data`: `gate_id`, `deplaning_equipment_id`, `deplaning_equipment_type`, `deplaning_equipment_readiness_time`, `deplaning_equipment_score`
- Updates `gate_equipments_base.csv` on disk (marks selected unit unavailable)
- Returns the `gate_dict` dictionary

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_gate_selection.aircraft_gate_selection.TrackerAPI`

Manages shared turnaround state. Called in Step 1 to retrieve identity parameters if missing, and again in Step 2 to persist the selection results.

> Note: The class path uses the `AirlineTurnaround.` root prefix, consistent with `deplaning_path_selector` and all other coded tools in the system.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `deplaning_equipment_type`, `deplaning_equipment_id`, `deplaning_equipment_readiness_time`, `deplaning_equipment_score`, `flight_number`, `gate_id`

**Return fields:**
`aircraft_type`, `deplaning_equipment_type`, `deplaning_equipment_id`, `deplaning_equipment_readiness_time`, `deplaning_equipment_score`, `flight_number`, `gate_id`

> Note: In this network the tracked fields and return fields are identical — `TrackerAPI` returns everything it tracks. This is different from all other networks where return fields are a strict subset of tracked fields.

> Note: The HOCON `TrackerAPI` description references two fields — `"engines_stop_status"` and `"wheels_chucks_installation_status"` (typo: "chucks" not "chocks"). Both are stale copy-paste artifacts — neither field is tracked by this network's Python config.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. Equipment Inventory — gate_equipments_base.csv

The CSV is the data source for all gate selection decisions. It is **mutable** — each successful `deplaning_path_selector` call marks the selected unit's `availability` as `no` and writes the file back to disk.

### Schema

|-----------------------------------|---------|---------------------------------------------------|
| Column                            | Type    | Description                                       |
|-----------------------------------|---------|---------------------------------------------------|
| `unit_id`                         | string  | Unique identifier for the equipment unit          |
| `type`                            | string  | `jetway` or `stairtruck`                          |
| `gate_id`                         | string  | Gate the unit is associated with                  |
| `aircraft_type`                   | string  | Aircraft type this unit serves (e.g. `B747`)      |
| `availability`                    | string  | `yes` or `no` — whether the unit is available     |
| `readiness`                       | integer | Minutes until unit is ready for deployment        |
| `air_conditioning_unit_readiness` | string  | `yes`/`no` — ACU readiness at this gate           |
| `ground_power_unit_readiness`     | string  | `yes`/`no` — GPU readiness at this gate           |
| `wheelchocks_readiness`           | string  | `yes`/`no` — Chocks readiness at this gate        |
| `tug_readiness`                   | string  | `yes`/`no` — Tug readiness at this gate           |
| `score`                           | float   | Pre-computed `1/(1+readiness)` — higher is better |
|-----------------------------------|---------|---------------------------------------------------|

### Current inventory (B747)

The baseline CSV contains 61 units for B747:
- 40 jetways (gates `A1`–`A40`): readiness 7–24 min; 3 pre-marked unavailable (`A4`, `A9`, `A24`, `A29`)
- 20 stairtrucks (gates `B1`–`B20`): readiness 17–21 min; all initially available

### Selection result (initial state)

Given all units available, the first call for a B747 will select:
- **Best jetway:** `jetway_05` at gate `A5`, readiness 9 min, score ≈ 0.100
- **Best stairtruck:** `stairtruck_03` / `stairtruck_08` / `stairtruck_13` / `stairtruck_18` at `B3`/`B8`/`B13`/`B18`, readiness 17 min, score ≈ 0.056

→ **Winner: jetway (9 min < 17 min)**

---

## 7. External Tool Dependencies

This network has no active external tool dependencies. The four sub-agent tools (`jetway_agent`, `stairtruck_agent`, `jetway_park_agent`, `stairtruck_park_agent`) are fully commented out in the HOCON and Python files.

---

## 8. Sample Queries

```
# Standard invocation
"Assign a gate for the parking flight AF84 which is a B747."

# Alternative phrasing
"Flight AF84 landed minutes ago. This B747 needs a gate assignment."
```

---

## 9. Example Execution Trace

**Input:**
> "Assign a gate for the parking flight AF84 which is a B747."

**Execution steps:**

1. `TrackerAPI` called (Step 1) — confirms `flight_number=AF84`, `aircraft_type=B747`
2. `deplaning_path_selector` called (Step 2) — reads CSV, selects best available unit
3. `TrackerAPI` called — persists `gate_id`, `deplaning_equipment_type`
4. Summary returned

**Output:**

```
**************************************
* Summary of aircraft gate selection *
**************************************
** flight number                      **: AF84
** aircraft type                      **: B747
** gate id                            **: A5
** deplaning equipment type           **: jetway
** deplaning equipment id             **: jetway_05
** deplaning equipment readiness time **: 9
** deplaning equipment score          **: 0.1
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "gate_id": "A5",
  "deplaning_equipment_type": "jetway",
  "deplaning_equipment_id": "jetway_05",
  "deplaning_equipment_readiness_time": 9,
  "deplaning_equipment_score": 0.1
}
```

---

## 10. Known Issues and Maintenance Notes

| Issue | Location | Notes |
|---|---|---|
| `aircraft_direction` and `gate_selection_status` do not exist | Prior documentation | These fields appear in the old doc as input parameters and tracked fields. Neither exists anywhere in HOCON, Python, or CSV. Remove from all external contracts. |
| CSV mutation is not thread-safe | `aircraft_gate_selection.py` lines 94–95 | `deplaning_path_selector` writes the entire CSV back to disk after each selection. Concurrent calls for different flights will race on the same file, potentially producing duplicate selections or corrupted availability state. |
| CSV path is hardcoded in constructor | `aircraft_gate_selection.py` line 24 | Path is `Path.cwd() / "coded_tools" / "AirlineTurnaround" / ...`. If the working directory differs from the expected root, the file will not be found and the tool will raise `FileNotFoundError`. |
| `if __name__ == "__main__"` inside class body | `aircraft_gate_selection.py` lines 101–103 | The `__main__` block is indented inside the `invoke` method body. It will never execute and references an undefined function `get_best_gate`. Dead code. |

---

## 11. Extensibility Guidance

- Add file locking (e.g. `filelock`) around CSV read-write operations to prevent race conditions under concurrent load
- Consider replacing the CSV with an in-memory store or database for production deployments
- Generalize beyond B747 by adding entries for other aircraft types to `gate_equipments_base.csv`

---

## 12. Compliance Notice

This network models simulated airport gate management workflows and is intended for software prototyping and workflow automation development. It is not certified for real-world airport operational control systems.
