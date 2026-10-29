# Codex Prompt — Initial Task

Paste this prompt into Codex after adding these documents to the repository.

---

You are the implementation partner for a small Ubuntu-only desktop productivity app. Before changing code, read `AGENTS.md`, `README.md`, and all files under `docs/`.

## MVP
1. Persistent Area Capture: take a region screenshot and remember the last selection width/height for repeated captures. Reuse position only when valid. Allow moving/resizing where the backend supports it.
2. Image Combiner: select 2+ images, reorder, choose Vertical or Horizontal, choose alignment for mismatched dimensions, preview, and export one PNG.

## First task: investigate only
Perform Phase 0 in `docs/ROADMAP.md`. Do not build the whole app yet.

1. Inspect the repository and detect/ask for Ubuntu version, desktop environment, and display server. Do not guess.
2. Investigate backend options for the actual environment.
3. Verify whether a backend can reuse a saved selection rectangle, not merely open a generic area-selection dialog.
4. Report dependencies, limitations, exact test steps, and a recommended path.
5. Update `docs/TECHNICAL_APPROACH.md` and `docs/ROADMAP.md`.
6. If persistent selection cannot be supported cleanly, explain options and wait for approval rather than silently changing the requirement.

After Phase 0 approval, implement the image merge service and tests first because it is independent of capture.

## Preferences
- Proposed stack: Python, PySide6, Pillow, pytest.
- Keep code simple and approachable for a beginner maintainer.
- Separate UI, capture backend, image composition, and settings.
- All processing local; no telemetry, uploads, network, or AI features.
- Never silently overwrite files or modify source images.
- Preserve image order and aspect ratios.
- Give actionable errors.

## Every task
Before editing, state plan, expected files, and acceptance criteria. After editing, report changed files, commands/tests and actual results, criteria completed, remaining issues, and documentation updates. Do not add scope without asking.
