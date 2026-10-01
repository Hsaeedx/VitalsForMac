# VitalsForMac

A tiny macOS menu bar app for downloading lecture materials from OSU's
[Vitals](https://vitals.osumc.edu) curriculum site — no browser clicking
through each day's schedule required.

<p align="center">🩺 lives quietly in your menu bar</p>

## Features

- **Download Today** — one click, grabs today's lecture files.
- **Download a Specific Day…** — pick any single day from a calendar.
- **Daily auto-download** — while the app is running, it checks about once
  an hour and automatically grabs that day's lectures the first time it sees
  a new date (no need to remember to click anything).

## Installing

1. Go to this repo's **Releases** page (on the right side of the repo's
   GitHub page) and download the latest `VitalsForMac.zip`.
2. Unzip it (double-click the file) and drag `VitalsForMac.app` into your
   **Applications** folder.
3. Open it like any other app (double-click, or Spotlight → "VitalsForMac").

**First launch only:** since this app isn't signed with a paid Apple
Developer certificate, macOS will block it the first time with a message
like *"Apple could not verify ... is free of malware."* This is normal for
small apps distributed outside the App Store — to allow it:
   - Click the 🩺-less dialog's **Done**, then open
     **System Settings → Privacy & Security**.
   - Scroll down to the security section — you'll see a line about
     "VitalsForMac was blocked." Click **Open Anyway**.
   - Confirm **Open** in the dialog that follows (may ask for your Mac
     password or Touch ID).

You only need to do this once. After that, it opens normally from
Applications or Spotlight.

(If you're building it yourself instead of downloading a release, see
[Building](#building) below.)

## Using it

1. Click the 🩺 icon in the menu bar.
2. **Set Credentials…** — enter your Vitals username and password.
3. **Choose Download Folder…** — pick where files should be saved.
4. **Download Today** or **Download a Specific Day…** to fetch lectures.

Downloaded files land in `<your folder>/<event date>/<event name>/`.

The menu also shows your current login state ("Logged in as ...") and the
selected download folder, so you can see at a glance whether you're set up.

## Building

Requires Python 3 and Xcode's command line tools (for `pyobjc`).

```bash
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

# Run directly during development:
python vitals_menubar.py

# Build a real double-clickable .app:
python setup.py py2app
open dist/VitalsForMac.app
```


## Disclaimer

This is an unofficial, personal tool for automating something you could do
manually in a browser. This is intended only to allow you to download lectures and content in a more streamlined way than the Vitals website currently does. This tool does not provide you with access to any protected resources--only to content that is available to you when you are logged into Vitals. Your password is never save Be a good citizen, as spamming this tool 
