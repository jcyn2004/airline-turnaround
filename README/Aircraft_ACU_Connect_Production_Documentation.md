# Aircraft ACU Connect  
## Agentic AI Network – Production Documentation

> **Source configuration:** `aircraft_acu_connect.hocon`  
> **Primary use case:** Connect an aircraft’s **ACU (Air Conditioning Unit)** at the gate during turnaround, ensuring prerequisites (on-blocks, engines stopped, chocks installed) are satisfied and tracked.

---

## 1. Purpose

This repository defines a production-oriented **agentic AI network** that orchestrates the operational steps required to **connect an ACU unit to an aircraft** at a gate as part of an aircraft turnaround process.

The network combines:

- An LLM-based orchestration agent for intent interpretation and workflow control
- Deterministic execution tools for operational actions (ACU connection) and tracking
- Explicit parameter schemas for predictable integration
- A safety-like gating flow to prevent ACU connection when prerequisites are not met

---

## 2. System Architecture

### 2.1 High-Level Design

```
User / Caller
   │
   ▼
ACU Connect Agent (LLM Orchestrator)
   │
   ├── TrackerAPI (Execution Tool: read/write turnaround state)
   │
   ├── Aircraft Engines Stop (External tool from included registry)
   │
   ├── Aircraft Chocks Install (External tool from included registry)
   │
   └── ACU Operator (Execution Tool: connect ACU)
```

### 2.2 Design Principles

- **Prerequisite enforcement:** ACU connection is only attempted when flight is on blocks, engines are stopped, and chocks are installed.
- **Tool-first execution:** Operational actions are performed by executable tools, not by the LLM directly.
- **Observability:** State is read and persisted via `TrackerAPI` before and after key actions.
- **Structured output:** Final response is a JSON block including all relevant parameters.

---

## 3. Runtime Configuration

### 3.1 LLM Configuration

The orchestrator uses:

- Model: `gpt-4o`

### 3.2 Execution Limits

- `max_iterations`: `40000`
- `max_execution_seconds`: `7200`

These settings bound long-running tool-driven loops (e.g., re-checking status after actions).

---

## 4. Components

### 4.1 ACU Connect Agent (Orchestrator)

**Tool name:** `acu_connect_agent`  
**Type:** LLM Agent (orchestration + delegation)

#### Responsibility

The orchestrator:

1. Extracts operational context from user inquiry
2. Reads the current turnaround state via `TrackerAPI`
3. Enforces prerequisites:
   - Flight must be **on blocks**
   - Engines must be **stopped**
   - Wheel chocks must be **installed**
4. Delegates prerequisite fulfillment if needed (engines stop, chocks install)
5. Calls `acu_operator` to connect the ACU once prerequisites are met
6. Writes updated state back to `TrackerAPI`
7. Returns a JSON summary report

#### Input Schema (Parameters)

| Parameter | Type | Required | Description |
|---|---:|:---:|---|
| `flight_number` | string | ✅ | Flight identifier |
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `flight_status` | string | ✅ | Flight status (e.g., “on blocks”) |
| `gate_id` | string | ✅ | Gate where aircraft is parked |
| `engines_stop_status` | string | ❌ | Engines state (e.g., “stopped”, “running”) |
| `wheels_chocks_installation_status` | string | ❌ | Chocks installation state (e.g., “installed”, “not installed”) |

#### Orchestration Logic (Operational Flow)

1. Parse inquiry and determine whether the following are provided:
   - `flight_status` (expected: “on blocks”)
   - `engines_stop_status` (expected: “stopped”)
   - `wheels_chocks_installation_status` (expected: “installed”)
2. Call `TrackerAPI` and store relevant statuses.
3. If `flight_status` is not **on blocks** → stop and report ACU cannot be connected.
4. If engines are not stopped → call external `aircraft_engines_stop`, then re-check via `TrackerAPI`.
5. If chocks are not installed → call external `aircraft_chocks_install`, then re-check via `TrackerAPI`.
6. When prerequisites are satisfied:
   - Call `acu_operator` and store `acu_connection_status`
7. Call `TrackerAPI` again to persist the updated state.
8. Return JSON summary including all parameters.

> Note: `aircraft_engines_stop` and `aircraft_chocks_install` are referenced by this agent and are expected to be available via the included registry configuration (`registries/aaosa_basic.hocon`).

