# Harness development checks

The Python tests and structural graders in this directory make no model calls and
cost no tokens:

```bash
for test in .harness-dev/test-*.py; do python3 "$test" || exit 1; done
python3 scripts/check-eval-suite.py
python3 scripts/runtime-preflight.py --claude-version 2.1.269
claude plugin validate .
```

The real local runtime preflight deliberately fails when the installed Claude
Code is older than 2.1.269. Passing a version override is suitable only for the
static test; it is not evidence that the installed runtime supports foreground
plugin evals.

Measure a completed run with explicit provenance, accepted work, retries and
independent accuracy evidence:

```bash
python3 .harness-dev/measure-context.py <session-dir> \
  --top-level-effort medium --top-level-reason-code CONTROLLER \
  --target-project <project> --milestone <id> --run-id <unique-id> \
  --arm treatment --accepted-units 1 --retry-count 0 \
  --accuracy-evidence <accuracy.json> --json <report.json>
```

`check-efficiency.py` applies the per-run hard gates. `compare-efficiency.py`
requires at least three complete reports per arm and applies the campaign cost,
token, worst-run and retry thresholds.

The native definitions under `evals/` can be checked and scaffolded for free with
`scripts/check-eval-suite.py`. Running `claude plugin eval` makes real model calls
and requires the explicit authorization procedure in
`runtime-efficiency-v3-runbook.md`.
