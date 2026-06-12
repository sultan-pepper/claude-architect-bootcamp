# Code Review Prompt

<!-- TODO: Write a review prompt that:
     1. Defines the exact bug categories you want Claude to find (with one-line definitions)
     2. States an explicit confidence threshold ("only report if confident")
     3. Excludes style preferences and speculative issues explicitly
     4. Injects prior findings for dedup (replace {{ prior_findings }} with actual JSON in ci_review.py)
     5. Embeds the file contents to review (replaced by ci_review.py at runtime)
     6. Instructs Claude to output valid JSON conforming to the findings schema
-->

Review the following Python code for the categories of bugs defined below.

## Bug categories

<!-- TODO: define each category with a one-line description.
     Categories in scope for this repo:
     - off-by-one
     - unhandled-none
     - resource-leak
     - swallowed-exception
     - mutable-default
     - wrong-comparison
     Add definitions that a reviewer would recognise unambiguously.
-->

## Confidence threshold

<!-- TODO: instruct Claude to only report issues it is confident are real defects.
     Explicitly exclude style, missing docs, and speculative observations.
-->

## Previously reported findings

<!-- TODO: include prior findings here at runtime so Claude can skip them.
     ci_review.py will replace this section with the actual JSON when --prior-findings is provided.
     When no prior findings exist, either omit this section or write: []
-->

{{ prior_findings }}

## Files to review

<!-- ci_review.py will replace this section with the file contents at runtime -->

{{ files }}

## Output format

Output a JSON array. Each element must be an object with these fields:
- `file` (string): relative path from repo root
- `line` (integer): line number of the issue
- `category` (string): one of the categories defined above
- `severity` (string): one of `critical`, `high`, `medium`, `low`
- `explanation` (string): one sentence describing the issue
- `fingerprint` (string): sha256 of `"file:line:category"`, first 16 hex characters

<!-- TODO: add any additional instructions that improve precision or reduce false positives -->
