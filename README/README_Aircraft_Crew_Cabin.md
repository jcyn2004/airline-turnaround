# Aircraft Crew Cabin
## Agentic AI Network – README

> **Configuration file:** `aircraft_crew_cabin.hocon`
> **Implementation file:** `aircraft_crew_cabin.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Execute three cabin-phase turnaround operations — door opening, passenger disembarkation, and crew debrief — routing to the correct branch based on a `task_id` correlation token or instruction text.

---

## 1. Overview

`aircraft_crew_cabin` is a three-branch routing agent within the AirlineTurnaround system. It sits below `aircraft_crew_pilot` in the call chain, handling the specific cabin operations that require the aircraft to be on blocks with doors accessible.

Each call to this network executes exactly one branch, determined by a `task_id` token (primary discriminant) or an `instruction` / inquiry text (fallback). The three branches correspond to turnaround STEPS 10, 11, and 13:

- **BRANCH A** (`STEP_10_DOOR_OPENING`) — open aircraft doors
- **BRANCH B** (`STEP_11_PAX_DISEMBARKATION`) — disembark passengers
- **BRANCH C** (`STEP_13_CREW_DEBRIEF`) — conduct crew debrief

The network contains a notable design decision in BRANCH B: it explicitly instructs the agent **not** to call TrackerAPI for prerequisite resolution, with an inline explanation of why.

No prior documentation existed for this network; this README is based entirely on the source files.

---

## 2. Repository Structure

```
aircraft_crew_cabin.hocon    # Agent network configuration
aircraft_crew_cabin.py       # TrackerAPI implementation (sly_data-first, 22 tracked fields)
registries/aaosa_basic.hocon # Shared registry (leaf operation networks)
```

---

## 3. System Architecture

```
aircraft_crew_pilot  (caller — routes BRANCHes G, H, I here)
   │
   ▼
cabin_crew_agent  (LLM Router — task_id-first branch selection)
   │
   ├── TrackerAPI                                       (Coded tool: sly_data-first state management)
   │
   ├── /AirlineTurnaround/aircraft_door_opening         (BRANCH A)
   │
   ├── /AirlineTurnaround/aircraft_disembark            (BRANCH B)
   │
   └── /AirlineTurnaround/aircraft_crew_debrief         (BRANCH C)
```

> Note: `aircraft_crew_cabin` is NOT called directly by `aircraft_turnaround_manager`. The turnaround manager routes STEPS 10, 11, and 13 to `aircraft_crew_pilot` (BRANCHes G, H, I), which in turn calls `aircraft_crew_cabin`. The HOCON instructions mention it "may be called by the turnaround orchestrator or directly by a user," but in the integrated system the path is always via `aircraft_crew_pilot`.

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

### 5.1 cabin_crew_agent (LLM Router)

The single entry-point agent. It reads the `task_id` field first, matches a branch, executes all steps for that branch in order, and returns the summary. It must not evaluate or execute steps from any other branch once a match is found.

> Note: The agent is named `cabin_crew_agent` in the HOCON. The HOCON metadata description says "Simple agent network using a single LLM-based agent" — generic boilerplate not updated for this network.

#### Input parameters

|-----------------------------------|--------|:--------:|-----------------------------------|
| Parameter                         | Type   | Required | Description                       |
|-----------------------------------|--------|:--------:|-----------------------------------|
| `aircraft_type`                   | string | ✅       | Aircraft model/type               |
| `flight_status`                   | string | ✅       | Expected: contains `on blocks`    |
| `flight_number`                   | string | ✅       | Flight identifier                 |
| `gate_id`                         | string | ❌       | Gate where the aircraft is parked |
| `task_id`                         | string | ❌       | **Primary routing discriminant**  |
| `deplaning_equipment_type`        | string | ❌       | `jetway` or `stairtruck`          |
| `jetbridge_connection_status`     | string | ❌       | Required for BRANCH A             |
| `stairtruck_connection_status`    | string | ❌       | Required for BRANCH A             |
| `acu_connection_status`           | string | ❌       | Required for BRANCH A             |
| `gpu_connection_status`           | string | ❌       | Required for BRANCH A             |
| `wheelchocks_installation_status` | string | ❌       | Required for BRANCH A             |
| `door_opening_status`             | string | ❌       | Required for BRANCH B + C         |
| `passenger_disembarkation_status` | string | ❌       | Required for BRANCH C             |
| `baggage_unload_status`           | string | ❌       | Required for BRANCH C             |
| `crew_debrief_status`             | string | ❌       | Output of BRANCH C                |
| `assigned_runway_id`              | string | ❌       | Contextual field                  |
|-----------------------------------|--------|:--------:|-----------------------------------|

#### Routing logic

The agent reads `task_id` FIRST before any inquiry text. Each branch carries an explicit override note:

|------------------------|--------------|--------------------------------------------------------------------------------------------------------------|
| `task_id` contains     | Branch       | Fallback triggers                                                                                            |
|------------------------|--------------|--------------------------------------------------------------------------------------------------------------|
| `'DOOR_OPENING'`       | **BRANCH A** | `instruction` contains `'open the aircraft door'` / `'open the door'`; or inquiry asks to open the door      |
| `'PAX_DISEMBARKATION'` | **BRANCH B** | `instruction` contains `'disembark passengers'` / `'passenger disembarkation'`; or inquiry asks to disembark |
| `'CREW_DEBRIEF'`       | **BRANCH C** | `instruction` contains `'debrief the crew'` / `'crew debrief'`; or inquiry asks for crew debrief             |
|------------------------|--------------|--------------------------------------------------------------------------------------------------------------|

> Note: The routing comment for each branch says: *"When task_id='STEP_1X_...' is present, this branch MUST execute. It is never irrelevant when this task_id is present."* This overrides the aaosa `Determine`/`Fulfill` protocol which might otherwise classify the network as not relevant.

---

#### BRANCH A — Open the aircraft door

**Triggered by:** `task_id` contains `'DOOR_OPENING'`

**STEP 1 — Verify prerequisites (from args, NOT TrackerAPI):**
- `flight_status` must contain `'on blocks'`
- At least one of `jetbridge_connection_status` or `stairtruck_connection_status` must contain `'connected'`
- If `flight_status` not on blocks → stop: `"Door cannot be opened — aircraft is not yet on blocks."`

**STEP 2 — Execute door opening:**
Call `/AirlineTurnaround/aircraft_door_opening` with: `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `acu_connection_status`, `gpu_connection_status`, `wheelchocks_installation_status`. Extract `door_opening_status`. Call `TrackerAPI` to store it.

