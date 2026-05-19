# Aircraft Engines Stop
## Agentic AI Network – README

> **Configuration file:** `aircraft_engines_stop.hocon`
> **Implementation file:** `aircraft_engines_stop.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Stop aircraft engines upon arrival at the gate, after confirming the aircraft is on blocks.

---

## 1. Overview

`aircraft_engines_stop` is one of the earliest-executing networks in the **AirlineTurnaround** agentic system, alongside `aircraft_chocks_install`. Engine shutdown is a foundational safety step — it is a prerequisite called by `aircraft_acu_connect` before ACU connection, and precedes all ground access operations.

The network combines:

- An LLM-based orchestration agent (`engines_stop_agent`) that interprets intent and drives the workflow
- One coded execution tool (`engines_stop_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python

This is the simplest networks in the system structurally: a single hard prerequisite (on blocks), no external tool dependencies, and the smallest TrackerAPI tracked field set (4 fields). It is also the only network with an **interactive user-wait loop** in its orchestration instructions — if the aircraft is not yet on blocks, the agent asks the user to wait and retry rather than simply aborting.

---

## 2. Repository Structure

```
aircraft_engines_stop.hocon          # Agent network configuration
aircraft_engines_stop.py             # Coded tool implementations (engines_stop_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (included but no external tools used)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
engines_stop_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI               (Coded tool: read/write turnaround state via sly_data)
   │
   └── engines_stop_operator    (Coded tool: stop aircraft engines)
```

### Design principles

- **Single hard prerequisite:** The aircraft must be on blocks. If not, the agent enters a wait-and-retry loop, asking the user rather than delegating to an external tool.
- **No external dependencies:** Unlike equipment-access networks, this network resolves all logic internally. No external turnaround networks are called.
- **Tool-first execution:** The LLM orchestrates; the engine shutdown is performed by `engines_stop_operator`.
- **sly_data as shared state:** `engines_stop_status` flows upstream so dependent networks (such as `aircraft_acu_connect`) can read it.

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

### 5.1 engines_stop_agent (LLM Orchestrator)

The entry-point agent. It checks flight status, enters a user-wait loop if the aircraft is not yet on blocks, calls the operator once the prerequisite is met, persists the result, and returns the summary.

> Note: The agent is named `engines_stop_agent` in the HOCON. The previous documentation referred to it as `aircraft_engines_stop_agent`, which does not match the actual runtime tool name.

#### Input parameters

|-----------------------|--------|:--------:|------------------------------------------------|
| Parameter             | Type   | Required | Description                                    |
|-----------------------|--------|:--------:|------------------------------------------------|
| `flight_number`       | string | ✅       | Flight identifier                              |
| `aircraft_type`       | string | ✅       | Aircraft model/type                            |
| `flight_status`       | string | ✅       | Flight status (expected: contains `on blocks`) |
| `gate_id`             | string | ✅       | Gate where the aircraft is parked              |
| `engines_stop_status` | string | ❌       | Current or previous engine stop status         |
|-----------------------|--------|:--------:|------------------------------------------------|

#### Orchestration flow

The instructions use numbered prose steps rather than the `CRITICAL: sequential executor` / `STEP` pattern used by more recent networks:

1. Determine if `flight_status` is provided by the user (expected: `on blocks`).
2. Call `TrackerAPI` — read and store `flight_status`.
3. If `flight_status` contains `on blocks` → skip to step 5.
4. If `flight_status` does not contain `on blocks`:
   - Report to user that engines cannot be stopped while not on blocks.
   - **Wait for user response.**
   - Return to step 2.
5. `flight_status` contains `on blocks` → call `engines_stop_operator`. Wait for response. Save as `engines_stop_status`. Report status.
6. Call `TrackerAPI` to read and confirm `flight_status` and `engines_stop_status`.
7. Return summary.

> Note: Step 4b instructs the agent to "wait for their [user's] responses" — this is unique in the system. No other network's orchestrator is designed to pause and wait for user input mid-workflow. All other networks either abort or delegate to an external tool when a prerequisite is unmet.

> Note: Step 6 is a redundant TrackerAPI call immediately after the operator. It re-reads `flight_status` (already confirmed in step 2) along with `engines_stop_status`. This step adds limited functional value in the normal path and primarily serves as a final-state confirmation before the summary.

#### sly_data contract

