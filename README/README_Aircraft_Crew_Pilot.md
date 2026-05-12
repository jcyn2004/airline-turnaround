# Aircraft Crew Pilot
## Agentic AI Network – README

> **Configuration file:** `aircraft_crew_pilot.hocon`
> **Implementation file:** `aircraft_crew_pilot.py`
> **Framework:** neuro-san (aaosa)
> **Primary use case:** Single-agent orchestrator for all pilot-operated turnaround phases, executing nine branches (A–I) covering landing clearance, landing, ground clearance, taxiing, engine stop, crew exit, door opening, passenger disembarkation, and crew debrief.

---

## 1. Overview

`aircraft_crew_pilot` is the most capable single agent in the AirlineTurnaround system. Called by `aircraft_turnaround_manager` for nine of the twenty turnaround steps (STEPs 1, 2, 5, 6, 7, 10, 11, 13, 14), it routes each call to one of nine branches based on a `task_id` correlation token, and directly delegates to leaf service networks.

The agent includes a formal engineering note in the HOCON (lines 181–188) documenting the **root cause of a previous orchestration failure** and the deliberate architectural fix applied. Its TrackerAPI is the most sophisticated in the system, implementing two-field normalisation with active eviction of transient values from sly_data.

The network contains:

- `flight_crew_agent` — the single LLM orchestrator with nine branches
- `TrackerAPI` — coded state manager with `flight_status` and `ground_clearance_status` normalisation, including eviction of transient values
- Ten external leaf networks registered in the tools list

No prior documentation existed for this network; this README is built entirely from source.

---

## 2. Repository Structure

```
aircraft_crew_pilot.hocon    # Agent network configuration (~790 lines)
aircraft_crew_pilot.py       # TrackerAPI implementation (sly_data-first, two-field normalisation, eviction)
registries/aaosa_basic.hocon # Shared registry (all leaf networks)
```

---

## 3. System Architecture

```
aircraft_turnaround_manager  (caller — STEPs 1, 2, 5, 6, 7, 10, 11, 13, 14)
   │
   ▼
flight_crew_agent  (LLM 9-branch Orchestrator — task_id-first routing)
   │
   ├── TrackerAPI                                        (Coded tool: normalising, evicting sly_data manager)
   │
   ├── /AirlineTurnaround/aircraft_traffic_controller    (BRANCH A — landing clearance)
   ├── /AirlineTurnaround/aircraft_landing               (BRANCH B — land aircraft)
   ├── /AirlineTurnaround/aircraft_ground_traffic        (BRANCHes C, D — ground clearance + taxiing)
   ├── /AirlineTurnaround/aircraft_ground_readiness      (BRANCH D — ground services readiness)
   ├── /AirlineTurnaround/aircraft_taxiing               (BRANCH D — execute taxiing)
   ├── /AirlineTurnaround/aircraft_engines_stop          (BRANCH E — stop engines)
   ├── /AirlineTurnaround/aircraft_crew_exit             (BRANCH F — crew exit)
   ├── /AirlineTurnaround/aircraft_door_opening          (BRANCH G — open doors)
   ├── /AirlineTurnaround/aircraft_disembark             (BRANCH H — passenger disembarkation)
   └── /AirlineTurnaround/aircraft_crew_debrief          (BRANCH I — crew debrief)
```

> Note: BRANCHes G, H, I call their leaf networks **directly** from `flight_crew_agent` — they do NOT route through `aircraft_crew_cabin`. Despite `aircraft_crew_cabin` existing in the system, this network bypasses it. The tools list confirms `aircraft_door_opening`, `aircraft_disembark`, and `aircraft_crew_debrief` are registered directly here.

---

## 4. Engineering Note — Design History (HOCON lines 181–188)

The HOCON contains a formal comment block documenting the fix that produced the current instruction design:

> *"FIX: The original instructions used ambiguous routing logic that caused the agent to guess which sub-task was being requested, often picking the wrong subsystem or short-circuiting. The fix introduces EXPLICIT INTENT DETECTION: the caller (aircraft_turnaround_manager) now always includes an 'explicit instruction' keyword phrase. This agent's new prompt maps those phrases to deterministic branches. This eliminates the core failure mode where mid-level agents relied on loose keyword matching against a broad inquiry string."*

This explains why every branch uses `task_id`-priority routing, and why the turnaround manager's instructions include so much per-step detail about parameter naming and tool routing.

---

## 5. Runtime Configuration

