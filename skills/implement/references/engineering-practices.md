# Engineering Practices

## RED

1. Identify the behaviour being added or fixed.
2. Write or identify a test proving that behaviour.
3. Run it.
4. Confirm failure for the expected reason.

## GREEN

1. Make the smallest reasonable implementation.
2. Run the focused test.
3. Stop when required behaviour works.

## REFACTOR

1. Improve structure after tests pass.
2. Preserve behaviour.
3. Remove justified duplication.
4. Avoid speculative abstractions.
5. Re-run tests.

## General rules

- Prefer small changes.
- Test observable behaviour.
- Preserve existing APIs unless requirements say otherwise.
- Follow established project patterns.
- Do not change unrelated code.
- Do not weaken tests to achieve green.
- Do not introduce abstractions without a current use.
- Do not introduce dependencies without justification.
- Run focused tests frequently.
- Run broader validation before milestone completion.
