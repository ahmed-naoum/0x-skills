# Forms

Read this when: building or fixing any form: sign-up, login, checkout, settings, search, a
multi-step flow, an editor that must not lose work, or a field that brings up the wrong keyboard
or will not autofill.

## The base every form starts from

```html
<form method="post" action="/account/profile">
  <label for="email">Email</label>
  <input id="email" name="email" type="email" autocomplete="email" required
         aria-describedby="email-error">
  <p id="email-error" role="alert" hidden></p>
  <button type="submit">Save</button>
</form>
```

- A real `<form>` with `action` and `method`, `name` on every field, and a submit button. This
  submits on Enter, on the mobile keyboard's Go key, with password managers, and before or
  without JavaScript. A framework's server-function forms (`<form action={fn}>` in Next.js) keep
  that property; an `onClick` handler on a button that gathers state does not. Wiring is in
  `0x:react-nextjs`.
- Every field has a visible `<label>` tied by `for`/`id` (or wrapping). A placeholder is not a
  label: it disappears on typing, is low-contrast, and is not reliably announced.
- Group radios and related checkboxes in `<fieldset>` with a `<legend>`.
- Buttons that do not submit need `type="button"`. A form with several submit buttons
  distinguishes them by `name`/`value` or `formaction`.
- `method="get"` for search and filters, so the state lives in a shareable URL. `post` for
  mutations, answered with a redirect (303) so reload and back do not resubmit.
- `disabled` fields are not submitted and cannot be focused; `readonly` fields are submitted.
  Unchecked checkboxes send nothing at all.
- Mark what is optional rather than starring everything required, and remove fields that are
  not needed now: each one costs completions.

## Types, autocomplete and keyboards

`type` picks validation and widget, `inputmode` picks the on-screen keyboard, `autocomplete`
tells browsers and password managers what to fill. Getting `autocomplete` right is the cheapest
conversion improvement on a phone.

| Field | Attributes |
|---|---|
| Email | `type="email" autocomplete="email" autocapitalize="none" spellcheck="false"` |
| Login identifier | `autocomplete="username"` (plus `type="email"` if it is an email) |
| Password, login | `type="password" autocomplete="current-password"` |
| Password, sign-up or change | `type="password" autocomplete="new-password"` (triggers the generator) |
| One-time code | `type="text" inputmode="numeric" autocomplete="one-time-code"` in **one** input |
| Full name | `autocomplete="name"`; if split, `given-name` and `family-name` |
| Phone | `type="tel" autocomplete="tel"` |
| Street, city, region, postal code, country | `street-address` (or `address-line1`/`2`), `address-level2`, `address-level1`, `postal-code`, `country` or `country-name` |
| Card (only if not using hosted fields) | `cc-name`, `cc-number`, `cc-exp`, `cc-csc`, each with `inputmode="numeric"` except the name |
| Whole number that is an identifier (code, ZIP where numeric, account number) | `type="text" inputmode="numeric" pattern="[0-9]*"` |
| Decimal amount | `type="text" inputmode="decimal"`, parsed and validated explicitly |
| Quantity with steppers | `type="number" min step` |
| Search | `type="search" enterkeyhint="search"` |
| URL | `type="url" autocapitalize="none"` |
| Date near today | `type="date"` with `min`/`max` |
| Date of birth | Three inputs (`bday-day`, `bday-month`, `bday-year`) or one text field with a stated format |

Traps:

- `type="number"` is for quantities only. For identifiers it drops leading zeros, accepts `e`,
  `+` and `-`, changes value on scroll wheel in some browsers, and returns an empty string for
  anything it cannot parse. Postal codes contain letters in many countries: use plain text
  unless the country is known.
- A six-box OTP widget breaks SMS autofill, paste and password managers unless built with great
  care. One input with `autocomplete="one-time-code"` and letter-spacing styled to look
  segmented does everything.
- Do not set `autocomplete="off"` on login or address fields: browsers ignore it for credentials
  and it only breaks legitimate autofill. Do not block paste in any field.
