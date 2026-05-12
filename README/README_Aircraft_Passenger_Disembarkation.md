# Aircraft Passenger Disembarkation
## Agentic AI Network – README

> **Configuration file:** `aircraft_disembark.hocon`
> **Implementation file:** `aircraft_disembark.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Disembark passengers from an aircraft at the gate during turnaround, after verifying the aircraft is on blocks, deplaning equipment is connected, and the aircraft door is open.

---

## 1. Overview

`aircraft_disembark` is an agentic network that orchestrates passenger disembarkation for an arriving aircraft. It is part of the broader **AirlineTurnaround** agentic system.

The network combines:

- An LLM-based orchestration agent (`passenger_disembark_agent`) that interprets intent and drives the workflow
- One coded execution tool (`passenger_disembark_operator`) implemented in Python
- A shared state manager (`TrackerAPI`) also implemented in Python
- Three external tool references (`aircraft_jetbridge_connect`, `aircraft_stairtruck_connect`, `aircraft_door_opening`) resolved from the shared registry `registries/aaosa_basic.hocon`

This network shares the same access-prerequisite pattern as `aircraft_baggage_unload`, `aircraft_crew_debrief`, and `aircraft_crew_exit` (equipment connected + door open), with the additional hard gate of requiring `flight_status` to contain `on blocks` or `block`. A distinctive feature compared to most other networks is its **fail-fast prerequisite resolution** — each external prerequisite tool is called at most once; if the condition is still unmet after that single call, the network stops and reports failure rather than retrying.

---

## 2. Repository Structure

```
aircraft_disembark.hocon             # Agent network configuration
aircraft_disembark.py                # Coded tool implementations (passenger_disembark_operator, TrackerAPI)
registries/aaosa_basic.hocon         # Shared registry (aircraft_jetbridge_connect, aircraft_stairtruck_connect, aircraft_door_opening)
```

---

## 3. System Architecture

```
User / Caller
   │
   ▼
passenger_disembark_agent  (LLM Orchestrator)
   │
   ├── TrackerAPI                                       (Coded tool: read/write turnaround state via sly_data)
   │
   ├── passenger_disembark_operator                     (Coded tool: perform passenger disembarkation)
   │
   ├── /AirlineTurnaround/aircraft_jetbridge_connect    (External tool — jetway gates only)
   │
   ├── /AirlineTurnaround/aircraft_stairtruck_connect   (External tool — stairtruck gates only)
   │
   └── /AirlineTurnaround/aircraft_door_opening         (External tool — when door not yet open)
