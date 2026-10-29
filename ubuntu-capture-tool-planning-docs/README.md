# Ubuntu Capture Tool

A small Ubuntu-focused productivity utility for repetitive screenshots and quick image composition.

## MVP
1. Area capture that remembers the last selection size and, where supported, position.
2. Combine 2+ images vertically or horizontally into one image.

## Important
Screenshot selection behavior depends on Ubuntu's desktop environment and display server. On Wayland, the desktop portal may own the selection UI and may not let an app prefill a saved rectangle. Verify this before claiming the capture feature works.

## Documents
- `docs/PRD.md`: requirements and scope
- `docs/TECHNICAL_APPROACH.md`: architecture and feasibility spike
- `docs/ACCEPTANCE_CRITERIA.md`: definition of done
- `docs/ROADMAP.md`: progress tracking
- `docs/CODEX_PROMPT.md`: prompt for Codex
- `AGENTS.md`: coding guardrails

Check environment with:
```bash
echo "$XDG_SESSION_TYPE"
echo "$XDG_CURRENT_DESKTOP"
```
result :
ubuntu session : wayland
lsb : ubuntu 24.04.4 LTS
ubuntu : GNOME

## Development and target environments

Development may happen on macOS, but Ubuntu is the runtime and integration-test target. macOS results do not establish Ubuntu desktop compatibility.

- Keep OS-independent image processing, configuration, and unit tests separate from the screenshot backend.
- Isolate screenshot integration behind a capture backend interface. Mocks can cover interface behavior in unit tests, but they do not prove screenshot support on GNOME Wayland.
- Maintain separate setup instructions for macOS development dependencies and Ubuntu runtime dependencies when implementation begins. Track dependencies in a manifest and setup commands in this README.
- Run unit tests on macOS during development and repeat relevant tests on Ubuntu. Perform manual capture tests on the actual target session for persistence, cancellation, output saving, and repeated capture.
- Declare Ubuntu compatibility only after the relevant acceptance criteria pass on the target.

The currently declared target is Ubuntu 24.04.4 LTS, GNOME, Wayland (from the project setup notes). Verify these details on the Ubuntu PC before integration testing. If the target details are unavailable before capture-backend implementation, ask the user rather than assuming.

## Current implementation

The current application includes local vertical/horizontal image composition, ordered image selection, alignment, preview, and PNG export. It also includes an experimental GNOME Shell area-capture backend, area selector controls, and persisted rectangle settings. The screenshot backend has not yet been validated on the declared Ubuntu PC; do not treat mocked tests as proof of desktop compatibility.

## Setup and run

### macOS development

Install Python 3.10 or newer, then from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
ubuntu-capture-tool
```

To update an existing clone when a new commit is published:

```bash
git pull origin main
source .venv/bin/activate
python -m pip install .
```

Run unit tests with:

```bash
pytest
```

### Ubuntu target runtime

Install Ubuntu's Python and Qt runtime libraries:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip libgl1 libegl1 libglib2.0-bin
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
ubuntu-capture-tool
```

These are setup instructions for the Ubuntu target. The experimental capture backend uses GNOME Shell's session-bus screenshot interface through `gdbus`; it requires a GNOME Wayland session and the `gdbus` command. Target compatibility remains unverified until the manual checks below pass.

### Ubuntu test run

To repeat the development test suite on the Ubuntu PC, use a virtual environment and install the optional test dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest
ubuntu-capture-tool
```

Record the Ubuntu version, GNOME Shell version, display server, test output, and manual UI results in the roadmap. A successful unit test run does not establish screenshot compatibility.

## Using the image combiner

1. Launch `ubuntu-capture-tool`.
2. Choose **Add images** and select at least two files. Supported formats are PNG, JPEG, BMP, GIF, TIFF, and WebP.
3. Reorder the list by dragging items or using **Move up** and **Move down**. The displayed order determines the merged order.
4. Choose **Vertical** or **Horizontal**, then choose Start, Center, or End alignment for images with different sizes.
5. Review the preview and choose **Export PNG**. Existing files require confirmation before replacement. Selected source files cannot be used as the output path.

The composition canvas fills unused space with white. Images keep their original pixel dimensions and are not stretched.

## Using area capture (experimental)

Area capture is intended for the declared Ubuntu GNOME Wayland target and is not available on macOS or other desktop sessions.

1. Open the **Area capture** tab and choose **Select area**. GNOME Shell opens its native area selector.
2. The selected coordinates and dimensions are saved in `~/.config/ubuntu-capture-tool/capture-geometry.json`. You can edit the X, Y, Width, and Height fields before capturing.
3. Choose **Capture saved area** to capture that exact rectangle. Repeat captures reuse the saved geometry without opening the selector.
4. Captures are written as uniquely named PNG files in `~/Pictures` (or the home folder if Pictures does not exist). Choose another folder with **Choose folder**.
5. Cancel the native area selector to return without creating a screenshot. If capture fails, the app displays the GNOME error and creates no output file.

### Ubuntu desktop validation still required

The project maintainer must verify on the actual Ubuntu PC:

- Record `lsb_release -ds`, `gnome-shell --version`, `echo "$XDG_CURRENT_DESKTOP"`, and `echo "$XDG_SESSION_TYPE"`.
- Select and capture a known small area; confirm the image opens and has the expected content and dimensions.
- Restart the app; confirm the prior coordinates and dimensions are restored.
- Capture the same saved rectangle twice; confirm both outputs are valid and have different filenames.
- Cancel the area selector and confirm no screenshot file appears.
- Try an invalid or out-of-bounds rectangle; confirm an actionable error appears and no partial output is left.

The GNOME Shell D-Bus interface documents both interactive `SelectArea` and explicit-rectangle `ScreenshotArea(x, y, width, height, ...)`. The backend is still experimental until these calls pass on the target session. See the [GNOME Shell screenshot interface](https://github.com/GNOME/gnome-shell/blob/main/data/dbus-interfaces/org.gnome.Shell.Screenshot.xml).

## Uninstall

Remove the virtual environment created in the repository:

```bash
deactivate
rm -rf .venv
```

If the package was installed into a shared Python environment instead, uninstall it there with `python -m pip uninstall ubuntu-capture-tool`.

## Scope and limitations

- The merge tool reads source images and writes a new PNG; it does not modify source files.
- Existing export files are never replaced without an explicit confirmation.
- Screen capture code is present, but remains experimental until manual checks pass on Ubuntu GNOME Wayland. Do not treat the macOS development host, mocks, or this documentation as Ubuntu desktop compatibility evidence.
