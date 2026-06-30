# Aircraft Turnaround Process Overview

> **Snapshot date:** 2026-05-15
> **Companion documentation:** 33 per-network READMEs in [`README/`](README/)

This repository implements a multi-agent system for aircraft turnaround management, orchestrating operations from aircraft entering the airport-controlled airspace through arrival at the gate, all ground services, and onward to departure of the next flight. The process is modeled as a coordinated, time-dependent workflow aligned with real airport operations, as illustrated in the turnaround Gantt chart. The current release covers the inbound phase through aircraft refueling.

The system is built on the **neuro-san** framework using the **AAOSA** (Adaptive Agent-Oriented Software Architecture) pattern: each capability is a self-describing agent network defined in HOCON, with Python-backed [`coded_tools/`](coded_tools/) for state persistence (`TrackerAPI`) and side-effecting actions.

---

## Summary — Network Catalog

Every agent network is listed below with direct links to its HOCON definition and its dated README. Click the HOCON link to jump to the registry file; click the README link to open the network's detailed documentation.

### Orchestrator

| Network                                                | HOCON                                                                                 | README                                                  |
|--------------------------------------------------------|---------------------------------------------------------------------------------------|---------------------------------------------------------|
| `aircraft_turnaround` (20-step top-level orchestrator) | [`aircraft_turnaround.hocon`](registries/AirlineTurnaround/aircraft_turnaround.hocon) | [README](README/README_Aircraft_Turnaround.md) |

### Aggregation Networks (Routers)

| Network                        | HOCON                                                                                                   | README                                                           |
|--------------------------------|---------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `aircraft_crew_pilot`          | [`aircraft_crew_pilot.hocon`](registries/AirlineTurnaround/aircraft_crew_pilot.hocon)                   | [README](README/README_Aircraft_Crew_Pilot.md)          |
| `aircraft_crew_cabin`          | [`aircraft_crew_cabin.hocon`](registries/AirlineTurnaround/aircraft_crew_cabin.hocon)                   | [README](README/README_Aircraft_Crew_Cabin.md)          |
| `aircraft_cabin_services`      | [`aircraft_cabin_services.hocon`](registries/AirlineTurnaround/aircraft_cabin_services.hocon)           | [README](README/README_Aircraft_Cabin_Services.md)      |
| `aircraft_gate_services`       | [`aircraft_gate_services.hocon`](registries/AirlineTurnaround/aircraft_gate_services.hocon)             | [README](README/README_Aircraft_Gate_Services.md)       |
| `aircraft_ground_operation`    | [`aircraft_ground_operation.hocon`](registries/AirlineTurnaround/aircraft_ground_operation.hocon)       | [README](README/README_Aircraft_Ground_Operation.md)    |
| `aircraft_ground_readiness`    | [`aircraft_ground_readiness.hocon`](registries/AirlineTurnaround/aircraft_ground_readiness.hocon)       | [README](README/README_Aircraft_Ground_Readiness.md)    |
| `aircraft_ground_rampservices` | [`aircraft_ground_rampservices.hocon`](registries/AirlineTurnaround/aircraft_ground_rampservices.hocon) | [README](README/README_Aircraft_Ground_Rampservices.md) |
| `aircraft_ground_servicing`    | [`aircraft_ground_servicing.hocon`](registries/AirlineTurnaround/aircraft_ground_servicing.hocon)       | [README](README/README_Aircraft_Ground_Servicing.md)    |

### Flight & Traffic

| Network                       | HOCON                                                                                                 | README                                                          |
|-------------------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| `aircraft_landing`            | [`aircraft_landing.hocon`](registries/AirlineTurnaround/aircraft_landing.hocon)                       | [README](README/README_Aircraft_Landing.md)            |
| `aircraft_taxiing`            | [`aircraft_taxiing.hocon`](registries/AirlineTurnaround/aircraft_taxiing.hocon)                       | [README](README/README_Aircraft_Taxiing.md)            |
| `aircraft_traffic_controller` | [`aircraft_traffic_controller.hocon`](registries/AirlineTurnaround/aircraft_traffic_controller.hocon) | [README](README/README_Aircraft_Traffic_Controller.md) |
| `aircraft_ground_traffic`     | [`aircraft_ground_traffic.hocon`](registries/AirlineTurnaround/aircraft_ground_traffic.hocon)         | [README](README/README_Aircraft_Ground_Traffic.md)     |