|---------------------|--------------------------------------------------------------------------------------|
| Direction           | Parameters                                                                           |
|---------------------|--------------------------------------------------------------------------------------|
| **To upstream**     | `engines_stop_status`                                                                |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`                         |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`                         |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `engines_stop_status`  |
|---------------------|--------------------------------------------------------------------------------------|

> Note: Unlike most other networks, `to_upstream` carries only `engines_stop_status` (a single field). The full context set flows in the other three directions but not back upstream. This is the same pattern as `aircraft_chocks_install`.

#### Down-chain tools

```
["TrackerAPI", "engines_stop_operator"]
```

---

### 5.2 engines_stop_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_engines_stop.aircraft_engines_stop.engines_stop_operator`

Performs the engine stop action. It validates all required parameters, checks that `flight_status` contains both `on` and `blocks`, sets `engines_stop_status = stopped`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

#### Input parameters

|-----------------|--------|:--------:|---------------------|
| Parameter       | Type   | Required | Source priority     |
|-----------------|--------|:--------:|---------------------|
| `flight_number` | string | ✅       | `args` → `sly_data` |
| `aircraft_type` | string | ✅       | `args` → `sly_data` |
| `flight_status` | string | ✅       | `args` → `sly_data` |
| `gate_id`       | string | ✅       | `args` → `sly_data` |
|-----------------|--------|:--------:|---------------------|

#### Engine stop logic

`engines_stop_status` is set to `stopped` when `flight_status` (lowercased) contains both `on` and `blocks`.

If the condition is not met, `running` (the initial value) is returned and `sly_data` is not updated.

#### Output

- Writes `engines_stop_status = 'stopped'` into `sly_data` on success
- Returns `engines_stop_status` string (`stopped` or `running`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_engines_stop.aircraft_engines_stop.TrackerAPI`

Manages shared turnaround state. Called in step 2 to read `flight_status`, and again in step 6 after the operator to confirm the final status.

This network's `TrackerAPI` has the **smallest tracked field set** in the system — just 4 fields — narrowly scoped to what the workflow actually needs.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `engines_stop_status`, `flight_number`, `flight_status`

**Return fields:**
`aircraft_type`, `engines_stop_status`, `flight_number`, `flight_status`

> Note: `gate_id` is absent from `FLIGHT_TURNAROUND_TRACKED_FIELDS` even though it is required by `engines_stop_operator`. TrackerAPI will not track or return it; it must always be provided through `args` on every operator call. This is the same gap present in `aircraft_disembark` and `aircraft_cabin_cleaning`.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`, consistent with `aircraft_chocks_install` and `aircraft_door_opening`.

---

## 6. External Tool Dependencies

This network has no external tool dependencies. The `registries/aaosa_basic.hocon` include is present in the HOCON header but no external tools appear in the agent's `tools` array.

---

## 7. Sample Queries

```
# Standard invocation — aircraft already on blocks
"Flight AF84 is on blocks at gate A1. It's a B747 aircraft. Stop its engines."
```

---

## 8. Example Execution Trace

**Input:**
> "Flight AF84 is on blocks at gate A1. It's a B747 aircraft. Stop its engines."

**Execution steps:**

1. `TrackerAPI` called (step 2) — reads: `flight_status=on blocks`
2. Flight status check: on blocks ✅ (step 3)
3. `engines_stop_operator` called (step 5) — returns `engines_stop_status=stopped`
4. `TrackerAPI` called (step 6) — confirms `engines_stop_status=stopped`, `flight_status=on blocks`
5. Summary returned (step 7)

**Output:**

```
************************************
* Summary of aircraft engines stop *
************************************
** flight status **:        on blocks
** engines stop status **:  stopped
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "engines_stop_status": "stopped"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Notes |
|---|---|---|
| User-wait loop in step 4b | `aircraft_engines_stop.hocon` line 133 | The instruction "wait for their responses" is unique in the system — no other network's orchestrator is designed to pause mid-workflow for user input. This may cause unexpected behavior in fully automated or upstream-called execution contexts where no human is present to respond. |

---

## 10. Extensibility Guidance

- Replace the user-wait loop (step 4b) with a definitive abort or a timed retry when called from an automated upstream network where no user is present
- Add `engines_stop_status` to the HOCON `required` array as optional but validated (e.g. accepted values: `running`, `stopped`) to improve LLM schema guidance

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation safety-critical systems.
