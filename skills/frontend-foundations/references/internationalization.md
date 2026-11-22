# Internationalization

Read this when: adding a second language or region, formatting dates, numbers or money, handling
users in different time zones, supporting a right-to-left script, or deciding how translations
are produced and shipped.

## Four settings, not one

Language, region formatting, currency and time zone are independent. A German speaker in the US
paying in euros exists. Conflating them is the root of most i18n bugs.

| Setting | Comes from | Never derive from |
|---|---|---|
| Language (which strings) | Explicit choice → URL → `Accept-Language` → default | IP address or country |
| Formatting locale (date and number shape) | The full locale tag in use (`en-GB`, `de-CH`) | The language alone |
| Currency | The price or transaction record; the market being sold in | The user's locale. Formatting a USD amount with the `de-DE` locale gives `1.234,56 $`, still dollars |
| Time zone | The device (`Intl.DateTimeFormat().resolvedOptions().timeZone`), stored on the profile | Locale or country |

Stage guidance: at Prototype, ship one language but do the three free things: format with
`Intl`, use logical CSS properties, and keep user-facing strings out of logic. Externalize
strings before Launch if a second language is plausible within a year; retrofitting a large
codebase is weeks.

## Formatting with Intl

```ts
const locale = 'de-CH', timeZone = 'Europe/Zurich';
new Intl.DateTimeFormat(locale, { dateStyle: 'medium', timeStyle: 'short', timeZone }).format(date);
new Intl.NumberFormat(locale, { style: 'currency', currency: order.currency }).format(amount);
new Intl.NumberFormat(locale, { notation: 'compact' }).format(15300);
new Intl.RelativeTimeFormat(locale, { numeric: 'auto' }).format(-1, 'day');   // "gestern"
new Intl.ListFormat(locale, { type: 'conjunction' }).format(names);
```

- Never assemble a date or number format by hand (`${d}/${m}/${y}`, `toFixed(2)` with a currency
  symbol). Order, separators, digit grouping, symbol position and even digits differ by locale.
  Use `dateStyle`/`timeStyle` or option bags, and `formatRange` for date ranges.
- Always pass the locale and, for dates, the `timeZone` explicitly. Formatters called without
  them use the runtime's defaults, which differ between the server and the browser: the same
  component renders two different strings and React reports a hydration mismatch. Either pass
  the user's locale and zone to both sides, or render absolute times on the client only.
- Currencies have different minor units (JPY none, most two, a few three). Store amounts as
  integer minor units with an ISO 4217 code and convert for display by the currency's exponent;
  money handling is owned by `0x:payments-billing`.
- Constructing a formatter is expensive relative to using it. Cache instances per
  locale-and-options when formatting in lists and tables.
- Do not parse localized input with `parseFloat`: `"1.234,56"` becomes `1.234`. Decide which
  decimal separators a field accepts and normalize deliberately.
- Units, percentages and compact notation are all `Intl.NumberFormat` options; plural
  categories come from `Intl.PluralRules`.

## Layouts that survive translation

- English is compact. Budget for other languages running about a third longer in sentences and
  two to three times longer in short labels (a five-letter button label is the worst case).
  Chinese, Japanese and Korean are shorter but need taller lines.
- No fixed widths or heights on anything containing text. Buttons, tabs, table headers and nav
  items size to content, wrap, or scroll; `min-width`, never `width`.
- Decide per element what happens when text does not fit: wrap (default), then scroll
  (tab bars), and truncate with an ellipsis only where the full text is available elsewhere.
- Long unbreakable words (German compounds, URLs): `overflow-wrap: anywhere`, and
  `hyphens: auto`, which works only when `lang` is set correctly.
- No text baked into images. No sentence built by concatenating styled fragments. No meaning
  carried by word position ("the red one on the left").
- Fonts: the brand typeface probably lacks Cyrillic, Greek, Arabic, Thai or CJK glyphs. Define
  fallback stacks per script and test that mixed-script lines sit acceptably; give scripts with
  tall marks (Thai, Arabic, Devanagari) more line height. Do not apply `letter-spacing` or
  forced uppercase to scripts where they break joining or do not exist.
