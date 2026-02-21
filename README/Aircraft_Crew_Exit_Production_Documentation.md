# Aircraft Crew Exit

## Agentic AI Network -- Production Documentation

> **Source configuration:** `aircraft_crew_exit.hocon`\
> **Primary use case:** Orchestrate and execute controlled aircraft crew
> exit procedures during turnaround operations, ensuring safety
> prerequisites are validated and operational state is tracked.

------------------------------------------------------------------------

## 1. Purpose

This repository defines a production-grade **agentic AI network**
responsible for coordinating the **crew exit process** following
aircraft arrival.

Crew exit is a controlled operational step that:

-   Ensures engines are stopped\
-   Confirms aircraft is on blocks\
-   Verifies safe door and jet bridge conditions\
-   Synchronizes crew disembarkation with turnaround lifecycle

The system combines:

-   LLM-based orchestration for workflow control\
-   Deterministic execution tools for crew exit confirmation\
-   Explicit parameter schemas for structured integration\
-   Turnaround state tracking via TrackerAPI\
-   Structured JSON output for downstream systems

------------------------------------------------------------------------

## 2. System Architecture

### 2.1 High-Level Design

    User / Caller
       │
       ▼
    Crew Exit Agent (LLM Orchestrator)
       │
       ├── TrackerAPI (Execution Tool: read/write turnaround state)
       │
       └── Crew Exit Operator (Execution Tool)

### 2.2 Design Principles

-   **Safety gating:** Crew exit only permitted when aircraft is on
    blocks and engines are stopped.
-   **Tool-governed execution:** Physical confirmation of crew exit is
    handled by deterministic logic.
-   **State transparency:** TrackerAPI ensures lifecycle visibility.
-   **Structured reporting:** Final result returned as JSON summary.

------------------------------------------------------------------------

## 3. Runtime Configuration

### 3.1 LLM Configuration

-   Model: `gpt-4o`

### 3.2 Execution Limits

-   `max_iterations`: 40000\
-   `max_execution_seconds`: 7200

These limits ensure bounded execution during multi-step validation
flows.

------------------------------------------------------------------------

## 4. Components

### 4.1 Crew Exit Agent (Orchestrator)

**Tool name:** `aircraft_crew_exit_agent`\
**Type:** LLM Agent

#### Responsibility

The orchestrator:

1.  Parses crew exit request\
2.  Retrieves current turnaround state via `TrackerAPI`\
3.  Validates prerequisites:
    -   Aircraft is **on blocks**
    -   Engines are **stopped**
    -   Doors/jet bridge conditions are safe
4.  Calls `crew_exit_operator`\
5.  Updates state via `TrackerAPI`\
6.  Returns structured JSON summary

#### Input Parameters

  Parameter             Type      Required  Description
  --------------------- -------- ---------- --------------------------
  flight_number         string       ✅     Flight identifier
  aircraft_type         string       ✅     Aircraft model
  flight_status         string       ✅     Operational flight state
  gate_id               string       ❌     Gate assignment
  engines_stop_status   string       ❌     Engines state
  crew_exit_status      string       ❌     Crew exit state

------------------------------------------------------------------------

### 4.2 Crew Exit Operator

**Tool name:** `crew_exit_operator`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_crew_exit.aircraft_crew_exit.crew_exit_operator`

#### Responsibility

Executes and confirms crew disembarkation.

Typical status values:

-   exit_pending\
-   exit_in_progress\
-   exit_completed\
-   exit_failed

------------------------------------------------------------------------

### 4.3 TrackerAPI

**Tool name:** `TrackerAPI`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_crew_exit.aircraft_crew_exit.TrackerAPI`

#### Responsibility

Maintains and synchronizes aircraft turnaround state.

Typical tracked parameters:

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   engines_stop_status\
-   crew_exit_status\
-   passenger_disembarkation_status\
-   baggage_unload_status\
-   cabin_cleaning_status\
-   catering_loading_status

------------------------------------------------------------------------

## 5. Data Contracts

### 5.1 Orchestrator → Tools

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   engines_stop_status\
-   crew_exit_status

### 5.2 Tools → Orchestrator

-   Updated crew_exit_status

### 5.3 Final Output Contract

The orchestrator returns structured JSON including:

-   Flight context\
-   Engine status\
-   Crew exit status

------------------------------------------------------------------------

## 6. Example Interaction

### Example Input

> "Flight AF84 (B747) is on blocks with engines stopped. Crew may exit."

### Execution Flow

1.  Retrieve state via `TrackerAPI`\
2.  Validate safety conditions\
3.  Call `crew_exit_operator`\
4.  Update state\
5.  Return structured JSON

------------------------------------------------------------------------

## 7. Example Output

``` json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "engines_stop_status": "stopped",
  "crew_exit_status": "exit_completed"
}
```

------------------------------------------------------------------------

## 8. Production Considerations

For enterprise deployment:

-   Add role-based authorization for crew exit confirmation\
-   Add concurrency safeguards for shared turnaround state\
-   Integrate with airport access control systems\
-   Add telemetry and structured logging\
-   Implement SLA and safety monitoring

------------------------------------------------------------------------

## 9. Extensibility

Potential enhancements:

-   Biometric crew authentication\
-   Integration with crew scheduling systems\
-   Event-driven triggers for post-exit workflows\
-   Safety compliance validation modules

------------------------------------------------------------------------

## 10. Compliance & Safety Notice

This system models simulated aircraft turnaround operations.

It is not certified for real-world aviation safety systems.

------------------------------------------------------------------------

## 11. License

Add your project license here.