```

### Design principles

- **Flight-status hard gate:** Before any equipment check, the agent verifies `flight_status` contains `on blocks` or `block`. If not, it stops immediately. This is an earlier gate than most other equipment-access networks in the system.
- **Fail-fast prerequisite resolution:** Each external tool (equipment connect, door opening) is called at most once. If the condition remains unmet after a single call, the agent stops and reports failure rather than looping.
- **Equipment-aware routing:** The agent routes the equipment connection step to the correct external tool based on `deplaning_equipment_type`. Unknown type accepts either connection status.
- **Tool-first execution:** All operational actions are performed by coded or external tools; the LLM orchestrates, not executes.
- **sly_data as shared state:** Parameters flow between tools without re-passing through the LLM.
- **Structured output:** The agent returns a formatted summary block on completion.

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

### 5.1 passenger_disembark_agent (LLM Orchestrator)

The entry-point agent. It resolves prerequisites in a strict sequential order, enforces the on-blocks gate, calls one external tool per unmet prerequisite (stopping on failure), executes disembarkation, and returns the final summary.

The instructions use `CRITICAL: sequential executor` language and explicit `STEP` labels — the same enforcement pattern as `aircraft_cabin_cleaning`.

#### Input parameters

| Parameter | Type | Required | Description |
|---|---|:---:|---|
| `flight_number` | string | ✅ | Flight identifier |
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `gate_id` | string | ✅ | Gate where the aircraft is parked |
| `flight_status` | string | ✅ | Flight status (expected: contains `on blocks` or `block`) |
| `door_opening_status` | string | ✅ | Aircraft door state (expected: contains `open`) |
| `jetbridge_connection_status` | string | ❌ | Jetbridge state — null on stairtruck gates |
| `stairtruck_connection_status` | string | ❌ | Stairtruck state — null on jetway gates |
| `deplaning_equipment_type` | string | ❌ | Equipment at gate: `jetway`/`jetbridge` or `stairtruck`/`stair` |

#### Orchestration flow

1. **STEP 1 — Resolve prerequisites:** Call `TrackerAPI` with all available parameters. Read back all values.
2. **STEP 2 — Verify flight status:** `flight_status` must contain `on blocks` or `block`. If not → stop and report `"Aircraft is not yet on blocks. Passengers cannot be disembarked."`
3. **STEP 3 — Ensure deplaning equipment is connected (ONE call if needed):**
   - `jetway`/`jetbridge` → require `jetbridge_connection_status` contains `connected`. If not → call `/AirlineTurnaround/aircraft_jetbridge_connect` once.
   - `stairtruck`/`stair` → require `stairtruck_connection_status` contains `connected`. If not → call `/AirlineTurnaround/aircraft_stairtruck_connect` once.
   - Unknown type → either connection status accepted.
   - If still not connected after one call → stop and report failure.
4. **STEP 4 — Ensure door is open (ONE call if needed):** If `door_opening_status` already contains `open` → skip. Otherwise → call `/AirlineTurnaround/aircraft_door_opening` once. If still not open → stop and report failure.
5. **STEP 5 — Execute passenger disembarkation:** Call `passenger_disembark_operator` with `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status`. Extract `passenger_disembarkation_status` from response. Call `TrackerAPI` to persist it.
6. **RETURN SUMMARY.**

> Note: The fail-fast design (one call per prerequisite, stop on failure) contrasts with `aircraft_baggage_unload` and `aircraft_crew_exit` which loop back to re-check after each external tool call. This network treats a single failed resolution attempt as a terminal error.

#### sly_data contract

| Direction | Parameters |
|---|---|
| **To upstream** | `passenger_disembarkation_status` |
| **To downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `door_opening_status`, `passenger_disembarkation_status` |
| **From upstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `door_opening_status`, `passenger_disembarkation_status` |
| **From downstream** | `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `door_opening_status`, `passenger_disembarkation_status` |

> Note: `passenger_disembarkation_status` propagates upstream only as a single field. The full 9-field context set flows to and from downstream and upstream, matching the pattern established in `aircraft_crew_exit`.

#### Down-chain tools

```
["TrackerAPI", "passenger_disembark_operator", "/AirlineTurnaround/aircraft_door_opening",
 "/AirlineTurnaround/aircraft_jetbridge_connect", "/AirlineTurnaround/aircraft_stairtruck_connect"]
```

---

### 5.2 passenger_disembark_operator (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_disembark.aircraft_disembark.passenger_disembark_operator`

Performs the passenger disembarkation completion check. It validates all required parameters, verifies that at least one piece of deplaning equipment is connected and the door is open, then sets `passenger_disembarkation_status = completed`, writes the result to `sly_data`, and appends a timestamped log entry to `test_debug/airlineturnaround.txt`.

> Note: The previous documentation referred to this tool as `disembarkation_operator`. The actual class and HOCON name is `passenger_disembark_operator`.

#### Input parameters

| Parameter | Type | Required | Source priority |
|---|---|:---:|---|
| `flight_number` | string | ✅ | `args` → `sly_data` |
| `aircraft_type` | string | ✅ | `args` → `sly_data` |
| `flight_status` | string | ✅ | `args` → `sly_data` |
| `gate_id` | string | ✅ | `args` → `sly_data` |
| `door_opening_status` | string | ✅ | `args` → `sly_data` |
| `jetbridge_connection_status` | string | ❌ | `args` → `sly_data` |
| `stairtruck_connection_status` | string | ❌ | `args` → `sly_data` |

