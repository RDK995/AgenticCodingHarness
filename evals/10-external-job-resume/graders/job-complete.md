---
type: regex
target: {source: file, path: .harness/state.json}
pattern: '"status"\s*:\s*"COMPLETE"[\s\S]*"result_sha256"'
---
