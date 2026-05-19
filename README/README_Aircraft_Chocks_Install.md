# Aircraft Chocks Install
## Agentic AI Network – README

> **Configuration file:** `aircraft_chocks_install.hocon`
> **Implementation file:** `aircraft_chocks_install.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Install wheel chocks on an aircraft that has arrived at the gate, securing it against unintended movement and enabling all subsequent ground operations.

---

## 1. Overview

`aircraft_chocks_install` is one of the earliest-executing networks in the **AirlineTurnaround** agentic system. Wheel chocks installation is a foundational ground safety step — it gates ACU connection, baggage unloading, catering loading, cabin cleaning, and other downstream turnaround operations.

The network combines:

- An LLM-based orchestration agent (`wheels_chocks_agent`) that interprets intent and drives the workflow
- One coded execution tool (`wheels_chocks_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python

This is one of the simplest networks in the system: a single prerequisite (aircraft on blocks), no external tool dependencies, and no prerequisite resolution loop — if the aircraft is not on blocks, the network aborts rather than waiting or delegating.

---

## 2. Repository Structure

```
aircraft_chocks_install.hocon        # Agent network configuration
aircraft_chocks_install.py           # Coded tool implementations (wheels_chocks_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (included but no external tools used by this network)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
wheels_chocks_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                  (Coded tool: read/write turnaround state via sly_data)
   │
   └── wheels_chocks_operator      (Coded tool: install wheel chocks)
```

### Design principles

- **Single hard prerequisite:** The aircraft must be on blocks. If not, the network stops and reports; it does not attempt to resolve or wait.
- **Minimal footprint:** No external tool dependencies. The workflow is: read state → check → install → persist → report.
- **Tool-first execution:** The LLM orchestrates; physical installation is performed by `wheels_chocks_operator`.
- **sly_data as shared state:** Both tools communicate through `sly_data` — the installation result flows to upstream and downstream networks without re-passing through the LLM.

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

### 5.1 wheels_chocks_agent (LLM Orchestrator)

The entry-point agent. It reads flight state, enforces the on-blocks prerequisite, calls the operator, and returns the summary.

> Note: The agent is named `wheels_chocks_agent` in the HOCON. The previous documentation referred to it as `aircraft_chocks_install_agent`, which does not match the actual runtime tool name.

#### Input parameters

|-------------------------------------|--------|:--------:|------------------------------------------------|
| Parameter                           | Type   | Required | Description                                    |
|-------------------------------------|--------|:--------:|------------------------------------------------|
| `flight_number`                     | string | ✅       | Flight identifier                              |
| `aircraft_type`                     | string | ✅       | Aircraft model/type                            |
| `flight_status`                     | string | ✅       | Flight status (expected: contains `on blocks`) |
| `gate_id`                           | string | ✅       | Gate where the aircraft is parked              |
| `wheels_chocks_installation_status` | string | ❌       | Current or previous installation status        |
|-------------------------------------|--------|:--------:|------------------------------------------------|

#### Orchestration flow

1. Call `TrackerAPI` — read and store `flight_status` (and all other available parameters).
2. If `flight_status` is not `on blocks` → report that chocks cannot be installed and stop.
3. If `flight_status` is `on blocks` → call `wheels_chocks_operator`. Wait for response.
4. Call `TrackerAPI` again to persist `wheels_chocks_installation_status`.
5. Return the formatted summary block.

> Note: The orchestrator instructions say to check that the user provides `flight_status` as `on blocks` or `landed`. `landed` is accepted in the instruction text but the coded operator only sets `installed` when both `on` and `blocks` are in the status string — `landed` alone would not trigger installation.

#### sly_data contract

| Direction | Parameters |
|---|---|
| **To upstream** | `wheels_chocks_installation_status` |
| **From upstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status` |
| **To downstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `wheels_chocks_installation_status` |

> Note: All four sly_data allow blocks (`to_upstream`, `from_upstream`, `to_downstream`, `from_downstream`) are defined in the HOCON. `wheels_chocks_installation_status` is propagated both upstream and downstream, making it directly available to adjacent networks such as `aircraft_acu_connect`.

#### Down-chain tools

```
["TrackerAPI", "wheels_chocks_operator"]
```

---

### 5.2 wheels_chocks_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_chocks_install.aircraft_chocks_install.wheels_chocks_operator`

Performs the chocks installation action. It validates all required parameters, checks that `flight_status` contains both `on` and `blocks`, sets `wheels_chocks_installation_status = installed`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

> Note: The previous documentation referred to this tool as `chocks_operator`. The actual class and HOCON name is `wheels_chocks_operator`.

#### Input parameters