|-------------------------|----------------|
| Setting                 | Value          |
|-------------------------|----------------|
| LLM model               | `gpt-5.4-mini` |
| `max_iterations`        | `40000`        |
| `max_execution_seconds` | `7200`         |
|-------------------------|----------------|

---

## 6. Components

### 6.1 flight_crew_agent (LLM 9-Branch Orchestrator)

The single entry-point agent handling all nine turnaround steps delegated by `aircraft_turnaround_manager`.

> Note: The agent is named `flight_crew_agent` in the HOCON — not `aircraft_crew_pilot_agent` or any variant of the network name.

#### Mandatory echo rule

Every response MUST include:
```
** task_id **: [echo unchanged, or NONE if not provided]
```

This enables `aircraft_turnaround_manager`'s per-step response validation (it checks whether the response echoes the expected `task_id`).

#### Input parameters

| Parameter | Type | Required | Description |
|---|---|:---:|---|
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `flight_number` | string | ✅ | Flight identifier |
| `flight_status` | string | ❌ | Current flight status |
| `gate_id` | string | ❌ | Gate identifier |
| `task_id` | string | ❌ | **Primary routing discriminant** |
| `aircraft_direction` | string | ❌ | `incoming` or `departing` |
| `clearance_type` | string | ❌ | ATC clearance type |
| `assigned_runway_id` | string | ❌ | Assigned runway |
| `assigned_runway_length` | string | ❌ | Runway length |
| `ground_clearance_type` | string | ❌ | `taxi in` or `taxi out` |
| `ground_clearance_status` | string | ❌ | Clearance status |
| `wheelchocks_readiness_status` | string | ❌ | From ground readiness |
| `acu_readiness_status` | string | ❌ | From ground readiness |
| `gpu_readiness_status` | string | ❌ | From ground readiness |
| `engines_stop_status` | string | ❌ | Engine state |
| `door_opening_status` | string | ❌ | Door state |
| `passenger_disembarkation_status` | string | ❌ | Disembarkation state |
| `baggage_unload_status` | string | ❌ | Baggage state |
| `crew_debrief_status` | string | ❌ | Debrief state |
| `crew_exit_status` | string | ❌ | Crew exit state |
| `deplaning_equipment_type` | string | ❌ | `jetway` or `stairtruck` |
| `jetbridge_connection_status` | string | ❌ | Jetbridge state |
| `stairtruck_connection_status` | string | ❌ | Stairtruck state |
| `acu_connection_status` | string | ❌ | ACU state |
| `gpu_connection_status` | string | ❌ | GPU state |
| `wheelchocks_installation_status` | string | ❌ | Chocks state |

---

#### Branch routing table

| `task_id` contains | Branch | Turnaround step | Primary action |
|---|---|---|---|
| (none / free text) | **BRANCH A** | STEP 1 | Request landing clearance |
| (none / free text) | **BRANCH B** | STEP 2 | Land aircraft |
| `'GROUND_CLEARANCE'` | **BRANCH C** | STEP 5 | Request ground clearance (taxi in) |
| `'TAXI_TO_GATE'` | **BRANCH D** | STEP 6 | Taxi aircraft to gate |
| `'STOP_ENGINES'` | **BRANCH E** | STEP 7 | Stop engines |
| `'CREW_EXIT'` | **BRANCH F** | STEP 14 | Authorise and execute crew exit |
| `'DOOR_OPENING'` | **BRANCH G** | STEP 10 | Open aircraft doors |
| `'PAX_DISEMBARKATION'` | **BRANCH H** | STEP 11 | Disembark passengers |
| `'CREW_DEBRIEF'` | **BRANCH I** | STEP 13 | Conduct crew debrief |

> Note: BRANCHes A and B have no `task_id` triggers — they rely on inquiry text matching. All other branches have `task_id`-priority routing with explicit overrides: *"When task_id='STEP_X_...' is present, this branch MUST execute. It is never irrelevant when this task_id is present."*

---

#### BRANCH A — Landing clearance

Calls `aircraft_traffic_controller`. Extracts and stores `clearance_type`, `assigned_runway_id`, `assigned_runway_length`. **Does NOT store `flight_status`** from this response — `'APPROACH'` is a transient ATC status that must not pollute sly_data and block the real `'landed'` status from BRANCH B.

---

#### BRANCH B — Land the aircraft

