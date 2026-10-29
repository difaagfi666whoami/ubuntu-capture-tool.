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

The current application includes local vertical/horizontal image composition, ordered image selection, alignment, preview, and PNG export. Area capture asks GNOME's XDG screenshot portal to open its interactive screenshot UI; the selected screenshot returned by GNOME is saved directly. The portal path still needs manual validation on the Ubuntu target; mocked tests do not prove desktop compatibility.

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
sudo apt install python3 python3-venv python3-pip libgl1 libegl1 xdg-desktop-portal xdg-desktop-portal-gnome
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
python scripts/install_desktop_launcher.py
ubuntu-capture-tool
```

The one-time launcher installer adds **Ubuntu Capture Tool** to **Show Applications** with its app icon. Open it there and pin it to the Dock to launch it with one click. Re-run `python scripts/install_desktop_launcher.py` if the project folder or virtual environment moves.

These are setup instructions for the Ubuntu target. On GNOME Wayland the app requests an interactive screenshot from the XDG screenshot portal. GNOME displays its screenshot UI; the user chooses a selection, drags over the desired area, and confirms. The portal returns the selected screenshot, which the app saves to the chosen capture folder. This interactive flow must be checked on the target PC.

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

### Launch from the application grid

The one-time launcher installer adds **Ubuntu Capture Tool** to GNOME's **Show Applications** grid. Search for the app and open it; drag its icon to the Dock to keep it there. You can then start the program without opening Terminal.

## Using the image combiner

1. Launch `ubuntu-capture-tool`.
2. Choose **Add images** and select at least two files. Supported formats are PNG, JPEG, BMP, GIF, TIFF, and WebP.
3. Reorder the list by dragging items or using **Move up** and **Move down**. The displayed order determines the merged order.
4. Choose **Vertical** or **Horizontal**, then choose Start, Center, or End alignment for images with different sizes.
5. Review the preview and choose **Export PNG**. Existing files require confirmation before replacement. Selected source files cannot be used as the output path.

The composition canvas fills unused space with white. Images keep their original pixel dimensions and are not stretched.

## Using area capture (experimental)

Area capture uses GNOME's interactive XDG Screenshot Portal instead of GNOME Shell's restricted private screenshot D-Bus methods. It does not take a silent full-screen screenshot and then ask you to crop it in the app.

1. Open **Area capture** and choose **Select area**.
2. In GNOME's screenshot UI, choose **Selection** (if a mode chooser appears), drag over the area, then confirm the screenshot.
3. The selected-area PNG is saved with a unique filename in `~/Pictures` (or the home folder if Pictures does not exist). Choose another folder with **Choose folder**.
4. Cancel GNOME's screenshot UI to return without creating a file.

GNOME controls the selection overlay. The portal does not let this app set the overlay's initial rectangle size or position, so every capture uses GNOME's normal interactive selection. The older private GNOME `SelectArea` method returned `AccessDenied` on Ubuntu 24.04.4 / GNOME 46 / Wayland. Do not claim compatibility until the interactive portal flow and saved output are checked on that target.

### Ubuntu desktop validation still required

The project maintainer must verify on the actual Ubuntu PC:

- Record `lsb_release -ds`, `gnome-shell --version`, `echo "$XDG_CURRENT_DESKTOP"`, and `echo "$XDG_SESSION_TYPE"`.
- Launch **Select area**; confirm GNOME's interactive screenshot UI appears. Choose **Selection**, drag over a known small region, and confirm.
- Open the saved PNG; confirm it contains only the selected region and has the expected dimensions.
- Capture another area and confirm the output uses a different filename.
- Cancel GNOME's screenshot UI and confirm no new capture file appears.

GNOME restricts access to its private Shell screenshot interface. The app now uses the [XDG Desktop Portal Screenshot API](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Screenshot.html) in interactive mode and saves the selected image returned by GNOME. Do not claim compatibility until selection, cancellation, and output checks pass on Ubuntu 24.04.4 GNOME Wayland.

## Uninstall

Remove the launcher first while the project environment is still installed, then remove the virtual environment:

```bash
source .venv/bin/activate
python scripts/install_desktop_launcher.py --uninstall
deactivate
rm -rf .venv
```

If the package was installed into a shared Python environment instead, uninstall it there with `python -m pip uninstall ubuntu-capture-tool`.

## Scope and limitations

- The merge tool reads source images and writes a new PNG; it does not modify source files.
- Existing export files are never replaced without an explicit confirmation.
- Screen capture code is present, but remains experimental until manual checks pass on Ubuntu GNOME Wayland. Do not treat the macOS development host, mocks, or this documentation as Ubuntu desktop compatibility evidence.
