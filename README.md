# Dipapipi Skrinsyun kustom

A simple Ubuntu desktop app for capturing a selected screen area and combining images into one PNG. Everything is processed locally on your computer.

## Features

- Capture a selected area using GNOME's screenshot interface.
- Combine two or more images vertically or horizontally.
- Reorder images, align them, preview the result, and export a PNG.
- Save captures with unique names so existing screenshots are not overwritten.

## Install on Ubuntu

The area-capture feature uses GNOME's screenshot portal and currently requires a GNOME Wayland session. The capture flow has been tested on Ubuntu 24.04.4 LTS with GNOME 46 and Wayland. Image combining does not depend on the screenshot portal.

Open Terminal and install the required system packages:

```bash
sudo apt update
sudo apt install git python3 python3-venv python3-pip libgl1 libegl1 xdg-desktop-portal xdg-desktop-portal-gnome
```

Download the project, install it in an isolated Python environment, and register the app in GNOME:

```bash
git clone https://github.com/difaagfi666whoami/ubuntu-capture-tool..git ubuntu-capture-tool
cd ubuntu-capture-tool
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
python scripts/install_desktop_launcher.py
```

Open **Show Applications**, search for **Dipapipi Skrinsyun kustom**, and click its icon. You can drag the icon to the Dock to keep it there. After installation, you do not need Terminal to start the app.

## Capture a screen area

1. Open the app and select the **Area capture** tab.
2. Choose **Choose folder** if you want to change where screenshots are saved. The default is `~/Pictures` when that folder exists, otherwise your home folder.
3. Click **Select area**. GNOME opens its screenshot interface.
4. Choose **Selection** if GNOME shows a mode chooser, drag around the area, then confirm the screenshot.
5. The app saves the selected area as a uniquely named PNG in the chosen folder. To stop, cancel GNOME's screenshot interface; no capture file is created.

GNOME controls the selection overlay. On Wayland, this app cannot preselect or remember the previous selection's size or position; GNOME's normal selection interface appears for each capture.

## Combine images

1. Open the **Image combiner** tab and click **Add images**. Select at least two images. Supported formats are PNG, JPEG, BMP, GIF, TIFF, and WebP.
2. Arrange the order by dragging images in the list or selecting an image and clicking **Move up** or **Move down**. The list order is the order used in the result.
3. Choose **Vertical** to stack images top to bottom or **Horizontal** to place them left to right.
4. Choose **Start**, **Center**, or **End** alignment for images with different dimensions. Review the preview.
5. Click **Export PNG**, choose a destination, and save. If the destination already exists, the app asks before replacing it. Selected source images cannot be used as the output file.

Images keep their original dimensions and proportions. Any unused space in the combined image is filled with white.

## Update

From the project folder, run:

```bash
git pull origin main
source .venv/bin/activate
python -m pip install .
python scripts/install_desktop_launcher.py
```

Run the launcher installer again if the project folder or its virtual environment moves. It updates the GNOME app entry and icon.

## Troubleshooting

### The app does not appear in Show Applications

From the project folder, activate the virtual environment and run the launcher installer again:

```bash
source .venv/bin/activate
python -m pip install .
python scripts/install_desktop_launcher.py
```

If GNOME still does not show it, log out and back in, then search for **Dipapipi Skrinsyun kustom**.

### Area capture is unavailable

Area capture currently requires GNOME on Wayland and the XDG desktop portal packages listed above. Check the session with:

```bash
echo "$XDG_CURRENT_DESKTOP"
echo "$XDG_SESSION_TYPE"
```

The desktop should report GNOME and `wayland`. Image combining remains available if the screenshot portal is unavailable.

## Uninstall

From the project folder, remove the GNOME launcher and the local Python environment:

```bash
source .venv/bin/activate
python scripts/install_desktop_launcher.py --uninstall
deactivate
rm -rf .venv
```

You can then delete the `ubuntu-capture-tool` project folder if you no longer need it.

## Development notes

See [`ubuntu-capture-tool-planning-docs/`](ubuntu-capture-tool-planning-docs/) for the product requirements, architecture notes, roadmap, and acceptance criteria.
