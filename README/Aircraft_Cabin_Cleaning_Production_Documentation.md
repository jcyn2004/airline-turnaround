# Aircraft Cabin Cleaning

## Agentic AI Network -- Production Documentation

> **Source configuration:** `aircraft_cabin_cleaning.hocon`\
> **Primary use case:** Orchestrate and execute aircraft cabin cleaning
> operations during turnaround, ensuring prerequisite states are
> satisfied and tracked.

------------------------------------------------------------------------

## 1. Purpose

This repository defines a production-grade **agentic AI network**
responsible for managing the **cabin cleaning process** of an aircraft
during airport turnaround.

The system combines:

-   LLM-based orchestration for workflow management\
-   Deterministic execution tools for cleaning operations\
-   Structured parameter schemas for safe integration\
-   Turnaround state tracking via a Tracker API\
-   Structured JSON output for downstream systems

The network ensures cabin cleaning is executed only when operational
prerequisites are met.

------------------------------------------------------------------------

## 2. System Architecture

### 2.1 High-Level Design

    User / Caller
       │
       ▼
    Cabin Cleaning Agent (LLM Orchestrator)
       │
       ├── TrackerAPI (Execution Tool: read/write turnaround state)
       │
       ├── Aircraft Doors Open (External tool, if required)
       │
       └── Cabin Cleaning Operator (Execution Tool)

### 2.2 Design Principles

-   **Operational gating:** Cleaning occurs only when aircraft is on
    blocks and cabin access is authorized (doors open, jet bridge
    connected if required).
-   **Tool-driven execution:** Physical cleaning actions are executed
    via deterministic tools.
-   **State observability:** TrackerAPI is used before and after
    cleaning operations.
-   **Structured output:** Final result is returned as a JSON state
    summary.

------------------------------------------------------------------------

## 3. Runtime Configuration

### 3.1 LLM Configuration

-   Model: `gpt-4o`

### 3.2 Execution Limits

-   `max_iterations`: 40000\
-   `max_execution_seconds`: 7200

These limits ensure bounded execution during multi-step ground
workflows.

------------------------------------------------------------------------

## 4. Components

### 4.1 Cabin Cleaning Agent (Orchestrator)

**Tool name:** `cabin_cleaning_agent`\
**Type:** LLM Agent

#### Responsibility

The orchestrator:

1.  Parses cleaning request\
2.  Retrieves current turnaround state via `TrackerAPI`\
3.  Verifies prerequisites:
    -   Aircraft must be **on blocks**
    -   Doors must be **open**
4.  Delegates prerequisite actions if needed\
5.  Calls `cabin_cleaning_operator` to perform cleaning\
6.  Updates state via `TrackerAPI`\
7.  Returns structured JSON summary

#### Input Parameters

  Parameter               Type      Required  Description
  ----------------------- -------- ---------- --------------------------
  flight_number           string       ✅     Flight identifier
  aircraft_type           string       ✅     Aircraft model
  flight_status           string       ✅     Flight operational state
  gate_id                 string       ✅     Assigned gate
  door_opening_status     string       ❌     Door status
  cabin_cleaning_status   string       ❌     Current cleaning status

------------------------------------------------------------------------

### 4.2 Cabin Cleaning Operator

**Tool name:** `cabin_cleaning_operator`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_cabin_cleaning.aircraft_cabin_cleaning.cabin_cleaning_operator`

#### Responsibility

Executes the cabin cleaning process and returns updated
`cabin_cleaning_status`.

Typical output values:

-   cleaning_started\
-   cleaning_in_progress\
-   cleaning_completed\
-   cleaning_failed

------------------------------------------------------------------------

### 4.3 TrackerAPI

**Tool name:** `TrackerAPI`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_cabin_cleaning.aircraft_cabin_cleaning.TrackerAPI`

#### Responsibility

Maintains and persists turnaround state across ground operations.

Typical tracked parameters:

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   door_opening_status\
-   cabin_cleaning_status\
-   engines_stop_status\
-   jetbridge_connection_status\
-   passenger_disembarkation_status\
-   baggage_unload_status

TrackerAPI ensures operational traceability and lifecycle visibility.

------------------------------------------------------------------------

## 5. Data Contracts

### 5.1 Orchestrator → Tools

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   door_opening_status\
-   cabin_cleaning_status

### 5.2 Tools → Orchestrator

-   Updated cabin_cleaning_status\
-   Updated door or readiness states (if modified)

### 5.3 Final Output Contract

The orchestrator returns a JSON summary including:

-   flight context\
-   prerequisite states\
-   cabin_cleaning_status

------------------------------------------------------------------------

## 6. Example Interaction

### Example Input

> "Flight AF84 (B747) is on blocks at gate A1. Doors are open. Start
> cabin cleaning."

### Execution Flow

1.  Retrieve state via `TrackerAPI`\
2.  Verify aircraft on blocks\
3.  Verify door status\
4.  Call `cabin_cleaning_operator`\
5.  Update `TrackerAPI`\
6.  Return structured JSON

------------------------------------------------------------------------

## 7. Example Output

``` json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "door_opening_status": "open",
  "cabin_cleaning_status": "cleaning_completed"
}
```

------------------------------------------------------------------------

## 8. Production Considerations

For enterprise-grade deployment:

-   Add retry and timeout logic for cleaning operations\
-   Implement concurrency controls for shared turnaround state\
-   Add persistent storage backend\
-   Add detailed logging, tracing, and metrics\
-   Integrate workforce allocation systems\
-   Add SLA monitoring and reporting

------------------------------------------------------------------------

## 9. Extensibility

Potential enhancements:

-   Zone-based cabin cleaning tracking\
-   Integration with crew scheduling systems\
-   Real-time progress monitoring dashboards\
-   Event-driven updates via message bus\
-   Predictive cleaning duration estimation

------------------------------------------------------------------------

## 10. Compliance & Safety Notice

This system models simulated airport turnaround operations.

It is not certified for real-world aviation control systems.

------------------------------------------------------------------------

## 11. License

Add your project license here.
