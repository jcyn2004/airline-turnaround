# Aircraft Ground Services
## Agentic AI Network – README

> **Configuration file:** `aircraft_ground_services.hocon` — **not available for this revision**
> **Implementation file:** `aircraft_ground_services.py`
> **Data file:** `aircraft_gate_selection/gate_equipments_base.csv` (shared read-only)
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Provide gate-level equipment readiness checks for ACU, GPU, and wheel chocks at an assigned gate, by reading from the shared gate equipment inventory CSV.

---

## 1. Overview

> **Note on missing HOCON:** The `aircraft_ground_services.hocon` configuration file was not available for this revision. This README is based exclusively on `aircraft_ground_services.py` and the previous production documentation. The agent network topology, orchestration flow, sly_data contracts, and tool registration cannot be verified without the HOCON. Sections that depend on HOCON content are marked accordingly.

`aircraft_ground_services` is an **earlier-generation implementation** in the AirlineTurnaround system. Its Python file contains three standalone readiness-check operators (`execute_air_conditioning_unit_operator`, `execute_ground_power_unit_operator`, `execute_wheels_chocks_operator`) and a `TrackerAPI` scoped only to those three readiness statuses.

This differs significantly from the previous production documentation, which described a high-level orchestration layer coordinating all 11+ turnaround services. The actual Python implementation is a focused equipment readiness layer — likely an earlier version of the functionality now split across `aircraft_ground_acu_setup` and `aircraft_ground_gpu_setup`.

---

## 2. Repository Structure

```
aircraft_ground_services.hocon       # Agent network configuration — NOT AVAILABLE
aircraft_ground_services.py          # Coded tool implementations (3 readiness operators + TrackerAPI)
coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv   # Shared inventory (read-only)
registries/aaosa_basic.hocon         # Shared registry
```

---

## 3. Architectural Position

This network reads equipment readiness from the same `gate_equipments_base.csv` shared by `aircraft_gate_selection`, `aircraft_ground_acu_setup`, and `aircraft_ground_gpu_setup`. Unlike those networks, `aircraft_ground_services.py` bundles all three readiness checks (ACU, GPU, chocks) into a single Python file.

```
gate_equipments_base.csv
   │
   ├── aircraft_gate_selection    ─── deplaning_path_selector (reads + writes availability)
   ├── aircraft_ground_acu_setup  ─── acu_setup (reads air_conditioning_unit_readiness)
   ├── aircraft_ground_gpu_setup  ─── gpu_setup (reads ground_power_unit_readiness)
   └── aircraft_ground_services   ─── all three operators (reads ACU + GPU + chocks readiness)
```

The three readiness operators in this file are functionally equivalent to `acu_setup` and `gpu_setup` in the dedicated setup networks, but with an older implementation style: `sly_data`-first parameter resolution without the `args` fallback pattern used in newer operators, and a direct `None` check rather than the `not value` pattern.

---

## 4. Runtime Configuration

*(HOCON not available — values below are from prior documentation and may not reflect the current HOCON)*

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

---

## 5. Coded Tool Components

### 5.1 execute_air_conditioning_unit_operator

**Purpose:** Read ACU readiness for a given gate from `gate_equipments_base.csv`.

**Class:** `AirlineTurnaround.aircraft_ground_services.aircraft_ground_services.execute_air_conditioning_unit_operator`

#### Constructor

Has an explicit `__init__` with `pass` followed by `print()` statements. The `print()` statements are **after `pass`** inside `__init__` and will execute normally when the class is instantiated. This is different from the class-body-level `print()` issue in `execute_ground_clearance` (which runs at import time).

#### Input parameters

| Parameter | Source priority |
|---|---|
| `aircraft_type` | `sly_data` → `args` |
| `flight_number` | `sly_data` → `args` |
| `gate_id` | `sly_data` → `args` |

> Note: This operator uses `sly_data`-first resolution explicitly written out as two conditional checks (sly_data → if None → check args). This is an older pattern; newer operators use the `_from_args_or_sly` / `_from_sly_or_args` helper functions.

#### Readiness lookup logic

1. Read `gate_equipments_base.csv` from:
   `Path.cwd() / "coded_tools" / "AirlineTurnaround" / "aircraft_gate_selection" / "gate_equipments_base.csv"`