- Password managers match on stable `name`/`id`/`autocomplete` and expect username and password
  in the same `<form>`. A two-step login should keep a (possibly hidden) username field with
  `autocomplete="username"` on the password step.
- Form controls must have a computed font size of at least 16px or iOS zooms the page on focus.
- `enterkeyhint` (`next`, `done`, `send`, `search`) labels the keyboard's action key.
- Card fields: prefer the payment provider's hosted fields over raw inputs
  (`0x:payments-billing`). Passkey autofill: `0x:auth-identity`.

## Validation: when, where and what to show

The server always validates; it is the only validation that counts. Client validation exists to
save the user a round trip.

| Moment | Do |
|---|---|
| While typing in an untouched field | Nothing. Do not show "invalid email" after the first character |
| On blur of a field that has content | Validate that field; show its error beside it |
| While typing in a field already showing an error | Re-validate on each input, so the error clears the moment it is fixed |
| On submit | Validate everything; keep all values; move focus to the first invalid field; for long forms also show a summary at the top linking to each field |
| Server responds with field errors | Render them through the same per-field slots; never as a single toast |

- Do not disable the submit button until the form is valid. A disabled button cannot say what is
  wrong; let the user submit and show the errors.
- Each error sits next to its field, is linked with `aria-describedby`, sets
  `aria-invalid="true"` on the input, and says how to fix it ("Enter a date after today", not
  "Invalid input"). Color alone is not an indicator. Announcement details are in
  `0x:accessibility`.
- Native constraints (`required`, `type`, `minlength`, `pattern`, `min`/`max`) give free
  validation before JS loads. If custom messages are rendered by JS, add `novalidate` to the
  form in JS (not in the HTML) so the unhydrated form still has browser validation. Style with
  `:user-invalid`, never `:invalid`, which matches before the user has done anything.
- Async checks (username available): debounce, abort the previous request, show a pending hint,
  and treat the answer as advisory. Uniqueness is enforced by a database constraint, and the
  submit handler must handle its violation.
- The server returns the same shape for every form: HTTP 400 or 422 with
  `{ fieldErrors: { email: ["..."] }, formError?: "..." }`, and the client maps keys to fields.
  A non-field error (rate limited, payment declined) goes in a form-level alert near the submit
  button.
- On error, never clear the form. Password fields may be emptied; nothing else.
- Normalize on the server (trim, lowercase emails, strip spaces in card and phone numbers)
  rather than rejecting formats a human would call correct.

## One schema for client and server

Define the rules once, in a module both sides import; the type falls out of it. Two hand-written
copies drift within a month.

```ts
// profile.schema.ts — no server-only imports in this file
export const ProfileSchema = z.object({
  name: z.string().trim().min(1, 'Enter your name').max(100),
  age: z.coerce.number().int().min(13, 'You must be 13 or older'),
  newsletter: z.literal('on').optional(),
});
export type Profile = z.infer<typeof ProfileSchema>;

// server
const parsed = ProfileSchema.safeParse(Object.fromEntries(formData));
if (!parsed.success) return { fieldErrors: z.flattenError(parsed.error).fieldErrors };
```

- `FormData` values are strings or files. Coerce numbers and dates explicitly; a checkbox is
  `'on'` or absent; an empty optional text field arrives as `''`, not `undefined`, so map empty
  strings to `undefined` before optional rules. `Object.fromEntries` keeps only the last value of
  a repeated name: use `formData.getAll('tags')` for multi-selects and checkbox groups.
- `z.flattenError` is the current Zod API; older major versions use `error.flatten()`. Follow the
  version installed.
- Rules that need the database or secrets (uniqueness, "current password is correct", coupon
  validity) live only on the server, added with `.refine`/`superRefine` on an extended schema
  there. The shared module must stay free of server imports or it will pull them into the
  client bundle.
- The client uses the same schema through the form library's resolver, or directly on blur for
  uncontrolled forms. Error messages live in the schema, or as keys to translate
  (`internationalization.md`).
