# Time, time zones and text encoding

Read this when: timestamps or scheduled jobs are off by an hour or a day, a job ran twice or not at
all around a clock change, tokens or certificates are rejected as expired or not yet valid,
durations come out negative, text shows as `Ã©` or `�`, or string length, comparison or uniqueness
behaves unexpectedly with accents and emoji.

## Four kinds of time data

Most time bugs come from storing one kind as another. Decide the kind before choosing a type.

| Kind | Examples | Store as | Trap |
|---|---|---|---|
| Instant: something happened or will happen at one moment everywhere | `created_at`, `paid_at`, token expiry | Postgres `timestamptz`; on the wire ISO 8601 with `Z` or an offset | `timestamp` without time zone stores digits with no meaning; the reader guesses the zone |
| Civil date: a calendar day with no time | birthday, invoice date, due date | `date` | Storing it as midnight UTC shows the previous day to every user west of Greenwich |
| Local wall time in a place | "opens 09:00", "meeting 14:00 in Berlin next June", a recurring report | local date and time plus an IANA zone name; compute the instant when needed | Converting a future local time to UTC now bakes in today's rules; they may change before the date arrives |
| Duration | timeout, subscription length | a number with a unit, or a calendar interval | "1 month" and "1 day" are not fixed lengths |

Rules for instants:

- Store and compute in UTC. Convert to a zone only at the edges: parsing input from a person and
  formatting output for a person.
- `timestamptz` does not store a zone. It stores the instant and renders it in the session's
  `TimeZone`. Keep the application's database sessions in UTC so results do not depend on a
  server setting.
- Anything "per day" needs a named zone: decide whose day (the account's, the business's) and
  bucket with it, for example `date_trunc('day', created_at AT TIME ZONE 'Europe/Berlin')`.
  `AT TIME ZONE` turns a `timestamptz` into a zoneless local timestamp and the reverse; applying
  it twice or to the wrong type shifts the value by the offset.
- JavaScript: `new Date('2026-03-08')` is parsed as UTC midnight, `new Date('2026-03-08T00:00')`
  as local time. Do not pass civil dates through `Date`; keep them as strings or use a date type.
- Epoch values: a date in January 1970 means seconds were read as milliseconds; a year tens of
  thousands of years ahead means the reverse.
- Never do zone arithmetic by adding hours. Use the platform's zone-aware API (`Intl`, the
  Temporal API where the runtime has it, or a maintained library) with zone names.
- Rendering on the server needs the user's zone from their profile or a cookie; the server's
  zone is never the right answer.

## Servers in UTC, clocks synced

```bash
timedatectl                          # zone, "System clock synchronized", "NTP service"
sudo timedatectl set-timezone UTC    # then restart long-running services; they read the zone at start
chronyc tracking                     # with chrony: current offset and drift
timedatectl timesync-status          # with systemd-timesyncd
```

- UTC on every host makes logs from different machines line up, removes daylight-saving gaps and
  repeats from host-level schedules, and makes `date` output unambiguous. Container images are
  UTC unless changed; leave them.
- Run exactly one time-sync service. `systemd-timesyncd` is enough for most hosts; chrony copes
  better with virtual machines that pause or drift. On a large cloud, point it at the provider's
  own time service.
- If outbound traffic is filtered, NTP (UDP port 123) to the chosen servers must be allowed, or
  the clock drifts with no error anywhere.
- Containers use the host's clock. A wrong time inside a container is fixed on the host.

A drifting clock rarely announces itself as a clock problem:

| Symptom | Mechanism |
|---|---|
| TLS errors "certificate is not yet valid" or "expired" for a good certificate | Validity is checked against the local clock |
| Tokens rejected as expired or "used before issued" | `exp`, `nbf`, `iat` compared across machines |
| Cloud API calls fail with a signature or "request time too skewed" error | Signed requests carry a timestamp with a tolerance of minutes |
| One-time codes from an authenticator app stop working | Codes are derived from 30-second time steps |
| `apt-get update` says a release file "is not valid yet" | Repository metadata is timestamped |
| Log lines from two hosts appear in the wrong order | Each stamped by its own clock |

When any of these appears on one machine only, check `timedatectl` before debugging the protocol.
A virtual machine restored from a snapshot or resumed from suspend can be off by hours until the
sync service steps it.

