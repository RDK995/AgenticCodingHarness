# Milestones

## M1 — A file of amounts is totalled and printed as a receipt

Status: REVIEW

### Outcome

`python3 -m receipt <file>` reads decimal amounts, totals them exactly, and
prints a receipt in dollars.

### Architecture

N/A

### Acceptance Criteria
- [ ] `parse_amount("19.99")` yields exactly nineteen dollars and ninety-nine
      cents, with no float rounding error
- [ ] Totalling one hundred amounts of `0.07` yields exactly seven dollars
- [ ] `python3 -m receipt receipt.txt` prints `$19.99`, `$0.07`, `$5.00` and
      `TOTAL $25.06`

### Baseline

The fixture's initial `baseline` commit, on the default branch.

### Evidence

- `receipt/parse.py` — `parse_amount(text)`, returning whole cents, and
  `AmountError` for input that cannot be parsed.
- `receipt/total.py` — `total(amounts)`.
- `receipt/report.py` — `render(lines)`, the receipt body.
- `receipt/__main__.py` — the `python3 -m receipt <file>` entry point.
- `tests/test_parse.py`, `tests/test_total.py` — 6 tests, all passing.

Tasks and tiers:
- T1 — `parse_amount` and its tests. **Cheap tier (haiku)**, attempt 1, accepted.
- T2 — `total` and its test. **Cheap tier (haiku)**, attempt 1, accepted.
- T3 — `render` and the `__main__` entry point. **Cheap tier (haiku)**,
  attempt 1, accepted. AC3 was verified by running the entry point; the
  transcript is under `### Validation`.
- T4 (cycle 1 correction) — reject malformed amounts. **Cheap tier (haiku)**,
  attempt 1, accepted by the verifier.

### Validation

```
$ python3 -m unittest discover -s tests
Ran 6 tests in 0.000s

OK
```

AC3, verified through the entry point:

```
$ python3 -m receipt receipt.txt
$19.99
$0.07
$5.00
TOTAL $25.06
```

### Review

**Cycle 1 — CHANGES REQUIRED. Review tier: `sonnet`.**

Per criterion: AC1 **PASS**, AC2 **PASS**, AC3 **PASS**, each re-verified by the
reviewer rather than credited from the record.

IMPORTANT — `receipt/parse.py` accepted input it should reject.
`parse_amount("1.2.3")`, `parse_amount("1.234")` and `parse_amount("1.23")` all
returned 123: the fractional part had its separators stripped and was truncated
to two digits rather than checked. `requirements.md` requires that an amount
which cannot be parsed is an error, not a zero and not a skip, and
`tests/test_parse.py` had no case for either malformed string.

Correction task T4 was routed and returned; the verifier re-ran the suite and
confirmed it green.

Files the correction changed: `receipt/parse.py`, `tests/test_parse.py` — both
named by the finding above, none outside it.

### Review Cycles
1

### Follow-ups

None recorded.
