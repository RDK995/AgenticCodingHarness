# Milestones

## M1 — A title can be turned into a URL slug

Status: REVIEW

### Outcome

`slugify(text)` is importable from the project and turns a human title into a
lowercase, hyphen-separated ASCII slug, transliterating accented Latin
characters rather than dropping them.

### Architecture

N/A

### Acceptance Criteria
- [ ] `slugify("Hello World")` returns `"hello-world"`
- [ ] `slugify("Café Crème")` returns `"cafe-creme"`

### Baseline

The fixture's initial `baseline` commit, on the default branch.

### Evidence

- `slugify.py` — `slugify(text)`, lowercases, maps spaces to hyphens, collapses
  runs of hyphens, drops anything that is not ASCII alphanumeric or a hyphen.
- `tests/test_slugify.py` — 3 tests, all passing.

Tasks and tiers:
- T1 — implement `slugify` plus its unittest suite. **Cheap tier (haiku)**,
  attempt 1, accepted.
- T2 (cycle 1 correction) — transliterate accented characters. **Cheap tier
  (haiku)**, attempt 1, accepted by the verifier; the fix did not hold.
- T3 (cycle 2 correction) — transliterate accented characters. **Mid tier
  (sonnet)**, attempt 1, accepted by the verifier; the fix did not hold.

### Validation

```
$ python3 -m unittest discover -s tests
Ran 3 tests in 0.000s

OK
```

### Review

**Cycle 1 — CHANGES REQUIRED. Review tier: `sonnet`.**

IMPORTANT — `slugify("Café Crème")` returns `"caf-crme"`, not `"cafe-creme"`.
The accented characters are dropped by the ASCII filter instead of being
transliterated first. `requirements.md` records transliteration as confirmed by
the human and names this exact string as the case that must not regress. The
suite is green because no test covers the criterion.

Correction task T2 was routed and returned; the reviewer's finding was not
resolved.

**Cycle 2 — CHANGES REQUIRED. Review tier: `sonnet`.**

IMPORTANT — unchanged. `slugify("Café Crème")` still returns `"caf-crme"`.
Acceptance criterion 2 remains unproven and unmet, and still has no test.

Correction task T3 was routed and returned; the reviewer's finding was not
resolved.

### Review Cycles
2

### Follow-ups

- No test covers acceptance criterion 2. Whatever resolves the criterion must
  bring a test with it; the green suite above proves nothing about it.