---

### 4.2 ACU Operator (Execution Tool)

**Tool name:** `acu_operator`  
**Type:** Deterministic execution class

**Implementation reference:**
- `AirlineTurnaround.aircraft_acu_connect.aircraft_acu_connect.acu_operator`

#### Responsibility

Executes the operational action to connect the ACU to the aircraft at the gate, returning an `acu_connection_status` (e.g., connected/failed/details).

#### Input Schema

| Parameter | Type | Required | Description |
|---|---:|:---:|---|
| `flight_number` | string | ✅ | Flight identifier |
| `aircraft_type` | string | ✅ | Aircraft model/type |
| `flight_status` | string | ✅ | Flight status |
| `gate_id` | string | ✅ | Gate where aircraft is parked |
| `acu_connection_status` | string | ❌ | Output/previous status field (used for reporting) |

---

### 4.3 TrackerAPI (Execution Tool)

**Tool name:** `TrackerAPI`  
**Type:** Deterministic execution class

**Implementation reference:**
- `AirlineTurnaround.aircraft_acu_connect.aircraft_acu_connect.TrackerAPI`

#### Responsibility

Acts as the turnaround state tracker. The ACU Connect Agent uses it to:

- Read current operational statuses (engines, chocks, etc.)
- Persist updates after actions (e.g., ACU connected)

#### Notable Tracked Parameters

| Parameter | Type | Description |
|---|---:|---|
| `flight_number` | string | Flight identifier |
| `aircraft_type` | string | Aircraft model/type |
| `flight_status` | string | Flight status |
| `gate_id` | string | Gate assignment |
| `ground_services_request_type` | string | Type of ground service request |
| `wheels_chocks_readiness_status` | string | Readiness indicator |
| `wheels_chocks_installation_status` | string | Installation indicator |
| `acu_readiness_status` | string | ACU readiness |
| `acu_connection_status` | string | ACU connection status |
| `engines_stop_status` | string | Engines stopped indicator |
| `jetbridge_connection_status` | string | Jetbridge status |
| `door_opening_status` | string | Door status |

> Implementation note: the HOCON schema includes `acu_connection_status` twice in the TrackerAPI properties. This appears to be redundant and can be safely deduplicated during schema maintenance.

---

## 5. Data Contracts

This network uses explicit parameter schemas to manage data exchange between agents and tools.

### 5.1 Orchestrator → Tools

- Always passes: `flight_number`, `aircraft_type`, `flight_status`, `gate_id`
- Passes/records additional statuses when available: `engines_stop_status`, `wheels_chocks_installation_status`, `acu_connection_status`

### 5.2 Tools → Orchestrator

- `TrackerAPI` returns latest known statuses
- `acu_operator` returns `acu_connection_status` (and optionally additional connection details)

### 5.3 Final Output Contract

The orchestrator returns a JSON block containing the end-state summary including:

- flight context (number, type, gate, status)
- prerequisite statuses (engines/chocks)
- ACU outcome (`acu_connection_status`)

---

## 6. Example Interaction

### Example Input

> “The B747 aircraft of flight AF84 is on blocks at gate A1. The engines are stopped and wheels chocks have been installed. Connect the ACU.”

### Expected Execution

1. `TrackerAPI` read
2. Validate: on blocks ✅, engines stopped ✅, chocks installed ✅
3. Call `acu_operator`
4. `TrackerAPI` write updated `acu_connection_status`
5. Return JSON summary

---

## 7. Example Output

```json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "engines_stop_status": "stopped",
  "wheels_chocks_installation_status": "installed",
  "acu_connection_status": "connected"
}
```

---

## 8. Extensibility Guidance

Common extensions for production use:

- Add explicit error codes and retry policies for `acu_operator`
- Add persistence/backing store behind `TrackerAPI`
- Add concurrency controls when multiple agents/tools update the same flight record
- Add richer readiness modeling (`acu_readiness_status`) and pre-checks before connection
- Add structured telemetry (traces/metrics) around tool calls

---

## 9. Compliance & Safety Notice

This network models **simulated turnaround operations** and is intended for software prototyping and workflow automation templates.

It is not certified for real-world aviation operations.

---

## 10. License

Add your project license here.
