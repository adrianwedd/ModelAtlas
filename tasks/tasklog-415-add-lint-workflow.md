# Task 415: Add lint workflow

## Summary
Implemented a reusable lint workflow running `black --check`, `isort --check`, and `flake8`. Updated `ci.yml` to call this workflow and only run tests and docs after lint passes.
