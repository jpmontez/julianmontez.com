# AGENTS.md

This repository is designed to be used by both human developers and AI agents (via the codex CLI or similar tools). This document explains how agents should orient themselves, what to read first, and how to update shared artifacts.

The goal: **avoid context loss, duplicated work, and conflicting changes** across multiple sessions and agents.

---

## 1. Files Every Agent Should Know

When you start a new session as an AI agent, assume you have *no* prior chat history. Your context comes from the repository itself.

Read or skim these files in this order:

1. `README.md`
   - High-level project overview (purpose, scope, architecture).
   - How to set up and run the project.
   - Key technologies and versions.
   - Important user-facing decisions.

2. `HANDOFF.md`
   - Tactical, time-sensitive context.
   - Current status, recent work, open challenges.
   - Next steps, environment details, data/artifact paths.
   - Gotchas and conventions.

3. `TODO.md`
   - A task-focused list of concrete items.
   - Use this to understand the current short- to mid-term work queue.
   - Keep it synchronized with reality as you complete or discover tasks.

If any of these files are missing or obviously stale, you should prioritize creating or updating them.

---

## 2. Agent Roles and Behaviors

Different prompts or invocations may put you into different roles. Regardless of role, **you must respect the shared docs** above.

### 2.1 Generalist / Navigator

When acting as a generalist:

- Map the project:
  - Identify main modules, entrypoints, and data flows.
  - Note findings in `HANDOFF.md` (in the appropriate sections).
- Cross-check `README.md`, `HANDOFF.md`, and `TODO.md`:
  - Flag inconsistencies.
  - Recommend minimal edits to keep them aligned.
- Suggest prioritized next actions and, when asked, update `TODO.md` accordingly.

### 2.2 Implementer / Coder

When implementing features, fixing bugs, or refactoring:

- Before coding:
  - Review `HANDOFF.md` and `TODO.md` to avoid duplicating work.
  - Confirm that the task you’re working on is either:
    - Already listed in `TODO.md`, or
    - Added by you to `TODO.md` (with a short description and reference to related files).
- While coding:
  - Follow existing patterns, conventions, and styles you infer from the code and docs.
  - Keep the existing architecture and contracts unless explicitly asked to change them.
  - Prefer the Makefile targets for common workflows (install/build/preview/import/lint) instead of ad-hoc commands when possible.
- After coding:
  - Update `TODO.md`:
    - Mark items as done or partially complete with a short note.
  - Update `HANDOFF.md`:
    - Summarize what you did, where, and why.
    - Mention any new TODO items or open questions.
  - Only update `README.md` if you have made changes that affect how users or contributors interact with the project (setup, commands, endpoints, etc.).

### 2.3 Reviewer / Auditor

When reviewing code or docs:

- Compare changes against:
  - `README.md` for architectural and user-facing consistency.
  - `HANDOFF.md` for current status, assumptions, and plans.
  - `TODO.md` for task tracking correctness.
- Document findings in `HANDOFF.md` under:
  - “Open Challenges & Risks” for risks.
  - “Next Steps” for recommended follow-ups.
- Update `TODO.md` with concrete action items if new work is needed.

### 2.4 Planner / Architect

When acting as a planner or architect:

- Use `README.md` to understand the intended long-term shape of the project.
- Use `HANDOFF.md` to understand current reality and constraints.
- Use `TODO.md` as an input for building or reshaping the roadmap.
- When you adjust direction:
  - Update `HANDOFF.md`:
    - Describe new decisions and rationale.
    - List re-prioritized steps in “Next Steps.”
  - Add or refine items in `TODO.md`.
  - Only update `README.md` when decisions change the public-facing description, architecture, or setup.

---

## 3. Update Rules and Conventions

To keep the repository coherent across multiple agents:

1. **Single source of truth per concern**
   - `README.md`: stable, high-level overview.
   - `HANDOFF.md`: transient, tactical continuity document.
   - `TODO.md`: task list and work queue.
   Avoid duplicating the same detailed information in multiple places.

2. **No speculative changes**
   - Do not invent tools, services, or version numbers.
   - Derive environment details and stack information from:
     - Code, config files, lockfiles, and scripts.
     - Existing content in `README.md` and `HANDOFF.md`.
   - If something is unclear, note it explicitly (e.g., “Version not specified; verify before assuming X”).

3. **Be explicit and file-specific**
   - When describing changes, always reference actual file paths and, when helpful, key functions, classes, or modules.
   - Example: “Updated `api/users.py` to validate email formats” rather than “Updated user API.”

4. **Keep docs in sync with code**
   - If a change affects how the project is run, configured, or extended:
     - Update `README.md`.
   - If a change affects ongoing work, open questions, or next steps:
     - Update `HANDOFF.md`.
   - If a change adds, removes, or completes tasks:
     - Update `TODO.md`.

5. **Be honest about uncertainty**
   - If you cannot fully determine a detail from the repo, mark it as uncertain rather than guessing.
   - Example: “Not sure whether X is still used; verify before deleting.”

---

## 4. Getting Started Checklist for a New Agent

When you first attach to this repo:

1. Read `README.md` to understand the project.
2. Read `HANDOFF.md` to understand current status and context.
3. Read `TODO.md` to see the current task queue.
4. Confirm the local environment and commands (from the docs and config files).
5. Ask (or infer) which role you are in (generalist, implementer, reviewer, planner).
6. Proceed with the smallest, highest-impact, well-defined task; then:
   - Update `HANDOFF.md` with what you did and what’s next.
   - Update `TODO.md` to reflect completed or new tasks.
   - Update `README.md` only if necessary for public-facing accuracy.

Following this process ensures that future agents—human or AI—can pick up the project quickly and safely without access to prior conversation history.
