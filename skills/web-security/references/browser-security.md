# CSP, CORS and browser security headers

Read this when: fixing a CORS error, adding or tightening a Content Security Policy, setting security headers, deciding what may frame or be framed, adding a third-party script, wiring `postMessage` between windows, or enabling cross-origin isolation.

## Baseline header set

Send these on every response, including error pages, redirects, API routes and static files; headers set only in page code usually miss those.

| Header | Default value | Flip when |
|---|---|---|
| `Content-Security-Policy` | The strict nonce policy below on app pages; everywhere else at least `frame-ancestors 'none'; object-src 'none'; base-uri 'self'` | See the CSP sections |
| `X-Content-Type-Options` | `nosniff` | Never |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | `no-referrer` on pages whose URL carries a token (reset, share, invite); `same-origin` on admin tools |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(), payment=(), usb=()` | Allow a feature for `self`, and for a named embed origin, only where the product uses it |
| `Cross-Origin-Opener-Policy` | `same-origin` | `same-origin-allow-popups` on pages that open OAuth or payment popups which report back |
| `X-Frame-Options` | `DENY` | Legacy duplicate of `frame-ancestors`; keep the two consistent |
| `Strict-Transport-Security` | Set at the edge: `0x:web-networking` (`tls-certificates.md`) | |

Do not send `X-XSS-Protection`: the legacy filter it controlled is gone from browsers and was itself exploitable. Remove `X-Powered-By` (`poweredByHeader: false` in the Next.js config).

Static headers belong in the framework config or at the proxy or CDN (in Next.js, `headers()` in `next.config`). Only a nonce-based CSP needs per-request code.

- `nosniff` makes the declared `Content-Type` binding. A script served as `text/plain` is refused, which is the point for user uploads and the usual cause of "refused to execute script, MIME type" errors right after enabling it.
- `Permissions-Policy` syntax: `feature=()` denies everywhere; `feature=(self)` allows the page's own origin; `feature=(self "https://embed.example")` adds a framed origin, which must also be granted on the iframe's `allow` attribute. Unknown feature names only produce console warnings, so keep the list to features worth denying.

## CORS

CORS relaxes the same-origin policy so that script on another origin may read a response. It is not access
control: non-browser clients ignore it, and simple cross-origin requests are still sent and executed (only the
response is withheld), so it is not a CSRF defense either. A "CORS error" most often means the architecture
should not be cross-origin: serve the API from the app's origin, or rewrite to it, and send no CORS headers at
all. That is the default.

| Situation | Configuration |
|---|---|
| Frontend and API on the same origin | No CORS headers |
| Public API without cookies (anonymous, or a bearer token in a header) | `Access-Control-Allow-Origin: *`, never with credentials. Not for anything reachable only from an internal network |
| Cookie-authenticated API on another origin of the product (`app.` calling `api.`) | Exact-match allow-list; echo the matched origin; `Access-Control-Allow-Credentials: true`; `Vary: Origin` |
| Preview deployments with changing origins | An anchored pattern on the non-production API only, or same-origin rewrites |
| Native mobile app or server-to-server client | Nothing; CORS is a browser mechanism |

```ts
const ALLOWED = new Set(["https://app.example.com", "https://admin.example.com"]);

export function corsHeaders(origin: string | null): Record<string, string> {
  if (!origin || !ALLOWED.has(origin)) return { Vary: "Origin" };
  return {
    "Access-Control-Allow-Origin": origin,
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET,POST,PUT,PATCH,DELETE",
    "Access-Control-Allow-Headers": "content-type,authorization",
    "Access-Control-Max-Age": "7200",
    Vary: "Origin",
  };
}
```

Traps:

- Browsers refuse `*` together with credentials, so the tempting fix is to reflect whatever `Origin` arrives. That is the forbidden combination by another route: every website can then read authenticated responses. Reflect only on an exact match.
- Loose matching: `origin.endsWith("example.com")` accepts `evilexample.com`; `startsWith("https://example.com")` accepts `https://example.com.evil.net`; an unanchored regex does both. Compare whole strings.
- Allowing `null`: sandboxed iframes and `data:` documents send `Origin: null`, so allowing it allows anyone.
- Trusting every subdomain: an XSS or a takeover on any one of them inherits API access.
- Missing `Vary: Origin` when the header value depends on the request: a CDN caches one origin's response and serves it to another.
- `Access-Control-Allow-Headers: *` does not cover `Authorization`, and wildcards are not honored at all on credentialed requests. List the headers.
- The preflight (`OPTIONS`) must answer 2xx with the headers and without requiring authentication, because the browser sends no credentials on it. A redirect in answer to a preflight fails.
- Error responses and redirects need the headers too. "No Access-Control-Allow-Origin header" on a request that works in curl usually means the handler threw and the 500 came from a layer that sets no CORS headers.
- Cookies not arriving: it takes `credentials: "include"` on the client, `Access-Control-Allow-Credentials: true` on the server, and a cookie the browser is willing to send. Sibling subdomains of one registrable domain are same-site, so `SameSite=Lax` works there; different sites need `SameSite=None; Secure` and then run into third-party-cookie blocking. Keep app and API same-site.

