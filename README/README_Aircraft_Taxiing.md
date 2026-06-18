# Aircraft Taxiing
## Agentic AI Network – README

> **Configuration file:** `aircraft_taxiing.hocon`
> **Implementation file:** `aircraft_taxiing.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Execute the complete taxi-in sequence for a landed aircraft — obtaining ground clearance, verifying ground equipment readiness, then taxiing to the assigned gate and setting `flight_status = 'on blocks'`.

---

## 1. Overview

`aircraft_taxiing` is one of the most architecturally sophisticated networks in the AirlineTurnaround system. It integrates three external networks (ground traffic, ground readiness), two LLM agents, and a coded execution tool into a single coordinated sequence, with carefully engineered `flight_status` normalisation to handle verbose LLM phrases.

The network combines:

- `aircraft_taxi_agent` — LLM orchestrator; entry point, coordinates all four steps
- `aircraft_taxiing_agent` — HOCON name for the coded class `execute_aircraft_taxiing`
- `execute_aircraft_taxiing` — coded tool; normalises flight_status and sets `'on blocks'` on successful taxiing
- `TrackerAPI` — coded tool with extended `_normalise_field` logic for flight_status canonicalisation
- Two external networks: `aircraft_ground_traffic` (ground clearance) and `aircraft_ground_readiness` (equipment readiness)

A comment in the Python file (line 30) dates the current implementation to post-20260123, noting it addresses "inconsistent behaviour of the previous version."

> **Important note on previous documentation:** The old doc described a flat `aircraft_taxiing_agent` → `taxiing_operator` structure. The actual entry point is `aircraft_taxi_agent`. There is no `taxiing_operator`, no `taxi_status` field, no `assigned_route`, and no conflict detection. The network's core innovation is `flight_status` normalisation, which the old doc did not mention at all.

---

## 2. Repository Structure

```
aircraft_taxiing.hocon              # Agent network configuration
aircraft_taxiing.py                 # Coded tool implementations (execute_aircraft_taxiing, TrackerAPI)
registries/aaosa_basic.hocon        # Shared registry (aircraft_ground_traffic, aircraft_ground_readiness)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
aircraft_taxi_agent  (LLM Orchestrator — STEP pattern — entry point)
   │
   ├── TrackerAPI                                      (Coded tool: normalising sly_data-first state management)
   │
   ├── /AirlineTurnaround/aircraft_ground_traffic      (External — STEP 2: ground clearance)
   │
   ├── /AirlineTurnaround/aircraft_ground_readiness    (External — STEP 3: ACU/GPU/chocks readiness)
   │
   └── aircraft_taxiing_agent                          (HOCON name for execute_aircraft_taxiing coded tool)
          ↳ execute_aircraft_taxiing                   (Coded tool: normalise flight_status, set 'on blocks')