### Gate Operations

| Network                       | HOCON                                                                                                 | README                                                          |
|-------------------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| `aircraft_gate_selection`     | [`aircraft_gate_selection.hocon`](registries/AirlineTurnaround/aircraft_gate_selection.hocon)         | [README](README/README_Aircraft_Gate_Selection.md)     |
| `aircraft_jetbridge_connect`  | [`aircraft_jetbridge_connect.hocon`](registries/AirlineTurnaround/aircraft_jetbridge_connect.hocon)   | [README](README/README_Aircraft_Jetbridge_Connect.md)  |
| `aircraft_stairtruck_connect` | [`aircraft_stairtruck_connect.hocon`](registries/AirlineTurnaround/aircraft_stairtruck_connect.hocon) | [README](README/README_Aircraft_Stairtruck_Connect.md) |
| `aircraft_door_opening`       | [`aircraft_door_opening.hocon`](registries/AirlineTurnaround/aircraft_door_opening.hocon)             | [README](README/README_Aircraft_Door_Opening.md)       |

### Ground Services — Readiness & Connection

| Network                                 | HOCON                                                                                                                     | README                                                           |
|-----------------------------------------|---------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| `aircraft_ground_acu_setup`             | [`aircraft_ground_acu_setup.hocon`](registries/AirlineTurnaround/aircraft_ground_acu_setup.hocon)                         | [README](README/README_Aircraft_Ground_ACU_Setup.md)    |
| `aircraft_ground_acu_connect`           | [`aircraft_ground_acu_connect.hocon`](registries/AirlineTurnaround/aircraft_ground_acu_connect.hocon)                     | [README](README/README_Aircraft_Ground_ACU_Connect.md)  |
| `aircraft_acu_connect`                  | [`aircraft_acu_connect.hocon`](registries/AirlineTurnaround/aircraft_acu_connect.hocon)                                   | [README](README/README_Aircraft_ACU_Connect.md)         |
| `aircraft_ground_gpu_setup`             | [`aircraft_ground_gpu_setup.hocon`](registries/AirlineTurnaround/aircraft_ground_gpu_setup.hocon)                         | [README](README/README_Aircraft_Ground_GPU_Setup.md)    |
| `aircraft_ground_gpu_connect`           | [`aircraft_ground_gpu_connect.hocon`](registries/AirlineTurnaround/aircraft_ground_gpu_connect.hocon)                     | [README](README/README_Aircraft_Ground_GPU_Connect.md)  |
| `aircraft_ground_wheels_chocks_setup`   | [`aircraft_ground_wheels_chocks_setup.hocon`](registries/AirlineTurnaround/aircraft_ground_wheels_chocks_setup.hocon)     | [README](README/README_Aircraft_Wheelchocks_Setup.md)   |
| `aircraft_ground_wheels_chocks_install` | [`aircraft_ground_wheels_chocks_install.hocon`](registries/AirlineTurnaround/aircraft_ground_wheels_chocks_install.hocon) | [README](README/README_Aircraft_Wheelchocks_Install.md) |
| `aircraft_chocks_install`               | [`aircraft_chocks_install.hocon`](registries/AirlineTurnaround/aircraft_chocks_install.hocon)                             | [README](README/README_Aircraft_Chocks_Install.md)      |
| `aircraft_engines_stop`                 | [`aircraft_engines_stop.hocon`](registries/AirlineTurnaround/aircraft_engines_stop.hocon)                                 | [README](README/README_Aircraft_Engines_Stop.md)        |

### Cabin & On-Aircraft Services

