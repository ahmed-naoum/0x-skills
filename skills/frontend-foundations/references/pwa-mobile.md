# PWA, offline and the native boundary

Read this when: the product must work offline or be installable, someone asks for "an app", the web app is to be wrapped for the
stores, links should open the installed app, a flow breaks inside Instagram's or another app's browser, or a store submission,
in-app purchase or app release needs handling.

## Web, PWA, wrapper or native

| Option | Choose when | What it costs |
|---|---|---|
| Responsive web app | Default at Prototype and for most products at Launch. Users arrive by link or search; use is occasional or desktop-heavy | Nothing extra |
| Installable PWA | Frequent repeat use, a home-screen icon and offline tolerance matter, and store presence does not | Manifest, service worker and its update discipline. On iOS: installation only via Share → Add to Home Screen, no install prompt, push only after installation |
| Web app wrapped with Capacitor | A store listing is required (discovery, customer expectation, enterprise device management) or a native capability is missing on the web, and the web app already exists | Store accounts and review, a statically built client talking to the API, native build tooling, releases that cannot be rolled back |
| React Native with Expo | The mobile app *is* the product, or needs native-feeling navigation, gestures, long lists and deep offline use | A second UI codebase (logic, types and API client are shared; components are not) |
| Fully native (Swift, Kotlin) | Platform-deep features: widgets, heavy background work, AR, games, wearables | Two more codebases and people who specialize in them |

Before agreeing to "we need an app", establish what the app would do that the website cannot. Legitimate answers: reliable push,
store discovery, device APIs, offline, customers who demand a listing. "It feels more serious" is paid for with store fees, a
share of in-app digital revenue, review delays on every release, and supporting old installed versions for as long as users keep
them.

## Offline: detect honestly, queue or block

- `navigator.onLine === false` reliably means offline. `true` means only that a network interface exists: captive portals, dead
  Wi-Fi and one-bar mobile all report online. The truth is the outcome of each request, so every request has a timeout and a
  failure path. The `online` event is a hint to retry, not proof.
- Classify every user action once, as a product decision:

| Class | Examples | Offline behavior |
|---|---|---|
| Queueable | Create or edit of the user's own data, with a client-generated id | Apply locally, store in an outbox (IndexedDB), mark the item "waiting to sync", replay on reconnect |
| Must be live | Payments, bookings against limited stock, anything needing fresh server truth, sign-in, destructive or irreversible actions | Disable with a stated reason ("You're offline — reconnect to pay"). No optimistic success |
| Read | Lists and documents seen before | Show cached data with its age ("Updated 2 h ago") |

- Outbox rules: each entry carries an idempotency key so replay after an ambiguous failure cannot duplicate; replay in order
  with backoff; a permanent rejection (validation, permission, conflict) is surfaced to the user for resolution, never dropped
  silently; nothing shows as "saved" until the server confirmed it.
- Replay on app start, on `online`, and when the tab becomes visible. Background sync from a service worker is not available in
  every browser, so it can only be an extra.
- Conflicts: for one person's data across their own devices, last write wins per field is acceptable. For shared data, send the
  version the edit was based on and show a conflict choice when it is stale. Conflict-free replicated data types are justified
  only when simultaneous collaboration is the product (`0x:backend-architecture`, `realtime.md`).
- Offline-first is an architecture, not a feature flag: every screen reads from a local store that syncs. Commit to it only when
  users regularly work without signal.

## An installable PWA

1. **Manifest**, linked from every page (`<link rel="manifest" href="/manifest.webmanifest">`; in Next.js, `app/manifest.ts`):