2. Filter by `gate_id`
3. If row found: read `air_conditioning_unit_readiness` from first matching row → store as `acu_readiness_status`
4. If no row found: set `acu_readiness_status = 'off'` (initial value)
5. Write to `sly_data["acu_readiness_status"]`
6. Append a timestamped log entry to `test_debug/airlineturnaround.txt`

**Return value:** `acu_readiness_status` (raw CSV value, e.g. `'yes'` — **not translated** to `'ready'`)

> Note: Unlike `aircraft_ground_acu_setup`'s `acu_setup`, this operator does **not** translate `'yes'` → `'ready'` or `'no'` → `'not ready'`. It returns the raw CSV value. Any downstream agent expecting `'ready'` will need to handle `'yes'` as well.

> Note: The log message incorrectly says `"ground power unit is ready"` even in the ACU operator (line 85) — copy-paste artifact from `execute_ground_power_unit_operator`.

---

### 5.2 execute_ground_power_unit_operator

**Purpose:** Read GPU readiness for a given gate from `gate_equipments_base.csv`.

**Class:** `AirlineTurnaround.aircraft_ground_services.aircraft_ground_services.execute_ground_power_unit_operator`

Structurally identical to `execute_air_conditioning_unit_operator`, differing only in:
- Column read: `ground_power_unit_readiness` (vs. `air_conditioning_unit_readiness`)
- Return field: `gpu_readiness_status` written to `sly_data`
- Print banner text: `GPU OPERATOR`

**Return value:** `gpu_readiness_status` (raw CSV value, e.g. `'yes'` — **not translated**)

> Note: Both the "ready" and "not ready" log messages say `"ground power unit"` — the ACU operator has an incorrect message, and the GPU operator has correct messages.

---

### 5.3 execute_wheels_chocks_operator

**Purpose:** Read wheel chocks readiness for a given gate from `gate_equipments_base.csv`.

**Class:** `AirlineTurnaround.aircraft_ground_services.aircraft_ground_services.execute_wheels_chocks_operator`

Structurally identical to the other two readiness operators, differing only in:
- Column read: `wheelchocks_readiness` *(note: no underscore between "wheel" and "chocks")*
- Initial value: `'off'`
- Return field: `wheels_chocks_readiness_status` written to `sly_data`
- Print banner text: `WHEELS CHOCKS OPERATOR`

**Return value:** `wheels_chocks_readiness_status` (raw CSV value — **not translated**)

> Note: The CSV column name is `wheelchocks_readiness` (consistent with the gate_equipments_base.csv schema). The field written to sly_data is `wheels_chocks_readiness_status` (with full underscore spelling). These are different strings — the column name and the sly_data key use different conventions.

> Note: The print banner on line 249 says `"WHEELS CHOCKSREADINESS INQUIRY"` (missing space between "CHOCKS" and "READINESS").

---

### 5.4 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_ground_services.aircraft_ground_services.TrackerAPI`

The most narrowly scoped TrackerAPI in the system — tracks only 6 fields, all focused on readiness statuses and gate identity.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration

**Tracked fields:**
`acu_readiness_status`, `aircraft_type`, `flight_number`, `gate_id`, `gpu_readiness_status`, `wheels_chocks_readiness_status`

**Return fields:**
`acu_readiness_status`, `aircraft_type`, `flight_number`, `gate_id`, `gpu_readiness_status`, `wheels_chocks_readiness_status`

Tracked fields and return fields are identical — consistent with `aircraft_gate_selection` and the setup networks.

---

## 6. CSV Data Reference

All three operators read from the same `gate_equipments_base.csv` file as `aircraft_gate_selection`, `aircraft_ground_acu_setup`, and `aircraft_ground_gpu_setup`. The relevant columns are:

| Operator | CSV column read |
|---|---|
| `execute_air_conditioning_unit_operator` | `air_conditioning_unit_readiness` |
| `execute_ground_power_unit_operator` | `ground_power_unit_readiness` |
| `execute_wheels_chocks_operator` | `wheelchocks_readiness` |

In the current baseline CSV, all three columns have value `'yes'` for all B747 entries at all gates. The operators return the raw `'yes'` value without translation.