Calls `aircraft_landing`. If `clearance_type` is None, executes BRANCH A first. Explicitly normalises: *"if aircraft_landing returns anything other than 'landed' in flight_status, use the value 'landed'"*. Summary hardcodes `** flight status **: landed`.

---

#### BRANCH C — Request ground clearance (taxi in)

Called for STEP 5. Calls `aircraft_ground_traffic` with `ground_clearance_type='taxi in'`. Stores `ground_clearance_type` and `ground_clearance_status` but **explicitly does NOT update `flight_status`** from this response:

> *"aircraft_ground_traffic returns the clearance authority status (e.g. TAXIING_IN, GRANTED), which is not the aircraft's actual flight state. Updating flight_status from this response would corrupt it."*

---

#### BRANCH D — Taxi the aircraft to the gate

The most complex branch — four steps, three sub-agent calls.

**STEP 1 — Ground clearance (one call maximum):** Checks if clearance is already in the inquiry text, in sly_data, or needs to be requested from `aircraft_ground_traffic`. Extracts clearance but **explicitly does NOT update `flight_status`** from the ground traffic response.

**STEP 2 — Ground services readiness (non-blocking):** Calls `aircraft_ground_readiness` once. Stores the three readiness statuses. **Continues regardless of readiness values.**

**STEP 3 — Execute taxiing:**

> *"CRITICAL: You MUST pass flight_status='landed' as a literal string. Do NOT read flight_status from sly_data, from TrackerAPI, or from any prior step result."*
> *"Before calling aircraft_taxiing, also call TrackerAPI with flight_status='landed' explicitly to overwrite any stale value."*
> *"Do NOT call TrackerAPI after this — the taxiing subsystem writes flight_status='on blocks' directly. Reading TrackerAPI here would risk returning a stale value."*

**STEP 4 — Return summary** with `flight_status` hardcoded as `on blocks`.

---

#### BRANCH E — Stop engines

Calls `aircraft_engines_stop`. Two conditions: `flight_status` must contain `'on blocks'`. Stores `engines_stop_status`.

---

#### BRANCH F — Authorise and execute crew exit

Four steps. Prerequisite validation from **args only** (not TrackerAPI) for the same stale-data reason documented in BRANCHes G and H. All four must be confirmed from args:
- `flight_status` contains `'on blocks'`
- `passenger_disembarkation_status` contains `'completed'`
- `baggage_unload_status` contains `'completed'`
- `crew_debrief_status` contains `'completed'`

The instructions explicitly prohibit calling any tool other than `aircraft_crew_exit` and `TrackerAPI`, and prohibit checking `aircraft_direction`.

---

#### BRANCH G — Open the aircraft door (cabin crew — under pilot authority)

Prerequisite check from **args only** (same TrackerAPI stale-data pattern). STEP 2: one isolated call to `aircraft_door_opening`. Stores `door_opening_status`.

---

#### BRANCH H — Disembark passengers (cabin crew — under pilot authority)

Prerequisite check from **args only** with full documented rationale (identical text to `aircraft_crew_cabin` BRANCH B). STEP 2 adds an important clause not present in `aircraft_crew_cabin`:

> *"CRITICAL — STAIRTRUCK PREREQUISITE: When deplaning_equipment_type contains 'stairtruck', the valid prerequisite is stairtruck_connection_status='connected'. jetbridge_connection_status will be null — this is EXPECTED and CORRECT for stairtruck gates. Do NOT treat null jetbridge_connection_status as a failure when deplaning_equipment_type is 'stairtruck'."*

---

#### BRANCH I — Crew debrief (cabin crew — under pilot authority)

Calls TrackerAPI for prerequisite verification (same design decision as `aircraft_crew_cabin` BRANCH C — by STEP 13 the values are reliably in sly_data). Three prerequisites: `flight_status = on blocks`, `passenger_disembarkation_status = completed`, `baggage_unload_status = completed`.

---

#### sly_data contract

All four directions carry the same 25-field set:

`flight_number`, `aircraft_type`, `flight_status`, `ground_clearance_type`, `gate_id`, `assigned_runway_id`, `assigned_runway_length`, `wheelchocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`, `aircraft_direction`, `clearance_type`, `engines_stop_status`, `ground_clearance_status`, `task_id`, `door_opening_status`, `passenger_disembarkation_status`, `jetbridge_connection_status`, `stairtruck_connection_status`, `deplaning_equipment_type`, `crew_debrief_status`, `baggage_unload_status`, `acu_connection_status`, `gpu_connection_status`, `wheelchocks_installation_status`

