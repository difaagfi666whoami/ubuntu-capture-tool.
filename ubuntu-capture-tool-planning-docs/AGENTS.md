# Agent Instructions

## Goal
Build a small Ubuntu productivity app with only two MVP features: (1) reusable area capture remembering the last selection size, (2) vertical/horizontal image merge.

## Cross-platform development workflow
- macOS is a development host only; Ubuntu is the target runtime. Never infer Ubuntu behavior from macOS.
- Keep platform-independent image processing, configuration, and tests separate from platform-specific screenshot integration.
- Define a capture backend interface. Platform-specific implementations must remain isolated behind it.
- Use mocks for unit tests where appropriate, but never count mocked capture tests as proof of desktop compatibility.
- Do not implement or validate the Ubuntu screenshot backend solely on macOS.
- Document Ubuntu runtime dependencies/install steps separately from macOS development dependencies.
- Keep the project reproducible through Git, a dependency manifest, and documented setup commands.
- Run unit tests on macOS during development, then repeat relevant tests on Ubuntu.
- Manually test capture on the actual Ubuntu desktop session, including selection persistence, cancellation, output saving, and repeated capture.
- Claim Ubuntu compatibility only after its acceptance criteria pass on the declared target environment.
- Before implementing the capture backend, ask for Ubuntu version, desktop environment, and display server if they are not documented. The current declared target is Ubuntu 24.04.4 LTS, GNOME, Wayland; verify it on the target PC before integration testing.

## Guardrails
- Read README and docs before coding.
- Do not expand scope without asking. No screen recording, OCR, annotation suite, cloud, accounts, telemetry, uploads, or Windows/macOS support.
- Do not claim Wayland compatibility unless tested on a real session.
- Keep capture backend separate from UI and image merge.
- Use small understandable modules and modest dependencies.
- Never overwrite source images or output files silently.
- Keep all processing local; no network calls at runtime.
- Update tests, roadmap, and docs as work is completed.
- Do not mark a feature complete unless acceptance criteria pass.

## Required workflow
Before coding: inspect repository, propose plan/files, identify acceptance criteria.
After coding: run relevant tests, report exact results, update roadmap, list remaining issues.

## Capture feasibility spike first
Detect Ubuntu session and desktop environment. Verify whether the proposed backend can reuse a previous rectangle (x, y, width, height), not merely open a generic area-selection dialog. If not, explain trade-offs and wait for approval before changing scope.
