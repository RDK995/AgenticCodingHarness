# Architecture

## Status

AGREED

## Overview

One process. An HTTP layer parses and responds, a domain layer decides, a store
persists, and a clock is injected so expiry is testable. Components are named by
tier because that is how the responsibilities divide — not as a build order.

## Components

### C1 — HTTP API

Responsibility: Parse and validate requests, call the domain, and turn results and
domain errors into status codes and JSON bodies. Owns routing and nothing else.
Location: `shortener/http.py`
Depends on: C2
Realises: FR1, FR2, FR3, FR4, FR5

### C2 — Link Service

Responsibility: All link behaviour — code generation, alias claiming, expiry
evaluation, hit counting. The only component that decides anything.
Location: `shortener/service.py`
Depends on: C3, C4
Realises: FR1, FR3, FR4, FR5

### C3 — Link Store

Responsibility: Persist and retrieve links and hit counts in SQLite. Owns the
schema and every SQL statement. Performs no policy.
Location: `shortener/store.py`
Depends on: C5
Realises: FR6

### C4 — Clock

Responsibility: Supply the current UTC instant, injectable so expiry can be tested
without waiting.
Location: `shortener/clock.py`
Depends on: None
Realises: FR5

### C5 — Config

Responsibility: Resolve the SQLite path and the public base URL used to build
`short_url`.
Location: `shortener/config.py`
Depends on: None
Realises: FR1

## Interfaces

C1 → C2 is the only boundary crossed per request. C1 never touches C3; the store
is reached through C2. C4 is injected into C2 rather than read globally.

## Data

A `links` table keyed by `code`, carrying the target URL, creation instant,
optional expiry instant, and a hit counter.

## Technology Choices

Standard library only: `http.server` for C1, `sqlite3` for C3.

## Requirement Coverage

FR1: C1, C2, C5 · FR2: C1, C2 · FR3: C1, C2, C3 · FR4: C1, C2, C3 · FR5: C1, C2, C4 · FR6: C3

## Risks

Expiry evaluated at read time means a clock injected in tests must also be
injected in production, or the two paths diverge.

## Open Architecture Questions

None

## Deviations