| Network                     | HOCON                                                                                             | README                                                        |
|-----------------------------|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------|
| `aircraft_cabin_cleaning`   | [`aircraft_cabin_cleaning.hocon`](registries/AirlineTurnaround/aircraft_cabin_cleaning.hocon)     | [README](README/README_Aircraft_Cabin_Cleaning.md)   |
| `aircraft_lavatory_service` | [`aircraft_lavatory_service.hocon`](registries/AirlineTurnaround/aircraft_lavatory_service.hocon) | [README](README/README_Aircraft_Lavatory_Service.md) |
| `aircraft_catering_loading` | [`aircraft_catering_loading.hocon`](registries/AirlineTurnaround/aircraft_catering_loading.hocon) | [README](README/README_Aircraft_Catering_Loading.md) |

### Cargo / Inspection / Fueling

| Network                   | HOCON                                                                                         | README                                                      |
|---------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| `aircraft_baggage_unload` | [`aircraft_baggage_unload.hocon`](registries/AirlineTurnaround/aircraft_baggage_unload.hocon) | [README](README/README_Aircraft_Baggage_Unload.md) |
| `aircraft_fueling`        | [`aircraft_fueling.hocon`](registries/AirlineTurnaround/aircraft_fueling.hocon)               | [README](README/README_Aircraft_Fueling.md)        |

### Crew

| Network                 | HOCON                                                                                     | README                                                    |
|-------------------------|-------------------------------------------------------------------------------------------|-----------------------------------------------------------|
| `aircraft_crew_debrief` | [`aircraft_crew_debrief.hocon`](registries/AirlineTurnaround/aircraft_crew_debrief.hocon) | [README](README/README_Aircraft_Crew_Debrief.md) |
| `aircraft_crew_exit`    | [`aircraft_crew_exit.hocon`](registries/AirlineTurnaround/aircraft_crew_exit.hocon)       | [README](README/README_Aircraft_Crew_Exit.md)    |

### Networks Without a Dedicated README

The following hocons exist in the registry but do not yet have a per-network README. They are typically internal helpers or future-scope networks.

| Network                                            | HOCON                                                                                                         |
|----------------------------------------------------|---------------------------------------------------------------------------------------------------------------|
| `aircraft_disembark`                               | [`aircraft_disembark.hocon`](registries/AirlineTurnaround/aircraft_disembark.hocon)                           |
| `aircraft_cleaning_procedure`                      | [`aircraft_cleaning_procedure.hocon`](registries/AirlineTurnaround/aircraft_cleaning_procedure.hocon)         |
| `aircraft_gpu_connect`                             | [`aircraft_gpu_connect.hocon`](registries/AirlineTurnaround/aircraft_gpu_connect.hocon)                       |
| `aircraft_inspection_maintenance`                  | [`aircraft_inspection_maintenance.hocon`](registries/AirlineTurnaround/aircraft_inspection_maintenance.hocon) |
| `manifest_aircraft_turnaround` (registry manifest) | [`manifest_aircraft_turnaround.hocon`](registries/AirlineTurnaround/manifest_aircraft_turnaround.hocon)       |

### Shared / Framework Registries

| File                                                                       | Purpose                              |
|----------------------------------------------------------------------------|--------------------------------------|
| [`registries/manifest.hocon`](registries/manifest.hocon)                   | Top-level registry manifest          |
| [`registries/aaosa.hocon`](registries/aaosa.hocon)                         | Shared AAOSA registry                |
| [`registries/aaosa_basic.hocon`](registries/aaosa_basic.hocon)             | Shared sub-network registry          |
| [`registries/aaosa_basic_debug.hocon`](registries/aaosa_basic_debug.hocon) | Debug variant of the shared registry |

---

## Process Phases

### Arrival and Initial Ground Setup

Upon entry to the airport's controlled airspace the aircraft requests clearance for landing. Ground services readiness is confirmed in parallel with gate assignment and the selection of the deplaning equipment (jetbridge or stairtruck).

Once the aircraft taxis to the gate and comes to a complete stop, wheel chocks are placed and engines are shut down to ensure safety. Ground power (GPU) and air conditioning (ACU) units are then connected, deplaning equipment is connected to the aircraft, and the cabin doors are opened.

