"""Generates AppIcon.icns from the 🩺 emoji (same glyph used in the menu bar).
Run once (or whenever you want to change the icon): python make_icon.py
Requires macOS's iconutil, which ships with Xcode command line tools.
"""

import shutil
import subprocess
from pathlib import Path

from AppKit import NSBitmapImageRep, NSBitmapImageFileTypePNG, NSFont, NSAttributedString, NSGraphicsContext
from Foundation import NSMakePoint

EMOJI = "🩺"
ICONSET_SIZES = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]


def render(emoji, size, out_path):
    rep = NSBitmapImageRep.alloc().initWithBitmapDataPlanes_pixelsWide_pixelsHigh_bitsPerSample_samplesPerPixel_hasAlpha_isPlanar_colorSpaceName_bytesPerRow_bitsPerPixel_(
        None, size, size, 8, 4, True, False, "NSCalibratedRGBColorSpace", 0, 0
    )
    ctx = NSGraphicsContext.graphicsContextWithBitmapImageRep_(rep)
    NSGraphicsContext.setCurrentContext_(ctx)
    font = NSFont.systemFontOfSize_(size * 0.78)
    s = NSAttributedString.alloc().initWithString_attributes_(emoji, {"NSFont": font})
    sz = s.size()
    s.drawAtPoint_(NSMakePoint((size - sz.width) / 2, (size - sz.height) / 2))
    NSGraphicsContext.setCurrentContext_(None)
    png = rep.representationUsingType_properties_(NSBitmapImageFileTypePNG, None)
    png.writeToFile_atomically_(str(out_path), True)


if __name__ == "__main__":
    iconset = Path("AppIcon.iconset")
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()

    for filename, size in ICONSET_SIZES:
        render(EMOJI, size, iconset / filename)

    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", "AppIcon.icns"], check=True)
    shutil.rmtree(iconset)
    print("Wrote AppIcon.icns")
