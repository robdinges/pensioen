---
name: functionele-berekenarchitectuur
description: "Use when working on pension calculations, tax logic, cashflow bugs, accountant differences, source-of-truth conflicts, or refactoring of fiscal calculation code. Helps map the task to a functional calculation step, identify the source of truth, choose the smallest safe implementation slice, and define required tests and migration guards."
argument-hint: "Describe the calculation change, bug, or refactor target"
user-invocable: true
disable-model-invocation: false
---

# Functionele Berekenarchitectuur

Use this skill for any task that changes or analyzes fiscal, pension, cashflow,
accountant, or calculation-related code.

## Purpose

This skill enforces the project rule that calculation work must be organized by
functional calculation step, not by random file boundaries.

## Functional Step Map

Always map the work to one primary step:

1. Scenario
2. Persoonsgegevens
3. Pensioen
4. AOW
5. Arbeid
6. Bruto inkomen
7. Eigen woning
8. Box 1
9. Heffingskortingen
10. Netto inkomen
11. Box 3
12. Vermogen
13. Resultaten

If multiple steps are involved, identify:

- primary step
- dependent steps
- why the dependency exists

## Mandatory Workflow

For every qualifying task:

1. Identify the primary functional step.
2. Identify the current source of truth.
3. Identify whether a second calculation path already exists.
4. Choose the smallest safe implementation slice.
5. Define the direct tests required for the building block.
6. Define the higher-level regression protection required.
7. Check whether the change should move logic toward engine output and away from UI.

## Output Format

When using this skill, produce these decisions explicitly before implementation:

- Primary step
- Current source of truth
- Conflicting or parallel paths
- Smallest safe slice
- Direct tests to add or update
- Higher-level regression checks
- Migration note if the path is not yet clean

## Rules

- Do not accept a calculation change without a clear primary step.
- Do not introduce new fiscal recomputation in presentation code.
- Do not remove a legacy path until the new path is covered by direct and
  regression tests.
- Prefer engine detail output over UI-side reconstruction.

## Relevant Project Documents

- `MASTERPLAN_PENSIOENAPPLICATIE.md`
- `UITVOERINGSPLAN_HERSTRUCTURERING.md`
- `EPIC6_WERKPAKKET_REGRESSIE_VALIDATIE_GOVERNANCE.md`
- `EPIC7_WERKPAKKET_OPSCHONING_DOELARCHITECTUUR.md`
- `docs/archive/epics/` voor historische Epic 1–5-besluiten

## Done Gate

A task using this skill is not ready until it can answer all of these:

- Which functional step changed?
- What is the source of truth now?
- Which tests directly prove the changed building block?
- Which regression check proves the end-to-end behavior?
- Did the change reduce, preserve, or worsen duplicate calculation paths?