## Zone names, not offsets

An offset such as `+02:00` is a fact about one instant. A zone such as `Europe/Berlin` is the
rule that produces the offset for any instant, including after the next clock change.

- Store the IANA zone name for each user, account or location. Obtain it in the browser with
  `Intl.DateTimeFormat().resolvedOptions().timeZone`; let the user override it.
- Never store or accept abbreviations (`CST`, `IST`, `EST`): several are ambiguous and none
  carries daylight-saving rules.
- Validate zone names at the boundary. Constructing `new Intl.DateTimeFormat('en', { timeZone })`
  throws a `RangeError` for an unknown name; Postgres lists its names in `pg_timezone_names`.
- Names get renamed (`Europe/Kiev` became `Europe/Kyiv`); old names stay valid as aliases, and
  different runtimes report either. Do not compare zone names as plain strings to decide whether
  two users share a zone.
- For a future local event, store local date-time plus zone as the source of truth. A computed
  UTC instant may be kept beside it for indexing, and must be recomputed when zone rules change.

Zone rules are data that changes: governments move or abolish daylight saving with months, and
sometimes weeks, of notice. Each layer carries its own copy:

| Layer | Where the zone data comes from | Kept current by |
|---|---|---|
| OS tools, cron, systemd, most C programs | the `tzdata` package | routine package updates |
| Node.js | bundled with the runtime's internationalization data; `process.versions.tz` shows the version | runtime upgrades |
| Postgres | the system's or its own bundled copy, depending on the build | minor version and OS updates |
| Browsers | shipped with the browser | the user's updates |
| Minimal container images | often absent | installing `tzdata` in the image when zone conversion happens there |

A missing zone database fails quietly in some runtimes (an unknown `TZ` is treated as UTC) and
loudly in others ("unknown time zone"). When server and browser disagree about a future time
right after a rule change, compare zone data versions before suspecting the code.

## Daylight saving and recurring local schedules

Two things happen on change days. In the spring gap an hour of local time does not exist (02:30
never occurs). In the autumn overlap an hour occurs twice (01:30 happens two times, with
different offsets). A local day is then 23 or 25 hours long.

| Requirement | Do | Not |
|---|---|---|
| Housekeeping at a quiet hour (backups, cleanup) | Schedule in UTC on the host | Local time on the host: the job is skipped or doubled once a year |
| "Every day at 09:00 for this customer" | Keep the rule (09:00, zone name). Compute each next run from the rule: next local date at 09:00 in the zone, converted to an instant | `previous_run + 24 hours`: it drifts by an hour after each change |
| "Start of the user's day" | Ask the zone library for the start of the day | Setting hours to 0: in some zones the change happens at midnight and 00:00 does not exist that day |
| A local time that falls in the gap | Run at the first valid time after it | Skip silently |
| A local time that falls in the overlap | Use the first occurrence, and make the job idempotent per (job, local date) so a second firing is a no-op | Run twice |
| Add a day, month or year to a date | Calendar arithmetic in the zone | Adding 86,400 seconds; "one month after January 31" needs a stated rule |
| Hourly rates over a local day | Divide by the day's real length | Assume 24 |

Further traps:

- Offsets are not whole hours everywhere (India is +05:30, Nepal +05:45), and regions change
  clocks on different dates, so the gap between two zones itself shifts for a few weeks a year.
- Avoid scheduling local-time jobs between 01:00 and 03:00 in zones with daylight saving.
- Host schedulers: `OnCalendar` in systemd accepts a zone name after the time; cron uses the
  host's zone. With hosts in UTC, per-customer local schedules belong in the application's job
  system (`0x:backend-architecture`), not in host timers.
- Tests: run the suite once under UTC and once under a zone with daylight saving
  (`TZ=America/New_York`), and include cases dated on the change days with a fake clock. Code
  that passes only on a UTC CI machine has not been tested.

## Monotonic versus wall-clock time

The wall clock can be stepped forward or backward by time sync, an administrator or a resumed
virtual machine. A monotonic clock only moves forward and has no relation to calendar time.

| Purpose | Clock | APIs |
|---|---|---|
| Measuring elapsed time, timeouts, retry backoff, rate limiting within one process | Monotonic | `performance.now()`, `process.hrtime.bigint()` in Node; `time.monotonic()` in Python; `time.Since` in Go |
| Timestamps shown to people, stored expiry, anything compared across processes or restarts | Wall clock in UTC | `Date.now()`, the database's `now()` |

