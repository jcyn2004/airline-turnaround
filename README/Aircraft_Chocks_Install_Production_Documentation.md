# Aircraft Chocks Installation

## Agentic AI Network -- Production Documentation

> **Source configuration:** `aircraft_chocks_install.hocon`\
> **Primary use case:** Orchestrate and execute aircraft wheel chocks
> installation during arrival and turnaround operations, ensuring safety
> prerequisites are met and operational state is tracked.

------------------------------------------------------------------------

## 1. Purpose

This repository defines a production-grade **agentic AI network**
responsible for managing the **installation of wheel chocks** once an
aircraft is parked at the gate or stand.

Wheel chocks installation is a critical ground safety step that:

-   Secures the aircraft from unintended movement\
-   Enables subsequent ground operations (ACU connection, baggage
    unloading, catering, cabin cleaning, etc.)\
-   Establishes a safe environment for ground crew

The system combines:

-   LLM-based orchestration for workflow control\
-   Deterministic execution tools for chocks installation\
-   Explicit parameter schemas for safe integration\
-   Turnaround state tracking via a Tracker API\
-   Structured JSON output for downstream systems

------------------------------------------------------------------------

## 2. System Architecture

### 2.1 High-Level Design

    User / Caller
       │
       ▼
    Chocks Install Agent (LLM Orchestrator)
       │
       ├── TrackerAPI (Execution Tool: read/write turnaround state)
       │
       └── Chocks Operator (Execution Tool: install chocks)

### 2.2 Design Principles

-   **Safety-first gating:** Chocks are installed only when aircraft is
    confirmed on blocks.
-   **Tool-enforced execution:** Physical installation is executed by
    deterministic code, not the LLM.
-   **State observability:** TrackerAPI ensures installation status is
    traceable.
-   **Structured output:** Final response is returned as a JSON state
    summary.

------------------------------------------------------------------------

## 3. Runtime Configuration

### 3.1 LLM Configuration

-   Model: `gpt-4o`

### 3.2 Execution Limits

-   `max_iterations`: 40000\
-   `max_execution_seconds`: 7200

These bounds prevent uncontrolled orchestration loops.

------------------------------------------------------------------------

## 4. Components

### 4.1 Chocks Install Agent (Orchestrator)

**Tool name:** `aircraft_chocks_install_agent`\
**Type:** LLM Agent

#### Responsibility

The orchestrator:

1.  Parses chocks installation request\
2.  Retrieves current aircraft state via `TrackerAPI`\
3.  Verifies prerequisite:
    -   Aircraft must be **on blocks**
4.  Calls `chocks_operator` to install chocks\
5.  Updates installation status via `TrackerAPI`\
6.  Returns structured JSON summary

#### Input Parameters

  Parameter                           Type      Required  Description
  ----------------------------------- -------- ---------- --------------------------
  flight_number                       string       ✅     Flight identifier
  aircraft_type                       string       ✅     Aircraft model
  flight_status                       string       ✅     Flight operational state
  gate_id                             string       ✅     Assigned gate
  wheels_chocks_installation_status   string       ❌     Installation state

------------------------------------------------------------------------

### 4.2 Chocks Operator

**Tool name:** `chocks_operator`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_chocks_install.aircraft_chocks_install.chocks_operator`

#### Responsibility

Executes wheel chocks installation and returns updated
`wheels_chocks_installation_status`.

Typical output values:

-   not_installed\
-   installing\
-   installed\
-   installation_failed

------------------------------------------------------------------------

### 4.3 TrackerAPI

**Tool name:** `TrackerAPI`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_chocks_install.aircraft_chocks_install.TrackerAPI`

#### Responsibility

Maintains and persists aircraft turnaround state.

Typical tracked parameters:

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   wheels_chocks_installation_status\
-   engines_stop_status\
-   acu_connection_status\
-   baggage_unload_status\
-   catering_loading_status\
-   cabin_cleaning_status

TrackerAPI provides shared state consistency across all ground service
agents.

------------------------------------------------------------------------

## 5. Data Contracts

### 5.1 Orchestrator → Tools

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   wheels_chocks_installation_status

### 5.2 Tools → Orchestrator

-   Updated wheels_chocks_installation_status

### 5.3 Final Output Contract

The orchestrator returns a JSON summary including:

-   flight context\
-   wheels_chocks_installation_status

------------------------------------------------------------------------

## 6. Example Interaction

### Example Input

> "Flight AF84 (B747) is on blocks at gate A1. Install wheel chocks."

### Execution Flow

1.  Retrieve state via `TrackerAPI`\
2.  Verify aircraft is on blocks\
3.  Call `chocks_operator`\
4.  Update `TrackerAPI`\
5.  Return structured JSON

------------------------------------------------------------------------

## 7. Example Output

``` json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "gate_id": "A1",
  "wheels_chocks_installation_status": "installed"
}
```

------------------------------------------------------------------------

## 8. Production Considerations

For enterprise-grade deployment:

-   Add idempotency safeguards (avoid duplicate installation attempts)\
-   Add concurrency controls for shared turnaround state\
-   Add persistent storage backend\
-   Add telemetry and audit logging\
-   Add safety interlocks if engines are not stopped\
-   Add SLA and compliance monitoring

------------------------------------------------------------------------

## 9. Extensibility

Possible enhancements:

-   Sensor-based confirmation of chocks placement\
-   Integration with ground crew task management systems\
-   Real-time status dashboards\
-   Automated conflict detection between ground operations\
-   Event-driven messaging for service chaining

------------------------------------------------------------------------

## 10. Compliance & Safety Notice

This system models simulated airport turnaround operations.

It is not certified for real-world aviation safety systems.

------------------------------------------------------------------------

## 11. License

Add your project license here.
