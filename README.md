# VitalsForMac

A small Mac menu bar app for downloading lecture files from OSU's Vitals site, instead of clicking through it by hand.

## Install

1. Go to the Releases page of this repo and download VitalsForMac.dmg.
2. Open it, then drag VitalsForMac into the Applications folder shown.
3. Open VitalsForMac from your Applications folder.

First time only: macOS will say it can't verify the app. Go to System Settings, then Privacy & Security, scroll down, and click "Open Anyway." Then click Open again. You only have to do this once.

## Use

Click the 🩺 icon in the menu bar.

- Set Credentials... - enter your Vitals username and password
- Choose Download Folder... - pick where files get saved
- Download Today, or Download a Specific Day... to get lectures

Files are saved into folders by date and lecture name.

Your password is only kept in memory while the app is running. It's never saved to disk or Keychain.

## Build it yourself

You need Python 3.

```
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt

python vitals_menubar.py        # run it directly
python setup.py py2app          # build VitalsForMac.app
```

## Disclaimer

This is an unofficial personal tool. It only downloads content you already have access to when logged into Vitals. You cannot access any locked/unreleased content. Regardless, be a good citizen of the site.
