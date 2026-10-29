#!/usr/bin/env python3
"""Register Dipapipi Skrinsyun kustom in the current user's application menu."""

import argparse
from pathlib import Path

from ubuntu_capture_tool.desktop_launcher import install_desktop_launcher, remove_desktop_launcher


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="remove the application-menu launcher and icon",
    )
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parent.parent
    if args.uninstall:
        desktop_file, icon_path = remove_desktop_launcher()
        print(f"Removed launcher: {desktop_file}")
        print(f"Removed app icon: {icon_path}")
        return 0

    desktop_file = install_desktop_launcher(project_root)
    print(f"Installed application launcher: {desktop_file}")
    print("Open Show Applications, search for Dipapipi Skrinsyun kustom, then pin it to the Dock if desired.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