> Note: `acu_readiness_status`, `gpu_readiness_status`, and `wheelchocks_readiness_status` each appear **twice** in all four sly_data allow blocks (lines 614–615, 622–624 in `to_upstream`, etc.). HOCON will likely use the last occurrence or deduplicate, but this is a redundancy to clean up.

---

### 6.2 TrackerAPI (Coded Tool — Two-Field Normalisation with Eviction)

**Class:** `AirlineTurnaround.aircraft_crew_pilot.aircraft_crew_pilot.TrackerAPI`

The most sophisticated TrackerAPI in the system. It extends the standard sly_data-first implementation with `_normalise_field()` for two fields, and implements **active eviction** of transient values from sly_data.

#### Normalisation rules

**`flight_status`:**

| Input contains | Normalised output | Action |
|---|---|---|
| `'land'` | `'landed'` | Stored |
| `'block'` | `'on blocks'` | Stored |
| `'approach'` or `'taxi'` | `None` | **EVICTED from sly_data** |
| Other mid-transit values | unchanged | Stored (fails downstream checks) |

**`ground_clearance_status`:**

| Condition | Normalised output | Action |
|---|---|---|
| Contains `'grant'` or `'clear'` AND `sly_data["flight_status"] == "on blocks"` | `None` | **EVICTED from sly_data** |
| All other values | unchanged | Stored |

#### Active eviction mechanism

When `_normalise_field` returns `None`, `_process_field` performs a `del sly_data[field_name]` — actively removing the transient value from shared state. This ensures that:

1. `'APPROACH'` from ATC does not persist and block the real `'landed'` status from being written
2. `'TAXIING_IN'` from ground traffic does not persist and block `'on blocks'`
3. `'GRANTED'` ground clearance is evicted once the aircraft is on blocks, so the next turnaround's clearance request finds null and routes correctly

The docstrings explicitly document these design choices:
> *"Returning None causes _process_field to evict any existing value and skip the write, leaving the field unset so the real terminal status from the next step can be stored without interference."*

#### Configuration (22 tracked fields = 22 return fields)

`aircraft_direction`, `aircraft_type`, `assigned_runway_id`, `assigned_runway_length`, `baggage_unload_status`, `clearance_type`, `crew_debrief_status`, `crew_exit_status`, `deplaning_equipment_type`, `door_opening_status`, `engines_stop_status`, `flight_number`, `flight_status`, `gate_id`, `ground_clearance_status`, `ground_clearance_type`, `jetbridge_connection_status`, `passenger_disembarkation_status`, `stairtruck_connection_status`, `wheelchocks_readiness_status`, `acu_readiness_status`, `gpu_readiness_status`

> Note: Tracked fields and return fields are identical — TrackerAPI returns everything it tracks.

> Note: The TrackerAPI HOCON schema correctly includes `"required": []`.

---

## 7. External Tool Dependencies

| Tool path | Branches | Purpose |
|---|---|---|
| `/AirlineTurnaround/aircraft_traffic_controller` | A | Landing clearance |
| `/AirlineTurnaround/aircraft_landing` | B | Land aircraft |
| `/AirlineTurnaround/aircraft_ground_traffic` | C, D | Ground clearance |
| `/AirlineTurnaround/aircraft_ground_readiness` | D | Equipment readiness |
| `/AirlineTurnaround/aircraft_taxiing` | D | Execute taxiing |
| `/AirlineTurnaround/aircraft_engines_stop` | E | Stop engines |
| `/AirlineTurnaround/aircraft_crew_exit` | F | Crew exit |
| `/AirlineTurnaround/aircraft_door_opening` | G | Open doors |
| `/AirlineTurnaround/aircraft_disembark` | H | Passenger disembarkation |
| `/AirlineTurnaround/aircraft_crew_debrief` | I | Crew debrief |

---

## 8. Sample Queries

```
# STEP 1 — landing clearance (BRANCH A)
"Request clearance for landing your incoming B747 aircraft which is identified as flight AF84."

# STEP 2 — land (BRANCH B)
"Land the incoming flight AF84. It has been cleared for landing on runway 19L. It is a B747."

# STEP 5 — ground clearance (BRANCH C, via task_id)
{"flight_number": "AF84", ..., "task_id": "STEP_5_GROUND_CLEARANCE_TAXI_IN",
 "ground_clearance_type": "taxi in", "instruction": "Request ground clearance to taxi in to gate."}

# STEP 6 — taxi (BRANCH D, via task_id)
{"flight_number": "AF84", ..., "task_id": "STEP_6_TAXI_TO_GATE",
 "instruction": "Taxi in the aircraft."}

# STEP 7 — engines stop (BRANCH E, direct query)
"Flight AF84 is on blocks at gate A1. It's a B747 aircraft. Stop its engines."
```

