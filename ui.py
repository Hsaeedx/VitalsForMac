"""Custom native dialogs for VitalsForMac.

rumps.Window only supports a single plain text field per alert, which is why
the built-in dialogs felt cramped (separate prompts for username/password,
typed YYYY-MM-DD dates). These helpers build NSAlert accessory views directly
with PyObjC so we get a real combined username+password form and an actual
calendar date-range picker.
"""

from datetime import datetime

from AppKit import (
    NSAlert,
    NSAlertFirstButtonReturn,
    NSAlertStyleInformational,
    NSColor,
    NSDatePicker,
    NSDatePickerElementFlagYearMonthDay,
    NSDatePickerStyleClockAndCalendar,
    NSFont,
    NSMakeRect,
    NSModalResponseOK,
    NSOpenPanel,
    NSSecureTextField,
    NSTextField,
    NSView,
)
from Foundation import NSDate, NSURL

CAPTION_FONT_SIZE = 11
FIELD_HEIGHT = 22
CAPTION_HEIGHT = 14
CAPTION_FIELD_GAP = 2
GROUP_GAP = 10


def _caption(text, frame):
    label = NSTextField.alloc().initWithFrame_(frame)
    label.setStringValue_(text)
    label.setBezeled_(False)
    label.setDrawsBackground_(False)
    label.setEditable_(False)
    label.setSelectable_(False)
    label.setFont_(NSFont.systemFontOfSize_(CAPTION_FONT_SIZE))
    label.setTextColor_(NSColor.secondaryLabelColor())
    return label


def _make_alert(title, message, ok_title, cancel_title, accessory_view):
    alert = NSAlert.alloc().init()
    alert.setAlertStyle_(NSAlertStyleInformational)
    alert.setMessageText_(title)
    if message:
        alert.setInformativeText_(message)
    alert.addButtonWithTitle_(ok_title)
    alert.addButtonWithTitle_(cancel_title)
    alert.setAccessoryView_(accessory_view)
    return alert


def ask_credentials(default_username="", message=""):
    """Shows one combined username + password form.
    Returns (username, password, confirmed)."""
    width = 280
    height = 2 * (CAPTION_HEIGHT + CAPTION_FIELD_GAP + FIELD_HEIGHT) + GROUP_GAP

    container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))

    y = height - CAPTION_HEIGHT
    container.addSubview_(_caption("Username", NSMakeRect(0, y, width, CAPTION_HEIGHT)))
    y -= CAPTION_FIELD_GAP + FIELD_HEIGHT
    username_field = NSTextField.alloc().initWithFrame_(NSMakeRect(0, y, width, FIELD_HEIGHT))
    username_field.setStringValue_(default_username)
    container.addSubview_(username_field)

    y -= GROUP_GAP + CAPTION_HEIGHT
    container.addSubview_(_caption("Password", NSMakeRect(0, y, width, CAPTION_HEIGHT)))
    y -= CAPTION_FIELD_GAP + FIELD_HEIGHT
    password_field = NSSecureTextField.alloc().initWithFrame_(NSMakeRect(0, y, width, FIELD_HEIGHT))
    container.addSubview_(password_field)

    alert = _make_alert("Vitals Credentials", message, "Continue", "Cancel", container)
    alert.window().setInitialFirstResponder_(username_field)

    response = alert.runModal()
    confirmed = response == NSAlertFirstButtonReturn
    return username_field.stringValue(), password_field.stringValue(), confirmed


def _pydate_to_nsdate(d):
    return NSDate.dateWithTimeIntervalSince1970_(datetime(d.year, d.month, d.day).timestamp())


def _nsdate_to_pydate(nsdate):
    return datetime.fromtimestamp(nsdate.timeIntervalSince1970()).date()


def _date_picker(default_date):
    picker = NSDatePicker.alloc().initWithFrame_(NSMakeRect(0, 0, 10, 10))
    picker.setDatePickerStyle_(NSDatePickerStyleClockAndCalendar)
    picker.setDatePickerElements_(NSDatePickerElementFlagYearMonthDay)
    picker.setDateValue_(_pydate_to_nsdate(default_date))
    picker.sizeToFit()
    return picker


def ask_single_date(default_date, message=""):
    """Shows one calendar date picker for a single day's download
    (downloads are capped at one day at a time to avoid hammering the Vitals site).
    Returns (date, confirmed) as a datetime.date object."""
    picker = _date_picker(default_date)
    picker_size = picker.frame().size

    width = picker_size.width
    height = CAPTION_HEIGHT + CAPTION_FIELD_GAP + picker_size.height

    container = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, width, height))

    container.addSubview_(_caption("Date", NSMakeRect(0, height - CAPTION_HEIGHT, width, CAPTION_HEIGHT)))
    picker.setFrameOrigin_((0, 0))
    container.addSubview_(picker)

    alert = _make_alert("Download a Day's Lectures", message, "Download", "Cancel", container)

    response = alert.runModal()
    confirmed = response == NSAlertFirstButtonReturn
    return _nsdate_to_pydate(picker.dateValue()), confirmed


def ask_folder(default_path=""):
    """Shows a native Finder folder picker. Returns the chosen path, or None if cancelled."""
    panel = NSOpenPanel.openPanel()
    panel.setCanChooseDirectories_(True)
    panel.setCanChooseFiles_(False)
    panel.setAllowsMultipleSelection_(False)
    panel.setCanCreateDirectories_(True)
    panel.setPrompt_("Choose")
    panel.setMessage_("Choose where downloaded lectures should be saved.")
    if default_path:
        panel.setDirectoryURL_(NSURL.fileURLWithPath_(default_path))

    if panel.runModal() == NSModalResponseOK:
        return panel.URLs()[0].path()
    return None