```json
{
  "id": "/",
  "name": "Acme Field Notes",
  "short_name": "Notes",
  "start_url": "/?source=pwa",
  "scope": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#0f172a",
  "icons": [
    { "src": "/icons/192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "/icons/maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

   The maskable icon is a separate file with the artwork inside the central 80%, because platforms crop it to their shape. Add
   `apple-touch-icon` in the HTML for iOS.
2. **HTTPS** everywhere, and a `start_url` that responds when offline.
3. **Service worker** at the site root (`/sw.js`): a worker controls only paths at or below its own location. Generate it with a
   maintained toolkit (Workbox, or a framework wrapper around it) instead of hand-writing cache logic.
4. **Offline shell.** Precache the application shell and a dedicated offline page.

| Request | Strategy |
|---|---|
| Page navigations (HTML) | Network first with a short timeout, fall back to cache, then to the offline page |
| Fingerprinted static assets | Cache first (the file name changes when the content does) |
| Public, non-personal GET data and images | Stale-while-revalidate with a maximum age and entry count |
| Personal or authenticated API data | Not in the HTTP cache layer; keep it in the app's own store, cleared at logout |
| POST, PUT, DELETE | Never cached; queue through the outbox if offline support is intended |

5. **Standalone behavior.** There is no browser chrome: provide in-app back navigation and a way to refresh, respect safe-area
   insets, and open external links in the system browser. Detect the mode with `matchMedia('(display-mode: standalone)')`.
6. **Install prompt.** Chromium fires `beforeinstallprompt`: keep the event and offer an install button after the user has done
   something of value, not on first load. iOS has no prompt API: show a short instruction sheet, only in iOS Safari and only
   when not already installed.

Check: DevTools → Application → Manifest shows no installability errors; with "Offline" ticked in the Service workers pane,
reload shows the shell or offline page; Lighthouse or the browser's install icon confirms the rest. Register the worker only in
production builds; a service worker in development serves stale code and wastes hours.

## Updating a service worker safely

A new worker installs alongside the old one and **waits** until every tab controlled by the old one has closed. A plain reload
does not activate it.

| Policy | Mechanism | Use when |
|---|---|---|
| Prompt to reload (default for apps) | Detect the waiting worker, show "Update available", on click send it a message to call `skipWaiting()`, then reload once on `controllerchange` | Any app with lazy-loaded code or unsaved state |
| Take over immediately | `skipWaiting()` in `install` and `clients.claim()` in `activate` | Content sites. Risk in apps: a page running old JavaScript suddenly gets new cached assets and fails loading old chunks |

Rules that prevent the classic disasters:

- Serve `/sw.js` with `Cache-Control: no-cache` and never fingerprint its file name. Browsers re-check it on navigation; a
  renamed or long-cached worker file leaves users on the old one.
- Never cache HTML cache-first without revalidation: users stay on an old app indefinitely.
- Name caches with a version and delete unknown caches in `activate`.
- Do not store personalized responses in shared caches, and on logout delete user-specific caches and local databases; on a
  shared device the next person would otherwise see the previous user's data offline.
- Do not cache opaque cross-origin responses (requests made with `no-cors`): their status cannot be read, so an error page can
  be cached as if it were the asset, and each one is charged a large padded size against quota.
- Long-lived tabs: call `registration.update()` periodically or when the tab becomes visible.
- Keep a kill switch ready. Deploying this file as `/sw.js` removes a broken worker from every client on its next check:

```js
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    for (const key of await caches.keys()) await caches.delete(key);
    await self.registration.unregister();
    for (const client of await self.clients.matchAll({ type: 'window' })) client.navigate(client.url);
  })());
});
```

  Deleting `sw.js` from the server does not help: a failed update check leaves the old worker in control. A `Clear-Site-Data:
  "storage"` response header is the server-side alternative.
- How service-worker caches interact with HTTP and CDN caching is covered in `0x:web-networking` (`http-caching.md`).

## Wrapping with Capacitor, or building with Expo

**Capacitor** puts the built web app inside a native shell with plugin access to native APIs.

- Bundle the web assets in the app. An app that only loads a remote URL in a web view fails offline and risks rejection as a
  repackaged website; it must offer something app-like.
- A Next.js app must be a static export for this, so server components that fetch at request time, server functions and route
  handlers do not exist inside the bundle. Everything dynamic goes over HTTPS to the hosted API. If the product leans heavily on
  server rendering, the wrapper is a data-layer rewrite: weigh that against a PWA or Expo.
- The API must therefore be a real, versioned API: CORS allowing the wrapper's origin, token authentication stored in the
  platform keychain through a secure-storage plugin (cookie sessions are unreliable across the web view boundary; `localStorage`
  is not a place for tokens), and backward compatibility with old app versions (`0x:api-design`, `versioning-evolution.md`).
- OAuth and social sign-in run in the system browser sheet with a redirect back to the app, not inside the web view, where
  providers block them (`0x:auth-identity`).

**Expo (React Native)** is a separate client with native UI.

- Share in a monorepo: the typed API client, validation schemas, types and pure business logic. Do not try to share components
  between Next.js and React Native at Launch stage.
- Use the managed workflow and its cloud build and submission service, so local native toolchains are not a prerequisite for
  shipping.
- Over-the-air updates can replace the JavaScript layer between store releases for fixes. Store rules do not allow using them to
  change what the app fundamentally is, and anything touching native code still needs a store build.

## Links that open the installed app

Use verified HTTPS links (universal links on iOS, app links on Android). The same URL opens the app when installed and the
website otherwise, so every linked route must exist on the web.

| | iOS | Android |
|---|---|---|
| File on the website | `/.well-known/apple-app-site-association` (JSON, no extension, no redirects) listing the app id (team id + bundle id) and path patterns | `/.well-known/assetlinks.json` listing the package name and SHA-256 signing-certificate fingerprints |
| In the app | Associated Domains entitlement `applinks:example.com` | Intent filter for the host with `android:autoVerify="true"` |
| Common failure | File behind a redirect, auth or wrong content type; the OS reads it through Apple's servers, so changes are not instant | Fingerprint of the upload key instead of the store's app-signing key |

- Check with `curl -i https://example.com/.well-known/apple-app-site-association` (expect 200, JSON, no redirect) and `adb shell
  pm get-app-links com.example.app` (expect `verified`).
- When they do not fire by design: a URL typed or pasted into the address bar; navigation within the same domain in the browser;
  a redirect not started by a tap; most in-app browsers; and on iOS after the user once chose to open that domain in the
  browser.
- Email click tracking rewrites links to the email provider's tracking domain, which is not associated with the app, so the link
  opens the browser. Use the provider's supported setup for app links on a branded tracking domain, or exclude app-bound links
  from click tracking (`0x:email-notifications`).
- In the app, map the incoming URL to a screen through the router; if the user is signed out, remember the target and continue
  to it after sign-in.
- Custom schemes (`myapp://`) are unverified, so any app can claim them: use them only where a protocol requires it. Carrying a
  link through installation ("deferred deep link") needs the store's install-referrer mechanism or a third-party service; decide
  whether it is worth it.
