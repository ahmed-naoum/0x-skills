# Accessible forms and authentication

Read this when: building or fixing a form, validation and error messages, sign-in, sign-up or
one-time-code entry, a session timeout, or a multi-step flow such as onboarding or checkout, and
it must work with a screen reader, keyboard, voice control and for users with cognitive
disabilities.

General form mechanics (native validation attributes, submission, input types) live in
`0x:frontend-foundations` (`forms.md`). This file covers what assistive-technology users need on
top.

## Labels, hints and grouping

Every field needs a visible label that is programmatically tied to it (WCAG 1.3.1, 3.3.2, 4.1.2).
The association is what lets a screen reader say "Email, edit text" on focus, lets a voice user
say "click Email", and makes the label a click target.

```tsx
const id = useId();
<label htmlFor={id}>Work email</label>
<input id={id} name="email" type="email" autoComplete="email" required
  aria-describedby={`${id}-hint ${id}-error`} aria-invalid={Boolean(error)} />
<p id={`${id}-hint`}>We send the invoice here.</p>
<p id={`${id}-error`}>{error}</p>
```

Decision rules:

| Question | Rule | Reason |
|---|---|---|
| Label or placeholder? | Always a visible `<label>`; placeholder only for an example format, if at all | Placeholder disappears on input, usually fails contrast, and is not a reliable name |
| Floating label? | Acceptable only if it stays visible, at readable size and contrast, after input | Otherwise it is a placeholder |
| No room for a label (search box)? | Visually hidden `<label>` or `aria-label`, plus a visible, named button | The name must still exist |
| Hint text? | Element referenced by `aria-describedby`, placed between label and input | Read on focus; text placed after the input is missed by screen-magnifier users |
| Several ids in `aria-describedby`? | Order them hint first, error second; keep both elements in the DOM | Read in listed order; ids that do not exist are skipped silently |
| Radio or checkbox set? | `<fieldset>` with `<legend>` holding the question | Otherwise each option is read without the question |
| Related fields (date parts, address)? | `<fieldset>`/`<legend>`, or `role="group"` with `aria-labelledby` | Same |
| Required field? | `required` attribute plus visible text or an explained asterisk | Color or an unexplained symbol alone is not an indication |
| Mostly required fields? | Mark the optional ones "(optional)" | Less noise |
| Format constraints? | State before the field, not only in the error | 3.3.2 Labels or Instructions |

Further defaults:

- Use the right `type`, `inputMode` and `autoComplete` token on every field that collects data
  about the user (1.3.5 Identify Input Purpose, AA): `name`, `given-name`, `family-name`,
  `email`, `tel`, `street-address`, `postal-code`, `country`, `organization`, `bday`,
  `username`, `current-password`, `new-password`, `one-time-code`, `cc-name`, `cc-number`,
  `cc-exp`, `cc-csc`. Correct tokens are also what makes autofill work, which is the largest
  single help for motor and cognitive disabilities.
- Do not disable the submit button until the form is valid. A disabled button is skipped by Tab,
  explains nothing, and usually fails contrast. Leave it enabled and report errors on submit.
- Use native `<select>`, checkbox and radio unless a tested primitive replaces them. A custom
  select that is a `div` list is the most common unlabelled control in audits.
- Dates the user knows (birth date, card expiry): text fields, not a calendar. Dates the user
  picks (booking): a date picker that also accepts typing. Never a calendar as the only input.
- Do not auto-advance focus between fields (card parts, code digits) and do not submit or
  navigate when a select or radio changes (3.2.2 On Input). Unexpected context changes disorient
  screen-reader and magnifier users.
- Instructions must not depend on position or color ("fields in red", "the button on the right").

## Validation and errors

Requirements: the field in error is identified and the error described in text (3.3.1), a fix is
suggested when one is known (3.3.3), and the message reaches users who cannot see it appear
(4.1.3).

Sequence on submit with errors:

1. Keep every value the user typed. Never clear the form; clearing a password field is the only
   accepted exception.
2. Render each message next to its field, in the element already referenced by
   `aria-describedby`, and set `aria-invalid="true"` on the field.
