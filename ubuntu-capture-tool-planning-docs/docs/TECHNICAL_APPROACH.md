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
- The first implementation called GNOME Shell's private `SelectArea()`/`ScreenshotArea()` methods. On the declared target (Ubuntu 24.04.4, GNOME Shell 46.0, Wayland), the user confirmed that `SelectArea` returns `org.freedesktop.DBus.Error.AccessDenied`; this backend was removed.
- The current implementation uses the [XDG Desktop Portal Screenshot API](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Screenshot.html) to request a whole-screen screenshot under desktop permission. The local UI lets the user select coordinates on that returned image; platform-independent Pillow code crops the selection. The same saved image-pixel rectangle is reapplied to subsequent portal screenshots. The full-screen portal output is read and removed before the cropped result is saved.
- `grim -g` accepts an explicit region on compatible Wayland compositors; upstream examples emphasize Sway/wlroots. GNOME/Mutter compatibility is unverified.

The portal-backed flow preserves the original saved-rectangle behavior, but obtains more screen content than the final crop. The GNOME permission prompt and temporary-file cleanup must be checked on the actual Ubuntu target; the implementation remains experimental until then.

Target-session test procedure:
1. Record `lsb_release -ds`, `echo "$XDG_CURRENT_DESKTOP"`, `echo "$XDG_SESSION_TYPE"`, and `gnome-shell --version`.
2. Launch the installed app and choose **Select area**. Approve the portal prompt. Confirm the app minimizes before the desktop image is taken and that the selector displays the returned screenshot.
3. Select a known rectangle, capture it, and compare image content/dimensions with the selected area. Check that no uncropped full-screen PNG remains in `~/Pictures/Screenshots` or the selected output folder.
4. Restart the app and capture the saved rectangle again. Confirm it reuses the coordinates without opening the area picker and creates a unique PNG.
5. Test portal cancellation, local picker cancellation, changed screen dimensions, and out-of-bounds geometry; confirm no incomplete capture remains. Record exact results in the roadmap.

Backend considerations:
- X11 may allow more direct region selection integration.
- Wayland GNOME restricts direct screen access. XDG Desktop Portal mediates screenshots but returns a whole-screen image in this design; the app temporarily handles that full image before cropping locally.
- `grim` can capture a specified region on compatible Wayland compositors, but do not assume it works on GNOME.
- Investigate the user's actual session before choosing.

Keep the portal adapter, local area selector, and image crop operation separate. Mocked tests cover image logic only; they do not prove portal consent or Ubuntu compatibility.

## Merge algorithm
Vertical: canvas width = maximum input width; canvas height = sum of heights.
Horizontal: canvas width = sum of widths; canvas height = maximum input height.
Place images in the displayed order with selected alignment. Preserve aspect ratio; never stretch. Use an explicit background policy for unused canvas area. PNG is the default output.

## Persistence
Store geometry/settings in the XDG config directory, not the repo or current working directory. Validate stored values on load.

## Errors and privacy
Give actionable errors for unavailable backend, invalid images, cancelled capture, and unwritable output. No telemetry, uploads, or network calls. Never log screen contents.