- `Date.now() - start` as a duration is the common bug: usually right, occasionally negative or
  hours long, and it then trips alerts, timeouts and billing by duration.
- Monotonic readings mean nothing outside the process that took them. Do not store or send them.
- Between services, pass a remaining time budget ("2 seconds left") rather than an absolute
  deadline, or allow for skew when comparing an absolute one.
- Postgres `now()` is the transaction's start time and does not advance inside a transaction;
  `clock_timestamp()` does. A long transaction that stamps rows with `now()` writes times that
  look out of order.

## Clock skew between machines

Assume two healthy servers differ by milliseconds to tens of milliseconds, a server with broken
sync by seconds or minutes, and users' devices by anything.

- Pick one clock per decision. When several app servers write expiry or ordering timestamps, use
  the database's clock (`now()` in the statement) rather than each server's.
- Never use a client-supplied timestamp for ordering, security or billing. Record the server's
  receive time; keep the client's value only as information.
- Validate token times with a small tolerance (30 to 60 seconds is common) using the library's
  clock-tolerance option, not by widening lifetimes.
- When verifying signed webhooks, enforce the timestamp tolerance the provider documents
  (minutes), which presumes the server's clock is right.
- Do not resolve concurrent writes by "latest timestamp wins" across machines: the machine with
  the fast clock silently wins every time. Use a version column or a database sequence
  (`0x:postgres-database`).
- A lock with an expiry time is only as safe as the clocks and pauses involved; correctness
  needs a fencing token checked by the resource (`0x:backend-architecture`).
- Incremental sync by "changed since my last timestamp" misses rows committed late or stamped by
  a slower clock. Re-read an overlap window and deduplicate, or use a server-issued cursor.
- Time-ordered identifiers (UUID version 7, ULID) sort approximately by creation time. Treat
  that as a convenience for index locality, not as a guaranteed order across machines.

## UTF-8 end to end

Text is bytes plus an agreed encoding, and every hop must agree: source files, the HTTP
`Content-Type` header (`charset=utf-8`), `<meta charset="utf-8">` early in the document, the
database's encoding and the connection's, files imported and exported, and the process locale.

| Layer | Check | Trap |
|---|---|---|
| Postgres | `SHOW server_encoding; SHOW client_encoding;` both `UTF8` | A database created as `SQL_ASCII` accepts any bytes and validates nothing |
| MySQL | character set `utf8mb4` | `utf8` there is a three-byte subset that cannot store emoji |
| Process locale | `locale`; in units and containers set `LANG=C.UTF-8` | cron, systemd and minimal images run in the `C` locale, where some tools and runtimes treat non-ASCII as errors or `?` |
| CSV for spreadsheets | Excel assumes a legacy code page unless the file starts with a byte-order mark | The same mark breaks JSON parsers, shebang lines and the first column name on import; add it only for that export |
| Streams | Decode with a streaming decoder (`TextDecoder` with `stream: true`) | Decoding chunk by chunk splits multi-byte characters at chunk borders |
| Postgres text | Strip NUL (`\0`) at input | Postgres rejects it with an "invalid byte sequence" error |

Diagnose mojibake from what it looks like:

| Seen instead of `é` or `’` | What happened | Recoverable |
|---|---|---|
| `Ã©`, `â€™` | UTF-8 bytes were decoded as Latin-1 or Windows-1252 | Yes: the bytes are intact or can be restored by reversing the step |
| `ÃƒÂ©` | The same mistake applied twice | Yes, by reversing twice |
| `�` (U+FFFD) | Bytes in a legacy encoding were decoded as UTF-8 | Not once saved; re-import from the original |
| `?` | Converted to an encoding that lacks the character | No; re-import |
| `é` shown literally | JSON-encoded twice | Yes; fix the double encoding |

Find the hop by looking at bytes rather than rendered text:

```bash
printf 'é' | xxd                 # c3 a9 = UTF-8; e9 = Latin-1; c3 83 c2 a9 = double-encoded
file -i export.csv               # guess a file's encoding
iconv -f UTF-8 -t UTF-8 export.csv > /dev/null       # fails at the first invalid sequence
iconv -f WINDOWS-1252 -t UTF-8 legacy.csv > clean.csv
```

