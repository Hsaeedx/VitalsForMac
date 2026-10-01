"""VitalsForMac — a simple macOS menu bar app for downloading OSU Vitals lecture materials."""

import os
import subprocess
import sys
import threading
import time
from datetime import datetime

import requests
import rumps
from PyObjCTools import AppHelper

import settings
import ui
import vitals_client
from vitals_client import VitalsError

DATE_FORMAT = "%Y-%m-%d"
AUTO_CHECK_INTERVAL_SECONDS = 60 * 60  # hourly
DOWNLOAD_COOLDOWN_SECONDS = 60


def _readme_path():
    if getattr(sys, "frozen", False):
        return os.path.join(os.environ["RESOURCEPATH"], "README.md")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md")


def _today_str():
    return datetime.now().strftime(DATE_FORMAT)


class VitalsMenuBarApp(rumps.App):
    def __init__(self):
        super().__init__("VitalsForMac", title="🩺", quit_button=None)

        self.status_item = rumps.MenuItem("Ready to Download")
        self.status_item.set_callback(None)

        self.account_item = rumps.MenuItem("Not logged in")
        self.account_item.set_callback(None)

        self.folder_item = rumps.MenuItem("No download folder selected")
        self.folder_item.set_callback(None)

        self.menu = [
            self.status_item,
            self.account_item,
            self.folder_item,
            None,
            rumps.MenuItem("Set Credentials…", callback=self.set_credentials),
            rumps.MenuItem("Choose Download Folder…", callback=self.choose_download_folder),
            None,
            rumps.MenuItem("Download Today", callback=self.download_today),
            rumps.MenuItem("Download a Specific Day…", callback=self.download_specific_day),
            None,
            rumps.MenuItem("About VitalsForMac", callback=self.show_about),
            rumps.MenuItem("Quit VitalsForMac", callback=rumps.quit_application),
        ]

        self._busy = False
        # In-memory only for this app session — never written to disk or Keychain.
        self._password = None
        # monotonic clock, immune to system clock changes; 0 means "never downloaded"
        self._last_download_at = 0.0
        self._refresh_status_items()

    def _refresh_status_items(self):
        username = settings.get("username")
        if username and self._password:
            self.account_item.title = f"Logged in as {username}"
        elif username:
            self.account_item.title = f"{username} (password needed)"
        else:
            self.account_item.title = "Not logged in"

        folder = settings.get("download_folder")
        self.folder_item.title = f"Folder: {folder}" if folder else "No download folder selected"

    def show_about(self, _):
        subprocess.Popen(["open", _readme_path()])

    # -- Setup ---------------------------------------------------------

    def set_credentials(self, _):
        username, password, confirmed = ui.ask_credentials(
            default_username=settings.get("username"),
        )
        username = username.strip()
        if not confirmed or not username or not password:
            return

        settings.set("username", username)
        self._password = password
        self._refresh_status_items()
        rumps.notification("VitalsForMac", "Credentials set for this session", f"Username: {username}")

    def _ensure_password(self, username):
        """Returns the in-memory password, prompting for it if not already cached
        this session. Never persisted to disk/Keychain."""
        if self._password:
            return self._password
        _, password, confirmed = ui.ask_credentials(
            default_username=username,
            message="Password is kept in memory only for this app session — never saved to disk or Keychain.",
        )
        if not confirmed or not password:
            return None
        self._password = password
        self._refresh_status_items()
        return self._password

    def choose_download_folder(self, _):
        folder = ui.ask_folder(default_path=settings.get("download_folder"))
        if not folder:
            return
        settings.set("download_folder", folder)
        self._refresh_status_items()
        rumps.notification("VitalsForMac", "Download folder saved", folder)

    # -- Downloading -----------------------------------------------------

    def _run_download(self, start_date, end_date, label):
        if self._busy:
            rumps.notification("VitalsForMac", "Already running", "A download is already in progress.")
            return

        # Cooldown between downloads so the app can't be used to hammer the
        # Vitals site with rapid repeat clicks. The status line already shows
        # the countdown (see _update_idle_status), so just block silently here.
        if self._cooldown_remaining() > 0:
            return

        username = settings.get("username")
        download_folder = settings.get("download_folder")
        if not username:
            rumps.alert("VitalsForMac", "Set your Vitals username first (menu → Set Credentials…).")
            return
        if not download_folder:
            rumps.alert("VitalsForMac", "Choose a download folder first (menu → Choose Download Folder…).")
            return
        password = self._ensure_password(username)
        if not password:
            return

        self._busy = True
        self._last_download_at = time.monotonic()
        thread = threading.Thread(
            target=self._download_worker,
            args=(username, password, download_folder, start_date, end_date, label),
            daemon=True,
        )
        thread.start()

    def _set_status(self, text):
        # AppKit/Cocoa calls must happen on the main thread; this method is
        # called from the background download thread, so hop back to main.
        AppHelper.callAfter(setattr, self.status_item, "title", text)

    def _notify(self, title, subtitle):
        AppHelper.callAfter(rumps.notification, "VitalsForMac", title, subtitle)

    def _mark_login_failed(self):
        # A VitalsError here means the login POST or the schedule fetch that
        # follows it didn't work as expected — almost always wrong credentials.
        # Drop the cached password so the next attempt re-prompts instead of
        # silently retrying with the same bad password.
        self._password = None
        AppHelper.callAfter(setattr, self.account_item, "title", "Login failed — check credentials")

    def _cooldown_remaining(self):
        return DOWNLOAD_COOLDOWN_SECONDS - (time.monotonic() - self._last_download_at)

    def _update_idle_status(self):
        # Only takes over the status line when no download is running — the
        # worker thread owns it (via _set_status) while one is in progress.
        if self._busy:
            return
        remaining = self._cooldown_remaining()
        if remaining > 0:
            self.status_item.title = f"Ready to Download in {int(remaining) + 1}s"
        else:
            self.status_item.title = "Ready to Download"

    @rumps.timer(1)
    def _tick_cooldown_display(self, _):
        self._update_idle_status()

    def _download_worker(self, username, password, download_folder, start_date, end_date, label):
        try:
            self._set_status(f"Downloading ({label})…")
            with requests.Session() as session:
                vitals_client.login(session, username, password)
                events = vitals_client.fetch_schedule(session, start_date, end_date)

                if not events:
                    self._notify(label, "No lectures found for that range.")
                    return

                total_files = 0
                for i, event in enumerate(events, start=1):
                    self._set_status(f"Downloading {label} ({i}/{len(events)})…")
                    total_files += vitals_client.download_event_files(session, event, download_folder)

            self._notify(
                f"{label} complete",
                f"{total_files} file(s) downloaded from {len(events)} event(s).",
            )
        except VitalsError as e:
            self._mark_login_failed()
            self._notify(f"{label} failed", str(e))
        except Exception as e:
            self._notify(f"{label} failed", f"Unexpected error: {e}")
        finally:
            self._busy = False
            AppHelper.callAfter(self._update_idle_status)

    def download_today(self, _):
        today = _today_str()
        settings.set("last_auto_download_date", today)
        self._run_download(today, today, "Today's lectures")

    def download_specific_day(self, _):
        # Downloads are capped at a single day at a time — no date ranges —
        # so this app can't be used to hammer the Vitals site with a big scrape.
        today = datetime.now().date()

        def _parse(value, fallback):
            try:
                return datetime.strptime(value, DATE_FORMAT).date()
            except (ValueError, TypeError):
                return fallback

        default_date = _parse(settings.get("last_start_date"), today)

        chosen_date, confirmed = ui.ask_single_date(default_date)
        if not confirmed:
            return

        date_str = chosen_date.strftime(DATE_FORMAT)
        settings.set("last_start_date", date_str)
        self._run_download(date_str, date_str, "Selected day")

    # -- Daily auto-download ----------------------------------------------

    @rumps.timer(AUTO_CHECK_INTERVAL_SECONDS)
    def check_daily_auto_download(self, _):
        if self._busy:
            return
        # Only runs if a password is already cached in memory this session
        # (e.g. from an earlier manual download) — never prompts unattended.
        username = settings.get("username")
        if not username or not self._password or not settings.get("download_folder"):
            return
        today = _today_str()
        if settings.get("last_auto_download_date") == today:
            return
        settings.set("last_auto_download_date", today)
        self._run_download(today, today, "Today's lectures (auto)")


if __name__ == "__main__":
    VitalsMenuBarApp().run()
