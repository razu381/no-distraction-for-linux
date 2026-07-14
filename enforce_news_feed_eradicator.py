#!/usr/bin/env python3
"""
no-distraction-for-linux
========================
Force-install the **News Feed Eradicator** extension into every browser on this
machine via enterprise policy, so the extension can no longer be disabled or
removed from the browser UI (the toggle is greyed out and labelled
"Installed by enterprise policy"). Optionally removes the defunct Pluckeye tool.

    sudo python3 enforce_news_feed_eradicator.py

Why root: browser policy lives in root-owned files under /etc.

The script is SURGICAL and IDEMPOTENT:
  * It preserves any unrelated policies already in each file.
  * It removes only Pluckeye's own entries (matched by known extension id or by
    a "pluck" URL) plus Pluckeye's inert ExtensionManifestV2Availability key.
  * It adds the News Feed Eradicator entry.
  * Re-running it makes no further changes once everything is in place.
  * Every file it changes is backed up to <file>.bak-<timestamp> first.

If you ever want to undo it: restore the .bak files (or just delete the policy
files) and restart the browsers.
"""

import json
import os
import shutil
import tarfile
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# News Feed Eradicator identifiers.
NFE_CHROMIUM_ID = "fjcldmjmjhkklehbacihaiopjklihlgg"      # Chrome Web Store id
NFE_FIREFOX_ID = "@news-feed-eradicator"                 # addons.mozilla.org id

NFE_CHROMIUM_ENTRY = {
    "installation_mode": "force_installed",
    "update_url": "https://clients2.google.com/service/update2/crx",
    "toolbar_pin": "force_pinned",
}
NFE_FIREFOX_ENTRY = {
    "installation_mode": "force_installed",
    "install_url": "https://addons.mozilla.org/firefox/downloads/latest/news-feed-eradicator/latest.xpi",
}

# Browser policy files: (path, kind). kind is "chromium" or "firefox".
# Only files that already exist are touched; the rest are skipped.
POLICY_FILES = [
    ("/etc/opt/chrome/policies/managed/plug.json", "chromium"),
    ("/etc/brave/policies/managed/plug.json", "chromium"),
    ("/etc/opt/edge/policies/managed/plug.json", "chromium"),
    ("/etc/chromium/policies/managed/plug.json", "chromium"),
    ("/etc/firefox/policies/policies.json", "firefox"),
]

# --- Pluckeye removal ------------------------------------------------------
# Known Pluckeye extension ids (its Edge id contains no "pluck" string, so it is
# listed explicitly). Any ExtensionSettings entry whose URL contains "pluck" is
# also treated as Pluckeye.
PLUCKEYE_EXT_IDS = {
    "njnachfbhaoikkegkmocpgllkfkggagg",   # Chrome / Brave / Chromium
    "caebpeaablfnmkfbmfnecpbjlgbbfomb",   # Edge
    "fluxo@pluckeye.net",                 # Firefox
}
# Remove the Pluckeye application files too (set False to keep the app, and only
# strip its browser policies).
REMOVE_PLUCKEYE_APP = True
PLUCKEYE_APP_PATHS = ["/usr/bin/pluck", "/opt/pluck"]

STAMP = time.strftime("%Y%m%d-%H%M%S")
BACKUP_DIR = "/var/backups"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def require_root():
    if os.geteuid() != 0:
        raise SystemExit(
            "Must run as root:  sudo python3 " + os.path.basename(__file__)
        )


def is_pluckeye_entry(ext_id, entry):
    if ext_id in PLUCKEYE_EXT_IDS:
        return True
    if isinstance(entry, dict):
        url = f"{entry.get('update_url', '')} {entry.get('install_url', '')}"
        return "pluck" in url.lower()
    return False


def configure_policy(path, kind):
    if not os.path.exists(path):
        print(f"SKIP    {path}  (browser not configured here)")
        return

    try:
        with open(path) as fh:
            data = json.load(fh)
        if not isinstance(data, dict):
            data = {}
    except (json.JSONDecodeError, OSError):
        data = {}

    # Firefox nests everything under a top-level "policies" object.
    container = data.setdefault("policies", {}) if kind == "firefox" else data

    ext = container.get("ExtensionSettings")
    if not isinstance(ext, dict):
        ext = {}

    # Strip Pluckeye's own extension entries, preserve anything else.
    for eid in [k for k, v in ext.items() if is_pluckeye_entry(k, v)]:
        del ext[eid]

    # Pluckeye's ExtensionManifestV2Availability is inert/unknown here — drop it.
    container.pop("ExtensionManifestV2Availability", None)

    # Add News Feed Eradicator.
    if kind == "firefox":
        ext[NFE_FIREFOX_ID] = NFE_FIREFOX_ENTRY
    else:
        ext[NFE_CHROMIUM_ID] = NFE_CHROMIUM_ENTRY
    container["ExtensionSettings"] = ext

    new_text = json.dumps(data, indent=2) + "\n"
    with open(path) as fh:
        if fh.read() == new_text:
            print(f"OK      {path}  (already correct)")
            return

    backup = f"{path}.bak-{STAMP}"
    shutil.copy2(path, backup)
    with open(path, "w") as fh:
        fh.write(new_text)
    print(f"DONE    {path}\n          News Feed Eradicator forced; Pluckeye removed"
          f"\n          backup: {backup}")


def remove_pluckeye_app():
    present = [p for p in PLUCKEYE_APP_PATHS if os.path.lexists(p)]
    if not present:
        print("OK      Pluckeye application already absent")
        return

    os.makedirs(BACKUP_DIR, exist_ok=True)
    archive = os.path.join(BACKUP_DIR, f"pluckeye-{STAMP}.tar.gz")
    with tarfile.open(archive, "w:gz") as tar:
        for p in present:
            tar.add(p)
    print(f"BACKUP  Pluckeye files -> {archive}")

    for p in present:
        if os.path.isdir(p) and not os.path.islink(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
        print(f"REMOVED {p}")


# ---------------------------------------------------------------------------
def main():
    require_root()

    print("== Enforcing News Feed Eradicator ==")
    for path, kind in POLICY_FILES:
        configure_policy(path, kind)

    if REMOVE_PLUCKEYE_APP:
        print("\n== Removing Pluckeye application ==")
        remove_pluckeye_app()

    print(
        "\nDone.\n"
        "  1. Fully quit every browser (kill background processes too), reopen.\n"
        "  2. Verify: chrome://policy , brave://policy , edge://policy ,\n"
        "     and about:policies (Firefox) — News Feed Eradicator should show as\n"
        "     'Installed by enterprise policy' with a locked toggle."
    )


if __name__ == "__main__":
    main()