A request is preflighted when it uses a method other than GET, HEAD or POST, a non-safelisted header such as `Authorization`, or a `Content-Type` other than form-encoded, multipart or `text/plain`; JSON requests therefore are. Browsers cap `Access-Control-Max-Age` (Chromium at two hours, Firefox at 24), and without the header a preflight is cached for only seconds.

Check both directions:

```bash
curl -si -X OPTIONS https://api.example.com/v1/items \
  -H 'Origin: https://evil.example' -H 'Access-Control-Request-Method: POST' | grep -i '^access-control'
```

The hostile origin must receive no `Access-Control-Allow-Origin`; repeat with a real origin and expect an exact echo. CSRF defenses for cookie sessions: `0x:auth-identity` (`sessions-tokens.md`).

## Framing and clickjacking

Send `Content-Security-Policy: frame-ancestors 'none'` on everything, or `'self'` if the app frames its own pages. It must be a response header: it is ignored in a `<meta>` policy and does not fall back to `default-src`. `X-Frame-Options: ALLOW-FROM` is obsolete; to allow specific embedders, list them in `frame-ancestors`.

If the product has an embeddable widget, give it its own route prefix, ideally its own origin, with a per-customer `frame-ancestors` list read from the database, and keep every other route at `'none'`. The embeddable surface must not offer one-click destructive actions on the visitor's session.

## Strict Content Security Policy

Host allow-lists in `script-src` are laborious and routinely bypassable: any allowed host that serves JSONP or an old framework build is a script gadget. Use a nonce-based policy, under which a script runs because the server marked it, not because of where it came from. Shown wrapped; send it as one line.

```text
Content-Security-Policy:
  default-src 'self';
  script-src 'nonce-RANDOM' 'strict-dynamic';
  style-src 'self' 'nonce-RANDOM';
  img-src 'self' data: blob:;
  connect-src 'self';
  object-src 'none';
  base-uri 'none';
  form-action 'self';
  frame-ancestors 'none';
  report-uri /api/csp-report
```

- The nonce is at least 128 bits from a CSPRNG, base64-encoded, fresh for every response. A reused or cached nonce is equivalent to `'unsafe-inline'`.
- `'strict-dynamic'` lets a nonced script load further scripts, which bundlers and tag managers need; with it, host sources in `script-src` are ignored.
- `object-src 'none'` and `base-uri` are not optional. Without `base-uri`, an injected `<base>` tag redirects every relative script URL.
- Inline event handlers (`onclick="..."`) and `javascript:` URLs stop working; a nonce cannot authorize them. Move them to `addEventListener`.
- Styles: a nonce covers `<style>` elements, not `style` attributes in server-rendered HTML; those need `style-src-attr 'unsafe-inline'`. `'unsafe-inline'` for styles is a tolerable compromise when a UI library requires it. In `script-src` it voids the policy, and `'unsafe-eval'` is for development only.
- `connect-src`, `img-src` and `form-action` limit where injected code can send data. Tighten them to the real destinations, and add `frame-src` for embedded providers such as payments or video.
- Pages that must control which third-party scripts run (payment pages under PCI DSS 6.4.3, pages with marketing tags where piggybacking must be blocked): omit `'strict-dynamic'`, keep the nonce for first-party scripts and list the exact vendor origins in `script-src`; restrict `connect-src`, `img-src` and `frame-src` to those vendors. Keep tag managers off those pages.

Cost: a nonce requires rendering the HTML per request, so pages under a nonce policy cannot be statically generated or cached as HTML at the CDN. Decide per route group. Dynamic, authenticated app pages get the nonce policy. Static marketing pages get a hash-based or host-based policy without a nonce, with the same `object-src`, `base-uri` and `frame-ancestors`.