### Passenger Disembarkation and Unloading Operations

Passenger disembarkation begins immediately after cabin access is established. In parallel, baggage, cargo, and mail unloading operations are carried out. A crew debrief occurs during this phase to communicate aircraft status, turnaround constraints, and task coordination between agents.

### Cabin Servicing and Maintenance

Cabin cleaning starts once passenger disembarkation is complete, followed by lavatory and water servicing. Catering is loaded while cleaning is in progress to minimize idle time. A technical inspection by the maintenance crew is conducted concurrently, ensuring the aircraft's airworthiness before departure.

### Refueling and Loading

Fueling operations are performed in coordination with maintenance and servicing activities. After unloading is complete and cabin servicing concludes, checked baggage and cargo for the outbound flight are loaded.

### Boarding and Departure Preparation *(future scope)*

Once the aircraft is secured and prepared, boarding is announced and passengers begin boarding. After boarding completion, doors are closed and final departure checks are performed. The pushback sequence follows, including ground unit disconnection and engine start.

### Pushback and Taxi Clearance *(future scope)*

The tug is disconnected after pushback, final safety checks are completed, and taxi clearance is received, marking the end of the turnaround process.

---

## High-Level Architecture

The system is organized as a four-layer orchestrated multi-agent workflow.

### Layer 1 — Orchestrator: `aircraft_turnaround`

The top-level orchestrator defined in [`aircraft_turnaround.hocon`](registries/AirlineTurnaround/aircraft_turnaround.hocon) drives the 20-step turnaround plan. It:
- Initializes the run, sequences the steps, and dispatches each step to the appropriate agent network.
- Tracks global state (aircraft status, flight phase, time window, constraints) and decides which tasks are eligible to start.
- Routes all 20 steps to one of four aggregation networks (`aircraft_crew_pilot`, `aircraft_cabin_services`, `aircraft_gate_services`, `aircraft_ground_operation`); no step calls a leaf network directly.

### Layer 2 — Aggregation Networks (Routers)

Aggregation networks fan out to multiple leaf networks based on an `instruction` field or a primary intent. They are the busiest call points in the system. The Downstream-leaves column lists each leaf on its own line for readability.

