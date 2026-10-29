# Acceptance Criteria

Check items only after testing and recording evidence.

## Area capture
Capture code uses GNOME's interactive screenshot portal and remains experimental until the actual Ubuntu desktop checks in README.md pass. The portal owns the selection UI and does not expose saved rectangle coordinates to the app.
- [ ] AC-CAP-01: Capture can be invoked from the app.
- [ ] AC-CAP-02: Image is saved successfully.
- [ ] AC-CAP-03: Last width/height persist after restart (not implemented in the portal flow).
- [ ] AC-CAP-04: On declared supported environment, next selection uses previous dimensions without manual resizing (not supported by the current portal API flow).
- [ ] AC-CAP-05: User can move/resize rectangle where backend supports it.
- [ ] AC-CAP-06: Cancel creates no file.
- [ ] AC-CAP-07: Invalid/out-of-bounds geometry recovers safely.
- [ ] AC-CAP-08: No silent filename overwrite.
- [ ] AC-CAP-09: README documents tested session and limitations.

## Image merge
- [x] AC-MRG-01: Select 2+ images. Multi-select dialog handling is tested with two files.
- [x] AC-MRG-02: Reorder images. Reordering updates the displayed input order in a PySide6 UI test.
- [x] AC-MRG-03: Vertical output stacks top-to-bottom in displayed order. Unit-tested on macOS; see roadmap evidence.
- [x] AC-MRG-04: Horizontal output places left-to-right in displayed order. Unit-tested on macOS; see roadmap evidence.
- [x] AC-MRG-05: Different dimensions align as selected. Start/center/end unit-tested on macOS; see roadmap evidence.
- [x] AC-MRG-06: No stretching/distortion. Composition uses original pixel dimensions; output geometry unit-tested on macOS.
- [x] AC-MRG-07: PNG is default output. Export helper writes PNG and output format is unit-tested on macOS.
- [x] AC-MRG-08: No silent overwrite. UI confirmation and existing-file preservation are covered by a PySide6 test; export helper rejects existing files by default.
- [x] AC-MRG-09: Invalid input gives a useful error. A PySide6 test confirms actionable preview feedback for an invalid image.
- [x] AC-MRG-10: Source files remain unchanged. Source-byte preservation is unit-tested on macOS.

## Quality/release
- [ ] AC-QA-06: User can launch the app from GNOME's application grid without opening a terminal (manual Ubuntu check pending).
- [x] AC-QA-01: Tests cover order, dimensions, alignment, and invalid input.
- [ ] AC-QA-02: Documented launch works on test Ubuntu setup.
- [x] AC-QA-03: No network/telemetry. Current implementation has no network or telemetry code paths.
- [x] AC-QA-04: README covers install, usage, limitations, uninstall.
- [x] AC-QA-05: Completed criteria have test evidence in roadmap.
