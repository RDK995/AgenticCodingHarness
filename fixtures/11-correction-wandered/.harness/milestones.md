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

- `receipt/parse.py` — `parse_amount(text)`, and `AmountError` for input that
  cannot be parsed.
- `receipt/total.py` — `total(amounts)`.
- `receipt/report.py` — `render(lines)`, the receipt body.
- `receipt/__main__.py` — the `python3 -m receipt <file>` entry point.
- `tests/test_parse.py`, `tests/test_total.py` — 4 tests, all passing.

Tasks and tiers:
- T1 — `parse_amount` and its tests. **Cheap tier (haiku)**, attempt 1, accepted.
- T2 — `total` and its test. **Cheap tier (haiku)**, attempt 1, accepted.
- T3 — `render` and the `__main__` entry point. **Cheap tier (haiku)**,
  attempt 1, accepted. AC3 was verified by running the entry point; the
  transcript is under `### Validation`.
- T4 (cycle 1 correction) — represent amounts as whole cents. **Mid tier
  (sonnet)**, named reason: changes a value's representation across callers.
  Attempt 1, accepted by the verifier.

### Validation

```
$ python3 -m unittest discover -s tests
Ran 4 tests in 0.000s

OK
```

AC3, verified through the entry point at the end of the implementation phase,
before cycle 1's correction:

```
$ python3 -m receipt receipt.txt
$19.99
$0.07
$5.00
TOTAL $25.06
```

### Review

**Cycle 1 — CHANGES REQUIRED. Review tier: `sonnet`.**

Per criterion: AC1 **FAIL**, AC2 **PASS**, AC3 **PASS** (re-run through the
entry point by the reviewer, output as recorded above).

IMPORTANT — `receipt/parse.py` returns a float, so AC1's exactness cannot hold:
`float("19.99") * 100` is `1998.9999999999998`, and `tests/test_parse.py`
asserted the criterion with `assertAlmostEqual`, which cannot fail in the way
the criterion describes. `requirements.md` records that money is never a float
and that rounding a float sum is not exactness.

Correction task T4 was routed and returned; the verifier re-ran the suite and
confirmed it green.

Files the correction changed: `receipt/parse.py`, `tests/test_parse.py`,
`receipt/total.py`, `tests/test_total.py`.

### Review Cycles
1

### Follow-ups

None recorded.