**RETURN SUMMARY:**
```
************************************
* Summary of aircraft door opening *
************************************
** task_id                       **: [task_id]
** flight status                 **: [flight_status]
** deplaning equipment type      **: [deplaning_equipment_type]
** jetbridge connection status   **: [jetbridge_connection_status]
** stairtruck connection status  **: [stairtruck_connection_status]
** door opening status           **: [door_opening_status]
```

---

#### BRANCH B — Disembark passengers

**Triggered by:** `task_id` contains `'PAX_DISEMBARKATION'`

**STEP 1 — Verify prerequisites (from args, NOT TrackerAPI — documented rationale):**

The instructions include an explicit inline engineering note:

> *"CRITICAL: Read ONLY from the incoming args. Do NOT call TrackerAPI to resolve these values — TrackerAPI may hold stale data from prior steps and will return null for door_opening_status, causing a false prerequisite failure. The manager has already passed the correct values as named parameters in this call. Trust the args, not TrackerAPI."*

- `flight_status` from args must contain `'on blocks'`
- `door_opening_status` from args must contain `'open'`
- Do NOT call any tool in this step

**STEP 2 — Execute passenger disembarkation:**
Call `/AirlineTurnaround/aircraft_disembark` with: `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status`. Extract `passenger_disembarkation_status`. Call `TrackerAPI` to store it.

**RETURN SUMMARY:**
```
*********************************
* Summary of aircraft disembark *
*********************************
** task_id                          **: [task_id]
** flight status                    **: [flight_status]
** deplaning equipment type         **: [deplaning_equipment_type]
** door opening status              **: [door_opening_status]
** passenger disembarkation status  **: [passenger_disembarkation_status]
```

---

#### BRANCH C — Crew debrief

**Triggered by:** `task_id` contains `'CREW_DEBRIEF'`

**STEP 1 — Resolve and verify prerequisites (via TrackerAPI — by design):**
Call `TrackerAPI` with: `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `door_opening_status`, `passenger_disembarkation_status`, `baggage_unload_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`. Wait. Verify ALL three:
- `flight_status` contains `'on blocks'`
- `passenger_disembarkation_status` contains `'completed'`
- `baggage_unload_status` contains `'completed'`

If any prerequisite fails → stop and report which one failed.

> Note: Unlike BRANCH B which explicitly avoids TrackerAPI for prerequisite resolution, BRANCH C calls TrackerAPI first. The difference reflects the timing: by STEP 13 (crew debrief), both passenger disembarkation (STEP 11) and baggage unload (STEP 12) should be in sly_data as confirmed values, so TrackerAPI can be trusted here.

**STEP 2 — Execute crew debrief:**
Call `/AirlineTurnaround/aircraft_crew_debrief` with: `flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `deplaning_equipment_type`, `jetbridge_connection_status`, `stairtruck_connection_status`, `door_opening_status`. Extract `crew_debrief_status`. Call `TrackerAPI` to store it.

