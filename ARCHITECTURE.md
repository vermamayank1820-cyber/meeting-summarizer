# ADR-001: Agentic AI Meeting Summarizer — Architecture Decision Record

**Status:** Accepted
**Date:** 2026-04-03
**Deciders:** Engineering Lead, Product Owner

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    MEETING SUMMARIZER SYSTEM                     │
│                                                                  │
│  ┌──────────────┐    ┌──────────────────────────────────────┐   │
│  │  /recordings │───▶│         ORCHESTRATOR                 │   │
│  │   (folder)   │    │   (pipeline coordinator)             │   │
│  └──────────────┘    └──────────────┬───────────────────────┘   │
│         ▲                           │                            │
│         │                           ▼                            │
│  ┌──────┴──────┐    ┌──────────────────────────────────────┐   │
│  │   WATCHER   │    │              AGENT PIPELINE           │   │
│  │    AGENT    │    │                                       │   │
│  │ (watchdog)  │    │  [1] Transcription Agent (Whisper)   │   │
│  └─────────────┘    │       ↓                              │   │
│                      │  [2] Cleaning Agent (Claude/OpenAI)  │   │
│  ┌─────────────┐    │       ↓                              │   │
│  │   MANUAL    │───▶│  [3] Summarization Agent (Claude)    │   │
│  │   UPLOAD    │    │       ↓                              │   │
│  │  (FastAPI)  │    │  [4] Storage Agent (JSON + SQLite)   │   │
│  └─────────────┘    └──────────────┬───────────────────────┘   │
│                                    │                             │
│                      ┌─────────────▼──────────────┐            │
│                      │        /outputs              │            │
│                      │  summaries/ transcripts/     │            │
│                      │  database.sqlite              │            │
│                      └─────────────┬───────────────┘            │
│                                    │                             │
│                      ┌─────────────▼──────────────┐            │
│                      │       FastAPI + React        │            │
│                      │         UI Layer             │            │
│                      │   localhost:8000 / :5173     │            │
│                      └─────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

---

## Context

We need a production-ready system to automatically process meeting recordings (Teams, Zoom, Google Meet) into consulting-grade summaries without manual intervention. The system must be autonomous, extensible, and run entirely locally.

---

## Decision

Build a **multi-agent pipeline system** orchestrated by a central coordinator. Each agent has a single, well-defined responsibility. Agents are Python classes that communicate via a shared state dictionary passed through the pipeline.

---

## Options Considered

### Option A: Single Script (Rejected)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Low |
| Extensibility | Very Low |
| Testability | Low |
| Production-readiness | Low |

**Cons:** Hard to debug individual stages, no retry granularity, unmaintainable at scale.

### Option B: Multi-Agent Pipeline (CHOSEN)
| Dimension | Assessment |
|-----------|------------|
| Complexity | Medium |
| Extensibility | High |
| Testability | High |
| Production-readiness | High |

**Pros:** Each agent is independently testable, retryable, and replaceable. Clear separation of concerns. Easy to swap Whisper for another transcription service or Claude for another LLM.

### Option C: Microservices with Message Queue (Over-engineered)
**Cons:** Requires Kafka/RabbitMQ infrastructure; overkill for local system.

---

## Agent Responsibilities

| Agent | Input | Output | Tech |
|-------|-------|--------|------|
| Watcher | `/recordings` folder events | Triggers pipeline | watchdog |
| Transcription | Audio/video file path | Raw transcript text | OpenAI Whisper |
| Cleaning | Raw transcript | Cleaned, structured transcript | Claude API |
| Summarization | Cleaned transcript | Structured JSON summary | Claude API |
| Storage | Summary + transcript | Saved JSON files + SQLite row | sqlite3, json |
| API Layer | HTTP requests | JSON responses | FastAPI |
| UI | User interaction | Display summaries | React + Tailwind |

---

## Consequences

**Easier:**
- Adding a new agent (e.g., speaker diarization) without touching other agents
- Retrying only the failed stage on error
- Testing each agent in isolation

**Harder:**
- Initial setup requires more files than a single script

**To revisit:**
- If volume grows, replace file-based queue with Redis/Celery
- If team grows, split API and UI into separate services

---

## Action Items

- [x] Define agent interfaces
- [x] Implement all 5 agents
- [x] Build FastAPI backend
- [x] Build React UI
- [x] Write requirements.txt and setup guide