- Pseudo-localization catches all of this before any translator is paid: generate a fake locale
  that accents every character, pads strings by about 40% and wraps them in markers
  (`[!! Šéţţîñĝš !!]`). Unbracketed text on screen is a hardcoded string; clipped brackets are a
  layout that will break in German. Run it in development and in visual tests.

## Strings as ICU messages

```json
{
  "cart.items": "{count, plural, =0 {Your cart is empty} one {# item in your cart} other {# items in your cart}}",
  "invite.sent": "{inviter} invited {invitee} to {team}",
  "legal.accept": "I accept the <terms>terms of service</terms>"
}
```

- One message per complete sentence, with named placeholders. Translators reorder words;
  concatenation (`t('you_have') + n + t('items')`) cannot be translated correctly.
- Plurals go through the message format, never `count === 1 ? ... : ...`. Languages have between
  one and six plural categories (`zero`, `one`, `two`, `few`, `many`, `other`); the library
  picks using the locale's rules. `other` is always required; `=0` and `=1` match exact numbers.
  The same applies to ordinals (`selectordinal`) and to grammatical variants (`select`).
- Rich text (links, emphasis) uses tags inside the message, mapped to components in code, so
  the translator controls where the link sits in the sentence.
- Keys name the place and purpose (`checkout.pay_button`), and are not reused across contexts:
  one English word may need two translations ("Open" as a verb and as a state).
- Fallback: regional locale → base language → default language. A missing key shows the default
  language and reports an error in production; it throws in development and CI.
- Load only the active locale's messages, and keep them out of the client bundle where server
  rendering allows. Make keys and placeholder names type-checked.
- Library defaults: `next-intl` for the Next.js App Router; FormatJS (`react-intl`) or a compiled
  catalog approach (Lingui, Paraglide) elsewhere. Keep the library the project has; the
  principles hold for all of them. Note that some popular libraries use their own plural syntax
  rather than ICU; follow their format consistently instead of mixing.
- Text produced outside the UI also needs a locale: emails, PDFs, push notifications, error
  messages. The API returns error *codes*; the client translates them. Emails use the
  recipient's stored language, not the sender's request (`0x:email-notifications`).

## Locale routing and detection

Put the locale in the URL: `/de/pricing`. Path prefixes on one domain are the default; separate
domains or subdomains per market are a business decision (local trust, separate operations), not
a technical need.

1. A URL with a locale is authoritative. Never redirect it elsewhere based on detection: shared
   links, bookmarks and crawlers must get the language the URL names.
2. Only a URL without a locale (normally just `/`) negotiates: stored user choice (cookie or
   account setting) → best match between `Accept-Language` and the supported list → default.
   Use a real matcher (for example `@formatjs/intl-localematcher`); naive string comparison
   fails on `zh-Hant-TW` or `pt` versus `pt-BR`.
3. A language switcher is visible on every page, lists languages by their own names
   ("Deutsch", "日本語") without flags, links to the *same page* in the other locale, and stores
   the choice so it wins next time.
4. Logged-in users have the locale on their profile; it drives emails and notifications.

- Do not vary the response for one URL by `Accept-Language`: it either breaks CDN caching or
  serves the wrong language from cache. Locale in the path makes the cache key correct for free.
- Decide once whether the default locale is prefixed (`/en/...`) or bare; changing it later
  breaks links. Prefixing all locales is simpler to reason about.
- Emit `<html lang>` (and `dir`) per locale, and alternate-language links between translations
  (`<link rel="alternate" hreflang="de" href="...">`, plus `x-default`), each page listing all
  its versions including itself.
