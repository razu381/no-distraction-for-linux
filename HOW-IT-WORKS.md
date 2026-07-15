# How this setup works

A three-layer defense against feed binging (YouTube, Facebook) on Linux,
applied by one script:

```bash
sudo python3 enforce_news_feed_eradicator.py
```

Each layer exists because the one before it has a specific hole. Understanding
the holes is the point — that's what makes the whole thing hard to bypass on
impulse.

---

## Layer 1 — News Feed Eradicator, force-installed

**What:** The [News Feed Eradicator](https://west.io/news-feed-eradicator/)
extension is marked `force_installed` via enterprise policy
(`ExtensionSettings`) in every browser's policy file under
`/etc/<browser>/policies/managed/`.

**Effect:** The browser installs it automatically, reinstalls it if removed,
and greys out the disable/remove buttons. The extensions page shows
*"Installed by enterprise policy."*

**Its hole:** The extension's **own settings** (per-site filter toggles) are
plain local data. Policy can't lock them — NFE ships no managed-storage
schema — so "turn off YouTube filtering" is always one click away inside the
extension's options.

## Layer 2 — Browser-enforced URL blocking

**What:** The same policy files carry `URLBlocklist` / `URLAllowlist`
(Chromium browsers) and `WebsiteFilter` (Firefox):

| Blocked | Still allowed |
|---------|---------------|
| all of `youtube.com` | `/watch` (direct videos), `/results` (search), `/embed` (embedded players) |
| all of `facebook.com` | `/messages`, `/groups` |

**Effect:** Typing the URL, opening a tab, or refreshing a feed page hits the
browser's "blocked by administrator" page. Enforced by the browser core —
there is **no toggle anywhere in the UI**, and the extension is irrelevant to
it.

**Its hole:** YouTube and Facebook are single-page apps. Clicking the site
logo doesn't load a page — it's an in-app route change done in JavaScript,
which URL policies never see. So the homepage feed was still reachable from a
watch/search page.

## Layer 3 — No Distraction Guard (custom extension)

**What:** A ~60-line MV3 extension (source in [`ext-src/`](ext-src/) — audit
it) whose content script watches the address on every SPA route change
(`yt-navigate` events, `popstate`, and a 300 ms poll) and bounces any feed
page to a static block page ("The feed stays closed"). It is packed and
signed (`ext/no_distraction_guard.crx`), served from this repo's GitHub
Pages, and **force-installed by the same policy as Layer 1** — so it also has
no off switch in the browser.

**Effect:** The logo click, Shorts, and every other in-app path to a feed all
dead-end at the block page, with a search box for deliberate use.

**Its hole:** none inside the browser. Bypassing any of the three layers
requires root: editing files under `/etc` in a terminal and restarting the
browser. That deliberate, boring chore — instead of a one-click toggle — is
the entire design. This is friction, not a wall: nothing can stop the
machine's own administrator, but nothing here can be undone in a moment of
weakness either.

---

## Also done by the script

- **Removed Pluckeye** (a defunct self-control tool) completely: the app
  (`/usr/bin/pluck`, `/opt/pluck`), its policy entries in all seven browser
  policy files (including Sidekick and Wavebox), and its native-messaging
  manifests. Everything is archived in `/var/backups/no-distraction/`.
- **Swept stray files out of the policy directories.** Chromium reads *every*
  file in `policies/managed/` as policy (alphabetical order, later files
  win), so even a leftover backup file silently overrides the real policy.
  This bit us once; the script now prevents it structurally.

## Files

| Path | What |
|------|------|
| `enforce_news_feed_eradicator.py` | The whole enforcement, idempotent, safe to re-run |
| `ext-src/` | Guard extension source (manifest, content script, block page) |
| `ext/no_distraction_guard.crx` | Packed signed Guard, served via GitHub Pages |
| `ext/updates.xml` | Update manifest the force-install policy points at |
| `~/.no-distraction/guard-key.pem` | Guard signing key — **not** in the repo; needed to ship Guard updates |
| `/var/backups/no-distraction/` | Every file the script changed or removed |

## Changing the rules

Edit the constants at the top of `enforce_news_feed_eradicator.py`
(`URL_BLOCKLIST`, `URL_ALLOWLIST`, `RULES` in `ext-src/cs.js` for the Guard,
`ENFORCE_URL_RULES` / `ENFORCE_GUARD` to disable a layer), then re-run it
with sudo. If you change the Guard's source, repack the CRX with the local
key, bump the version in `manifest.json` and `updates.xml`, and push — the
browsers pick up the update from GitHub Pages.

Full undo instructions are in the [README](README.md#undo).

## Verifying it's active

1. `brave://policy` (or `chrome://policy`, `edge://policy`) → Reload policies →
   `ExtensionSettings`, `URLBlocklist`, `URLAllowlist` all present, Status OK.
2. `brave://extensions` → both *News Feed Eradicator* and *No Distraction
   Guard* say "Installed by enterprise policy," with no Remove button.
3. Open `youtube.com` directly → browser block page. Click the YouTube logo
   from a search page → "The feed stays closed."
