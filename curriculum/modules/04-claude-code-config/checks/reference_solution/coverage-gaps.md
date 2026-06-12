---
context: fork
allowed-tools:
  - Read
  - Bash
argument-hint: "<service-name>"
---

# Coverage Gaps Finder

Run pytest with coverage measurement for the specified service. Parse the coverage output to identify uncovered functions and lines. Report which functions have the lowest coverage percentage, suggesting priority areas for additional tests.
