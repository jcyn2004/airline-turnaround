# Aircraft Crew Debrief

## Agentic AI Network -- Production Documentation

> **Source configuration:** `aircraft_crew_debrief.hocon`\
> **Primary use case:** Orchestrate and document post-flight crew
> debrief activities during aircraft turnaround, ensuring structured
> reporting and operational state synchronization.

------------------------------------------------------------------------

## 1. Purpose

This repository defines a production-grade **agentic AI network**
responsible for coordinating the **post-flight crew debrief process** as
part of aircraft turnaround operations.

Crew debrief is a structured operational step used to:

-   Capture flight performance insights\
-   Record incidents or irregularities\
-   Synchronize operational observations\
-   Provide structured data for downstream analytics and compliance
    systems

The system combines:

-   LLM-based orchestration for structured dialogue and workflow
    control\
-   Deterministic execution tools for recording and persisting debrief
    data\
-   Explicit parameter schemas for controlled integration\
-   Turnaround lifecycle tracking via a TrackerAPI\
-   Structured JSON output for reporting systems

------------------------------------------------------------------------

## 2. System Architecture

### 2.1 High-Level Design

    User / Caller
       │
       ▼
    Crew Debrief Agent (LLM Orchestrator)
       │
       ├── TrackerAPI (Execution Tool: read/write turnaround state)
       │
       └── Crew Debrief Recorder (Execution Tool: persist debrief report)

### 2.2 Design Principles

-   **Structured reporting:** Debrief data is captured in a controlled
    JSON schema.
-   **Separation of reasoning and persistence:** LLM structures debrief
    content; execution tools persist it.
-   **Lifecycle synchronization:** TrackerAPI ensures debrief status is
    reflected in turnaround state.
-   **Auditability:** All debrief records are traceable and structured.

------------------------------------------------------------------------

## 3. Runtime Configuration

### 3.1 LLM Configuration

-   Model: `gpt-4o`

### 3.2 Execution Limits

-   `max_iterations`: 40000\
-   `max_execution_seconds`: 7200

These limits ensure bounded orchestration during structured dialogue
flows.

------------------------------------------------------------------------

## 4. Components

### 4.1 Crew Debrief Agent (Orchestrator)

**Tool name:** `aircraft_crew_debrief_agent`\
**Type:** LLM Agent

#### Responsibility

The orchestrator:

1.  Parses crew debrief request\
2.  Retrieves flight context via `TrackerAPI`\
3.  Structures debrief information (observations, incidents, notes)\
4.  Calls `crew_debrief_recorder` to persist the report\
5.  Updates turnaround state via `TrackerAPI`\
6.  Returns structured JSON summary

#### Input Parameters

  Parameter        Type      Required  Description
  ---------------- -------- ---------- -----------------------------------
  flight_number    string       ✅     Flight identifier
  aircraft_type    string       ✅     Aircraft model
  flight_status    string       ✅     Operational state
  gate_id          string       ❌     Gate assignment
  debrief_notes    string       ❌     Structured or raw debrief content
  debrief_status   string       ❌     Debrief process state

------------------------------------------------------------------------

### 4.2 Crew Debrief Recorder

**Tool name:** `crew_debrief_recorder`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_crew_debrief.aircraft_crew_debrief.crew_debrief_recorder`

#### Responsibility

Persists structured debrief reports and returns updated
`debrief_status`.

Typical status values:

-   debrief_started\
-   debrief_recorded\
-   debrief_validated\
-   debrief_failed

------------------------------------------------------------------------

### 4.3 TrackerAPI

**Tool name:** `TrackerAPI`\
**Type:** Deterministic execution class

**Implementation reference:**\
`AirlineTurnaround.aircraft_crew_debrief.aircraft_crew_debrief.TrackerAPI`

#### Responsibility

Maintains turnaround state synchronization.

Typical tracked parameters:

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   debrief_status\
-   engines_stop_status\
-   passenger_disembarkation_status\
-   baggage_unload_status\
-   cabin_cleaning_status\
-   catering_loading_status

TrackerAPI ensures crew debrief completion is reflected in the broader
turnaround lifecycle.

------------------------------------------------------------------------

## 5. Data Contracts

### 5.1 Orchestrator → Tools

-   flight_number\
-   aircraft_type\
-   flight_status\
-   gate_id\
-   debrief_notes\
-   debrief_status

### 5.2 Tools → Orchestrator

-   Updated debrief_status\
-   Confirmation of report persistence

### 5.3 Final Output Contract

The orchestrator returns a structured JSON block summarizing:

-   Flight context\
-   Debrief content (or reference ID)\
-   Debrief status

------------------------------------------------------------------------

## 6. Example Interaction

### Example Input

> "Flight AF84 (B747) has arrived. Record crew debrief with notes about
> minor turbulence and catering delay."

### Execution Flow

1.  Retrieve flight context via `TrackerAPI`\
2.  Structure debrief content\
3.  Call `crew_debrief_recorder`\
4.  Update turnaround state\
5.  Return structured JSON summary

------------------------------------------------------------------------

## 7. Example Output

``` json
{
  "flight_number": "AF84",
  "aircraft_type": "B747",
  "flight_status": "on blocks",
  "debrief_status": "debrief_recorded",
  "debrief_notes": "Minor turbulence encountered. Catering delay reported."
}
```

------------------------------------------------------------------------

## 8. Production Considerations

For enterprise deployment:

-   Integrate persistent storage (database or document store)\
-   Add validation schema for structured debrief fields\
-   Add role-based access controls\
-   Add digital signature capability\
-   Implement audit trail logging\
-   Integrate with compliance and safety reporting systems

------------------------------------------------------------------------

## 9. Extensibility

Potential enhancements:

-   Incident severity classification\
-   Integration with safety management systems (SMS)\
-   Automatic analytics tagging\
-   Natural language summarization for dashboards\
-   Event-driven workflow triggers (maintenance, safety review)

------------------------------------------------------------------------

## 10. Compliance & Safety Notice

This system models simulated aircraft turnaround and reporting
workflows.

It is not certified for real-world regulatory aviation reporting
systems.

------------------------------------------------------------------------

## 11. License

Add your project license here.