|-------------------------------------|--------|:--------:|------------------------------------------------|
| Parameter                           | Type   | Required | Source priority                                |
|-------------------------------------|--------|:--------:|------------------------------------------------|
| `flight_number`                     | string | ✅       | `args` → `sly_data`                            |
| `aircraft_type`                     | string | ✅       | `args` → `sly_data`                            |
| `flight_status`                     | string | ✅       | `args` → `sly_data`                            |
| `gate_id`                           | string | ✅       | `args` → `sly_data`                            |
| `wheels_chocks_installation_status` | string | ❌       | `args` → `sly_data` (read after install logic) |
|-------------------------------------|--------|:--------:|------------------------------------------------|

#### Installation logic

`wheels_chocks_installation_status` is set to `installed` when `flight_status` (lowercased) contains both `on` and `blocks`.

If the condition is not met, the status remains `pending` (the initial value) and `sly_data` is not updated.

#### Code logic anomaly

The operator contains a significant logic issue worth noting:

```python
# Line 107-108: First set of the installation status
if (('on' in flight_status) & ('blocks' in flight_status)):
    wheels_chocks_installation_status = 'installed'

# Lines 111-114: OVERWRITES the value just set
wheels_chocks_installation_status = args.get("wheels_chocks_installation_status", None)
if not wheels_chocks_installation_status:
    wheels_chocks_installation_status = sly_data.get("wheels_chocks_installation_status")

# Lines 117-118: Second (redundant) set — this is the one that actually persists
if (('on' in flight_status) & ('blocks' in flight_status)):
    wheels_chocks_installation_status = 'installed'
```

The first `installed` assignment (lines 107–108) is immediately overwritten by reading from `args`/`sly_data` (lines 111–114). If `args` or `sly_data` contains a previous status value (e.g. `pending`), that value temporarily replaces `installed` before being corrected by the second conditional (lines 117–118). In practice this produces the correct final result, but the intermediate overwrite is a latent bug — if the second block were ever removed or the flow changed, the first assignment would be lost silently.

#### Output

- Writes `wheels_chocks_installation_status` into `sly_data`
- Returns `wheels_chocks_installation_status` string (`installed` or `pending`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_chocks_install.aircraft_chocks_install.TrackerAPI`

Manages shared turnaround state. Called before the operator to read current flight status, and again after the operator to persist the installation result.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is the most minimal in the system:

**Tracked fields:**
`aircraft_type`, `flight_number`, `flight_status`, `gate_id`, `wheels_chocks_installation_status`

**Return fields:**
`flight_status`, `wheels_chocks_installation_status`

> Note: The HOCON `TrackerAPI` schema exposes a broader set of LLM-facing parameters than this network uses (including `ground_services_request_type`, `wheels_chocks_readiness_status`, `gpu_readiness_status`, `acu_connection_status`, `gpu_connection_status`, `engines_stop_status`, `jetbridge_connection_status`, and `door_opening_status`). The HOCON field names themselves use the correctly spelled `wheels_chocks_*` form (matching Python); only some description strings inside the schema use the unspaced `wheelchocks` term. The Python field names are what actually flow through `sly_data`. This descriptive inconsistency has no runtime impact but may confuse LLM tool-call generation if it reads the schema description literally.

---

## 6. External Tool Dependencies

This network has no external tool dependencies. The `registries/aaosa_basic.hocon` include is present in the HOCON header but no external tools are listed in the agent's `tools` array.

---

## 7. Sample Queries

```
# Standard invocation
"The B747 aircraft of flight AF84 is on blocks at gate A1. Install wheels chocks."
```

---

## 8. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 is on blocks at gate A1. Install wheels chocks."

**Execution steps:**

1. `TrackerAPI` called — reads: `flight_status=on blocks`
2. Flight status check: on blocks ✅
3. `wheels_chocks_operator` called — returns `wheels_chocks_installation_status=installed`
4. `TrackerAPI` called again — persists `wheels_chocks_installation_status=installed`
5. Summary returned

**Output:**

```
**************************************
* Summary of aircraft chocks install *
**************************************
** flight status **:                       on blocks
** Wheels chocks installation status **:   installed
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "wheels_chocks_installation_status": "installed"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Notes |
|---|---|---|
| Double-assignment logic anomaly in operator | `aircraft_chocks_install.py` lines 107–118 | First `installed` assignment is immediately overwritten by reading from `args`/`sly_data` before being re-set. Produces correct output today but is fragile. Consolidate into a single assignment after args/sly_data lookup. |

---

## 10. Extensibility Guidance

- Consolidate the double-assignment logic in `wheels_chocks_operator` into a single clean conditional to eliminate the fragile overwrite pattern
- Align `wheelchocks` references inside HOCON description strings with the correctly spelled `wheels_chocks_*` form used by the field names and Python
- Remove the stray bareword token `wheels_chocks_installation_status` that appears between the `wheels_chocks_agent` and `wheels_chocks_operator` blocks in the HOCON
- Add `wheels_chocks_readiness_status` tracking if a pre-check step is added before installation
- Add idempotency guard: if `wheels_chocks_installation_status` is already `installed` in `sly_data`, skip the operator call and return immediately
- Add sensor-based confirmation of physical chocks placement for production environments

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety systems.