3. Move focus:
   - Short form (up to about six fields): focus the first invalid field. The screen reader
     reads its label, state and error together.
   - Long form or multi-section page: render an error summary at the top, a heading ("There are
     3 problems") plus a list of links to each field, give the container `tabindex="-1"` and
     focus it.
4. On a full page reload (no JavaScript, server-rendered form post), prefix the document title
   with "Error:" so the first thing announced says the submission failed.

```tsx
// After a failed submit, once the errors have rendered:
useEffect(() => {
  if (!errors) return;
  const first = formRef.current?.querySelector<HTMLElement>('[aria-invalid="true"]');
  first?.focus();
}, [errors]);
```

Timing rules:

| Moment | Behavior |
|---|---|
| While typing, before the first blur | No errors. "Invalid email" after one character is noise by ear |
| On blur | Validate that field; show the error inline without moving focus |
| While correcting a field already in error | Re-validate on input so the error clears as soon as it is fixed |
| On submit | Validate everything, then the focus sequence above |
| Server-side failure (card declined, email taken) | Same rendering and focus path as client errors, not a toast |

Details that decide whether it works by ear:

- An inline error that appears while focus is elsewhere is silent unless announced. The
  focus-first-invalid step covers submit; for on-blur errors the association is enough, because
  the message is read when the user returns to the field. Do not put every inline error in an
  assertive live region: tabbing through an untouched form then shouts five alerts.
- A form-level message with no field ("Could not save, try again") goes in a `role="alert"`
  container that exists before the message is set.
- Use `aria-describedby` for errors. `aria-errormessage` is the purpose-built attribute but its
  screen-reader support has been uneven; use it only in addition, after testing.
- Native validation bubbles are inconsistent across browsers and vanish on their own. Default:
  `noValidate` on the form, keep `required`, `type` and `pattern` attributes for semantics, and
  render messages from the schema (Zod) used on the server so client and server agree.
- Message wording: what is wrong and how to fix it, in the field's own terms. "Enter a date after
  today, for example 14 03 2027", not "Invalid input". Never blame, never use only a code.
- Errors need a non-color cue: text plus an icon, since a red border alone fails 1.4.1.
- With schema-driven forms and server functions, return errors keyed by field name and feed them
  to the same components; one rendering path for both sources prevents the server error ending up
  in a toast nobody hears.

## Sign-in and sign-up

WCAG 3.3.8 Accessible Authentication (Minimum, AA) forbids requiring a cognitive function test,
which covers remembering a password, transcribing a code and solving a puzzle, unless there is an
alternative or a mechanism that does it for the user. Password managers and paste are such
mechanisms, so the rule in practice is: nothing may get in their way.

| Do | Why |
|---|---|
| Allow paste in every field, including password, confirm-email and code fields | Blocking paste fails 3.3.8 outright |
| `autoComplete="username"` and `"current-password"` on sign-in; `"new-password"` on sign-up and reset | Lets managers fill and generate |
| Keep username and password as real `<input>`s in one `<form>`, visible at the same time or in a standard two-step | Managers fail on custom or lazily mounted fields |
| One-time code as a single input with `autoComplete="one-time-code"` and `inputMode="numeric"` | Platform autofill from SMS and paste both work; six separate boxes break paste, announce six unlabeled fields, and fight screen readers |
| Offer a method with no memory or transcription: passkey, magic link, or OAuth | Satisfies the criterion by alternative |
| Show-password toggle: a `<button aria-pressed>` named "Show password" | Reduces errors for motor and cognitive disabilities |
| State password rules before the field, tied with `aria-describedby` | Not only after failure |
| Report sign-in failure in text, keep the username, focus the first field | |

Traps:

- A code sent to another device that must be typed by hand is a transcription test. It passes
  only because copy and paste or autofill is available; if the flow blocks those, it fails.
- CAPTCHA: an image-recognition puzzle is tolerated by the AA wording but locks out blind users
  unless an equivalent in another modality exists (1.1.1 requires alternative forms). Text
  distortion puzzles and "which image is rotated" tasks are cognitive tests. Default: an
  invisible or risk-based challenge that only escalates to interaction for suspicious traffic,
  and a non-puzzle fallback such as email verification. Bot defense strategy belongs to
  `0x:auth-identity` (`abuse-defense.md`).
- Security questions ("first pet's name") are memory tests with no manager support. Do not add
  them.
- Short code lifetimes and lockouts after few attempts punish slow typists and screen-reader
  users. Give codes minutes, not seconds, and make "send a new code" obvious.
- Email verification links must not expire before a user who switches devices with assistive
  technology can reasonably act.

## Session timeouts

WCAG 2.2.1 Timing Adjustable (A): a time limit set by the product must be one the user can turn
off, adjust, or extend. For extension the stated terms are: warn before expiry, allow at least
20 seconds to respond with a simple action, and allow extending at least 10 times. Exceptions:
real-time events (auctions), limits that are essential, and limits longer than 20 hours.

Implementation default at Launch:

1. Sliding sessions: activity extends the session, so the warning is rare.
2. Warn well before the 20-second minimum; a rule of thumb is 2 minutes before expiry, since a
   screen-reader user needs time to hear, understand and reach the button.
3. The warning is a modal `role="alertdialog"` that takes focus, with "Stay signed in" as the
   focused default action and the remaining time in text. Update the spoken countdown at coarse
   intervals; do not announce every second.
4. Extending is one activation: no password re-entry for a simple extension.
5. If the session does expire, preserve the work: keep form state (local draft or server-side
   draft) and restore it after re-authentication. Losing a long form to a timeout is the failure
   users report most.
6. Say up front when a flow has a limit (ticket holds, payment windows), and how long it is.

Banking-grade short timeouts are a risk decision; they are allowed, with the warning and
extension in place.

## Multi-step and payment flows

Each step must be understandable alone, because a screen-reader user perceives one step at a time
with no view of the whole.

- Unique title and heading per step with position: "Shipping address - Step 2 of 4 - Checkout".
  On step change, focus the step heading (`tabindex="-1"`), or load a new page.
- Progress indicator: an ordered list; the current step has `aria-current="step"`; completed
  steps say "completed" in text, not only with a check icon; future steps are not links.
- Back never loses data, and browser Back works: each step is a URL or history entry.
- "Next" stays enabled; validation runs on activation with the error sequence above.
- Conditional fields appear after the control that reveals them in the DOM, so the next Tab
  reaches them; do not insert content above the user's position.
- Async steps (address lookup, shipping rates, promo code): announce the result in a status
  region ("Code applied, total is now $84"), and keep focus where it was.
- Order summary and totals that update live need the same announcement; a silent price change
  before payment is both an accessibility and a trust failure.
- The submit button during processing: keep it focusable (`aria-disabled="true"`, handler guards
  against double submit), change its text to "Processing...", and announce completion or failure.
  On success, navigate to a confirmation page whose heading takes focus.

Payment specifics:

- Default to the provider's hosted checkout page or embedded payment element. The vendor
  maintains its accessibility and tests it with assistive technology; a hand-built card form
  does not get that. Ask the vendor for its conformance report when an enterprise buyer asks for
  the product's.
- Embedded fields are iframes: the surrounding page still owns the heading, the visible labels
  or group label around the element, the error text returned by the SDK (render it in an
  associated, announced element), and focus after failure.
- Hand-built card fields, if unavoidable: one input per datum with labels and `cc-*`
  autocomplete tokens, no auto-tab between number, expiry and CVC, formatting that still accepts
  pasted digits with or without spaces, and no card-brand information conveyed by a logo alone.
- Bank authentication challenges (3-D Secure) open third-party frames. Give the iframe a `title`,
  move focus into it, and return focus to the result message when it closes.
- Wallet buttons need accessible names ("Pay with ...") and keyboard operation; test the ones
  rendered by SDKs instead of assuming.

## Redundant entry and review before submit

WCAG 3.3.7 Redundant Entry (A, new in 2.2): information the user already entered in the same
process is auto-populated or available to select, not asked again. Exceptions: re-entry that is
essential, needed for security, or data that is no longer valid.

| Pattern | Fix |
|---|---|
| Billing address after shipping address | "Same as shipping" checked by default |
| Email asked at step 1 and again at account creation | Prefill, editable |
| "Confirm email" field | Remove it; show the address for review instead. A confirm field with paste blocked fails twice |
| Returning after an error or timeout | Restore every field |
| Search or filter values lost between pages of results | Carry them in the URL |

"Confirm password" on password creation is allowed (security), but a show-password toggle is the
better tool.

WCAG 3.3.4 Error Prevention (AA) applies to submissions that create legal or financial
commitments, or modify or delete user data. At least one of: the action is reversible, the input
is checked and the user can correct it, or a review-and-confirm step precedes the final submit.

- Checkout, plan changes, anything billed: a review step showing every entered value with an
  "Edit" link per section that returns to the review afterwards.
- Destructive actions (delete account, remove data): prefer undo with a grace period over a
  confirmation dialog; where undo is impossible, a confirmation that names the object and has
  focus on Cancel.
- "Type DELETE to confirm" is a transcription task; acceptable only with paste allowed and for
  truly irreversible actions.

## Checks

- Click each label: focus moves to its field. In the accessibility pane each field has a name;
  each radio or checkbox group has a group name.
- Submit the empty form with a screen reader running: the failure is announced, focus lands on
  the first error or the summary, and each field reads label, required state and error.
- Fix one field: its error disappears and `aria-invalid` is removed.
- A password manager fills sign-in and offers to save on sign-up; paste works in every field,
  including the one-time code.
- Browser autofill completes name, email, address and card fields correctly.
- Let the session approach expiry: the warning takes focus, one key press extends, and after a
  forced expiry the form content is restored.
- Complete checkout or the main multi-step flow with keyboard only and again with a screen
  reader, including a deliberately declined payment.
- No step asks for data already given earlier in the same flow.

## Ask the user

- **How long may a session last, and is an "extend" prompt acceptable to your security
  requirements?** It trades account risk against lockouts for slow users. Default: sliding
  session with a warning dialog and unlimited extensions while the user is present.
- **Which sign-in methods will exist besides a password?** One memory-free method is needed for
  3.3.8 by alternative. Default: magic link or passkey alongside password, paste never blocked.
- **Is a CAPTCHA required, and where?** It is the element most likely to lock users out. Default:
  none until abuse appears, then an invisible risk-based challenge with a non-puzzle fallback.
- **Hosted checkout or custom payment form?** Custom forms move the accessibility burden onto
  the product. Default: the payment provider's hosted or embedded checkout.
- **Is a review step acceptable before purchase and plan changes?** It adds a screen and
  satisfies error prevention. Default: yes for anything that charges money or deletes data.