#### Disembarkation logic

The operator evaluates `equipment_connected` as:

```
jetbridge_connection_status contains 'connected'
OR
stairtruck_connection_status contains 'connected'
```

`passenger_disembarkation_status` is set to `completed` when both of the following are true (case-insensitive):

- `equipment_connected` is `True`
- `door_opening_status` contains `open`

If `equipment_connected` is False, the tool returns an error string immediately without updating `sly_data`. If the door condition fails after equipment is confirmed connected, `pending` (the initial value) is returned. If `door_opening_status` is missing, the tool also returns an error string.

#### Output

- Writes `passenger_disembarkation_status` into `sly_data`
- Returns `passenger_disembarkation_status` string (`completed` or `pending`)
- Appends a timestamped log line to `test_debug/airlineturnaround.txt`

---

### 5.3 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_disembark.aircraft_disembark.TrackerAPI`

Manages shared turnaround state. Called in Step 1 to read all current values, and again in Step 5 after the operator to persist `passenger_disembarkation_status`.

#### Data resolution priority

For each tracked field:

1. **`sly_data[field]`** — authoritative; returned immediately if present. `args` is ignored for that field.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data` for future calls.
3. **Neither** — field is logged as `NOT_FOUND` and returned as `None`.

#### Configuration

`TrackerAPI` is configuration-driven via a `TrackerConfig` dataclass, resolved in this order: `args['_config']` → `sly_data['_tracker_config']` → default config (lazy-initialized once per request).

The default configuration for this network is:

**Tracked fields:**
`aircraft_type`, `deplaning_equipment_type`, `door_opening_status`, `flight_number`, `flight_status`, `jetbridge_connection_status`, `passenger_disembarkation_status`, `stairtruck_connection_status`

**Return fields:**
`deplaning_equipment_type`, `door_opening_status`, `flight_status`, `jetbridge_connection_status`, `passenger_disembarkation_status`, `stairtruck_connection_status`

> Note: `gate_id` is absent from `FLIGHT_TURNAROUND_TRACKED_FIELDS` even though it is a required parameter for `passenger_disembark_operator`. TrackerAPI will not track or return it; the operator must receive it through `args` on each call. This is the same gap noted in `aircraft_cabin_cleaning`.

> Note: The HOCON `TrackerAPI` tool definition is missing a `"required": []` field in its `parameters` object — the schema closes with just `}`. Consistent with `aircraft_crew_debrief` and `aircraft_crew_exit`. No runtime impact.

---

## 6. External Tool Dependencies

These tools are not defined in this network. They are resolved at runtime from `registries/aaosa_basic.hocon`:

| Tool path | Purpose | Condition triggering call |
|---|---|---|
| `/AirlineTurnaround/aircraft_jetbridge_connect` | Connect jetbridge to aircraft | Equipment not connected on a jetway gate (called once; stops if still unmet) |
| `/AirlineTurnaround/aircraft_stairtruck_connect` | Connect stairtruck to aircraft | Equipment not connected on a stairtruck gate (called once; stops if still unmet) |
| `/AirlineTurnaround/aircraft_door_opening` | Open aircraft door | Door not yet open after equipment confirmed connected (called once; stops if still unmet) |

---

## 7. Sample Queries

```
# All prerequisites already met
"The flight AF84 is on blocks at gate A1. The jetbridge is connected to the plane.
The plane is a B747 and its door is open. Disembark passengers."