---

## 7. Agent Network Topology

*(HOCON not available — the following is based on the prior production documentation and cannot be verified)*

The prior documentation described a high-level orchestration layer coordinating 11+ turnaround services. Given the actual Python content (three readiness-check operators), the more likely current role of this network is as a **gate equipment readiness service** called by a higher-level orchestrator before individual service networks are activated.

The HOCON is required to determine:
- The actual agent name(s) registered
- Which tools are exposed vs. which are internal
- The sly_data contract (to/from upstream/downstream)
- Whether an LLM orchestrator exists in this network or if the operators are called directly from an upstream network

---

## 8. Sample Queries

*(HOCON not available — inferred from the Python operators and prior documentation)*

```
"The B747 aircraft of flight AF84 has been assigned gate A1.
Report equipment readiness at the gate."
```

---

## 9. Comparison: This Network vs. Dedicated Setup Networks

The three readiness operators in this file duplicate functionality now present in the dedicated setup networks, with notable differences:

| Aspect | `aircraft_ground_services.py` | `aircraft_ground_acu_setup.py` / `aircraft_ground_gpu_setup.py` |
|---|---|---|
| `'yes'` → `'ready'` translation | No — returns raw `'yes'` | Yes — translates to `'ready'` |
| `'no'` → `'not ready'` translation | No — returns raw `'no'` | Yes (ACU setup only) |
| Parameter resolution style | Explicit two-step conditional | Helper functions |
| All three in one file | Yes | Separate files per unit |
| Log message (ACU) | Incorrectly says "ground power unit" | Correct |
| TrackerAPI tracked fields | 6 readiness fields only | 3 fields (unit-specific) |
| Constructor with `print()` | Yes (`__init__` has `print` after `pass`) | No constructor |

---

## 10. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| HOCON not available | — | **Critical** | Agent network topology, tool registration, sly_data contracts, and runtime agent name cannot be verified. Obtain and review `aircraft_ground_services.hocon` before production use. |
| ACU operator log message says "ground power unit" | `aircraft_ground_services.py` line 85 | Medium | `execute_air_conditioning_unit_operator` logs `"ground power unit is ready"` — copy-paste from GPU operator. Should say `"air conditioning unit"`. |
| Raw `'yes'`/`'no'` returned without translation | All three operators | Medium | Unlike `acu_setup` and `gpu_setup`, these operators return the raw CSV value. Downstream agents expecting `'ready'` must also handle `'yes'`. |
| `wheelchocks_readiness` column name vs. `wheels_chocks_readiness_status` sly_data key | `execute_wheels_chocks_operator` | Low | Column read as `wheelchocks_readiness`; written to sly_data as `wheels_chocks_readiness_status`. Different strings — the CSV column and sly_data key use different naming conventions. |
| `print()` in `__init__` after `pass` | All three operator constructors | Low | `pass` followed by `print()` is valid Python but unusual. `pass` is not needed when statements follow. |
| Print banner typo: `"WHEELS CHOCKSREADINESS INQUIRY"` | `execute_wheels_chocks_operator` line 249 | Low | Missing space between "CHOCKS" and "READINESS". |
| TrackerAPI tracks `wheels_chocks_readiness_status` but operators write using different naming | All three operators vs. TrackerAPI | Low | The `wheels_chocks_readiness_status` key written by `execute_wheels_chocks_operator` is tracked by TrackerAPI under the same name — this is consistent. However, if the column name `wheelchocks_readiness` is ever used as a sly_data key elsewhere, it would not be tracked. |

---

## 11. Extensibility Guidance

- Obtain and review `aircraft_ground_services.hocon` to complete this documentation
- Align return value translations with `aircraft_ground_acu_setup` and `aircraft_ground_gpu_setup`: add `'yes'` → `'ready'` and `'no'` → `'not ready'` translations to all three operators
- Fix the ACU operator log message (replace "ground power unit" with "air conditioning unit")
- Consider consolidating this network with the dedicated setup networks (`aircraft_ground_acu_setup`, `aircraft_ground_gpu_setup`) or deprecating this file in favor of them
- Replace the explicit two-step parameter resolution pattern with the `_from_sly_or_args` helper function used in newer operators

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational control systems.
