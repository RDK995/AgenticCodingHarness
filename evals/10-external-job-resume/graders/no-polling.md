---
type: regex
target: trace
pattern: 'TaskOutput|(?:^|[;&|]\\s*)sleep\\s|(?:^|[;&|]\\s*)(?:while|until)\\s'
match: not_contains
---
