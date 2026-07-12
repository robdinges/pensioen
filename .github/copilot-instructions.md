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

## Internal reporting discipline

- Keep internal progress reporting minimal by default (max 1 short status update per meaningful step).

- Do not generate extra narrative reports or duplicate summaries unless explicitly requested.

- Prefer concise deltas over full recaps when work is incremental.

- If token usage can be reduced by skipping optional explanation, skip it.

## Data handling

- Never duplicate large JSON structures in examples.

- Use placeholders for repeated structures (e.g. `...` or `see input`).

- Avoid regenerating unchanged objects in full.

## Code generation

- Prefer incremental diffs or targeted functions instead of full-file rewrites.

- Only modify relevant sections.

## Done criteria (project gate)

- Treat calculation-affecting changes as incomplete until related tests/fixtures are updated.

- For fiscal or cashflow logic updates, require raw testcase updates plus regenerated normalized artifacts.

- For fiscal, pension, cashflow, accountant, or tax-related work, first map the task to exactly one functional calculation step from the project masterplan before proposing or making code changes.

- For calculation-affecting work, explicitly identify the current source of truth and do not introduce a second calculation path in UI, API, reporting, or helper code.

- Prefer small implementation slices per calculation building block. Do not mix unrelated calculation steps in one change unless the dependency is explicit and unavoidable.

- When changing a calculation, require both:
	- direct tests for the touched building block when they do not exist yet
	- regression protection at the higher-level path where the bug or behavior appears

- Treat standalone fiscal recomputation in presentation code as architecture debt. Prefer moving detail logic into engine output rather than reproducing formulas in UI code.

## Context discipline

- Assume upstream context is available; do not re-explain it.

- Ask for missing data instead of guessing or expanding.