```

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

### 5.1 aircraft_taxi_agent (LLM Orchestrator — Entry Point)

The top-level agent. It verifies flight status, obtains ground clearance, checks ground equipment readiness, then delegates the actual taxiing to `aircraft_taxiing_agent` (the coded tool).

> Note: The true entry point is `aircraft_taxi_agent`. `aircraft_taxiing_agent` in the HOCON is the name given to the coded tool `execute_aircraft_taxiing` — not an LLM orchestrator. The previous documentation called the orchestrator `aircraft_taxiing_agent`, which now names the coded tool.

#### Input parameters

| Parameter                      | Type   | Required | Description                                      |
|--------------------------------|--------|:--------:|--------------------------------------------------|
| `flight_number`                | string |    ✅     | Flight identifier                                |
| `aircraft_type`                | string |    ✅     | Aircraft model/type                              |
| `flight_status`                | string |    ✅     | Expected: contains `landed`, `taxi`, or `blocks` |
| `gate_id`                      | string |    ✅     | Destination gate                                 |
| `ground_clearance_type`        | string |    ❌     | e.g. `taxi in` or `taxi out`                     |
| `ground_clearance_status`      | string |    ❌     | Expected: contains `clear` or `grant`            |
| `wheels_chocks_readiness_status` | string |    ❌     | From `aircraft_ground_readiness`                 |
| `acu_readiness_status`         | string |    ❌     | From `aircraft_ground_readiness`                 |
| `gpu_readiness_status`         | string |    ❌     | From `aircraft_ground_readiness`                 |

#### Orchestration flow (STEP pattern)

**STEP 1 — Verify flight status:**
`flight_status` must contain `'landed'`, `'taxi'`, or `'blocks'`. If not → stop and report.

**STEP 2 — Resolve ground clearance (ONE call maximum):**
If `ground_clearance_status` already contains `'clear'` or `'grant'` → skip to STEP 3. Otherwise call `/AirlineTurnaround/aircraft_ground_traffic` once with all parameters and `ground_clearance_type='taxi in'`. Wait. Store results. If clearance not granted → stop and report failure.

**STEP 3 — Resolve ground services readiness (ONE call, non-blocking):**
Call `/AirlineTurnaround/aircraft_ground_readiness` once with `aircraft_type`, `gate_id`. Wait. Extract and store the three readiness statuses via `TrackerAPI`. **Continue to STEP 4 regardless of readiness values.** Report any unready items in the summary only.

**STEP 4 — Execute taxiing:**
Call `aircraft_taxiing_agent` with all parameters. Wait for response.
- The response string IS the new `flight_status` value.
- If response contains `'on blocks'` or `'block'` → taxiing succeeded.
- Otherwise → report failure: `"STEP 4 FAILED: taxiing did not complete."`
- **Do NOT call TrackerAPI after this step.**

The instructions explain the reason in detail: the taxiing coded tool has already written `flight_status='on blocks'` into sly_data directly. Reading TrackerAPI would risk returning the stale incoming `flight_status` that was present before taxiing ran.

**RETURN SUMMARY:** `flight_status` is hardcoded as `'on blocks'` in the summary template — the instructions explicitly say "Write this hardcoded value into the summary. Do NOT substitute a variable."

> Note: STEP 3 is **non-blocking** — ground equipment readiness is checked informatively and does not gate the taxi execution. This is a deliberate design choice: the aircraft can taxi even if ACU/GPU/chocks are not yet confirmed ready, but those unready items are flagged in the summary. This differs from the jetbridge/stairtruck networks where readiness is a hard gate.

#### sly_data contract

| Direction           | Parameters |
|---------------------|------------|
| **To upstream**     | `flight_status` |
| **From upstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `assigned_runway_id`, `ground_clearance_type`, `ground_clearance_status`, `acu_readiness_status`, `gpu_readiness_status`, `wheels_chocks_readiness_status` |
| **To downstream**   | `flight_number`, `aircraft_type`, `gate_id`, `flight_status`, `assigned_runway_id`, `ground_clearance_type`, `ground_clearance_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `gate_id`, `ground_clearance_type`, `ground_clearance_status`, `acu_readiness_status`, `gpu_readiness_status`, `wheels_chocks_readiness_status` |

#### Down-chain tools

```
["aircraft_taxiing_agent", "TrackerAPI",
 "/AirlineTurnaround/aircraft_ground_readiness",
 "/AirlineTurnaround/aircraft_ground_traffic"]
```

---

### 5.2 aircraft_taxiing_agent / execute_aircraft_taxiing (Coded Tool)

**HOCON name:** `aircraft_taxiing_agent`
**Python class:** `AirlineTurnaround.aircraft_taxiing.aircraft_taxiing.execute_aircraft_taxiing`

The coded execution tool. It reads all parameters using the `_from_sly_or_args` helper (sly_data-first), applies the `flight_status` normalisation pipeline, evaluates the taxiing condition, and returns the final `flight_status` string.

#### `flight_status` normalisation (in-tool)

