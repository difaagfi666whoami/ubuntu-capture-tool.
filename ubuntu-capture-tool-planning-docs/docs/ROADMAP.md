# Roadmap and Progress Tracker

Statuses: TODO / IN PROGRESS / BLOCKED / DONE

## Phase 0 — Environment and feasibility
- [x] P0.1 Record available environment details (see evidence below; target details are from the README, not live-verified).
- [ ] P0.2 Test the GNOME screenshot backend on the actual Ubuntu session. PENDING: the Ubuntu test reported so far covered the image combiner, not screenshot integration.
- [ ] P0.3 Verify saved selection dimensions can be reused on the actual session. PENDING target capture test.
- [x] P0.4 Record findings and the provisional decision: implement the user-approved GNOME candidate, but do not claim support until P0.2/P0.3 pass.

### Phase 0 evidence (2026-10-29)
- Project README records target as Ubuntu 24.04.4 LTS, GNOME, Wayland. This is project-provided information, not a fresh measurement.
- Live workspace host: macOS 26.6.2 (Darwin arm64); `XDG_SESSION_TYPE`, `XDG_CURRENT_DESKTOP`, `DISPLAY`, and `WAYLAND_DISPLAY` are unset.
- `gnome-screenshot`, `gdbus`, `busctl`, `grim`, `slurp`, `xdg-desktop-portal`, and `xdg-desktop-portal-gnome` are unavailable on this host. No target-session capture was run.
- Candidate: GNOME Shell's D-Bus `org.gnome.Shell.Screenshot.ScreenshotArea(x, y, width, height, ...)` accepts explicit rectangle coordinates according to its interface definition. If present and callable on the target GNOME version, it could reuse persisted dimensions without a generic area picker. This interface is GNOME-specific and still needs real-session validation.
- XDG Desktop Portal's Screenshot interface offers an interactive user-selected Area target, but its documented request options do not include rectangle coordinates. It therefore does not establish saved-rectangle reuse.
- `grim -g` supports explicit geometry on compatible Wayland compositors, but its upstream examples focus on wlroots/Sway; it is not evidence that it works on GNOME/Mutter.
- Next test on the actual Ubuntu session: run `gnome-shell --version`; inspect `org.gnome.Shell.Screenshot` with `gdbus introspect --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Screenshot`; if the method is present, call it with a small known rectangle and a unique temporary path, for example `gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Screenshot --method org.gnome.Shell.Screenshot.ScreenshotArea 0 0 320 240 false /tmp/uct-phase0-a.png`. Check the result and `file /tmp/uct-phase0-a.png`; repeat with different dimensions and another unique path. Verify bounds/error behavior and any cancellation/naming handling before selecting this backend.
- Decision: the user approved an experimental GNOME candidate implementation after the image combiner passed on Ubuntu. Actual screenshot support and saved-rectangle reuse remain unverified on the target.

Exit condition: user approval allows the experimental candidate UI; target compatibility remains gated on P0.2/P0.3.

## Phase 1 — Foundation
- [x] P1.1 Create project structure and dependency manifest.
- [x] P1.2 Create minimal PySide6 window.
- [x] P1.3 Add pytest setup.
- [x] P1.4 Document basic run instructions for macOS development and Ubuntu target.

## Phase 2 — Image merge
- [x] P2.1 Implement Pillow composition service and unit tests.
- [x] P2.2 Test vertical/horizontal layouts, order, alignment, errors, export safety, and source preservation on macOS.
- [x] P2.3 Add ordered file list with drag/drop and move controls.
- [x] P2.4 Add orientation and alignment controls.
- [x] P2.5 Add preview and PNG export.
- [x] P2.6 Verify AC-MRG criteria. Automated criteria pass, and the user reports that the image combiner ran successfully on Ubuntu. The new capture tab still needs target testing.

## Phase 3 — Persistent area capture
- [x] P3.1 Define platform-neutral capture backend interface contract.
- [x] P3.2 Implement experimental GNOME Shell candidate behind the interface; target validation remains pending.
- [x] P3.3 Implement XDG geometry persistence and load it in the capture UI.
- [x] P3.4 Handle area-selection cancellation, invalid geometry errors, unique naming, and safe local output.
- [ ] P3.5 Manually test on target session.
- [ ] P3.6 Verify AC-CAP criteria.

## Phase 4 — Release
- [x] P4.1 Add package launcher entry point.
- [ ] P4.2 Test install/uninstall instructions.
- [ ] P4.3 Add real app screenshots.
- [x] P4.4 Document limitations.
- [ ] P4.5 Tag initial release after acceptance criteria pass.

## Change log
- 2026-10-29: Planning docs created; implementation has not started.
- 2026-10-29: Phase 0 documentation/investigation completed on the available host; target-session execution remains blocked pending access to Ubuntu 24.04.4 GNOME Wayland.
- 2026-10-29: Added Python package, local image combiner, capture interface contract, validated XDG geometry store, setup instructions, and unit tests. macOS test suite: 19 passed; PySide6 window and entry point smoke checks passed; editable package dry-run passed. Ubuntu runtime and desktop integration have not been tested.
- 2026-10-29: Added experimental GNOME Shell area capture tab/backend, cancellation and output handling, plus mocked backend/UI tests. User reports that the image combiner works on the Ubuntu PC; capture integration is not yet tested there.

## Implementation validation evidence
- `PYTHONPATH=src python3 -m pytest -q`: 29 passed on macOS 26.6.2, Python 3.13.14, Pillow 12.3.0, PySide6 6.11.1.
- `python3 -m compileall -q src tests`: passed.
- Offscreen PySide6 `MainWindow()` startup smoke check: passed; this checks widget construction only, not screenshot support or Ubuntu compatibility.
- PySide6 UI tests cover multi-file selection handling, reordering, preview updates, useful invalid-input feedback, PNG export, explicit overwrite confirmation, and source-file protection.
- Merge unit tests cover vertical/horizontal order and dimensions, start/center/end alignment, invalid input, PNG output, overwrite refusal, atomic output replacement, and source-file preservation.
- Geometry-store tests cover XDG config path selection, round-trip persistence, and safe handling of corrupt or invalid saved values. Negative x/y coordinates remain valid for multi-monitor layouts; screen bounds are backend-specific and still need target validation.
- Mocked capture tests cover GNOME D-Bus argument/result handling, cancellation, saved geometry across panel recreation, local PNG output, and safe errors. These tests do not demonstrate real GNOME compatibility.
- Remaining: install this updated commit on Ubuntu; verify environment and GNOME Shell version; manually test selector, cancel, capture output, geometry persistence after restart, repeated capture with unique filenames, and invalid/out-of-bounds recovery. Then record actual results and revisit capture acceptance criteria.

## Decisions
- D-001: MVP limited to persistent area capture and vertical/horizontal image merge.
- D-002: Python + PySide6 + Pillow proposed, pending feasibility spike.
- D-003: Wayland compatibility must be demonstrated, not assumed.