---

## 9. TrackerAPI Normalisation — System-Wide Comparison

`aircraft_crew_pilot.py`'s TrackerAPI has the most comprehensive normalisation in the system:

| Network TrackerAPI | `flight_status` normalisation | `ground_clearance_status` normalisation | Eviction |
|---|---|---|---|
| `aircraft_taxiing` | Yes (3 tokens: landed/taxiing/on blocks) | No | No |
| `aircraft_crew_pilot` | Yes (landed/on blocks; APPROACH/TAXI → evict) | Yes (evict when on blocks) | **Yes** |
| All others | No | No | No |

---

## 10. Known Issues and Maintenance Notes

| Issue | Location | Severity | Notes |
|---|---|:---:|---|
| Duplicate sly_data fields in allow blocks | `aircraft_crew_pilot.hocon` lines 614–615, 622–624 (and equivalents in all 4 directions) | Low | `acu_readiness_status`, `gpu_readiness_status`, `wheelchocks_readiness_status` each appear twice. HOCON parsers typically use last value. Clean up. |
| `aircraft_crew_cabin` bypassed by direct tool registration | `aircraft_crew_pilot.hocon` line 735–747 | Info | BRANCHes G, H, I register and call leaf networks directly. `aircraft_crew_cabin` exists as a standalone network but is not used in the integrated call path through `aircraft_crew_pilot`. |
| ~145-line commented-out `execute_aircraft_landing` class | `aircraft_crew_pilot.py` lines 28–143 | Low | Identical block in `aircraft_cabin_services.py` and `aircraft_crew_cabin.py`. Dead code. |
| Unused imports: `fcntl`, `asyncio`, `random`, `os`, `platform` | `aircraft_crew_pilot.py` lines 7–12 | Low | All unused. `fcntl` Unix-only, fails on Windows. |
| BRANCH D STEP 3: TrackerAPI called before taxiing to write `flight_status='landed'` | `aircraft_crew_pilot.hocon` BRANCH D STEP 3 | Info | Intentional: overwrites any stale mid-transit value before passing to `aircraft_taxiing`. The eviction mechanism in TrackerAPI supports this. |

---

## 11. Key Design Decisions — TrackerAPI Avoidance Pattern

This network's instructions contain the most detailed documentation of when NOT to call TrackerAPI and why. The pattern appears in five separate branches:

| Branch | Avoids TrackerAPI for... | Reason |
|---|---|---|
| A | `flight_status` after clearance | `'APPROACH'` is ATC status, not aircraft state |
| C | `flight_status` after ground traffic | `'TAXIING_IN'` is authority status, not aircraft state |
| D STEP 1 | `flight_status` after ground traffic | Same as BRANCH C |
| D STEP 3 | Reading after taxiing | Taxiing tool writes directly; TrackerAPI would return stale pre-taxi value |
| F STEP 1 | Prerequisite verification | Local sly_data may not reflect latest upstream values |
| G STEP 1 | Prerequisite verification | Same stale-data concern |
| H STEP 1 | Prerequisite verification | Same stale-data concern (identical text to `aircraft_crew_cabin` BRANCH B) |

The TrackerAPI's eviction mechanism (`del sly_data[field_name]` when normalisation returns `None`) is the counterpart to these avoidance rules — it proactively removes transient values that would cause false reads on the next TrackerAPI call.

---

## 12. Extensibility Guidance

- Fix the duplicate sly_data field entries (remove duplicates from all four allow directions)
- Remove the ~145-line commented-out `execute_aircraft_landing` block from the Python file
- Remove unused imports (`fcntl`, `asyncio`, `random`, `os`, `platform`)
- Consider whether `aircraft_crew_cabin` should be used for BRANCHes G, H, I (currently bypassed) or deprecated since its functionality is duplicated here
- If a departing aircraft sequence is added, BRANCHes for takeoff clearance, pushback, and taxi-out would follow the same `task_id`-priority pattern as existing branches

---

## 13. Compliance Notice

This network models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.
