# Roadmap and Progress Tracker

Statuses: TODO / IN PROGRESS / BLOCKED / DONE

## Phase 0 — Environment and feasibility
- [x] P0.1 Record available environment details (target confirmed by user on 2026-10-29).
- [ ] P0.2 Test the XDG Desktop Portal backend on the actual Ubuntu session. The earlier GNOME Shell D-Bus backend was rejected with `AccessDenied` (user report, 2026-10-29).
- [ ] P0.3 Verify GNOME's interactive area selection returns an area-only PNG on the actual session.
- [x] P0.4 Record findings and the provisional decision: implement the user-approved GNOME candidate, but do not claim support until P0.2/P0.3 pass.

### Phase 0 evidence (2026-10-29)
- User-confirmed target: Ubuntu 24.04.4 LTS, GNOME Shell 46.0, `XDG_CURRENT_DESKTOP=ubuntu:GNOME`, `XDG_SESSION_TYPE=wayland` (2026-10-29). `lsb_release` printed a harmless “No LSB modules are available” notice before the release string.
- Live workspace host: macOS 26.6.2 (Darwin arm64); `XDG_SESSION_TYPE`, `XDG_CURRENT_DESKTOP`, `DISPLAY`, and `WAYLAND_DISPLAY` are unset.
- `gnome-screenshot`, `gdbus`, `busctl`, `grim`, `slurp`, `xdg-desktop-portal`, and `xdg-desktop-portal-gnome` are unavailable on this host. No target-session capture was run.
- Candidate: GNOME Shell's D-Bus `org.gnome.Shell.Screenshot.ScreenshotArea(x, y, width, height, ...)` accepts explicit rectangle coordinates according to its interface definition. If present and callable on the target GNOME version, it could reuse persisted dimensions without a generic area picker. This interface is GNOME-specific and still needs real-session validation.
- XDG Desktop Portal's Screenshot interface offers an interactive user-selected Area target, but its documented request options do not include rectangle coordinates. It therefore does not establish saved-rectangle reuse.
- `grim -g` supports explicit geometry on compatible Wayland compositors, but its upstream examples focus on wlroots/Sway; it is not evidence that it works on GNOME/Mutter.
- Next test on the actual Ubuntu session: run `gnome-shell --version`; inspect `org.gnome.Shell.Screenshot` with `gdbus introspect --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Screenshot`; if the method is present, call it with a small known rectangle and a unique temporary path, for example `gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Screenshot --method org.gnome.Shell.Screenshot.ScreenshotArea 0 0 320 240 false /tmp/uct-phase0-a.png`. Check the result and `file /tmp/uct-phase0-a.png`; repeat with different dimensions and another unique path. Verify bounds/error behavior and any cancellation/naming handling before selecting this backend.
- Decision: the user approved an experimental GNOME candidate implementation after the image combiner passed on Ubuntu. Target testing reports `SelectArea` is denied on Ubuntu 24.04.4 / GNOME Shell 46.0 / Wayland, so this backend is unusable on the declared target.

### Target feedback (2026-10-29)
- The user tested the installed app on their Ubuntu PC. Clicking **Select area** returned `GDBus.Error:org.freedesktop.DBus.Error.AccessDenied: SelectArea is not allowed`.
- The user confirmed the target session details: Ubuntu 24.04.4 LTS, GNOME Shell 46.0, Ubuntu GNOME, Wayland.
- Do not count the capture backend as working or compatible. The documented XDG Desktop Portal Screenshot API supports a user-selected Area target but does not expose rectangle coordinates for saved-region reuse.
- The first portal replacement used `interactive=false`, which returns the entire screen and led to confusing behavior. The revised flow uses GNOME's interactive screenshot UI and saves the selected image returned by GNOME directly.
- The app no longer shows a separate local picker or geometry editor. GNOME's UI owns area selection. The portal does not let this app prefill or reuse the exact selection rectangle.
- Target verification remains required for GNOME's selection overlay, area-only output, cancellation, and repeated output naming. Keep capture acceptance criteria open until these checks pass.

Exit condition: target compatibility remains gated on P0.2/P0.3.

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
- [x] P3.2 Implement interactive XDG Desktop Portal capture and save its returned image; target validation remains pending.
- [ ] P3.3 Reuse a saved rectangle size. The portal flow does not expose a prefilled selection rectangle.
- [x] P3.4 Handle portal cancellation, unique naming, and safe local output.
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
- 2026-10-29: User confirmed Ubuntu 24.04.4 LTS, GNOME Shell 46.0, Wayland. The private GNOME Shell `SelectArea` D-Bus method returned `AccessDenied`. Replaced that candidate with XDG Portal full-screen capture plus a local selector/crop flow to preserve saved rectangle reuse; Ubuntu portal integration testing is still pending.
- 2026-10-29: User reported that the portal replacement showed no area selection and produced a full-screen image. The cause was `interactive=false`. Switched to GNOME's interactive screenshot UI, removed the separate local picker and geometry controls, and saves the selected image returned by the portal directly. Ubuntu retest is pending.

## Implementation validation evidence
- Earlier unit-test runs are historical evidence only; see the latest run below after the interactive portal change.
- `python3 -m compileall -q src tests`: passed.
- Offscreen PySide6 `MainWindow()` startup smoke check: passed; this checks widget construction only, not screenshot support or Ubuntu compatibility.
- PySide6 UI tests cover multi-file selection handling, reordering, preview updates, useful invalid-input feedback, PNG export, explicit overwrite confirmation, and source-file protection.
- Merge unit tests cover vertical/horizontal order and dimensions, start/center/end alignment, invalid input, PNG output, overwrite refusal, atomic output replacement, and source-file preservation.
- UI tests cover direct saving of the image returned by the portal, cancellation, and safe errors. Portal tests assert that the request is interactive and verify temporary-file cleanup. They do not demonstrate real GNOME compatibility.
- Latest unit-test result: `python3 -m pytest -q`: 20 passed after simplifying area capture to GNOME's interactive screenshot UI.
- Remaining: install the interactive portal update on Ubuntu; confirm GNOME's selection UI appears, returns area-only output, supports cancellation, and saves unique files. Then record actual results and revisit capture acceptance criteria.

## Decisions
- D-001: MVP limited to persistent area capture and vertical/horizontal image merge.
- D-002: Python + PySide6 + Pillow proposed, pending feasibility spike.
- D-003: Wayland compatibility must be demonstrated, not assumed.