# Prerequisites not yet confirmed — agent will resolve them (up to one attempt each)
"The B747 aircraft of flight AF84 is on blocks at gate A1. Disembark passengers."
```

---

## 8. Example Execution Trace

**Input:**
> "The flight AF84 is on blocks at gate A1. The jetbridge is connected to the plane. The plane is a B747 and its door is open. Disembark passengers."

**Execution steps:**

1. `TrackerAPI` called (Step 1) — reads: `flight_status=on blocks`, `jetbridge_connection_status=connected`, `door_opening_status=open`
2. Flight status check: on blocks ✅ (Step 2)
3. Equipment check: jetbridge connected ✅ (Step 3)
4. Door check: open ✅ (Step 4)
5. `passenger_disembark_operator` called — returns `passenger_disembarkation_status=completed` (Step 5)
6. `TrackerAPI` called — persists `passenger_disembarkation_status=completed`
7. Summary returned

**Output:**

```
*********************************
* Summary of aircraft disembark *
*********************************
** flight status                    **: on blocks
** deplaning equipment type         **: jetway
** jet bridge connection status     **: connected
** stairtruck connection status     **: null
** door opening status              **: open
** passenger disembarkation status  **: completed
```

**JSON equivalent:**

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "deplaning_equipment_type": "jetway",
  "jetbridge_connection_status": "connected",
  "stairtruck_connection_status": null,
  "door_opening_status": "open",
  "passenger_disembarkation_status": "completed"
}
```

---

## 9. Known Issues and Maintenance Notes

| Issue | Location | Notes |
|---|---|---|
| Operator name mismatch with prior documentation | `aircraft_disembark.hocon` line 244 | Operator is `passenger_disembark_operator`, not `disembarkation_operator` as previously documented. |
| `gate_id` absent from `FLIGHT_TURNAROUND_TRACKED_FIELDS` | `aircraft_disembark.py` | `gate_id` is required by `passenger_disembark_operator` but not tracked or returned by `TrackerAPI`. Must always be provided through `args`. Same gap as in `aircraft_cabin_cleaning`. |
| HOCON TrackerAPI missing `"required": []` | `aircraft_disembark.hocon` line 366 | `parameters` object closes without `"required": []`. Consistent pattern across `aircraft_crew_debrief`, `aircraft_crew_exit`, and this network. No runtime impact. |
| Log message copy-paste artifact | `aircraft_disembark.py` line 151 | Message reads `"...door {door_opening_status}.  installed. Its passenger disembarkation status is status is {passenger_disembarkation_status}."` — contains `"installed"` (from earlier networks) and duplicated `"status is"`. Also spells `"DISMEMBARKATION"` in print banners (lines 56, 62). |
| Print banner typo | `aircraft_disembark.py` lines 56, 62 | Both debug banners print `"PASSENGER DISMEMBARKATION OPERATOR"` (extra `M`). Should read `"DISEMBARKATION"`. |
| Hardcoded log path comment | `aircraft_disembark.py` line 50 | Commented-out absolute path remains; active path uses `Path.cwd()`. |
| Fail-fast behavior undocumented in previous docs | `aircraft_disembark.hocon` steps 3–4 | The one-call-then-stop design is a meaningful departure from the looping pattern in `aircraft_baggage_unload` and `aircraft_crew_exit`. Worth aligning across networks or explicitly documenting the design intent. |

---

## 10. Extensibility Guidance

- Align fail-fast vs. retry behavior explicitly across the equipment-access networks (`aircraft_baggage_unload`, `aircraft_crew_exit`, `aircraft_crew_debrief`, `aircraft_disembark`) — currently they differ inconsistently
- Add `gate_id` to `FLIGHT_TURNAROUND_TRACKED_FIELDS` so TrackerAPI can persist and return it
- Fix the `"DISMEMBARKATION"` typo in print banners and the log message copy-paste artifacts
- Add `"required": []` to the HOCON TrackerAPI parameters schema for consistency
- Consider adding `engines_stop_status` as a tracked field, since it appears in the HOCON TrackerAPI schema and is operationally relevant to passenger safety

---

## 11. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