- Greenfield default in React: uncontrolled fields with the framework's form action and
  `useActionState` for simple forms; a form library (React Hook Form with its Zod resolver, or
  Conform for progressive enhancement) once there are dependent fields, field arrays or many
  inputs. Keep the library the project already has.

## Double submits and pending state

A disabled button is a courtesy; it does not make the operation safe. Enter key repeats, a
retry after a timeout, the back button and a flaky network all resubmit.

1. In the `submit` handler (not the button's `click` handler, where disabling can cancel the
   submission), set a pending flag synchronously and ignore further submits while it is set.
2. Show pending on the button itself: disabled or `aria-disabled`, label changed ("Saving…"),
   width unchanged. React exposes this as `useFormStatus().pending` or the pending value from
   `useActionState`.
3. Clear pending in `finally`. On error the form is usable again with values intact.
4. For anything that creates or charges, make the server idempotent: render a hidden field with
   a UUID generated when the form is first shown, and have the server return the original result
   for a repeated key. Mechanics are in `0x:api-design` (`idempotency-rate-limits.md`).
5. After success, navigate or replace the form with a confirmation; a form left on screen
   invites a second submit.

If the request can take more than about a second, say what is happening; past ten seconds, show
progress or move the work to a background job and report completion.

## Keeping what the user typed

| Event | What happens by default | Make it work |
|---|---|---|
| Reload, or back to the page | Browsers restore field values for fields present in the initial HTML with stable `name`/`id` | Do not set `autocomplete="off"` on the form; in React, controlled inputs initialized from state overwrite the restored value on hydration, so use `defaultValue`/uncontrolled inputs or read the DOM value on mount |
| Back/forward cache restore | The whole page comes back as it was, JS state included | Avoid `unload` handlers, which disable it; refresh stale data on `pageshow` when `event.persisted` |
| Phone switches apps (to read an SMS code or copy a password) | The OS may discard the tab; returning reloads the page | Write a draft to `sessionStorage` on input (debounced) and on `visibilitychange`; restore on load; clear on success |
| Server-side validation error | A full-page response re-renders the form | Return the submitted values and render them back |
| Session expired on submit | 401; naive handling redirects to login and drops the data | Keep the form mounted, re-authenticate in a dialog or new tab, resubmit; or stash the draft and restore after login |
| Filters and search inputs | Lost on navigation | Keep them in the URL query string |

Never persist passwords, card data or one-time codes to storage. Key drafts by form and record
id, version them, and expire them.

## Preventing lost work

Match the protection to the effort at risk:

| Form | Protection |
|---|---|
| Under a minute to refill (login, short settings) | Browser restoration is enough |
| Long text or many fields (applications, support tickets, reviews) | Local draft as above, restored with a visible "Draft restored — discard?" note |
| Documents and records edited over time | Autosave to the server: debounce 1–2 s after the last change, also on blur and on `visibilitychange`; show a status ("Saving…", "Saved", "Offline — changes kept on this device"); send a version or `updatedAt` so a concurrent edit is detected instead of overwritten (`0x:api-design`) |

- Autosave and an explicit Save button answer different expectations; do not autosave a form
  whose submission has consequences (sending, publishing, paying). Autosave the draft, keep the
  final action explicit.
- Unsaved-changes warning: register `beforeunload` only while the form is dirty and remove it
  when clean. The handler calls `event.preventDefault()`; the browser shows its own generic text.
  It does not fire reliably on mobile and never covers in-app (client-side) navigation, so it is
  a supplement to drafts, not a replacement.
- Client-side route changes need the router's own guard or a confirmation dialog on the links
  that leave; see `0x:react-nextjs`.
- Destructive actions inside an editor (delete, discard draft) get an undo rather than a
  confirm dialog where feasible.

## Multi-step forms

Use steps when the form is long enough to intimidate, when later questions depend on earlier
answers, or when partial completion has value. Otherwise one page is faster.

- Each step is its own `<form>` with its own schema; the full schema is their composition
  (`StepOne.extend(StepTwo.shape)` or a merge), validated again on the server at the final
  submit. Never trust step validity remembered by the client.
