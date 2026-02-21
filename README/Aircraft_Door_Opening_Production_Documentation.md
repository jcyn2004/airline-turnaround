# Aircraft Door Opening

## Agentic AI Network -- Production Documentation

> **Source configuration:** `aircraft_door_opening.hocon`\
> **Primary use case:** Orchestrate and execute controlled aircraft door
> opening procedures during arrival and turnaround, ensuring safety
> prerequisites are validated and lifecycle state is tracked.

------------------------------------------------------------------------

## 1. Purpose

This repository defines a production-grade **agentic AI network**
responsible for coordinating the **aircraft door opening process**
following arrival.

Door opening is a safety-critical step that:

-   Requires aircraft to be confirmed **on blocks**\
-   Requires engines to be **stopped**\
-   Must precede passenger disembarkation, crew exit, catering, and
    cleaning\
-   Must be synchronized with jet bridge or stair positioning

The system combines:

-   LLM-based orchestration for workflow control\
-   Deterministic execution tools for physical door operations\
-   Explicit parameter schemas for safe integration\
-   Shared lifecycle state management via TrackerAPI\
-   Structured JSON output for downstream systems

------------------------------------------------------------------------

## 2. System Architecture

### 2.1 High-Level Design

    User / Caller
       │
       ▼
    Door Opening Agent (LLM Orchestrator)
       │
       ├── TrackerAPI (Execution Tool: read/write turnaround state)
       │
       ├── Jet Bridge Connect (External tool, if required)
       │
       └── Door Operator (Execution Tool)

### 2.2 Design Principles

-   **Safety-first gating:** Doors may only open when aircraft is on
    blocks and engines are stopped.
-   **Access validation:** Jet bridge or mobile stairs must be
    positioned before opening doors (if required by configuration).
-   **Tool-governed execution:** Physical door operations are executed
    by deterministic code.
-   **State transparency:** TrackerAPI ensures lifecycle
    synchronization.
-   **Structured reporting:** Final result returned as JSON summary.

------------------------------------------------------------------------

## 3. Runtime Configuration

### 3.1 LLM Configuration

-   Model: `gpt-4o`

### 3.2 Execution Limits

-   `max_iterations`: 40000\
-   `max_execution_seconds`: 7200

These limits ensure bounded orchestration during multi-step validation
workflows.

------------------------------------------------------------------------

## 4. Components

### 4.1 Door Opening Agent (Orchestrator)

**Tool name:** `aircraft_door_opening_agent`\
**Type:** LLM Agent

#### Responsibility

The orchestrator:

1.  Parses door opening request\
2.  Retrieves current turnaround state via `TrackerAPI`\
3.  Validates prerequisites:
    -   Aircraft is **on blocks**
    -   Engines are **stopped**
4.  Verifies jet bridge or stairs positioning (if required)\
5.  Calls `door_operator`\
6.  Updates door status via `TrackerAPI`\
7.  Returns structured JSON summary

#### Input Parameters

  Parameter                     Type      Required  Description
  ----------------------------- -------- ---------- -------------------
  flight_number                 string       ✅     Flight identifier
  aircraft_type                 string       ✅     Aircraft model
  flight_status                 string       ✅     Operational state
  gate_id                       string       ❌     Gate assignment
  engines_stop_status           string       ❌     Engine state
  jetbridge_connection_status   string       ❌     Jet bridge status
  door_opening_status           string       ❌     Door state

------------------------------------------------------------------------

### 4.2 Door Operator

**Tool name:** `door_operator`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_door_opening.aircraft_door_opening.door_operator`

#### Responsibility

Executes aircraft door opening procedure and returns updated
`door_opening_status`.

Typical status values:

-   door_closed\
-   door_opening\
-   door_open\
-   door_open_failed

------------------------------------------------------------------------

### 4.3 TrackerAPI

**Tool name:** `TrackerAPI`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_door_opening.aircraft_door_opening.TrackerAPI`

#### Responsibility

Maintains aircraft turnaround lifecycle state.

Typical tracked parameters:

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   engines_stop_status\
-   jetbridge_connection_status\
-   door_opening_status\
-   passenger_disembarkation_status\
-   crew_exit_status\
-   baggage_unload_status\
-   catering_loading_status\
-   cabin_cleaning_status

TrackerAPI ensures consistent state propagation across dependent ground
service agents.

------------------------------------------------------------------------

## 5. Data Contracts

### 5.1 Orchestrator → Tools

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   engines_stop_status\
-   jetbridge_connection_status\
-   door_opening_status

### 5.2 Tools → Orchestrator

-   Updated door_opening_status

### 5.3 Final Output Contract

The orchestrator returns structured JSON including:

-   Flight context\
-   Engine and access validation states\
-   door_opening_status

------------------------------------------------------------------------

## 6. Example Interaction

### Example Input

> "Flight AF84 (B747) is on blocks at gate A1. Engines stopped and jet
> bridge connected. Open aircraft doors."

### Execution Flow

1.  Retrieve state via `TrackerAPI`\
2.  Validate safety conditions\
3.  Verify jet bridge positioning\
4.  Call `door_operator`\
5.  Update state via `TrackerAPI`\
6.  Return structured JSON

------------------------------------------------------------------------

## 7. Example Output

``` json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "engines_stop_status": "stopped",
  "jetbridge_connection_status": "connected",
  "door_opening_status": "door_open"
}
```

------------------------------------------------------------------------

## 8. Production Considerations

For enterprise deployment:

-   Add hardware sensor validation for door state\
-   Implement concurrency safeguards for shared turnaround state\
-   Integrate with airport access control systems\
-   Add structured logging and telemetry\
-   Implement SLA and safety monitoring\
-   Add emergency override logic

------------------------------------------------------------------------

## 9. Extensibility

Potential enhancements:

-   Multi-door coordination (front/rear doors)\
-   Integration with automated jet bridge alignment systems\
-   Real-time status dashboards\
-   Event-driven triggers for passenger disembarkation workflows

------------------------------------------------------------------------

## 10. Compliance & Safety Notice

This system models simulated aircraft turnaround operations.

It is not certified for real-world aviation safety-critical systems.

------------------------------------------------------------------------

## 11. License

Add your project license here.
