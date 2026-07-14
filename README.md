# no-distraction-for-linux

Force-install the [**News Feed Eradicator**](https://west.io/news-feed-eradicator/)
browser extension across every browser on a Linux machine using **enterprise
policy**, so you can't disable or remove it from the browser UI in a moment of
weakness. The extension's toggle becomes greyed out and labelled *"Installed by
enterprise policy."*

This repo also cleanly removes [Pluckeye](https://www.pluckeye.net/) (an older
self-control tool) if it's present.

> **Honest expectation-setting:** this is *friction, not a wall.* You own the
> machine, so you can always undo it with `sudo` (see [Undo](#undo)). The point
> is to turn a one-click impulse into a deliberate, annoying chore — which is
> usually enough to break a binge reflex.

---

## What it does

`enforce_news_feed_eradicator.py`:

1. Writes an `ExtensionSettings` **enterprise policy** that force-installs News
   Feed Eradicator into each installed browser:

   | Browser | Policy file | Extension source |
   |---------|-------------|------------------|
   | Chrome   | `/etc/opt/chrome/policies/managed/plug.json` | Chrome Web Store |
   | Brave    | `/etc/brave/policies/managed/plug.json`      | Chrome Web Store |
   | Edge     | `/etc/opt/edge/policies/managed/plug.json`   | Chrome Web Store |
   | Chromium | `/etc/chromium/policies/managed/plug.json`   | Chrome Web Store |
   | Firefox  | `/etc/firefox/policies/policies.json`        | addons.mozilla.org |

2. Removes any **Pluckeye** entries from those same files, and (by default)
   deletes the Pluckeye application (`/usr/bin/pluck`, `/opt/pluck`).

It is **surgical** (keeps any unrelated policies you already have),
**idempotent** (safe to re-run — it only changes what isn't already correct),
and **backs up** every file it touches to `<file>.bak-<timestamp>` before
writing. The removed Pluckeye app is archived to `/var/backups/pluckeye-<timestamp>.tar.gz`.

---

## Requirements

- Linux with `python3` (3.6+; standard library only — no pip installs).
- `sudo`/root access (the policy files live under `/etc`).

---

## Usage

```bash
sudo python3 enforce_news_feed_eradicator.py
```

Then **fully quit and reopen** each browser — Chrome and Brave keep background
processes alive, so `pkill -f chrome` / `pkill -f brave` if unsure.

### Verify it worked

- Chromium browsers: open `chrome://policy` (or `brave://policy`,
  `edge://policy`) → **Reload policies**. `ExtensionSettings` should list the
  News Feed Eradicator id `fjcldmjmjhkklehbacihaiopjklihlgg`.
- Firefox: open `about:policies`.
- On each browser's extensions page, News Feed Eradicator shows as
  *"Installed by enterprise policy"* with a locked toggle.

---

## Configuration — editing the script

All knobs are constants near the top of `enforce_news_feed_eradicator.py`:

| Constant | Purpose |
|----------|---------|
| `NFE_CHROMIUM_ID` / `NFE_FIREFOX_ID` | The extension ids. Change these to enforce a *different* extension instead. |
| `NFE_CHROMIUM_ENTRY` / `NFE_FIREFOX_ENTRY` | The policy body (e.g. drop `toolbar_pin` if you don't want it pinned). |
| `POLICY_FILES` | The list of `(path, kind)` policy files. Add a browser here if yours isn't listed. `kind` is `"chromium"` or `"firefox"`. |
| `PLUCKEYE_EXT_IDS` | Extension ids treated as Pluckeye and stripped out. |
| `REMOVE_PLUCKEYE_APP` | Set to `False` to strip Pluckeye's browser policies but **keep** the app installed. |
| `PLUCKEYE_APP_PATHS` | Files deleted when removing the Pluckeye app. |

**Finding an extension's id** to enforce a different one:
- Chromium: `chrome://extensions` → enable *Developer mode* → copy the id.
- Firefox: the id is the add-on's `browser_specific_settings.gecko.id`
  (visible via the AMO API: `https://addons.mozilla.org/api/v5/addons/addon/<slug>/`).

---

## Undo

```bash
# Restore the most recent backups (adjust the timestamp glob as needed):
for f in /etc/opt/chrome/policies/managed/plug.json \
         /etc/brave/policies/managed/plug.json \
         /etc/opt/edge/policies/managed/plug.json \
         /etc/chromium/policies/managed/plug.json \
         /etc/firefox/policies/policies.json; do
  ls "$f".bak-* 2>/dev/null | tail -1 | xargs -I{} sudo cp {} "$f"
done

# ...or simply remove the policies entirely:
sudo rm -f /etc/opt/chrome/policies/managed/plug.json \
           /etc/brave/policies/managed/plug.json \
           /etc/opt/edge/policies/managed/plug.json \
           /etc/chromium/policies/managed/plug.json \
           /etc/firefox/policies/policies.json
```

Restart the browsers afterward. Restore Pluckeye (if you removed it) by
extracting `/var/backups/pluckeye-*.tar.gz` back to `/`.

---

## Caveats

- **Not tamper-proof against yourself.** Anyone with `sudo` can undo it. That's
  unavoidable — no software locks out the machine's own root user.
- **Don't `chattr +i` these files.** It's tempting to make them immutable for
  more friction, but do it only on files nothing else manages. (Previously these
  were shared with Pluckeye; now they're standalone, so immutability is safe if
  you want it — but it also blocks this script from updating them until you
  `chattr -i` first.)
- **Edge** force-installs a *Chrome Web Store* extension. This works on
  Chromium-based Edge, but is the most likely browser to need a nudge; if the
  extension doesn't appear, install it once manually and the policy will lock it.

---

## Saving / updating this project on GitHub

First-time setup (already done for this repo):

```bash
echo "# no-distraction-for-linux" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/razu381/no-distraction-for-linux.git
git push -u origin main
```

To save later edits:

```bash
git add -A
git commit -m "describe your change"
git push
```