- Website visitors can be pointed to the app with a smart banner (`<meta name="apple-itunes-app" content="app-id=...">` on iOS).

## In-app browsers

Links tapped inside Instagram, Facebook, TikTok, LinkedIn, X, messaging apps and many email apps open in an embedded web view,
not the user's browser. For products that advertise or get shared on social platforms, this is where a large share of first
visits happen.

| Symptom | Cause | Fix |
|---|---|---|
| "Sign in with Google" shows an error about a disallowed user agent | Google blocks OAuth inside embedded web views | Offer email one-time code as an alternative; show an "Open in browser" hint when a web view is detected |
| User signs up, then is logged out when they open the site in their real browser | Separate cookie jars; the web view's storage may be discarded when it closes | Complete the critical flow in one context; send a sign-in link by email so the session can be re-established anywhere |
| Emailed magic link opens in a different browser and "does not work" | The flow started in the web view, the link opened elsewhere, and state was bound to the first context | Make links self-contained, or use a typed code instead of a link |
| Apple Pay or Google Pay button missing | Wallet availability in web views is limited and varies by app and OS version | Always render the card form; let the payment provider's element decide which wallets to show |
| Payment redirect (bank authentication, wallet app) never returns | Return lands in another browser, or the web view was closed | Restore state on the return URL from a server-side session id, not from memory or `sessionStorage`; confirm payment by webhook (`0x:payments-billing`) |
| Popups, `target="_blank"`, downloads, file upload do nothing | Web view restrictions | Full-page redirects instead of popups; offer "email me the file" |
| Autofill and password manager absent | Not integrated in the web view | Shorter sign-up, one-time codes, defer password creation |

- Detection is by user-agent substrings (for example `FBAN`, `FBAV`, `Instagram`), which are unstable. Use detection only to
  show a hint or adjust the offered sign-in methods, never to block.
- Escaping to the real browser is not reliably possible from the page, particularly on iOS. Design the first-visit flow to
  succeed inside the web view.
- Test before any paid social campaign: send the landing URL to yourself in each target app, tap it, and run sign-up through
  payment inside that browser on a real phone.

## Store review

Budget review time into every launch plan: first submissions commonly take days and may bounce more than once. Do not announce a
date on the day of submission.

What reviewers and policies check, on both stores unless noted:

- **Account deletion.** If accounts can be created, deletion must be startable inside the app; Google also requires a web URL
  where deletion can be requested without the app.
- **Privacy declarations** (Apple's privacy labels, Google's Data safety form) must match what the app and every embedded SDK
  actually collect. Inventory analytics, crash and advertising SDKs first. A privacy policy URL is mandatory
  (`0x:privacy-compliance`, `terms-policies.md`).
- **Sign-in.** Apple requires that apps offering third-party social login also offer an equivalent privacy-preserving option;
  Sign in with Apple satisfies it. Supply a working demo account in the review notes; a reviewer who cannot log in rejects.
- **Permission prompts** must explain the specific use ("to scan receipts"), and the app must work when permission is refused.
- **Tracking** across apps and sites requires Apple's tracking permission prompt.
- **Minimum functionality.** A thin wrapper around a website, placeholder content, broken links and crashes on launch are
  routine rejections.
