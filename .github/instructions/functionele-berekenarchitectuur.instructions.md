---
description: "Use when working on fiscal, pension, cashflow, accountant, or calculation-related Python code. Enforces the functional calculation architecture, source-of-truth mapping, and small-slice migration strategy from the project masterplan."
applyTo: "src/pensioen/**/*.py"
---

## Functional Calculation Architecture Rules

Before changing code in this scope, first map the task to exactly one functional
calculation step:

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

If the task spans multiple steps, state the primary step and list the dependent
steps explicitly before editing.

## Source Of Truth Rules

- Every change must identify the current source of truth for the touched step.
- Do not create a second calculation path in UI, API, reporting, or helper code.
- If the current source of truth is not clean, preserve behavior while making the
  conflict explicit in code comments, tests, or documentation.

## Small-Slice Refactoring Rules

- Prefer one calculation building block per change.
- Do not combine pension-source migration, eigen-woning harmonization, and
  box-1 or box-3 changes in one edit unless the dependency is unavoidable.
- Introduce or strengthen direct tests for the touched building block before or
  alongside broader orchestration changes.

## Accountant And Presentation Rules

- Treat any fiscal recomputation in presentation code as temporary debt.
- Prefer adding detail output to the engine over reproducing formulas in UI.
- If a presentation path still recomputes, document that explicitly as a known
  migration gap.

## Required Cross-Checks For Calculation Changes

For 2025 box-1 work, preserve the separate birth-cohort IB boundary and the
common premium boundary; do not derive the premium boundary from an IB bracket.
Preserve the configured employment-credit build-up segments through tariff
period resolution. Regression cases: `tc_2025_013` through `tc_2025_015` and
`tests/test_ola_fiscale_correcties.py`. The 2025 assessment rounds IB per bracket
down, total premiums from the unrounded sum down, and completed tax credits up.
Displayed premium parts need not sum to the rounded premium total. Keep the
explicit AOW-AHK maximum to avoid rounding an approximate factor above its cap.
Do not change source values or increase OLA tolerance to hide regressions.

For 2025 elderly-credit work, preserve the €45,308 phase-out threshold, €2,035
maximum and 15% phase-out. Direct and engine regressions live in
`tests/test_ola_aow_pensioen.py`, with OLA sources `tc_2025_016/017`.
Their €1 AHK differences remain explicit; fiscal annual output and rounded
monthly allocations must be checked separately. Matching AOW inputs for tax
validation does not validate the statutory SVB benefit amount.

For any calculation-affecting change, verify all of the following:

- the touched building block has direct tests, or this change adds them
- the higher-level path that exposes the behavior has regression protection
- the used tariffs and grounds are explicit
- the change aligns with the current masterplan and execution plan documents

Relevant guidance documents:

- `MASTERPLAN_PENSIOENAPPLICATIE.md`
- `UITVOERINGSPLAN_HERSTRUCTURERING.md`
- `EPIC6_WERKPAKKET_REGRESSIE_VALIDATIE_GOVERNANCE.md`
- `EPIC7_WERKPAKKET_OPSCHONING_DOELARCHITECTUUR.md`
