# no-distraction-for-linux

Force-install the [**News Feed Eradicator**](https://west.io/news-feed-eradicator/)
browser extension across every browser on a Linux machine using **enterprise
policy**, so you can't disable or remove it from the browser UI in a moment of
weakness. The extension's toggle becomes greyed out and labelled *"Installed by
enterprise policy."*

This repo also cleanly removes [Pluckeye](https://www.pluckeye.net/) (an older
self-control tool) if it's present.

> **Read [HOW-IT-WORKS.md](HOW-IT-WORKS.md)** for the full three-layer
> architecture and why each layer exists.

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
   | Sidekick | `/etc/sidekick/policies/managed/plug.json`   | Chrome Web Store |
   | Wavebox  | `/etc/wavebox/policies/managed/plug.json`    | Chrome Web Store |
   | Firefox  | `/etc/firefox/policies/policies.json`        | addons.mozilla.org |

2. Adds **browser-enforced feed blocking** (`URLBlocklist`/`URLAllowlist` in
   Chromium browsers, `WebsiteFilter` in Firefox). This is the layer the
   extension can't give you: News Feed Eradicator's own per-site toggles live
   in its local settings and can always be switched off, but a URL policy is
   enforced by the browser with **no UI toggle anywhere**. Default rules:
   YouTube and Facebook are blocked *except* YouTube search (`/results`),
   direct videos (`/watch`, `/embed`), Facebook Messages and Groups — so the
   feeds die but deliberate use still works. Edit `URL_BLOCKLIST` /
   `URL_ALLOWLIST` (and the `FF_*` equivalents) in the script to taste, or set
   `ENFORCE_URL_RULES = False` to skip this layer.

3. **Sweeps stray files out of each `policies/managed/` directory.** This is
   load-bearing: Chromium browsers read *every* file in that directory as
   policy (alphabetically, later files win), so a leftover backup like
   `plug.json.bak-...` silently overrides the real policy. See
   [Troubleshooting](#troubleshooting).

4. Removes any **Pluckeye** entries from those same files, and (by default)
   deletes the Pluckeye application (`/usr/bin/pluck`, `/opt/pluck`) and its
   `net.pluckeye.*` native-messaging manifests.

It is **surgical** (keeps any unrelated policies you already have),
**idempotent** (safe to re-run — it only changes what isn't already correct),
and **backs up** everything it touches into `/var/backups/no-distraction/`
(never into the policy directories themselves). The removed Pluckeye app is
archived to `/var/backups/no-distraction/pluckeye-<timestamp>.tar.gz`.

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

All backups live in `/var/backups/no-distraction/` with the original path
encoded in the filename (`/` replaced by `__`). To drop the enforcement
entirely, just remove the policy files:

```bash
sudo rm -f /etc/opt/chrome/policies/managed/plug.json \
           /etc/brave/policies/managed/plug.json \
           /etc/opt/edge/policies/managed/plug.json \
           /etc/chromium/policies/managed/plug.json \
           /etc/sidekick/policies/managed/plug.json \
           /etc/wavebox/policies/managed/plug.json \
           /etc/firefox/policies/policies.json
```

Restart the browsers afterward. To restore an original file instead, copy the
matching backup out of `/var/backups/no-distraction/` — but **never leave a
backup copy inside a `policies/managed/` directory** (see Troubleshooting).
Restore Pluckeye (if you removed it) by extracting
`/var/backups/no-distraction/pluckeye-*.tar.gz` back to `/`.

---

## Troubleshooting

**The extension isn't force-installed even after a full restart / reboot.**
The most likely cause — and a bug an early version of this script had — is a
stray file sitting next to the policy: Chromium browsers load **every file**
in `policies/managed/` as policy, in alphabetical order, with later files
overriding earlier ones. A leftover `plug.json.bak-...` therefore silently
overrides `plug.json`. Check with:

```bash
ls /etc/brave/policies/managed/   # must contain ONLY your policy file(s)
```

Re-running the script fixes this automatically (it sweeps stray files into
`/var/backups/no-distraction/`).

Other checks, in order:
1. `brave://policy` → **Reload policies** → `ExtensionSettings` must show the
   extension id with Status **OK**.
2. Fully quit the browser (`pkill -f brave`) and reopen — policy loads at
   startup; give it a minute on first launch to download the extension.
3. If the policy shows correctly but the extension still doesn't appear,
   install it once manually from the store — the `force_installed` policy
   then locks the manually-installed copy (Remove/disable disappear).

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
