---
name: write-code
description: Implement, modify, and verify code in existing repositories with minimal-risk, evidence-driven changes. Use when requests involve feature implementation, bug fixes, refactors with behavior parity, test creation, CI or build updates, or review follow-up code changes.
---

# Write Code

Follow this workflow to deliver correct, minimal, and verified code changes.

## 1. Define the target before editing

- Restate requested behavior in concrete input and output terms.
- Define acceptance criteria that are testable.
- List assumptions that can be falsified by a command or test.
- Ask one targeted question only when blocked; provide a recommended default.

## 2. Discover authoritative context

- Read the closest tests first, then public interfaces and types, then implementation details.
- Find existing patterns with focused search (`rg` for symbols, file names, and config keys).
- Identify repository invariants: architecture boundaries, lint and type rules, and CI expectations.
- For non-trivial work (3+ steps, multi-file, behavior change), maintain `tasks/todo.md` with:
  - checklist steps
  - explicit verification tasks
  - risk level and rollback notes for medium or high risk
  - working notes for constraints, decisions, and pitfalls

## 3. Plan a minimal safe change

- Prefer the smallest change that satisfies acceptance criteria.
- Reuse existing abstractions and conventions before adding dependencies.
- Avoid drive-by refactors unless they materially reduce risk in the current task.
- Gate high-risk changes (auth, billing, migrations, secrets, deployment) behind a safe rollout strategy.

## 4. Implement in thin slices

- Implement one observable behavior slice at a time.
- Keep one step in progress and verify it before expanding scope.
- Preserve explicit control flow and readable naming.
- Stop immediately when unexpected failures appear; diagnose before adding more changes.

## 5. Add regression protection

- For bug fixes, reproduce first and add a failing test when feasible.
- Add the smallest test that would have caught the issue.
- Prefer:
  - unit tests for pure logic
  - integration tests for boundaries (database, network, queue)
  - e2e tests only for critical user flows
- Validate boundary inputs and error paths, not only happy paths.

## 6. Verify before declaring done

Run the highest relevant verification tier and record outcomes.

- Tier 1: targeted tests plus lint and typecheck
- Tier 2: integration tests plus deterministic local repro
- Tier 3: e2e or staging checks plus rollout monitoring signals (when applicable)

If any check cannot run, state why and provide exact commands to run later.

## 7. Report with evidence

Provide a concise diff-oriented summary:

- what changed
- what behavior changed and what stayed the same
- commands run and outcomes
- remaining risks, assumptions, and rollback notes (if applicable)

Reference concrete artifacts: file paths, test names, and command lines.

## Optional parallelization

- Use focused subagents for repository discovery, failing test triage, and risk review.
- Require structured deliverables from subagents: files, symbols, constraints, and verification commands.

## Guardrails

- Never invent paths, APIs, or config keys; verify in-repo before asserting.
- Never expose secrets in code, logs, or output.
- Fail loudly and safely when behavior cannot be proven.
- Prefer reversible changes and explicit diagnostics over silent fallback behavior.