In Postgres, `SELECT encode(convert_to(col, 'UTF8'), 'hex')` shows what is stored. If the stored
bytes are right, the fault is on the read path (connection encoding, response header). If they
are wrong, it is on the write path, and stored rows need a one-time repair after the cause is
fixed: on a copy first, only on rows matching the corruption pattern, with a backup. Do not
patch the display layer to reverse the damage; it corrupts the rows that were correct.

Cutting a string by bytes or by UTF-16 code units can split a character and leave an invalid
sequence that later becomes `�`. Truncate on character boundaries.

## Normalization, length and case

**Normalization.** The same visible text can be different code points: `é` is U+00E9 or `e`
followed by U+0301. The two are unequal as strings, sort apart, and both fit in a unique index.
Decomposed forms arrive from macOS file names, some keyboards and pasted text.

- Normalize free text to NFC at the input boundary (`s.normalize('NFC')`) before validation,
  storage and comparison.
- For identifiers (usernames, slugs, tags) apply a stricter canonical form: NFKC, case folding
  and a restricted character set, stored in its own column with the unique index
  (`0x:auth-identity` covers look-alike abuse). Do not apply NFKC to free text: it rewrites
  ligatures, superscripts and full-width forms.
- Passwords: apply the same normalization when setting and when verifying, or a user is locked
  out when their device changes how it composes a character.
- Invisible characters survive naive trimming: zero-width space and joiners, a byte-order mark
  in the middle of concatenated files, non-breaking spaces pasted into env files and config.
  When two strings look equal and compare unequal, dump their code points.

**Length** has four answers; pick the one the limit is about.

| Measure | Example: a family emoji | Used by |
|---|---|---|
| Bytes in UTF-8 | 25 | Storage and protocol limits, index size limits, password hash input limits |
| UTF-16 code units | 11 | JavaScript `.length` |
| Code points | 7 | Postgres `char_length` and `varchar(n)`; `[...s].length` in JavaScript |
| Grapheme clusters | 1 | What a person counts; `Intl.Segmenter` with `granularity: 'grapheme'` |

A client check on `.length` and a database `varchar(n)` disagree for any text outside the basic
plane, so valid input is rejected or an insert fails after validation passed. Define user-facing
limits in one measure, enforce the same measure on both sides, and truncate on grapheme
boundaries so an emoji or accented letter is never cut in half.

**Case.** Lowercasing is language-dependent and is not the same as case-insensitive comparison:
German `ß` uppercases to `SS`, and in Turkish locales `I` lowercases to dotless `ı`.

- For matching (emails, usernames, tags), compare a canonical form computed without locale
  rules, and enforce uniqueness in the database: a unique index on `lower(email)`, the `citext`
  type, or a case-insensitive collation. A check in application code alone loses the race.
- In runtimes whose default case conversion follows the process locale, pass an explicit
  invariant locale for identifiers; otherwise behavior changes with the server's `LANG`.
- For display sorting use a collator (`Intl.Collator`) with the user's locale. Byte order puts
  `Z` before `a` and accented letters after everything.
- Database sort order comes from the collation, which Postgres usually takes from the operating
  system's C library. Moving a data directory to an OS release with different collation rules
  silently invalidates indexes on text columns until they are rebuilt. Plan for it in any OS
  upgrade or host replacement that carries the data files across (`0x:postgres-database`).

## Ask the user

- **Whose day counts for daily reports, limits and billing periods: UTC, the company's zone or
  each customer's?** The numbers differ at every boundary. Default: each account's zone for what
  the customer sees, UTC for internal metrics.
- **Are there users in more than one time zone, or will there be?** It decides whether a zone
  must be stored per user now. Default: yes; store the IANA name from the first signup.
- **When a scheduled local time does not exist or occurs twice on a clock-change day, what
  should happen?** It is a product rule, especially for reminders and charges. Default: run
  once, at the first valid time.
- **Is there existing data or are there import files in an older encoding?** That needs a
  one-time conversion and a decision about unrecoverable characters. Default: convert at import,
  reject files that are not valid UTF-8 with a clear message.
- **Which characters are allowed in usernames and other identifiers?** Wider sets need more
  spoofing defenses. Default: lowercase ASCII letters, digits and hyphens for identifiers; any
  text for display names.