| Aggregation network                                                                               | Role                                                                                        | Downstream leaves                                                                                                                                                                                                                                                                                                                                    |
|---------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`aircraft_ground_operation`](registries/AirlineTurnaround/aircraft_ground_operation.hocon)       | Pure pass-through router. Two-level routing chain when calling `aircraft_ground_servicing`. | [`aircraft_ground_readiness`](registries/AirlineTurnaround/aircraft_ground_readiness.hocon)<br>[`aircraft_ground_rampservices`](registries/AirlineTurnaround/aircraft_ground_rampservices.hocon)<br>[`aircraft_ground_servicing`](registries/AirlineTurnaround/aircraft_ground_servicing.hocon)                                                      |
| [`aircraft_ground_servicing`](registries/AirlineTurnaround/aircraft_ground_servicing.hocon)       | Routes baggage, inspection/maintenance, fueling.                                            | [`aircraft_baggage_unload`](registries/AirlineTurnaround/aircraft_baggage_unload.hocon)<br>[`aircraft_inspection_maintenance`](registries/AirlineTurnaround/aircraft_inspection_maintenance.hocon)<br>[`aircraft_fueling`](registries/AirlineTurnaround/aircraft_fueling.hocon)                                                                      |
| [`aircraft_ground_rampservices`](registries/AirlineTurnaround/aircraft_ground_rampservices.hocon) | Wheelchocks install, ACU connect, GPU connect (consolidated ramp operation).                | [`aircraft_ground_wheels_chocks_install`](registries/AirlineTurnaround/aircraft_ground_wheels_chocks_install.hocon)<br>[`aircraft_ground_acu_connect`](registries/AirlineTurnaround/aircraft_ground_acu_connect.hocon)<br>[`aircraft_ground_gpu_connect`](registries/AirlineTurnaround/aircraft_ground_gpu_connect.hocon)                            |
| [`aircraft_ground_readiness`](registries/AirlineTurnaround/aircraft_ground_readiness.hocon)       | Pre-flight readiness checks for ground services.                                            | [`aircraft_ground_wheels_chocks_setup`](registries/AirlineTurnaround/aircraft_ground_wheels_chocks_setup.hocon)<br>[`aircraft_ground_acu_setup`](registries/AirlineTurnaround/aircraft_ground_acu_setup.hocon)<br>[`aircraft_ground_gpu_setup`](registries/AirlineTurnaround/aircraft_ground_gpu_setup.hocon)                                        |
| [`aircraft_cabin_services`](registries/AirlineTurnaround/aircraft_cabin_services.hocon)           | Cabin cleaning, lavatory service, catering loading.                                         | [`aircraft_cabin_cleaning`](registries/AirlineTurnaround/aircraft_cabin_cleaning.hocon)<br>[`aircraft_lavatory_service`](registries/AirlineTurnaround/aircraft_lavatory_service.hocon)<br>[`aircraft_catering_loading`](registries/AirlineTurnaround/aircraft_catering_loading.hocon)                                                                |
| [`aircraft_gate_services`](registries/AirlineTurnaround/aircraft_gate_services.hocon)             | Jetbridge / stairtruck connection by deplaning equipment type.                              | [`aircraft_jetbridge_connect`](registries/AirlineTurnaround/aircraft_jetbridge_connect.hocon)<br>[`aircraft_stairtruck_connect`](registries/AirlineTurnaround/aircraft_stairtruck_connect.hocon)                                                                                                                                                     |
| [`aircraft_crew_pilot`](registries/AirlineTurnaround/aircraft_crew_pilot.hocon)                   | Crew/pilot orchestration: landing, taxiing, traffic-controller coordination.                | [`aircraft_landing`](registries/AirlineTurnaround/aircraft_landing.hocon)<br>[`aircraft_taxiing`](registries/AirlineTurnaround/aircraft_taxiing.hocon)<br>[`aircraft_traffic_controller`](registries/AirlineTurnaround/aircraft_traffic_controller.hocon)<br>[`aircraft_ground_traffic`](registries/AirlineTurnaround/aircraft_ground_traffic.hocon) |
| [`aircraft_crew_cabin`](registries/AirlineTurnaround/aircraft_crew_cabin.hocon)                   | Cabin crew sequencing including debrief and crew exit.                                      | [`aircraft_crew_debrief`](registries/AirlineTurnaround/aircraft_crew_debrief.hocon)<br>[`aircraft_crew_exit`](registries/AirlineTurnaround/aircraft_crew_exit.hocon)                                                                                                                                                                                 |

### Layer 3 — Leaf Operational Networks

Each leaf network represents a single bounded capability (engines stop, door opening, baggage unload, etc.). Each:
- Is defined by a `*.hocon` file describing the agent, its parameters, instructions, and allowed `sly_data` flow.
- Receives task assignments from its caller, executes the operation through one or more sub-agents and `coded_tools`, persists state via `TrackerAPI`, and returns a structured response.
- Emits its status (started / in-progress / blocked / completed) and the relevant fields back to the caller.

### Layer 4 — Shared State (`TrackerAPI`) and Event Flow (`sly_data`)

Each network includes a `TrackerAPI` agent (Python-backed `coded_tool`) that reads and writes a shared turnaround context. Two parallel state channels exist:
- **`TrackerAPI`** — authoritative persistence of tracked fields (aircraft type, flight status, gate id, every operational status). Read at the start of each step, written after each meaningful state change.
- **`sly_data`** — neuro-san's per-call payload channel. Each network's `allow` block declares the fields permitted to flow `to_upstream`, `from_upstream`, `to_downstream`, and `from_downstream`. The per-network READMEs document these contracts in detail.

  The `allow` blocks follow a directional convention that minimises payload noise:
  - **`to_upstream`** — only the status fields this network *produces* (e.g. `acu_connection_status` for `aircraft_acu_connect`, `fueling_status` for `aircraft_fueling`). Inputs the network merely received are not echoed back.
  - **`from_upstream`** — the inputs the caller is allowed to inject, ordered consistently as `flight_number, aircraft_type, gate_id, flight_status, ...` followed by any prerequisite statuses.
  - **`to_downstream`** — the subset of context forwarded to sub-networks; typically excludes this network's own output (it hasn't been produced yet).
  - **`from_downstream`** — what sub-networks are allowed to return; includes their produced outputs.

  Symmetric allow lists (the older pattern that echoed every field in every direction) have been replaced by these tighter contracts. The per-network README tables under [`README/`](README/) reflect the current allow blocks verbatim.

