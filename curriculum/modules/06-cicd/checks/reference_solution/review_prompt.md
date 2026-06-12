# Code Review Prompt

Review the following code files for exactly these bug categories:

- off-by-one: incorrect range boundaries that miss the first or last element
- wrong-comparison: field or value in a comparison that does not match the actual type schema
- unhandled-none: method called on a value that could be None without a guard
- resource-leak: file/socket/connection opened and never closed
- swallowed-exception: except block that catches and then passes or discards silently
- mutable-default: mutable default argument (list, dict, or set) in a function signature

Only report issues you are confident are real defects. Do not report style preferences,
missing docstrings, or speculative "could be improved" observations.

## Prior Findings

Previously reported findings — do not duplicate these:
{{ prior_findings }}

## Files to Review

{% for file_path, content in files %}
=== {{ file_path }} ===
{{ content }}
{% endfor %}

## Output Format

Output a JSON array. Each element must have:
- file (string): relative path from repo root
- line (integer): line number of the issue
- category (string): issue category from the list above
- severity (string): critical, high, medium, or low
- explanation (string): one-sentence explanation of the issue
- fingerprint (string): sha256 of "file:line:category", first 16 hex chars