**RETURN SUMMARY:**
```
************************************
* Summary of aircraft crew debrief *
************************************
** task_id                       **: [task_id]
** flight status                 **: [flight_status]
** deplaning equipment type      **: [deplaning_equipment_type]
** door opening status           **: [door_opening_status]
** passenger disembarkation      **: [passenger_disembarkation_status]
** baggage unload                **: [baggage_unload_status]
** crew debrief status           **: [crew_debrief_status]
```

---

#### sly_data contract

All four directions carry the same 16-field set:

`flight_number`, `aircraft_type`, `flight_status`, `gate_id`, `engines_stop_status`, `door_opening_status`, `passenger_disembarkation_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `crew_debrief_status`, `baggage_unload_status`, `task_id`, `acu_connection_status`, `gpu_connection_status`, `wheelchocks_installation_status`

> Note: `engines_stop_status` is in the sly_data allow blocks but is **absent from the Python `FLIGHT_TURNAROUND_TRACKED_FIELDS`**. It propagates through the sly_data channel between networks but TrackerAPI will not log or return it.

> Note: `task_id` propagates in all four sly_data directions, consistent with its role as a correlation token threading through the entire call chain.

#### Down-chain tools

```
["/AirlineTurnaround/aircraft_door_opening",
 "/AirlineTurnaround/aircraft_disembark",
 "/AirlineTurnaround/aircraft_crew_debrief",
 "TrackerAPI"]
```

---

### 5.2 TrackerAPI (Coded Tool)

**Class:** `AirlineTurnaround.aircraft_crew_cabin.aircraft_crew_cabin.TrackerAPI`

Standard sly_data-first implementation. Called to persist results after BRANCH A STEP 2, BRANCH B STEP 2, and BRANCH C STEPs 1 and 2.

#### Data resolution priority

1. **`sly_data[field]`** — authoritative; returned immediately if present.
2. **`args[field]`** — used only when `sly_data` has no value; promoted into `sly_data`.
3. **Neither** — logged as `NOT_FOUND`, returned as `None`.

#### Configuration (22 tracked fields = 22 return fields)

`acu_connection_status`, `acu_readiness_status`, `aircraft_direction`, `aircraft_type`, `assigned_runway_id`, `assigned_runway_length`, `baggage_unload_status`, `clearance_type`, `crew_debrief_status`, `deplaning_equipment_type`, `door_opening_status`, `flight_number`, `flight_status`, `gate_id`, `gpu_connection_status`, `ground_clearance_status`, `ground_clearance_type`, `jetbridge_connection_status`, `passenger_disembarkation_status`, `stairtruck_connection_status`, `wheelchocks_installation_status`, `wheelchocks_readiness_status`

> Note: Tracked fields and return fields are identical — TrackerAPI returns everything it tracks.

> Note: `engines_stop_status` is in the sly_data allow blocks and the HOCON TrackerAPI parameter schema but **absent from Python tracked fields**. It will not be tracked or returned.

> Note: The HOCON TrackerAPI description contains `"wheels_chucks_installation_status"` (line 417) — double-`c` typo. Should be `wheelchocks_installation_status`. Stale copy-paste artifact also seen in several other networks.

> Note: The HOCON `TrackerAPI` definition correctly includes `"required": []`.

---

## 6. External Tool Dependencies

|--------------------------------------------|----------|----------------------|
| Tool path                                  | Branch   | Purpose              |
|--------------------------------------------|----------|----------------------|
| `/AirlineTurnaround/aircraft_door_opening` | BRANCH A | Open aircraft doors  |
| `/AirlineTurnaround/aircraft_disembark`    | BRANCH B | Disembark passengers |
| `/AirlineTurnaround/aircraft_crew_debrief` | BRANCH C | Conduct crew debrief |
|--------------------------------------------|----------|----------------------|

---

## 7. Sample Queries

```
# BRANCH A — door opening (with task_id)
{"flight_number": "AF84", "aircraft_type": "B747", "flight_status": "on blocks",
 "gate_id": "A1", "deplaning_equipment_type": "jetway",
 "jetbridge_connection_status": "connected",
 "task_id": "STEP_10_DOOR_OPENING",
 "instruction": "Open the aircraft door."}

# BRANCH A — door opening (direct user query)
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The jetbridge is connected to the plane. Open the aircraft door."