Next.js pattern: generate the nonce in the proxy (called middleware before Next.js 16) and set the policy on both the forwarded request headers and the response. The framework reads the nonce from the request's CSP header and applies it to its own scripts.

```ts
// proxy.ts (Next.js 16 and later). In Next.js 15 and earlier: middleware.ts, exporting `middleware`.
import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const nonce = btoa(String.fromCharCode(...crypto.getRandomValues(new Uint8Array(16))));
  const csp = buildCsp(nonce); // the directives above; add 'unsafe-eval' to script-src in development only

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  response.headers.set("Content-Security-Policy", csp);
  return response;
}
```

Read it in the root layout with `(await headers()).get("x-nonce")` and pass `nonce` to `<Script>` components for third-party tags. Exclude static assets and prefetch requests in the matcher, as the framework's CSP guide shows; a prefetched or cached page would otherwise carry a nonce that no longer matches its header.

A `<meta http-equiv>` policy works when the host gives no header control, with limits: no `frame-ancestors`, no reporting, and it must precede every script.

## Rolling out CSP: report-only first

1. Ship the target policy as `Content-Security-Policy-Report-Only` with a reporting endpoint. Nothing is blocked.
2. Collect for one to two weeks across every flow: sign-in, checkout, OAuth, embeds, admin, links from emails. Send both `report-uri` (older, widely supported) and `report-to` with a `Reporting-Endpoints` header. The endpoint accepts `application/csp-report` and `application/reports+json`, is rate-limited, and may be a hosted collector such as the error tracker's CSP endpoint.
3. Filter noise before reading. Browser extensions inject scripts and cause most reports: drop those whose source file or blocked URI starts with `chrome-extension:`, `moz-extension:` or `safari-web-extension:`. Group the rest by directive and blocked host.
4. Fix real violations: nonce the inline scripts, replace inline handlers, add the destinations actually needed.
5. Switch the header to enforcing. Keep the next, stricter policy in Report-Only beside it; both headers can be sent at once, which is how to tighten without breakage.
6. Alert on a jump in violations after a deploy (a new script or vendor) and outside deploys (an injection attempt or a compromised third party).

Guard it in end-to-end tests by failing on any violation:

```ts
await page.addInitScript(() => {
  document.addEventListener("securitypolicyviolation", (e) => {
    console.error(`CSP_VIOLATION ${e.effectiveDirective} ${e.blockedURI}`);
  });
});
page.on("console", (msg) => {
  if (msg.text().startsWith("CSP_VIOLATION")) violations.push(msg.text());
});
```

Grade the policy text with Google's CSP Evaluator before enforcing.

## Third-party scripts and Subresource Integrity

Inventory first: every third-party origin that executes script, with its purpose, owner, pages, how it loads (direct tag or through a tag manager) and what it can see. Build the list from CSP reports and a search for script tags; delete what nobody claims. A hosted script is a standing ability for that vendor, and for whoever compromises or buys the vendor's domain, to change what users run.

| Preference | How | Limit |
|---|---|---|
| 1. Self-host | Install the package and bundle it | None; updates go through the lockfile |
| 2. Pin with SRI | A versioned URL plus `integrity` and `crossorigin="anonymous"` | Only for immutable files; the CDN must send CORS headers |
| 3. Unpinned vendor loader | Payment SDKs, tag managers and analytics loaders change on the vendor's schedule and cannot be pinned | Confine: load only on pages that need it, never on sign-in, reset or admin; constrain with CSP |

```bash
curl -s https://cdn.example.com/lib@1.2.3/lib.min.js | openssl dgst -sha384 -binary | openssl base64 -A
```

```html
<script src="https://cdn.example.com/lib@1.2.3/lib.min.js"
        integrity="sha384-BASE64_FROM_ABOVE" crossorigin="anonymous"></script>
```

A hash mismatch blocks the script. That is the intended failure, so the page must degrade without it. Payment pages carry extra script-inventory and tamper-detection duties under PCI DSS: `0x:privacy-compliance` (`pci-soc2-iso.md`).

## postMessage and embedded iframes

```ts
window.addEventListener("message", (event) => {
  if (event.origin !== "https://widget.example.com") return;
  const msg = WidgetMessage.safeParse(event.data);
  if (!msg.success) return;
  handle(msg.data);
});

frame.contentWindow?.postMessage(payload, "https://widget.example.com");
```

