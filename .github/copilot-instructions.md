# AI Coding Guidelines

## General principles

- Prefer minimal context usage: only request or include data that is strictly required.

- Avoid verbose explanations unless explicitly requested.

- Keep responses and generated code compact.

## Token efficiency rules

- Do not repeat input data in outputs.

- Avoid restating problem descriptions.

- Prefer references to variables/functions instead of inline duplication.

- Summaries must be <= 5 bullet points unless explicitly expanded.

## Data handling

- Never duplicate large JSON structures in examples.

- Use placeholders for repeated structures (e.g. `...` or `see input`).

- Avoid regenerating unchanged objects in full.

## Code generation

- Prefer incremental diffs or targeted functions instead of full-file rewrites.

- Only modify relevant sections.

## Context discipline

- Assume upstream context is available; do not re-explain it.

- Ask for missing data instead of guessing or expanding.