"""Vitals login/scrape/download logic, adapted from the original scrape_vitals.py CLI script."""

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
from datetime import datetime
import json
import re

MAIN_URL = "https://vitals.osumc.edu/Home/LogOnUser"
SCHEDULE_URL = "https://vitals.osumc.edu/Notification/GetScheduleStudent"

DOWNLOADABLE_EXTENSIONS = [
    ".pdf", ".pptx", ".docx", ".xlsx", ".xls", ".csv", ".zip", ".doc", ".ppt", ".txt",
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://vitals.osumc.edu",
    "Referer": "https://vitals.osumc.edu/",
    "Cookie": "VitalsLoginType=MC;",
}


class VitalsError(Exception):
    pass


def clean_filename(text):
    cleaned = re.sub(r'[\\/*?:"<>|]', "", text).strip()
    return cleaned[:100]


def login(session, username, password):
    payload = {
        "LogonType": "MC",
        "LoginTabIndex": "0",
        "RedirectUrl": "",
        "UserName": username,
        "Password": password,
    }
    response = session.post(MAIN_URL, headers=HEADERS, data=payload)
    if response.status_code != 200:
        raise VitalsError("Login failed. Check your credentials and try again.")


def fetch_schedule(session, start_date, end_date):
    """start_date / end_date are 'YYYY-MM-DD' strings. Returns a list of event dicts."""
    params = {"Start": start_date, "End": end_date}
    response = session.get(SCHEDULE_URL, params=params)
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        raise VitalsError("Failed to load schedule. Check your credentials and try again.")


def _extract_download_links(url, session):
    response = session.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    links = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if not any(ext in href for ext in DOWNLOADABLE_EXTENSIONS):
            continue
        full_link = urljoin(url, href)
        suffix = Path(href).suffix.strip()
        if not suffix:
            continue
        name = clean_filename(link.get_text()) or "file"
        links.append((full_link, f"{name}{suffix}"))
    return links


def download_event_files(session, event, dest_root, on_progress=None):
    """Downloads all linked files for one schedule event under
    dest_root/<event date>/<event name>/<file>. Returns the number of files written.
    Folders are only created once we know there's something to download."""
    event_link = f'https://vitals.osumc.edu{event["EventLink"]}'.replace(
        "GetContent", "GetStudentMaterials"
    )
    links = _extract_download_links(event_link, session)
    if not links:
        return 0

    event_date = datetime.strptime(event["Start"], "%Y-%m-%dT%H:%M:%S").strftime("%Y-%m-%d")
    event_name = clean_filename(event["Name"]) or "Untitled"
    folder = Path(dest_root) / event_date / event_name
    folder.mkdir(parents=True, exist_ok=True)

    written = 0
    for full_link, file_name in links:
        download_path = folder / file_name
        if download_path.is_file():
            continue
        if on_progress:
            on_progress(file_name)
        file_response = session.get(full_link)
        with open(download_path, "wb") as f:
            f.write(file_response.content)
        written += 1
    return written