- The step is in the URL (a route segment or `?step=2`). Back and forward buttons then move
  between steps, reload stays on the step, and a step can be linked from an email.
- Going back never loses later answers. Store the accumulated data outside the step component:
  `sessionStorage` for short anonymous flows, a server-side draft record for anything long,
  logged-in, or worth resuming on another device. A server draft also allows a "finish your
  application" email, which needs a lawful basis (`0x:privacy-compliance`).
- On entering a step, move focus to its heading and set the page title; show position
  ("Step 2 of 4") and, before the final submit, a review screen with an edit link per section.
- Conditional paths: derive the step list from the answers so far in one function, used by both
  the progress indicator and the navigation guard. Opening step 3 by URL with step 1 incomplete
  redirects to the first incomplete step.
- Order steps so the cheap, motivating questions come first and account creation or payment
  comes last. The final submit is idempotent.

## Date, combobox and file inputs

| Need | Default | Move to a library primitive when |
|---|---|---|
| A date | `<input type="date">`: native pickers are good on phones; the submitted value is always `YYYY-MM-DD` whatever the display | Ranges, blocked dates, availability or prices shown in the calendar, or a design that must match across browsers |
| Date of birth, card expiry | Separate text inputs; a calendar is the wrong tool for a date decades away | — |
| Choose one of a fixed short list | `<select>` or radios (radios when five or fewer and space allows) | Options need search, icons or grouping beyond `<optgroup>` |
| Choose from many, or from a server search | Library combobox | Always; `<datalist>` is too inconsistent across browsers to carry a key flow |
| Multi-select, tags | Checkbox group for short lists | Long lists: library combobox with multiple selection |
| Files | `<input type="file">` with a styled `<label>` | Never replace it; add to it |

- Date picker, combobox and listbox are the most expensive widgets to build correctly: focus
  management, typeahead, screen-reader announcements, IME composition, virtual keyboards, and
  positioning. Take them from an accessible headless library (React Aria, Radix-family
  primitives, Base UI, Ariakit) and style them with the project's tokens. Do not hand-roll.
- Custom pickers must still submit: render a hidden input with the `name` and a canonical value
  (ISO date, option id). Dates and time zones: `internationalization.md`.
- File drop zone: the file input stays the foundation (keyboard, screen readers, phone camera
  and library). The drop area is an enhancement around it:

```js
zone.addEventListener('dragover', (e) => e.preventDefault());   // required, or drop never fires
zone.addEventListener('drop', (e) => {
  e.preventDefault();
  input.files = e.dataTransfer.files;
  input.dispatchEvent(new Event('change', { bubbles: true }));
});
```

- `accept` filters the picker but proves nothing. Check type and size on the client for fast
  feedback and again on the server, where the content, not the extension, is inspected. Upload
  transport (direct-to-storage, resumable, scanning) is in `0x:backend-architecture`
  (`file-uploads.md`).
- Show each file with name, size, progress, a cancel button and a retry on failure. Preview
  images with `URL.createObjectURL(file)` and revoke the URL when done.
- `accept="image/*"` on a phone offers camera and library. The `capture` attribute forces the
  camera and removes the library option; use it only when a fresh photo is required. Phone
  photos are large and may arrive in formats the server's image pipeline must handle (HEIC).

## Ask the user

- **Which fields are truly required at this moment?** Every field lowers completion; some can
  be asked later or derived. Default: only what is needed to perform the action now.
- **What happens to abandoned, partly filled forms?** Saving them server-side enables resumption
  and follow-up emails but stores personal data from people who did not submit. Default: local
  drafts only until the user is logged in.
- **Should long forms autosave or require an explicit save?** It sets user expectations about
  when changes take effect. Default: autosave drafts, explicit final action.
- **Is a duplicate submission harmful here (charge, order, message sent twice)?** If yes,
  server idempotency is mandatory, not optional. Default: treat creates and payments as harmful.
- **Which countries will fill in address and phone fields?** It decides field layout and
  validation strictness. Default: international-safe, permissive fields
  (`internationalization.md`).
