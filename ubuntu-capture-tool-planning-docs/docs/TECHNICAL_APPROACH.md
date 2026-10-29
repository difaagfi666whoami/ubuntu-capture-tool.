# Technical Approach

## Proposed stack
- Python 3
- PySide6 for desktop UI
- Pillow for image composition/export
- pytest for tests

This stack is proposed, not final. Keep dependencies modest.

## Suggested structure
- `ui/`: main window and merge/capture screens
- `capture/`: backend interface, environment detection, geometry persistence
- `image_merge/`: image validation, composition, export
- `settings/`: local settings under XDG config directory
- `tests/`: merge and settings/geometry tests

Image merge must work independently of the screenshot backend.
The platform-neutral capture contract lives in `src/ubuntu_capture_tool/capture/backend.py`. It selects a rectangle and captures it as PNG bytes. The experimental GNOME Shell implementation is isolated in `src/ubuntu_capture_tool/capture/gnome_shell.py`; the UI is in `src/ubuntu_capture_tool/capture/ui.py`. `src/ubuntu_capture_tool/settings/geometry_store.py` atomically stores validated geometry under the XDG config directory. The implementation is ready for target testing, but is not declared Ubuntu-compatible until the actual session checks pass.

## Cross-platform development and validation
macOS is a development host; Ubuntu is the target runtime. Do not use macOS behavior as evidence for Ubuntu support.

- Keep image processing, configuration logic, and most tests OS-independent.
- Put platform-specific screenshot integrations behind the capture backend interface.
- Mocks may test the application's handling of backend results and errors. They do not establish real desktop compatibility.
- Use a dependency manifest and documented setup commands. Document macOS development dependencies separately from Ubuntu runtime dependencies.
- Run unit tests on macOS while developing and repeat relevant tests on Ubuntu. Manually test the actual Ubuntu desktop session for selection persistence, cancellation, output saving, and repeated capture.
- Claim Ubuntu compatibility only after the related acceptance criteria pass on the declared target.

The declared target is Ubuntu 24.04.4 LTS, GNOME, Wayland, based on the project README. Verify the version, desktop environment, and display server on the Ubuntu PC before integration testing. If target details are not documented before capture-backend implementation, ask the user.

## Phase 0: capture feasibility spike
Run:
```bash
echo "$XDG_SESSION_TYPE"
echo "$XDG_CURRENT_DESKTOP"
```

### Phase 0 findings (2026-10-29; target testing still pending)
The project README records the intended test target as Ubuntu 24.04.4 LTS, GNOME, Wayland. The available development host was macOS 26.6.2 (Darwin arm64), with no XDG/Wayland session variables and no Linux screenshot utilities installed. These facts mean the target backend could not be exercised in this run.

Backend notes from upstream interface documentation:
- The XDG Desktop Portal Screenshot interface can request an Area target, but the documented options contain no rectangle coordinates. It is a user-driven selection and does not by itself meet saved-dimension reuse.
- GNOME Shell's `org.gnome.Shell.Screenshot.ScreenshotArea(x, y, width, height, ...)` accepts explicit geometry. This is the strongest candidate for GNOME Wayland, subject to verifying that the interface exists, is callable, and captures the intended pixels on Ubuntu 24.04.4. It is GNOME-specific and must not be treated as a stable cross-desktop API without further evidence.
- GNOME Shell's screenshot interface also declares `SelectArea()`, which returns the chosen rectangle. The implementation calls this selector on first use or when the user chooses Select area, then calls `ScreenshotArea` for repeat captures using the saved rectangle. The upstream interface is documented at [GNOME Shell Screenshot D-Bus XML](https://github.com/GNOME/gnome-shell/blob/main/data/dbus-interfaces/org.gnome.Shell.Screenshot.xml). This is a private GNOME API and may differ by Shell release; the Ubuntu target test is required.
- `grim -g` accepts an explicit region on compatible Wayland compositors; upstream examples emphasize Sway/wlroots. GNOME/Mutter compatibility is unverified.

The user approved implementing the GNOME candidate for target testing. It remains experimental: if its D-Bus methods are unavailable or unreliable, do not claim support; report the result and revisit the backend choice.

Target-session test procedure:
1. Record `lsb_release -ds`, `echo "$XDG_CURRENT_DESKTOP"`, `echo "$XDG_SESSION_TYPE"`, and `gnome-shell --version`.
2. Inspect the session-bus interface with `gdbus introspect --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Screenshot` and confirm the `ScreenshotArea` signature.
3. Call `gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell/Screenshot --method org.gnome.Shell.Screenshot.ScreenshotArea 0 0 320 240 false /tmp/uct-phase0-a.png`; inspect the method result and `file /tmp/uct-phase0-a.png` for the expected pixel dimensions.
4. Call again with a different stored width/height and another unique path; confirm the second output dimensions match without opening a selection dialog.
5. Test negative/out-of-bounds coordinates, cancellation behavior (if applicable), and output naming/overwrite handling. Record exact commands and observed results in the roadmap.

Backend considerations:
- X11 may allow more direct region selection integration.
- Wayland GNOME has stronger restrictions. XDG Desktop Portal can request area screenshots, but its selection UI may not accept a saved custom rectangle.
- `grim` can capture a specified region on compatible Wayland compositors, but do not assume it works on GNOME.
- Investigate the user's actual session before choosing.

Keep the real GNOME selector and screenshot calls separate behind the capture interface; do not substitute a fake flow. If the target session cannot honor saved geometry cleanly, report the limitation before claiming support.

## Merge algorithm
Vertical: canvas width = maximum input width; canvas height = sum of heights.
Horizontal: canvas width = sum of widths; canvas height = maximum input height.
Place images in the displayed order with selected alignment. Preserve aspect ratio; never stretch. Use an explicit background policy for unused canvas area. PNG is the default output.

## Persistence
Store geometry/settings in the XDG config directory, not the repo or current working directory. Validate stored values on load.

## Errors and privacy
Give actionable errors for unavailable backend, invalid images, cancelled capture, and unwritable output. No telemetry, uploads, or network calls. Never log screen contents.
