# Technical Approach

## Proposed stack
- Python 3
- PySide6 for desktop UI
- Pillow for image composition/export
- pytest for tests

This stack is proposed, not final. Keep dependencies modest.

## Suggested structure
- `ui/`: main window and merge/capture screens
- `capture/`: portal backend and local output handling
- `image_merge/`: image validation, composition, export
- `settings/`: local settings under XDG config directory
- `tests/`: image merge and capture workflow tests

Image merge must work independently of the screenshot backend.
The capture contract lives in `src/ubuntu_capture_tool/capture/backend.py`. The XDG portal backend asks GNOME to show its interactive screenshot UI and returns the selected PNG. The UI saves that PNG directly. This avoids calling GNOME Shell's restricted private screenshot method and avoids presenting a separate app-owned crop window.

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
- The current implementation uses the [XDG Desktop Portal Screenshot API](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Screenshot.html) in interactive mode. GNOME displays its screenshot UI; the user chooses Selection, drags the region, and confirms. The portal returns the selected image, which the app saves directly. A prior implementation used `interactive=false`, causing GNOME to return the entire screen; this was the reason the user saw a full-screen result.
- `grim -g` accepts an explicit region on compatible Wayland compositors; upstream examples emphasize Sway/wlroots. GNOME/Mutter compatibility is unverified.

The native portal selection is the simplest supported path on GNOME Wayland. It does not expose a way to prefill or retrieve the selected rectangle's screen position, so app-controlled saved-rectangle reuse is not supported by this path. The flow remains experimental until tested on the actual Ubuntu target.

Target-session test procedure:
1. Record `lsb_release -ds`, `echo "$XDG_CURRENT_DESKTOP"`, `echo "$XDG_SESSION_TYPE"`, and `gnome-shell --version`.
2. Launch the app and choose **Select area**. Confirm GNOME's screenshot UI appears.
3. Choose **Selection**, drag over a known area, and confirm. Verify the saved PNG contains only that selected area and has the expected dimensions.
4. Capture a second area. Confirm it has a unique filename.
5. Cancel GNOME's screenshot UI. Confirm no capture file was created, then record all results in the roadmap.

Backend considerations:
- X11 may allow more direct region selection integration.
- Wayland GNOME restricts direct screen access. The XDG Desktop Portal owns the native interactive screenshot and area-selection UI; use `interactive=true` so the result is the selected screenshot rather than a full-screen image.
- `grim` can capture a specified region on compatible Wayland compositors, but do not assume it works on GNOME.
- Investigate the user's actual session before choosing.

Keep the portal adapter separate from output saving. Mocked tests do not prove portal UI behavior or Ubuntu compatibility.

## Merge algorithm
Vertical: canvas width = maximum input width; canvas height = sum of heights.
Horizontal: canvas width = sum of widths; canvas height = maximum input height.
Place images in the displayed order with selected alignment. Preserve aspect ratio; never stretch. Use an explicit background policy for unused canvas area. PNG is the default output.

## Errors and privacy
Give actionable errors for unavailable backend, invalid images, cancelled capture, and unwritable output. No telemetry, uploads, or network calls. Never log screen contents.
