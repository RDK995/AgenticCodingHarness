# Requirements

## Goal

A command-line tool that converts a temperature from Celsius to Fahrenheit.

## Functional Requirements

- Given a Celsius value as a command-line argument, print the equivalent
  Fahrenheit value.
- The conversion follows F = C * 9/5 + 32.
- The conversion formula must be implemented as a standalone function that
  can be unit-tested directly, in isolation from command-line argument
  parsing and process I/O.

## Acceptance Criteria

- Running the CLI with `0` prints `32.0`.
- Running the CLI with `100` prints `212.0`.
- Running the CLI with a non-numeric argument exits with a non-zero status and
  an error message on stderr, rather than a stack trace.
- A unit test calls the conversion function directly (no subprocess, no
  argv) and asserts its return value.

## Constraints

- Python 3, standard library only.
- Single-shot CLI invocation — no interactive prompt, no daemon.

## Non-Goals

- Fahrenheit-to-Celsius conversion.
- Any unit other than Celsius/Fahrenheit.
- A GUI or web interface.

## Edge Cases

- Negative Celsius values.
- Non-numeric input.

## Decisions / Clarifications

- Output is the bare numeric value (e.g. `32.0`), not a sentence — this is a
  script-friendly CLI, not a chat interface.
- The formula function and the CLI entrypoint are separate units on purpose
  (see Functional Requirements) — this is a deliberate testability
  requirement, not an invitation to add more layers than that.

## Open Questions

None