- **User-generated content** needs reporting, blocking and moderation.
- **Payments** for digital goods must follow the store billing rules (next section).
- **Google-specific.** A current target API level, a content rating questionnaire, and for new personal developer accounts a
  closed testing period with a minimum number of testers before production access. Check the current requirements when planning
  dates.

Rejections: read the cited guideline and the reviewer's note exactly. If the reviewer misunderstood, reply in the review thread
with specifics, steps and a screen recording before changing anything. If the finding is real, fix and resubmit with a note
describing the fix. If you disagree with the reading of a guideline, use the formal appeal. Stay factual; a second reviewer
often decides differently. For urgent fixes Apple accepts expedited-review requests, sparingly. Keep the web version fully
functional so a rejection delays a channel, not the business.

## In-app purchases and store billing

The rule that decides the architecture: **digital goods and services consumed in the app** (subscriptions to app features,
credits, content unlocks) must, as a baseline, be sold through the store's billing system, which takes a commission. **Physical
goods and real-world services** (deliveries, rides, bookings) use ordinary payment processing.

- Regional and category exceptions keep changing through litigation and regulation (the US, the EU, South Korea, Japan and
  others each differ on external purchase links and alternative billing, and there are special programs for certain app
  categories). Read both stores' current payment guidelines for each storefront before designing checkout; do not rely on what
  was true last year, and get legal advice before depending on an exception.
- Common path for B2B and web-first SaaS: sell on the web, and let the app be a sign-in companion for existing customers.
  Whether the app may mention or link to web purchase depends on storefront and current rules.
- If selling in the app: use a subscription infrastructure service that wraps both stores' billing libraries, validates
  purchases server-side and sends webhooks, rather than integrating each store directly.
- One entitlement record per user in the backend, with its source (web processor, Apple, Google), updated only from
  server-to-server notifications from each source. The client never grants access from its own purchase callback. A customer who
  paid on the web must not be sold the same plan again in the app (`0x:payments-billing`, `subscriptions.md`).
- Store-billed customers cancel and get refunds through the store, not through your support team; the app must link to the
  store's subscription management, include "Restore purchases", and handle grace-period, billing-retry, refunded and revoked
  states.
- Prices come from store price tiers per country, and the store acts as seller for tax purposes on those sales; keep that
  revenue separate in reporting (`0x:pricing-monetization`).

## Rollouts, crashes and forced upgrades

A shipped binary cannot be rolled back; the only fix is a new version through review. Everything here exists to limit that
exposure.

- **Staged rollout.** Release to internal testers, then a beta group, then production by percentage. Google Play lets you set
  and halt the percentage; Apple's phased release ramps automatic updates over a week and can be paused. Advance only while
  crash and error metrics hold against the previous version.
- **Remote control.** Put risky features behind server-side flags with a kill switch (`0x:ci-cd-release`, `feature-flags.md`),
  and keep over-the-air update capability for the JavaScript layer.
- **Crash reporting** from the first build, in the same error tracker as the web where possible. Upload debug symbols and source
  maps in the build pipeline or stack traces are unreadable. Watch the crash-free rate per release, and the stores' own
  stability dashboards, since poor stability reduces store visibility.
- **Forced upgrade must be built into version 1.0**, because it cannot be added to versions already installed:
  1. The app sends its version and platform with every request (a header).
  2. At startup and resume it fetches a small config: minimum supported version, recommended version, maintenance flag, store
     URL.
  3. Below minimum: a blocking screen with a store link. Below recommended: a dismissible nudge.
  4. The API also rejects too-old clients with a distinct, documented error the app turns into the same blocking screen.
- **Support window.** Decide how long old versions stay supported and check the version distribution in analytics before raising
  the minimum. Until then, API changes are additive and fields are never repurposed.

## Ask the user

- **What must the app do that the website cannot?** It decides the whole path and its recurring cost. Default: responsive web,
  add PWA installability when repeat use is proven.
- **Which actions must work without a connection, and which must never appear to succeed offline?** Wrongly queued payments or
  bookings cause real harm. Default: reads from cache, own-data edits queued, everything involving money or shared inventory
  blocked.
- **Will digital goods be sold inside the app, and in which countries?** It determines store commission, billing integration and
  price presentation. Default: sell on the web only and confirm what the app may say about it under current rules.
- **How long are old app versions supported?** Longer windows constrain API changes. Default: the current and two previous
  releases, or six months, whichever is longer, with forced-upgrade capability from the first release.
- **Is paid social a main acquisition channel?** If so, in-app browser compatibility of sign-up and checkout is launch-blocking.
  Default: test in the top two social apps before spending.
- **Who owns the store accounts and release approvals?** Accounts should belong to the company with more than one admin, not to
  a contractor's personal identity.
