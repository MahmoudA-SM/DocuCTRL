---
description: Research-first workflow, interactive planning, quality gate, production-ready
globs:
  - "**/*"
alwaysApply: true
---

Start every response with `RULE_ACTIVE: Project/compyle-like-behavior`.
MANDATORY WORKFLOW: Research → Plan → Build → Verify → Quality Gate when claiming “done” (no skipping)
<!-- MANDATORY WORKFLOW: Research → Interactive Plan → Build (no skipping) -->
<!-- 1) RESEARCH PHASE (no solutions yet)
   - Goal: understand the codebase + problem space thoroughly before suggesting changes.
   - You MUST do all of the following before proposing any fix or plan:
     a) Identify & list the relevant files/modules you will inspect (by name/path if known).
     b) Extract key constraints from the repo (framework, patterns, existing architecture). -->


1) RESEARCH PHASE (bounded, evidence-driven; no solutions yet)
   - Goal: gather just enough repo evidence to choose the correct approach.
   - Before proposing any fix/plan, you MUST output a “Research Snapshot” containing:
     a) Files/modules to inspect first (minimal plausible set; exact paths if known).
     b) Repo constraints discovered from inspection (framework/runtime, scripts, patterns).
     c) Current vs desired behavior (1–3 bullets each) + explicit assumptions if needed.
   - Expand the file list only if evidence demands it (no repo tours).



2) PLAN PHASE (single-shot by default)
   - Produce a complete plan in ONE response:
     A) Scope & success criteria
     B) Options (at least 2 when non-trivial) + recommendation
     C) File-by-file change list
     D) Data/State changes
     E) API/Contracts
     F) UI/UX changes (if applicable)
     G) Tests/verification steps
     H) Rollout/rollback plan
   - Ask questions ONLY when missing info blocks correctness; otherwise proceed with explicit assumptions.
   - No implementation until explicit “Yes” (keep this requirement).


<!-- 2) INTERACTIVE PLAN PHASE (section-by-section, with questions)
   - After research is accepted, create the plan in sections.
   - For EACH section below:
     - Draft ONLY that section
     - Ask me 2–6 questions specific to that section (if needed)
     - STOP and wait for my answers/approval before continuing to the next section

   Plan sections (in this order):
   A) Scope & success criteria (definition of done)
   B) Proposed approach options (at least 2) + why choose one
   C) File-by-file change list (exact files; what changes per file)
   D) Data/State changes (DB/schema/state, migrations, backwards compatibility)
   E) API/Contracts (endpoints, types, inputs/outputs, error cases)
   F) UI/UX changes (if applicable)
   G) Tests/verification steps (unit/integration/e2e, manual checklist)
   H) Rollout/rollback plan (flags, migration order, how to revert safely)

   - At the end, show the full consolidated plan and ask for final approval:
     “Approve plan? (Yes/No/Edits)”
   - No implementation until explicit “Yes”. -->

3) BUILD PHASE (after explicit approval only)
   - Implement strictly the approved plan.
   - Keep changes minimal and incremental.
   - Always show diffs/summaries and ask before broad refactors or multi-file sweeps.

4) QUALITY GATE: fix + build BEFORE any push / PR / “done”

- Whenever you say anything like:
  - “push to GitHub”, “prepare a PR”, “ready to merge”, “finish this task”, or
  - ask the agent to commit/push changes in any way,
  the agent MUST treat that as a quality gate.

- Before doing ANY Git operations or saying the task is “done” / “ready to push”:
  0) Ensure “NO MOJIBAKE” verification is satisfied (fixture/test or explicit check) if strings/IO/UI are touched.
  1) Run `npm run fix` in the repo root.
  2) If it fails, analyze errors, propose fixes, and repeat `npm run fix` until it succeeds or you explicitly say to stop.
  3) Run VERIFY (lint/check/tsc). If it fails: fix → re-run until pass or failures explicitly accepted.
  4) Run `npm run build`.
  5) If `npm run build` fails, diagnose and fix, repeating until it succeeds or you explicitly say to stop.


- The agent must NOT:
  - create commits,
  - push to GitHub,
  - say that work is “done”, “ready to push”, or “ready for PR/merge”
  until `npm run build` has completed successfully in this session.

- If the agent cannot run commands itself, it must instead:
  - tell me to run `npm run fix` then `npm run build`,
  - wait for the outputs, and
  - continue the loop based on my results.


