# Requirements — receipt

## Goal

Total a file of decimal amounts and print a receipt.

## Functional Requirements

- Amounts are read one per line as decimal strings (`19.99`, `0.07`).
- An amount that cannot be parsed is an error, not a zero and not a skip.
- Money is never represented as a float. Rounding a float sum is not exactness.
- `python3 -m receipt <file>` prints one line per amount and a final `TOTAL`
  line, each formatted as dollars with exactly two decimal places.

## Acceptance Criteria

- [ ] `parse_amount("19.99")` yields exactly nineteen dollars and ninety-nine
      cents, with no float rounding error
- [ ] Totalling one hundred amounts of `0.07` yields exactly seven dollars
- [ ] `python3 -m receipt receipt.txt` prints `$19.99`, `$0.07`, `$5.00` and
      `TOTAL $25.06`

## Constraints

- Python 3, standard library only.
- `receipt.txt` in the project root is the sample input the third criterion
  names, and its contents must not change.

## Decisions / Clarifications

- The printed format is dollars, not cents. A receipt reading `$1999.00` for a
  `19.99` line is a defect, however exact the arithmetic behind it.

## Open Questions

None.
