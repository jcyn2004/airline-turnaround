# Aircraft Turnaround Process Overview

This repository implements a multi-agent system for aircraft turnaround management, orchestrating operations from aircraft entering the airport controlled airspace to arrival at the gate and through all steps thereafter until departure of the next flight. The process is modeled as a coordinated, time-dependent workflow aligned with real airport operations, as illustrated in the turnaround Gantt chart. In its current release, this implementation covers the inbound phase up to the aircraft refueling.

## Arrival and Initial Ground Setup

Upon aircraft entry to the airspace on the airport control, its request clearance for landing. From that point, ground services readiness is confirmed in parallel with gate assignment and plane deboarding equipment.

Once the aircraft taxis to the gate and comes to a complete stop, wheel chocks are placed and engines are shut down to ensure safety. Ground power and air conditioning units are then connected, deboarding equipment (jetbridge or stairtruck) is connected to the aircraft, and the cabin doors are opened.

## Passenger Disembarkation and Unloading Operations

Passenger disembarkation begins immediately after cabin access is established. In parallel, baggage, cargo, and mail unloading operations are carried out. A crew debrief occurs during this phase to communicate aircraft status, turnaround constraints, and task coordination between agents.

## Cabin Servicing and Maintenance

Cabin cleaning starts once passenger disembarkation is complete, followed by lavatory and water servicing. Catering is loaded while cleaning is in progress to minimize idle time. A technical inspection by the maintenance crew is conducted concurrently, ensuring the aircraft's airworthiness before departure.

## Refueling and Loading

Fueling operations are performed in coordination with maintenance and servicing activities. After unloading is complete and cabin servicing concludes, checked baggage and cargo for the outbound flight are loaded.

## Boarding and Departure Preparation

Once the aircraft is secured and prepared, boarding is announced and passengers begin boarding. After boarding completion, doors are closed and final departure checks are performed. The pushback sequence follows, including ground unit disconnection and engine start.

## Pushback and Taxi Clearance

The tug is disconnected after pushback, final safety checks are completed, and taxi clearance is received, marking the end of the turnaround process.

## Multi-Agent System Perspective

Each major activity is managed by specialized agentic system (e.g., aircraft_ground_servics, aircraft_baggage_unload, aircraft_inspection_maintenance). Agents operate both sequentially and in parallel, respecting task dependencies and safety constraints, with the goal of minimizing total turnaround time while maintaining operational reliability.

## High-Level Architecture

The system is organized around an orchestrated multi-agent workflow that executes a turnaround plan with task dependencies and parallelism.

### Core Components

#### Orchestrator / Supervisor – The aircraft_turnaround Multi-Agent System

The aircraft_turnaround is the orchestrator:
- Defined in the `aircraft_turnaround.hocon` file
- Initializes the turnaround run, sets the tasks sequence and calls agentic subsystems in charge of each phase of the flow
- Tracks global state (aircraft status, time window, constraints) and determines which tasks are eligible to start

#### Sub Agent Layer (Specialized Operational Agentic Systems)

Independent agent systems represent functional roles (e.g., ground services, inspection maintenance, fueling, maintenance).

Each agentic system:
- Is defined by a `*.hocon` file
- Receives task assignments from the orchestrator (assign gate, stop engines, disembark passengers)
- Executes task logic
- Emits status updates (started / in-progress / blocked / completed) and resource usage

#### Shared State & Event Bus

Each sub agentic system includes the TrackerAPI agent that reads and writes state or event to the shared state and event bus using a python tool.

The shared state store maintains the authoritative turnaround context (gate availability, runways and characteristics, aircraft types and landing or takeoff requirements).

An event bus (or message passing interface) distributes updates between agents and the orchestrator for coordination and conflict resolution.

#### Logging, Metrics, and Reporting

Captures event timelines and task execution traces.

## Repository Layout