# BRANCH B — passenger disembarkation
"The B747 aircraft of flight AF84 is on blocks at gate A1.
The jetbridge is connected. The aircraft door is open.
Disembark passengers from the aircraft."
```

---

## 8. Key Design Decision — BRANCH B TrackerAPI Avoidance

The explicit instruction in BRANCH B STEP 1 not to call TrackerAPI for prerequisite validation reflects a specific concurrency/ordering constraint in the turnaround workflow:

By the time BRANCH B executes (STEP 11), `door_opening_status` has just been set by STEP 10. However, in the sly_data-first TrackerAPI model, the value of `door_opening_status` in sly_data depends on whether TrackerAPI was called to write it after BRANCH A completed. If there was any lag or missed TrackerAPI write, calling TrackerAPI in BRANCH B STEP 1 would return `null` — causing a false prerequisite failure.

The solution: require the caller (`aircraft_crew_pilot`) to pass `door_opening_status` explicitly as a named parameter. BRANCH B then reads it directly from args rather than from TrackerAPI. This is the same pattern documented in `aircraft_turnaround`'s STEP 6 ("Read flight_status DIRECTLY from this response... Do NOT use the flight_status value from TrackerAPI").

This contrasts with BRANCH C, which calls TrackerAPI first — by STEP 13, both `passenger_disembarkation_status` and `baggage_unload_status` have had enough time and intermediate steps to be reliably in sly_data.

---

## 9. Known Issues and Maintenance Notes

|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|:--------:|------------------------------------------------------------------------------------------------------------|
| Issue                                                                           | Location                                                                           | Severity | Notes                                                                                                      |
|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|:--------:|------------------------------------------------------------------------------------------------------------|
| `engines_stop_status` in sly_data allow blocks but not in Python tracked fields | `aircraft_crew_cabin.hocon` lines 328, 348; `aircraft_crew_cabin.py` lines 426–448 | Low      | The field propagates between networks via sly_data channels but TrackerAPI will not track or echo it back. |
| HOCON TrackerAPI description `"wheels_chucks_installation_status"` typo         | `aircraft_crew_cabin.hocon` line 417                                               | Low      | Double-`c` in `chucks`. Should be `wheelchocks_installation_status`.                                       |
| ~145-line commented-out `execute_aircraft_landing` class                        | `aircraft_crew_cabin.py` lines 28–143                                              | Low      | Identical block also present in `aircraft_cabin_services.py`. Belongs in `aircraft_landing.py`. Dead code. |
| Unused imports: `fcntl`, `asyncio`, `random`, `os`, `platform`                  | `aircraft_crew_cabin.py` lines 7–12                                                | Low      | All unused. `fcntl` Unix-only, fails on Windows. Same issue as other networks.                             |
| HOCON metadata description not updated                                          | `aircraft_crew_cabin.hocon` line 6                                                 | Low      | Says "Simple agent network using a single LLM-based agent" — generic boilerplate.                          |
| BRANCH B design decision should be documented in code                           | `aircraft_crew_cabin.hocon` BRANCH B STEP 1                                        | Info     | The "Trust the args, not TrackerAPI" rationale is documented inline. Well-designed; no fix needed.         |
|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------|:--------:|------------------------------------------------------------------------------------------------------------|

---

## 10. Comparison with `aircraft_cabin_services` (Parallel Pattern)

Both `aircraft_crew_cabin` and `aircraft_cabin_services` are three-branch routing agents. The key structural differences:

|--------------------------------------|----------------------------------------|-------------------------------------|
| Aspect                               | `aircraft_cabin_services`              | `aircraft_crew_cabin`               |
|--------------------------------------|----------------------------------------|-------------------------------------|
| Entry agent name                     | `cabin_services`                       | `cabin_crew_agent`                  |
| Primary routing discriminant         | `instruction` field (keyword match)    | `task_id` token (priority-first)    |
| Branches                             | clean / lavatory / catering            | door opening / disembark / debrief  |
| Called by                            | `aircraft_turnaround_manager` directly | `aircraft_crew_pilot`               |
| TrackerAPI avoidance in any branch   | No                                     | Yes — BRANCH B explicitly avoids it |
| Execution limits                     | 3,000 / 300s                           | 40,000 / 7,200s                     |
| TrackerAPI class path                | Wrong module                           | Correct module                      |
|--------------------------------------|----------------------------------------|-------------------------------------|

---

## 11. Extensibility Guidance

- Add `engines_stop_status` to `FLIGHT_TURNAROUND_TRACKED_FIELDS` and `RETURN_FIELDS` in Python, or remove it from the sly_data allow blocks
- Remove the commented-out `execute_aircraft_landing` class from the Python file
- Remove unused imports (`fcntl`, `asyncio`, `random`, `os`, `platform`)
- Fix the `"wheels_chucks_installation_status"` typo in the HOCON TrackerAPI description
- Update the metadata description from the generic boilerplate
- If a crew exit branch is ever added here (currently it's in `aircraft_crew_pilot` as a direct call to `aircraft_crew_exit`), add it as BRANCH D with a `CREW_EXIT` task_id trigger

---

## 12. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
