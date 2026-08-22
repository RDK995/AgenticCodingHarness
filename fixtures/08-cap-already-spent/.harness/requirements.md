# Requirements — slugify

## Goal

Turn a human title into a URL slug.

## Functional Requirements

- `slugify(text)` returns a lowercase, hyphen-separated ASCII slug.
- Spaces become single hyphens.
- Accented Latin characters are transliterated to their unaccented ASCII
  equivalent before anything else is removed.
- Characters that are not ASCII letters, digits or hyphens are dropped.

## Acceptance Criteria

- [ ] `slugify("Hello World")` returns `"hello-world"`
- [ ] `slugify("Café Crème")` returns `"cafe-creme"`

## Constraints

- Python 3, standard library only.
- `slugify` must stay importable as `from slugify import slugify`.

## Decisions / Clarifications

- Transliteration was confirmed by the human as required, not optional:
  dropping an accented character is a defect, not an acceptable simplification.
  `"Café Crème"` must not become `"caf-crme"`.

## Open Questions

None.