5) PRODUCTION-LEVEL QUALITY (always)
   - Implement everything as if it will run in production immediately:
     - Prefer clear, maintainable architecture over quick hacks.
     - Handle errors, edge cases, and unhappy paths explicitly.
     - Avoid temporary logging, debug flags, and commented-out code in final diffs.
   - For any significant change, include:
     - Types and interfaces kept consistent across the codebase.
     - Input validation and safe handling of external data.
     - Tests or at least a concrete test/verification plan.
   - If there is a tradeoff between speed and robustness, ask me which to prioritize instead of guessing.


6) TEXT ENCODING / NO MOJIBAKE (always)

- Never introduce mojibake (garbled text from encoding errors) in any user-visible output, logs, filenames, or persisted data.
- Preserve original Unicode text exactly end-to-end (input → processing → storage → rendering).
- Do not assume ASCII. Treat all strings as Unicode and all external bytes as explicitly encoded.
- When reading/writing files or network payloads, specify encoding explicitly (default: UTF-8) and avoid implicit platform defaults.
- If encountering decode/encode errors:
  - Prefer failing fast with a clear error message over silently replacing characters.
  - If a tolerant path is required, use an explicit strategy and surface warnings/metrics.
- Tests/verification (at least one):
  - Include a fixture with non-Latin text (e.g., Arabic/emoji) and assert round-trip integrity.
  - For UI: verify rendering in the target environment; for APIs: verify headers/content-type/charset.

- If no existing encoding test exists, add a minimal one as part of the change (unless you explicitly say not to).


<!-- 6) DIFF STYLE: mark added/removed lines

- When showing code changes or diffs, NEVER use plain +/- only.
- For every removed line, append a trailing comment `// removed`.
  - Example: `const oldValue = foo(); // removed`
- For every added line, append a trailing comment `// added`.
  - Example: `const newValue = bar(); // added`
- When a line is modified, show the old line (with `// removed`) and the new line (with `// added`) on separate lines.
- Apply this style both in inline code blocks and in any file-by-file diff summaries. -->

7) DIFF STYLE (readable, reviewable)
   - Show diffs as unified patches in code blocks (git-style).
   - Do NOT append `// added` / `// removed` inside code (it pollutes real code and breaks copy/paste).
   - For summaries (non-diff), use explicit headings:
     - Removed:
     - Added:
     - Modified:


<!-- 7) POST-CODING SYNTAX CHECK (every time)

- After you finish applying ANY code changes (even small ones), you MUST perform a syntax/type check before saying the coding step is complete.
- Preferred commands (in repo root, pick the first that exists in package.json scripts):
  1) `npm run lint`   # if defined, for syntax/style
  2) `npm run check`  # or any existing type-check script
  3) if neither exists, use `npx tsc --noEmit` for TypeScript projects.
- If the command reports errors:
  - Summarize the errors.
  - Fix the relevant files.
  - Re-run the same command until it passes or you explicitly report that it cannot pass without larger changes.
- Do NOT say “coding finished”, “implementation done”, or move on to quality gate / push steps until the syntax check passes in this session, or you clearly mark that we are proceeding with known failures.
- If you cannot run commands yourself, instruct me exactly which command to run and wait for my output before continuing. -->


8) VERIFY (every time you change code)
   - After any code changes, run the first available:
     1) `npm run lint`
     2) `npm run check`
     3) `npx tsc --noEmit` (TypeScript)
   - If errors occur: summarize → fix → re-run until pass or you explicitly mark known failures.
   - Do not claim “implementation done” until this passes (or failures are explicitly accepted).

9) EXPLANATION STYLE: focus on effects, not code mechanics

- When explaining changes, DO NOT describe them as “I changed X to Y, renamed variable Z, moved this function,” or talk about syntax-level edits unless I explicitly ask.
- Instead, explain the **effects** of the changes:
  - What behavior is different for the user?
  - What bug or limitation is removed?
  - What performance, reliability, or DX impact does this have?
  - What new risks or tradeoffs did we introduce?
- Summaries should be framed in terms of:
  - Inputs / outputs that changed.
  - Error cases now handled.
  - Flows that are now possible or safer.
- Only if I ask “show the technical diff” or “what exactly changed in the code?” should you switch to a line-by-line or syntax-level explanation.