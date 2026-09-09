# Requirements — text statistics

A small library of independent text statistics. Each function is separately
useful and none depends on another, so the work parallelises cleanly.

R1. `word_count(text)` returns the number of whitespace-separated words.
R2. `char_frequency(text)` returns a mapping of character to count, ignoring
    whitespace and treating case as insignificant.
R3. `longest_word(text)` returns the longest whitespace-separated word, and the
    first such word when several tie.

Human-confirmed: an empty string is a legitimate input to all three. `word_count`
returns `0`, `char_frequency` returns an empty mapping, and `longest_word`
returns the empty string.
