# Aircraft Engines Stop

## Agentic AI Network -- Production Documentation

> **Source configuration:** `aircraft_engines_stop.hocon`\
> **Primary use case:** Orchestrate and execute controlled aircraft
> engine shutdown procedures during arrival and turnaround operations,
> ensuring safety prerequisites are validated and lifecycle state is
> tracked.

------------------------------------------------------------------------

## 1. Purpose

This repository defines a production-grade **agentic AI network**
responsible for coordinating the **aircraft engine shutdown process**
following arrival.

Engine shutdown is a safety-critical operation that:

-   Confirms the aircraft has reached final parking position (on
    blocks)\
-   Secures the aircraft for ground crew access\
-   Enables downstream ground operations (chocks installation, door
    opening, disembarkation, servicing)\
-   Establishes a safe state before any physical interaction with the
    aircraft

The system combines:

-   LLM-based orchestration for workflow control\
-   Deterministic execution tools for engine shutdown\
-   Explicit parameter schemas for safe integration\
-   Shared lifecycle state management via TrackerAPI\
-   Structured JSON output for downstream systems

------------------------------------------------------------------------

## 2. System Architecture

### 2.1 High-Level Design

    User / Caller
       │
       ▼
    Engines Stop Agent (LLM Orchestrator)
       │
       ├── TrackerAPI (Execution Tool: read/write turnaround state)
       │
       └── Engines Stop Operator (Execution Tool)

### 2.2 Design Principles

-   **Safety-first gating:** Engines can only be stopped when aircraft
    is confirmed on blocks.
-   **Deterministic execution:** Physical engine shutdown confirmation
    handled by executable logic.
-   **State synchronization:** TrackerAPI maintains lifecycle
    consistency.
-   **Structured reporting:** Final result returned as JSON summary.

------------------------------------------------------------------------

## 3. Runtime Configuration

### 3.1 LLM Configuration

-   Model: `gpt-4o`

### 3.2 Execution Limits

-   `max_iterations`: 40000\
-   `max_execution_seconds`: 7200

These values ensure bounded orchestration and prevent runaway loops.

------------------------------------------------------------------------

## 4. Components

### 4.1 Engines Stop Agent (Orchestrator)

**Tool name:** `aircraft_engines_stop_agent`\
**Type:** LLM Agent

#### Responsibility

The orchestrator:

1.  Parses engine shutdown request\
2.  Retrieves aircraft state via `TrackerAPI`\
3.  Validates prerequisite:
    -   Aircraft is **on blocks**
4.  Calls `engines_stop_operator`\
5.  Updates state via `TrackerAPI`\
6.  Returns structured JSON summary

#### Input Parameters

  Parameter             Type      Required  Description
  --------------------- -------- ---------- -----------------------
  flight_number         string       ✅     Flight identifier
  aircraft_type         string       ✅     Aircraft model
  flight_status         string       ✅     Operational state
  gate_id               string       ❌     Gate assignment
  engines_stop_status   string       ❌     Engine shutdown state

------------------------------------------------------------------------

### 4.2 Engines Stop Operator

**Tool name:** `engines_stop_operator`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_engines_stop.aircraft_engines_stop.engines_stop_operator`

#### Responsibility

Executes engine shutdown confirmation and returns updated
`engines_stop_status`.

Typical status values:

-   engines_running\
-   shutdown_in_progress\
-   engines_stopped\
-   shutdown_failed

------------------------------------------------------------------------

### 4.3 TrackerAPI

**Tool name:** `TrackerAPI`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_engines_stop.aircraft_engines_stop.TrackerAPI`

#### Responsibility

Maintains aircraft turnaround lifecycle state.

Typical tracked parameters:

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   engines_stop_status\
-   wheels_chocks_installation_status\
-   door_opening_status\
-   passenger_disembarkation_status\
-   crew_exit_status\
-   baggage_unload_status\
-   catering_loading_status\
-   cabin_cleaning_status

TrackerAPI ensures downstream services only proceed when engines are
confirmed stopped.

------------------------------------------------------------------------

## 5. Data Contracts

### 5.1 Orchestrator → Tools

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   engines_stop_status

### 5.2 Tools → Orchestrator

-   Updated engines_stop_status

### 5.3 Final Output Contract

The orchestrator returns structured JSON including:

-   Flight context\
-   engines_stop_status

------------------------------------------------------------------------

## 6. Example Interaction

### Example Input

> "Flight AF84 (B747) is on blocks at gate A1. Stop engines."

### Execution Flow

1.  Retrieve state via `TrackerAPI`\
2.  Validate aircraft is on blocks\
3.  Call `engines_stop_operator`\
4.  Update state via `TrackerAPI`\
5.  Return structured JSON

------------------------------------------------------------------------

## 7. Example Output

``` json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "engines_stop_status": "engines_stopped"
}
```

------------------------------------------------------------------------

## 8. Production Considerations

For enterprise deployment:

-   Integrate with engine monitoring sensors\
-   Add idempotency safeguards for repeated shutdown requests\
-   Implement concurrency control for shared turnaround state\
-   Add telemetry, audit logging, and compliance reporting\
-   Integrate with safety management systems

------------------------------------------------------------------------

## 9. Extensibility

Potential enhancements:

-   Multi-engine state modeling\
-   Integration with APU management workflows\
-   Automated confirmation from aircraft systems\
-   Event-driven triggers for subsequent ground operations

------------------------------------------------------------------------

## 10. Compliance & Safety Notice

This system models simulated aircraft turnaround operations.

It is not certified for real-world aviation safety-critical systems.

------------------------------------------------------------------------

## 11. License

Add your project license here.