A canonical normalisation is applied before any condition check:

```python
if 'land' in flight_status:   → 'landed'
elif 'taxi' in flight_status: → 'taxiing'
elif 'block' in flight_status:→ 'on blocks'
```

The normalised value is immediately written back to `sly_data["flight_status"]`. This prevents verbose LLM-extracted phrases like `"landed on runway 19R"` from propagating to downstream agents that expect `'landed'`.

#### Input parameters (sly_data-first via `_from_sly_or_args`)

| Parameter                        | Required | Notes                          |
|----------------------------------|:--------:|--------------------------------|
| `flight_number`                  |    ✅     |                                |
| `aircraft_type`                  |    ✅     |                                |
| `flight_status`                  |    ✅     | Normalised before use          |
| `gate_id`                        |    ✅     |                                |
| `assigned_runway_id`             |    ✅     |                                |
| `ground_clearance_type`          |    ✅     | Lowercased before use          |
| `ground_clearance_status`        |    ❌     | Lowercased before use          |
| `gpu_readiness_status`           |    ✅     | Read but not used in condition |
| `wheels_chocks_readiness_status` |    ✅     | Read but not used in condition |
| `acu_readiness_status`           |    ❌     | Read but not used in condition |

> Note: The HOCON `required` list for `aircraft_taxiing_agent` is `["flight_number", "aircraft_type", "ground_clearance_type", "flight_status", "assigned_runway_id", "gate_id", "gpu_readiness_status", "wheels_chocks_readiness_status"]`. `acu_readiness_status` and `ground_clearance_status` are declared in `properties` but are not in `required`.

> Note: Only `flight_status` and `ground_clearance_status` influence the taxiing condition. The three readiness statuses (`gpu_readiness_status`, `wheels_chocks_readiness_status`, `acu_readiness_status`) are read and printed but play no role in whether taxiing proceeds — consistent with STEP 3 being non-blocking.

#### Taxiing condition

```python
if (('land' in flight_status OR 'taxi' in flight_status)
    AND ('clear' in ground_clearance_status OR 'grant' in ground_clearance_status)):
    flight_status = 'on blocks'
```

Both flight status keywords (`'land'`, `'taxi'`) and clearance keywords (`'clear'`, `'grant'`) use substring matching. Note: after the in-tool normalisation, `flight_status` will already be `'landed'` or `'taxiing'`, so these are effectively checking the canonical tokens.

#### Output

- If condition met: writes `flight_status = 'on blocks'` into `sly_data`; returns `'on blocks'`; appends log entry
- If condition not met: returns the normalised `flight_status` string without updating sly_data (the value set by normalisation on line 129 remains in sly_data)
- Returns `flight_status` string in all cases — not a structured dict

> Note: The log message on line 289 contains a typo: `"has taied to gate"` — should be `"has taxied to gate"`.

> Note: Class-level `print()` statements at lines 38–44 execute at **import time**, not per invocation. The banner `"EXECUTE AIRCRAFT TAXIING CALLED FOR AIRCRAFT TAXIING"` appears once on module load.

---

### 5.3 TrackerAPI (Coded Tool — Extended with Normalisation)

**Class:** `AirlineTurnaround.aircraft_taxiing.aircraft_taxiing.TrackerAPI`

This TrackerAPI extends the standard sly_data-first implementation with a `_normalise_field` method that canonicalises `flight_status` values on both read and write. This is the only TrackerAPI in the system with field normalisation logic.

#### Normalisation logic

On every read or write of `flight_status`:
- `"land"` in value → `"landed"`
- `"block"` in value → `"on blocks"`
- Mid-transit values like `"TAXIING_IN"` are NOT mapped (left as-is)

The docstring explains: *"the taxiing coded tool sets flight_status='on blocks' directly when taxiing completes."*

#### Configuration