- Country detection by IP is acceptable for *suggesting* a region or currency ("Shopping from
  Canada?"), never for silently switching language.

## Right-to-left

Set `dir="rtl"` on `<html>` for Arabic, Hebrew, Persian and Urdu. Flexbox, grid, tables and text
alignment then mirror automatically, provided the CSS speaks in logical directions.

| Physical (avoid) | Logical | Tailwind |
|---|---|---|
| `margin-left` / `margin-right` | `margin-inline-start` / `-end` | `ms-*` / `me-*` |
| `padding-left` / `padding-right` | `padding-inline-start` / `-end` | `ps-*` / `pe-*` |
| `left` / `right` | `inset-inline-start` / `-end` | `start-*` / `end-*` |
| `text-align: left` | `text-align: start` | `text-start` |
| `border-left`, `border-top-left-radius` | `border-inline-start`, `border-start-start-radius` | `border-s`, `rounded-ss-*` |

- Logical properties cost nothing in a left-to-right product; use them from the first commit and
  lint against the physical utilities once RTL is on the roadmap.
- Not mirrored automatically: `transform: translateX()`, absolutely positioned offsets written
  with `left`, background positions, shadows with a horizontal offset, slide-in animations.
  Handle with the `rtl:` variant or `:dir(rtl)`.
- Mirror icons that express direction (back, next, chevrons, reply, progress). Do not mirror
  logos, checkmarks, media controls, clocks, or anything depicting a real object.
- Numbers, phone numbers, email addresses, URLs and code stay left-to-right inside RTL text:
  set `dir="ltr"` on those inputs and cells.
- User-generated content can be in any direction regardless of the UI: put `dir="auto"` on
  elements and inputs that show it, and wrap inline names in `<bdi>` so a Hebrew username does
  not reorder the surrounding sentence.
- Cheap test long before translation exists: set `dir="rtl"` on `<html>` in DevTools on the
  English site. Everything that does not flip, overlaps, or points the wrong way is a bug.

## Translation workflow

1. **Extract.** No user-facing literal in components; a lint rule or the pseudo-locale enforces
   it. The default-language message file in the repository is the source of truth.
2. **Give context.** Each message gets a description: where it appears, what the placeholders
   hold, any length limit. Keep a glossary (product terms, words that must not be translated)
   and a tone note per language (formal or informal address is a brand decision in German,
   French, Spanish and others).
3. **Draft with an LLM.** With the glossary, tone note, descriptions and neighboring strings in
   the prompt, model drafts of UI strings are good. Without context they are word-for-word and
   wrong in ways that are invisible to a non-speaker.
4. **Human review, risk-ranked.** A native speaker reviews marketing pages, onboarding,
   checkout and payment, error messages that guide recovery, and anything legal. Long-tail
   settings screens can ship on reviewed-by-sample drafts with a "report a translation issue"
   link. Legal documents need review for the jurisdiction, not just the language
   (`0x:privacy-compliance`).
5. **Check in CI.** Every locale has every key; messages parse as valid ICU; placeholders and
   tags match the source; each plural message has the categories its locale requires.
6. **Handle change.** When the meaning of a source string changes, change its key (or mark the
   translations stale) so old translations are not silently kept. Do not block a release on
   translation: fall back to the default language and fill in afterwards.

Message files in the repository are enough for a few languages maintained by the team. Adopt a
translation management platform when outside translators need an editor, screenshots and
review states, or when the locale count makes pull requests unmanageable.

## Time zones

Classify every date-time value before storing it; the three kinds need different storage.

| Kind | Examples | Store | Display |
|---|---|---|---|
| Instant: a moment that happened or will happen worldwide | Created at, paid at, token expiry, a live webinar start | UTC timestamp (`timestamptz`), transmitted as ISO 8601 with `Z` | Convert to the viewer's zone with `Intl` |
| Calendar date: no time, no zone | Birthday, invoice date, due date, public holiday | A date type (`YYYY-MM-DD`) | As written; never convert |
| Local wall time in a place | A recurring 9:00 class in Berlin, shop opening hours, a reminder "at 8 every morning" | Local date-time plus an IANA zone name (`Europe/Berlin`) | Compute the instant when needed, with current zone rules |

- Store IANA zone names, never offsets. `+02:00` is wrong for half the year, and governments
  change zone rules; a future instant precomputed today can be off by an hour when it arrives.
- `new Date('2026-03-01')` is parsed as UTC midnight and displays as the previous day anywhere
  west of Greenwich. Do not push calendar dates through `Date`; keep them as strings or a
  plain-date type, and compare as strings.
- `<input type="datetime-local">` returns wall time without a zone. Combine it explicitly with
  the intended zone (the user's, or the event's), and say on screen which zone applies whenever
  two people in different zones will see the same value.
- "Add one day" is a calendar operation in a zone, not 24 hours: across a DST change, a day has
  23 or 25 hours, and some local times do not exist or occur twice.
- Run servers, databases and CI in UTC. Run the test suite under at least one other zone
  (`TZ=America/Los_Angeles`, and a half-hour-offset zone such as `Asia/Kolkata`) with a frozen
  clock; date bugs hide when developer and server share a zone.
- Any "per day" rule (daily limits, streaks, billing cutoffs, "today's" report) needs a stated
  zone: the user's, the account's or UTC.
- `Temporal` models these three kinds directly (`Instant`, `PlainDate`, `ZonedDateTime`). Use it
  when it is Baseline for the target; until then use a date library with zone support, or its
  polyfill, for arithmetic, and `Intl` for display.

## Names, addresses, phone numbers and sorting

- **Names.** One "Full name" field, plus an optional "What should we call you?" if the product
  greets people. Split given and family name only when a downstream system demands it. Do not
  assume order, a single surname, a minimum length or a Latin alphabet; do not reject
  apostrophes, hyphens or spaces; do not auto-capitalize.
- **Addresses.** Ask for the country first and adapt the rest. Region and postal code are
  optional unless the country requires them; postal codes are not numeric everywhere and some
  countries have none. Store structured fields plus the country as an ISO 3166-1 alpha-2 code.
  When delivery accuracy matters, use an address autocomplete and validation service rather
  than writing per-country rules.
- **Phone numbers.** Store in E.164 (`+14155550123`). Parse and validate with a
  libphonenumber-based library, using the user's country as the default region; length-based
  regular expressions reject valid numbers. Display in national format to same-country viewers
  and international format otherwise.
- **Sorting and comparing.** `array.sort()` without a comparator orders by UTF-16 code units:
  uppercase before lowercase, accented letters after `z`, `"10"` before `"9"`.

  ```ts
  const collator = new Intl.Collator(locale, { numeric: true, sensitivity: 'base' });
  items.sort((a, b) => collator.compare(a.name, b.name));
  ```

  Sorting done in the database follows the column's collation, which may differ from the
  browser's; sort a paginated list in one place only (`0x:postgres-database`).
- **Text operations.** Normalize to NFC before storing or comparing identifiers. Count and
  truncate by grapheme with `Intl.Segmenter`, or an emoji or accented character is cut in half.
  Case conversion is locale-dependent (`toLocaleUpperCase('tr')`); never compare identifiers by
  uppercasing with the user's locale.
- **Calendar conventions.** The first day of the week, 12- or 24-hour clocks, measurement units
  and paper sizes vary by region; take them from the locale, with a user override for units.

## Ask the user

- **Which languages and markets, and when?** Each one is ongoing translation, support, email and
  legal work, not a one-time export. Default: one language at Prototype with i18n-safe code;
  add the second only with someone able to review it.
- **Who reviews translations?** Unreviewed machine translation in checkout or legal text is a
  business risk. Default: LLM drafts everywhere, native-speaker review for marketing, checkout
  and legal before a locale is announced.
- **Formal or informal tone per language?** It cannot be changed cheaply later. Default: follow
  what direct competitors in that market do; ask the reviewer.
- **Does a market get its own currency and prices?** That is pricing, tax and payment-method
  work beyond formatting. Default: one currency until `0x:pricing-monetization` says otherwise.
- **Whose time zone governs shared things (events, deadlines, daily limits)?** Default: instants
  shown in each viewer's zone with the zone labeled; per-day rules in the account's zone.
