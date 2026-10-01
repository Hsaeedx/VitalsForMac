"""Persisted app settings: username/download folder/dates in a small JSON file.

The Vitals password is intentionally NOT persisted here (not to disk, not to
Keychain) — it's kept in memory only, for the current app session, in
VitalsMenuBarApp. See vitals_menubar.py."""

import json
from pathlib import Path

APP_SUPPORT_DIR = Path.home() / "Library" / "Application Support" / "VitalsForMac"
SETTINGS_FILE = APP_SUPPORT_DIR / "settings.json"

_DEFAULTS = {
    "username": "",
    "download_folder": "",
    "last_start_date": "",
    "last_end_date": "",
    "last_auto_download_date": "",
}


def _load():
    if not SETTINGS_FILE.is_file():
        return dict(_DEFAULTS)
    try:
        data = json.loads(SETTINGS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return dict(_DEFAULTS)
    merged = dict(_DEFAULTS)
    merged.update(data)
    return merged


def _save(data):
    APP_SUPPORT_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2))


def get(key):
    return _load().get(key, _DEFAULTS.get(key))


def set(key, value):
    data = _load()
    data[key] = value
    _save(data)
