---
type: regex
target: {source: file, path: .harness/state.json}
pattern: '"status"\s*:\s*"DONE"'
match: not_contains
---
