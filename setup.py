"""
py2app build script.

Usage:
    python setup.py py2app
Produces dist/VitalsForMac.app — a double-clickable, menu-bar-only app
(no Dock icon, via LSUIElement).
"""

from setuptools import setup

APP = ["vitals_menubar.py"]
DATA_FILES = ["README.md"]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "AppIcon.icns",
    "plist": {
        "LSUIElement": True,
        "CFBundleName": "VitalsForMac",
        "CFBundleIdentifier": "com.hsaeedx.VitalsForMac",
        "CFBundleShortVersionString": "1.0.0",
    },
    "packages": ["rumps", "requests", "bs4"],
}

setup(
    app=APP,
    name="VitalsForMac",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