- Receiving: compare `event.origin` with an allow-list by exact equality. `includes`, `indexOf`, `endsWith` and unanchored patterns are the recurring bug. Then validate the shape, and never route `event.data` into an HTML sink, `eval` or `location`.
- Sending: name the target origin. `"*"` delivers the data to whatever document occupies the frame now, including after a navigation.
- A sandboxed frame without `allow-same-origin` has the origin `"null"`, indistinguishable from any other opaque origin. Check `event.source === frame.contentWindow`, or hand the frame a `MessageChannel` port at load.

Iframe sandbox: start from the bare `sandbox` attribute and add tokens one at a time.

| Token | Rule |
|---|---|
| `allow-scripts` | Usually needed |
| `allow-same-origin` | Only for content from a different origin. Combined with `allow-scripts` on same-origin content, the frame can remove its own sandbox |
| `allow-forms`, `allow-popups` | When the embedded content needs them |
| `allow-top-navigation` | Avoid: the frame can redirect the whole page to a phishing copy. Use `allow-top-navigation-by-user-activation` if navigation is required |

List embeddable providers in `frame-src`. When the product is the embedded party, treat every message from the parent as untrusted input and keep the widget on its own origin, apart from the main application's cookies.

## Trusted Types

`Content-Security-Policy: require-trusted-types-for 'script'; trusted-types app-sanitizer dompurify` makes the browser reject plain strings at DOM injection sinks (`innerHTML`, `script.src`, `eval` and similar); only values produced by a named policy pass. DOM XSS review shrinks from every sink in the codebase and its dependencies to a few policy functions.

```ts
const policy = window.trustedTypes?.createPolicy("app-sanitizer", {
  createHTML: (dirty: string) => DOMPurify.sanitize(dirty),
});
```

- Decision: adopt at Scale, for applications with a large client-side codebase and sensitive data, after a strict CSP is enforced. Skip at Prototype and Launch.
- Roll out in Report-Only like any CSP change; each violation names the offending sink with file and line. Third-party scripts that write to sinks are the main cost.
- Libraries that create their own policies (DOMPurify does) must be listed by policy name in `trusted-types`.
- Do not define a pass-through `default` policy; it re-authorizes every string. A `default` policy that sanitizes is acceptable as a migration aid.
- Browsers without support ignore the directive, so enforcing is safe everywhere and protects where supported. All major engines now ship it, Firefox and Safari only in recent versions, so users on older browsers are not covered.

## Cross-origin isolation: COOP, COEP, CORP

| Header | Set it | Effect and trap |
|---|---|---|
| `Cross-Origin-Opener-Policy: same-origin` | On documents, by default | Cuts `window.opener` links with other origins, which blocks cross-window leaks and tab hijacking. Breaks popup flows that message back; use `same-origin-allow-popups` on the pages that open them |
| `Cross-Origin-Resource-Policy` | `same-origin` on API and private file responses (`same-site` when sibling subdomains load them); `cross-origin` on assets meant to be embedded elsewhere | Stops other sites from pulling the resource into their own process through `<img>` or `<script>` |
| `Cross-Origin-Embedder-Policy: require-corp` | Only on routes that need isolation | Every cross-origin subresource must opt in through CORP or CORS or it fails to load: third-party images, embeds and scripts break |

Cross-origin isolation (`COOP: same-origin` plus `COEP: require-corp` or `credentialless` on the document) is the precondition for `SharedArrayBuffer` and high-resolution timers: multithreaded WebAssembly, in-browser video or audio processing, some in-browser databases. If the product uses none of these, do not send COEP.

If it does: scope both headers to the route that needs them (`/editor`); verify with `self.crossOriginIsolated
=== true` in the console; use redirect-based sign-in there, because popups lose their opener; trial with the
`-Report-Only` variants of both headers. `credentialless` is easier to adopt, since cross-origin requests are
sent without cookies instead of requiring CORP, but check browser support before relying on it.

## Ask the user

- **Which third-party scripts are required: analytics, chat, ads, a tag manager?** Each widens the policy and the attack surface. Default: analytics only, self-hosted or proxied through the first party, absent from sign-in, payment and admin pages.
- **Does another origin need to call the API from a browser?** It decides whether CORS exists at all. Default: no; same-origin API.
- **Should any page be embeddable on customers' sites?** It decides `frame-ancestors` and the widget design. Default: nothing is embeddable.
- **Are marketing pages statically generated, and does that matter more than a nonce policy there?** Nonces force dynamic rendering. Default: marketing stays static with a non-nonce policy; the app gets the nonce policy.
- **Do sign-in or payment flows use popups?** It decides the COOP value. Default: redirects, with `same-origin`.