### Logging, Metrics, and Reporting

Execution traces and per-agent thinking output are written under [`logs/`](logs/). The optional [`plugins/phoenix/`](plugins/phoenix/) plugin adds OpenTelemetry-based tracing; [`plugins/langfuse/`](plugins/langfuse/) and [`plugins/langsmith/`](plugins/langsmith/) provide alternative observability targets.

---

## Repository Layout

The tree below is a visual reference; for clickable navigation use the [Summary — Network Catalog](#summary--network-catalog) above and the linked file index below the tree.

```
├── run.py                                # Main entrypoint
├── Makefile                              # Common dev targets
├── logging.json                          # Logging config
├── pyproject.toml
├── requirements.txt
├── requirements-build.txt
│
├── registries/                           # HOCON workflow & tool manifests
│   ├── manifest.hocon
│   ├── aaosa.hocon                       # Shared AAOSA registry
│   ├── aaosa_basic.hocon                 # Shared registry (sub-networks)
│   ├── aaosa_basic_debug.hocon           # Debug variant
│   └── AirlineTurnaround/                # All 37 network definitions
│       ├── manifest_aircraft_turnaround.hocon
│       └── aircraft_*.hocon              # 36 network hocons (see Summary above)
│
├── coded_tools/                          # Python executors (one folder per capability)
│   └── AirlineTurnaround/                # 37 capability folders + __init__.py
│       └── aircraft_*/                   # See linked tools section below
│
├── README/                               # 33 per-network README files
│   └── README_Aircraft_*.md              # One README per network
│
├── plugins/                              # Observability and validation plugins
├── servers/neuro_san/                    # Server wrapper utilities
├── toolbox/toolbox_info.hocon
├── logs/                                 # Runner logs + agent thinking traces
├── tests/
├── hocon_est_and_log_parsing/
└── LICENSE.txt
```

### Linked top-level files

- Entrypoint and config: [`run.py`](run.py) · [`Makefile`](Makefile) · [`logging.json`](logging.json) · [`pyproject.toml`](pyproject.toml) · [`pytest.ini`](pytest.ini) · [`requirements.txt`](requirements.txt) · [`requirements-build.txt`](requirements-build.txt) · [`LICENSE.txt`](LICENSE.txt)
- Log parsing helpers: [`parse_test_hocon_log.py`](parse_test_hocon_log.py) · [`parse_test_hocon_log_sequence.py`](parse_test_hocon_log_sequence.py)
- Toolbox: [`toolbox/toolbox_info.hocon`](toolbox/toolbox_info.hocon)

### Linked `coded_tools/` folders

Each network's Python implementation lives in [`coded_tools/AirlineTurnaround/`](coded_tools/AirlineTurnaround/) under a same-named folder:

[`aircraft_turnaround/`](coded_tools/AirlineTurnaround/aircraft_turnaround/) ·
[`aircraft_crew_pilot/`](coded_tools/AirlineTurnaround/aircraft_crew_pilot/) ·
[`aircraft_crew_cabin/`](coded_tools/AirlineTurnaround/aircraft_crew_cabin/) ·
[`aircraft_crew_debrief/`](coded_tools/AirlineTurnaround/aircraft_crew_debrief/) ·
[`aircraft_crew_exit/`](coded_tools/AirlineTurnaround/aircraft_crew_exit/) ·
[`aircraft_landing/`](coded_tools/AirlineTurnaround/aircraft_landing/) ·
[`aircraft_taxiing/`](coded_tools/AirlineTurnaround/aircraft_taxiing/) ·
[`aircraft_traffic_controller/`](coded_tools/AirlineTurnaround/aircraft_traffic_controller/) ·
[`aircraft_ground_traffic/`](coded_tools/AirlineTurnaround/aircraft_ground_traffic/) ·
[`aircraft_gate_selection/`](coded_tools/AirlineTurnaround/aircraft_gate_selection/) ·
[`aircraft_gate_services/`](coded_tools/AirlineTurnaround/aircraft_gate_services/) ·
[`aircraft_jetbridge_connect/`](coded_tools/AirlineTurnaround/aircraft_jetbridge_connect/) ·
[`aircraft_stairtruck_connect/`](coded_tools/AirlineTurnaround/aircraft_stairtruck_connect/) ·
[`aircraft_ground_readiness/`](coded_tools/AirlineTurnaround/aircraft_ground_readiness/) ·
[`aircraft_ground_rampservices/`](coded_tools/AirlineTurnaround/aircraft_ground_rampservices/) ·
[`aircraft_ground_servicing/`](coded_tools/AirlineTurnaround/aircraft_ground_servicing/) ·
[`aircraft_ground_acu_setup/`](coded_tools/AirlineTurnaround/aircraft_ground_acu_setup/) ·
[`aircraft_ground_acu_connect/`](coded_tools/AirlineTurnaround/aircraft_ground_acu_connect/) ·
[`aircraft_ground_gpu_setup/`](coded_tools/AirlineTurnaround/aircraft_ground_gpu_setup/) ·
[`aircraft_ground_gpu_connect/`](coded_tools/AirlineTurnaround/aircraft_ground_gpu_connect/) ·
[`aircraft_ground_wheels_chocks_setup/`](coded_tools/AirlineTurnaround/aircraft_ground_wheels_chocks_setup/) ·
[`aircraft_ground_wheels_chocks_install/`](coded_tools/AirlineTurnaround/aircraft_ground_wheels_chocks_install/) ·
[`aircraft_acu_connect/`](coded_tools/AirlineTurnaround/aircraft_acu_connect/) ·
[`aircraft_gpu_connect/`](coded_tools/AirlineTurnaround/aircraft_gpu_connect/) ·
[`aircraft_chocks_install/`](coded_tools/AirlineTurnaround/aircraft_chocks_install/) ·
[`aircraft_engines_stop/`](coded_tools/AirlineTurnaround/aircraft_engines_stop/) ·
[`aircraft_door_opening/`](coded_tools/AirlineTurnaround/aircraft_door_opening/) ·
[`aircraft_cabin_services/`](coded_tools/AirlineTurnaround/aircraft_cabin_services/) ·
[`aircraft_cabin_cleaning/`](coded_tools/AirlineTurnaround/aircraft_cabin_cleaning/) ·
[`aircraft_cleaning/`](coded_tools/AirlineTurnaround/aircraft_cleaning/) ·
[`aircraft_cleaning_procedure/`](coded_tools/AirlineTurnaround/aircraft_cleaning_procedure/) ·
[`aircraft_lavatory_service/`](coded_tools/AirlineTurnaround/aircraft_lavatory_service/) ·
[`aircraft_catering_loading/`](coded_tools/AirlineTurnaround/aircraft_catering_loading/) ·
[`aircraft_disembark/`](coded_tools/AirlineTurnaround/aircraft_disembark/) ·
[`aircraft_baggage_unload/`](coded_tools/AirlineTurnaround/aircraft_baggage_unload/) ·
[`aircraft_inspection_maintenance/`](coded_tools/AirlineTurnaround/aircraft_inspection_maintenance/) ·
[`aircraft_fueling/`](coded_tools/AirlineTurnaround/aircraft_fueling/)

### Plugins and servers

[`plugins/phoenix/`](plugins/phoenix/) · [`plugins/langfuse/`](plugins/langfuse/) · [`plugins/langsmith/`](plugins/langsmith/) · [`plugins/log_bridge/`](plugins/log_bridge/) · [`plugins/authorization/`](plugins/authorization/) · [`plugins/env_validator/`](plugins/env_validator/) · [`plugins/llm_config_validator/`](plugins/llm_config_validator/) · [`servers/neuro_san/`](servers/neuro_san/)

---

## How It Works (High Level)

### 1) Registries define the workflow

The turnaround workflow and per-capability agents are described via HOCON under:
- [`registries/manifest.hocon`](registries/manifest.hocon)
- [`registries/AirlineTurnaround/manifest_aircraft_turnaround.hocon`](registries/AirlineTurnaround/manifest_aircraft_turnaround.hocon)
- [`registries/AirlineTurnaround/`](registries/AirlineTurnaround/) — one `aircraft_*.hocon` per network/capability (see [Summary — Network Catalog](#summary--network-catalog))

These registry files act as the source of truth for what steps exist and how they are composed. Each network's HOCON declares its `function` (parameters), `instructions` (LLM prompt), `allow` block (`sly_data` flow), and the `tools` it can call (other networks and Python `coded_tools`).

### 2) Coded tools implement each operational capability

Each [`coded_tools/AirlineTurnaround/<capability>/`](coded_tools/AirlineTurnaround/) module is the executable handler for the network's `TrackerAPI` and any side-effecting actions (CSV lookups, file logging, simulation logic).

### 3) Runner executes and logs

[`run.py`](run.py) is the entrypoint that loads config and registries, runs the scenario, and writes:
- [`logs/runner.log`](logs/) — execution traces
- [`logs/nsflow.log`](logs/) — neuro-san framework log
- [`logs/thinking_dir/`](logs/) — per-agent reasoning / tool-level traces

---

## Requirements

- Python (recommended: match your environment; code appears compatible with Python 3.12 based on compiled cache names)
- Install dependencies from [`requirements.txt`](requirements.txt)
- Optional plugin dependencies:
  - [`plugins/phoenix/requirements.txt`](plugins/phoenix/)
  - other plugin-specific requirements as needed ([`langfuse`](plugins/langfuse/), [`langsmith`](plugins/langsmith/))

---

## Setup

### 1) Create a virtual environment (recommended)

```bash
python -m venv venv
source venv/bin/activate
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-build.txt
pip install -r plugins/phoenix/requirements.txt
```

---

## Run

From repo root:

```bash
python run.py
```

Logs will appear under:
- [`logs/runner.log`](logs/) (and date-stamped variants)
- [`logs/nsflow.log`](logs/)
- [`logs/thinking_dir/`](logs/)

---

## Workflows & Turnaround Steps

The 20-step turnaround plan is defined in:
- [`registries/AirlineTurnaround/aircraft_turnaround.hocon`](registries/AirlineTurnaround/aircraft_turnaround.hocon)
- [`registries/AirlineTurnaround/manifest_aircraft_turnaround.hocon`](registries/AirlineTurnaround/manifest_aircraft_turnaround.hocon)

See [`README_Aircraft_Turnaround.md`](README/README_Aircraft_Turnaround.md) for the full step list, routing cheatsheet, and dependency graph.

---

## Data Files

Some coded tools ship with baseline CSVs used by the executors:

### Aircraft base
Lists aircraft types and runway length requirements for landing and takeoff:
- [`coded_tools/AirlineTurnaround/aircraft_traffic_controller/aircraft_base.csv`](coded_tools/AirlineTurnaround/aircraft_traffic_controller/aircraft_base.csv)

### Runways base
Lists available runways and their length:
- [`coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv`](coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv)

### Gate equipment base
Lists gates with their deplaning equipment availability, aircraft model compatibility, and readiness preparation time:
- [`coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv`](coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv)

These are reference inputs for simulation and configuration.

---

## Compliance Notice

This system models simulated turnaround operations and is intended for software prototyping and workflow automation development. It is not certified for real-world aviation operational or safety-critical systems.

---

## License

See [`LICENSE.txt`](LICENSE.txt).

## Author

JC Noubeyo
