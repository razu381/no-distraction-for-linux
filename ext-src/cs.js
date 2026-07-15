// No Distraction Guard — blocks feed pages even when reached via SPA
// navigation (history.pushState), which browser URLBlocklist policy cannot see.
// Runs in every top-level youtube.com / facebook.com page.

(() => {
  "use strict";

  if (window.top !== window) return; // top frame only; embeds stay usable

  // Paths that stay usable. Everything else on these hosts is a feed
  // surface and gets bounced to the block page.
  const RULES = [
    {
      host: /(^|\.)youtube\.com$/i,
      allow: [
        /^\/watch/,        // a video you navigated to deliberately
        /^\/results/,      // search
        /^\/live_chat/,    // part of watch pages
        /^\/embed\//,      // embedded players
      ],
    },
    {
      host: /(^|\.)facebook\.com$/i,
      allow: [
        /^\/messages/,
        /^\/groups/,
      ],
    },
  ];

  function isBlocked(loc) {
    for (const rule of RULES) {
      if (!rule.host.test(loc.hostname)) continue;
      return !rule.allow.some((re) => re.test(loc.pathname));
    }
    return false;
  }

  function enforce() {
    if (!isBlocked(location)) return;
    const dest =
      chrome.runtime.getURL("blocked.html") +
      "#" + location.hostname + location.pathname;
    // Stop the feed from loading/rendering while the redirect happens.
    try { window.stop(); } catch (e) {}
    location.replace(dest);
  }

  enforce();

  // SPA route changes: YouTube fires its own navigation events; a cheap
  // poll catches everything else (Facebook, future site changes).
  window.addEventListener("yt-navigate-start", enforce, true);
  window.addEventListener("yt-navigate-finish", enforce, true);
  window.addEventListener("popstate", enforce, true);
  let lastPath = location.pathname;
  setInterval(() => {
    if (location.pathname !== lastPath) {
      lastPath = location.pathname;
      enforce();
    }
  }, 300);
})();