**Tracked fields (HOCON parameters, 11 total):**
`flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `wheels_chocks_readiness_status`, `wheels_chocks_installation_status`, `gpu_readiness_status`, `acu_readiness_status`, `ground_clearance_type`, `ground_clearance_status`, `assigned_runway_id`

**Return fields:** Identical to tracked fields (all 11 returned).

> Note: The TrackerAPI HOCON schema includes `wheels_chocks_installation_status`, which is not declared on the `aircraft_taxi_agent` or `aircraft_taxiing_agent` parameter schemas and is not present in any sly_data allow block.

> Note: `aircraft_direction` appears in the `aircraft_taxi_agent` `to_downstream` and `to_upstream` sly_data allow blocks but is absent from the TrackerAPI parameter schema and from all agent parameter schemas — no producer is defined in this network.

> Note: Class-level `print()` statements at lines 369–375 execute at **import time** — banner `"TRACKER API CALLED FOR AIRCRAFT TAXIING"` prints once on module load.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

| Tool path                                      | Purpose                                | Step   | Blocking?                                  |
|------------------------------------------------|----------------------------------------|--------|--------------------------------------------|
| `/AirlineTurnaround/aircraft_ground_traffic`   | Request and confirm ground clearance   | STEP 2 | Yes — clearance failure stops the workflow |
| `/AirlineTurnaround/aircraft_ground_readiness` | Check ACU/GPU/chocks readiness at gate | STEP 3 | No — workflow continues regardless         |

---

## 7. Field Naming Consistency — Wheelchocks Readiness

All locations in this network use the single field name `wheels_chocks_readiness_status`:

| Location                                                                | Field name used                  |
|-------------------------------------------------------------------------|----------------------------------|
| `aircraft_taxi_agent` agent schema                                    | `wheels_chocks_readiness_status` |
| `aircraft_taxiing_agent` (`execute_aircraft_taxiing`) schema `required` | `wheels_chocks_readiness_status` |
| TrackerAPI Python tracked/return fields                                 | `wheels_chocks_readiness_status` |
| TrackerAPI HOCON schema                                                 | `wheels_chocks_readiness_status` |
| HOCON sly_data allow blocks                                             | `wheels_chocks_readiness_status` |

The field name is consistent across the network. (A separate field `wheels_chocks_installation_status` exists only on the TrackerAPI schema — see Section 5.3.)

---

## 8. Sample Queries

```
# Full information provided
"The B747 aircraft of flight AF84 has landed on runway 19R. The clearance to taxi in
has been granted. The ground power unit, the air conditioning unit and the wheelchocks
are ready. Please taxi the plane to gate A1."
```

---

## 9. Example Execution Trace

**Input:**
> "The B747 aircraft of flight AF84 has landed on runway 19R. The clearance to taxi in has been granted. The GPU, ACU, and wheelchocks are ready. Please taxi the plane to gate A1."

**Execution steps:**

1. STEP 1: `flight_status` contains `'landed'` ✅
2. STEP 2: `ground_clearance_status` contains `'grant'` ✅ — skip `aircraft_ground_traffic` call
3. STEP 3: `aircraft_ground_readiness` called → `acu_readiness_status=ready`, `gpu_readiness_status=ready`, `wheels_chocks_readiness_status=ready`. `TrackerAPI` stores them.
4. STEP 4: `aircraft_taxiing_agent` (`execute_aircraft_taxiing`) called. Flight status normalised `'landed'` → condition met → `flight_status = 'on blocks'`. Returns `'on blocks'`.
5. Summary returned (TrackerAPI NOT called after STEP 4)

**Output:**

```
*******************************
* Summary of aircraft taxiing *
*******************************
** flight number           **: AF84
** aircraft type           **: B747
** gate id                 **: A1
** assigned runway id      **: 19R
** ground clearance type   **: taxi in
** ground clearance status **: granted
** ACU readiness           **: ready
** GPU readiness           **: ready
** wheelchocks readiness   **: ready
** flight status           **: on blocks
```

---

## 10. Known Issues and Maintenance Notes

| Issue                                                                                             | Location                                                          | Severity | Notes                                                                                                                                                                |
|---------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|:--------:|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Agent name mismatch with prior documentation                                                      | `aircraft_taxiing.hocon` lines 88, 278                            |   Low    | Entry point is `aircraft_taxi_agent`; prior doc called the orchestrator `aircraft_taxiing_agent`. That name now refers to the coded tool wrapper.                  |
| Class-level `print()` in `execute_aircraft_taxiing`                                               | `aircraft_taxiing.py` lines 38–44                                 |   Low    | Executes at import time, not per invocation. Banner prints once on module load.                                                                                      |
| Class-level `print()` in `TrackerAPI`                                                             | `aircraft_taxiing.py` lines 369–375                               |   Low    | Same issue — prints at module load.                                                                                                                                  |
| `aircraft_direction` allowed in manager sly_data but no producer defined                          | `aircraft_taxiing.hocon` lines 214, 229                           |   Low    | Field appears in `to_downstream`/`to_upstream` allow blocks of `aircraft_taxi_agent` but is not in any agent or TrackerAPI parameter schema.                       |
| `wheels_chocks_installation_status` on TrackerAPI but nowhere else                                | `aircraft_taxiing.hocon` line 317                                 |   Low    | Tracked by TrackerAPI parameter schema but absent from agent parameter schemas and from all sly_data allow blocks.                                                   |
| Ground equipment readiness is non-blocking (by design)                                            | `aircraft_taxiing.hocon` STEP 3                                   |   Info   | ACU/GPU/chocks not-ready does not prevent taxiing. This is a documented design decision. Consider whether it aligns with operational requirements.                   |
| `'block'` substring in STEP 1 and normalisation                                                   | `aircraft_taxiing.hocon` line 150; `aircraft_taxiing.py` line 125 |   Low    | Matches `"unblocked"`, `"roadblock"`, etc. The canonical normalisation mitigates most risk by mapping first-match.                                                   |
| STEP 4 prohibits TrackerAPI call — documented rationale                                           | `aircraft_taxiing.hocon` lines 184–188                            |   Info   | Documented and intentional. Do not add a TrackerAPI read after STEP 4 without understanding the stale-state risk.                                                    |

---

## 11. Key Differences from Prior Documentation

| Aspect                        | Old documentation        | Actual implementation                                            |
|-------------------------------|--------------------------|------------------------------------------------------------------|
| Entry-point agent name        | `aircraft_taxiing_agent` | `aircraft_taxi_agent`                                          |
| Coded tool name               | `taxiing_operator`       | `execute_aircraft_taxiing`                                       |
| Output field                  | `taxi_status`            | `flight_status` (updated to `'on blocks'`)                       |
| Conflict detection            | Described                | Does not exist                                                   |
| Assigned route returned       | Yes (`["RWY-27", ...]`)  | Does not exist                                                   |
| External dependencies         | None described           | `aircraft_ground_traffic` + `aircraft_ground_readiness`          |
| `flight_status` normalisation | Not mentioned            | Core feature; documented in both operator and TrackerAPI         |
| Ground equipment readiness    | Not mentioned            | STEP 3 — checked non-blockingly                                  |
| Post-20260123 version note    | Not mentioned            | Line 30 comment documents the implementation date and motivation |

---

## 12. Extensibility Guidance

- Either define a producer for `aircraft_direction` (currently allowed by the manager's sly_data but never written by any in-network agent) or remove it from the `to_downstream`/`to_upstream` allow blocks
- Either declare `wheels_chocks_installation_status` on the upstream agent schemas and sly_data allow blocks, or remove it from the TrackerAPI parameter schema

---

## 13. Compliance Notice

This network models simulated aircraft taxiing workflows and is intended for software prototyping and workflow automation development. It is not certified for real-world air traffic control or aviation safety-critical systems.