```
├── run.py                          # Main entrypoint
├── logging.json                    # Logging config
├── registries/                     # HOCON workflow & tool manifests
│   ├── manifest.hocon
│   ├── AirlineTurnaround/
│   │   ├── manifest_aircraft_turnaround.hocon
│   │   ├── aircraft_turnaround.hocon
│   │   ├── aircraft_landing.hocon
│   │   ├── aircraft_taxiing.hocon
│   │   ├── aircraft_gate_selection.hocon
│   │   ├── aircraft_traffic_controller.hocon
│   │   ├── aircraft_ground_traffic.hocon
│   │   ├── aircraft_ground_services.hocon
│   │   ├── aircraft_engines_stop.hocon
│   │   ├── aircraft_chocks_install.hocon
│   │   ├── aircraft_jetbridge_connect.hocon
│   │   ├── aircraft_gpu_connect.hocon
│   │   ├── aircraft_acu_connect.hocon
│   │   ├── aircraft_door_opening.hocon
│   │   ├── aircraft_cabin_opening.hocon
│   │   ├── aircraft_disembark.hocon
│   │   ├── aircraft_baggage_unload.hocon
│   │   ├── aircraft_catering_loading.hocon
│   │   ├── aircraft_cabin_cleaning.hocon
│   │   ├── aircraft_cleaning.hocon
│   │   ├── aircraft_cleaning_procedure.hocon
│   │   ├── aircraft_lavatory_service.hocon
│   │   ├── aircraft_fueling.hocon
│   │   ├── aircraft_inspection_maintenance.hocon
│   │   ├── aircraft_crew_debrief.hocon
│   │   └── aircraft_crew_exit.hocon
│   ├── aaosa.hocon
│   └── aaosa_basic.hocon
├── coded_tools/                    # Python executors (one folder per capability)
│   ├── AirlineTurnaround/
│   │   ├── aircraft_landing/aircraft_landing.py
│   │   ├── aircraft_taxiing/aircraft_taxiing.py
│   │   ├── aircraft_traffic_controller/aircraft_traffic_controller.py
│   │   ├── aircraft_gate_selection/aircraft_gate_selection.py
│   │   ├── aircraft_ground_traffic/aircraft_ground_traffic.py
│   │   ├── aircraft_ground_services/aircraft_ground_services.py
│   │   ├── aircraft_engines_stop/aircraft_engines_stop.py
│   │   ├── aircraft_chocks_install/aircraft_chocks_install.py
│   │   ├── aircraft_jetbridge_connect/aircraft_jetbridge_connect.py
│   │   ├── aircraft_gpu_connect/aircraft_gpu_connect.py
│   │   ├── aircraft_acu_connect/aircraft_acu_connect.py
│   │   ├── aircraft_door_opening/aircraft_door_opening.py
│   │   ├── aircraft_disembark/aircraft_disembark.py
│   │   ├── aircraft_baggage_unload/aircraft_baggage_unload.py
│   │   ├── aircraft_catering_loading/aircraft_catering_loading.py
│   │   ├── aircraft_cabin_cleaning/aircraft_cabin_cleaning.py
│   │   ├── aircraft_cleaning/aircraft_cleaning.py
│   │   ├── aircraft_cleaning_procedure/aircraft_cleaning.py
│   │   ├── aircraft_lavatory_service/aircraft_lavatory_service.py
│   │   ├── aircraft_fueling/aircraft_fueling.py
│   │   ├── aircraft_inspection_maintenance/aircraft_inspection_maintenance.py
│   │   ├── aircraft_crew_debrief/aircraft_crew_debrief.py
│   │   └── aircraft_crew_exit/aircraft_crew_exit.py
│   └── __init__.py
├── plugins/
│   ├── phoenix/                    # Optional plugin (with its own README + reqs)
│   └── log_bridge/                 # Log bridge processing
├── servers/
│   └── neuro_san/                  # Server wrapper utilities
├── logs/                           # Runner logs + agent thinking traces
│   ├── runner.log
│   ├── nsflow.log
│   └── thinking_dir/
├── toolbox/toolbox_info.hocon
├── pyproject.toml
├── requirements.txt
├── requirements-build.txt
├── .flake8
├── .pymarkdownlint.yaml
└── LICENSE.txt
```

## How It Works (High Level)

### 1) Registries define the workflow

Your turnaround workflow and capabilities are described via HOCON under:
- `registries/manifest.hocon`
- `registries/AirlineTurnaround/manifest_aircraft_turnaround.hocon`
- `registries/AirlineTurnaround/*.hocon` (one per step/capability)

These registry files act as the source of truth for what steps exist and how they are composed.

### 2) Coded tools implement each operational capability

Each `coded_tools/AirlineTurnaround/<capability>/...py` module is the executable handler for a workflow step (e.g., taxiing, fueling, cleaning, traffic control).

### 3) Runner executes and logs

`run.py` is the entrypoint that loads config + registries, runs the scenario, and writes:
- `logs/runner.log*` for execution traces
- `logs/thinking_dir/` for agent reasoning / tool-level traces

## Requirements

- Python (recommended: match your environment; code appears compatible with Python 3.12 based on compiled cache names)
- Install dependencies from `requirements.txt`
- Optional plugin dependencies:
  - `plugins/phoenix/requirements.txt`

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

### 3) Set path to data files

Find and replace the following path in all files under `/airline-turnaround/` with its equivalent on your own computer.

Basically, use `/Edit/Replace in Files/` menu to find `/Users/971244/workspace/airline-turnaround/` and replace it with the equivalent path on your computer so that a data file path such as:

```
/Users/971244/workspace/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv
```

is replaced by:

```
/Location of the package folder on your computer/airline-turnaround/coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv
```

## Run

From repo root:

```bash
python run.py
```

Logs will appear under:
- `logs/runner.log` (and date-stamped variants)
- `logs/nsflow.log`
- `logs/thinking_dir/`

## Workflows & Turnaround Steps

Key workflows and steps are defined under:
- `registries/AirlineTurnaround/aircraft_turnaround.hocon`
- `registries/AirlineTurnaround/manifest_aircraft_turnaround.hocon`

## Data Files

Some coded tools ship with baseline CSVs used by the executors:

### Aircraft base
Lists aircraft types and runway length requirements for landing and takeoff:
- `coded_tools/AirlineTurnaround/aircraft_traffic_controller/aircraft_base.csv`

### Runways base
Lists available runways and their length:
- `coded_tools/AirlineTurnaround/aircraft_traffic_controller/runways_base.csv`

### Gate equipment base
Lists gates with their deplaning equipment availability, aircraft models compatibility and readiness preparation time:
- `coded_tools/AirlineTurnaround/aircraft_gate_selection/gate_equipments_base.csv`

These are typically used as reference inputs for simulation/configuration.

## License

See LICENSE.txt.

## Author

JC Noubeyo
