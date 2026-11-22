# Microcopy and interface writing

Read this when: writing or reviewing the words in the interface: labels, buttons, dialogs, error messages, empty states, hints, confirmations, feature and plan names; setting a voice and tone guide; preparing copy for translation or for screen readers.

## The rules that settle most strings

Interface text is read in fragments by people in the middle of a task. They scan the first two or three words of a line and act. Write for that.

- **Front-load the meaning.** Put the distinguishing word first: "Invoice sent", not "Your invoice has been successfully sent".
- **Name the action with a verb and its object**: "Save changes", "Send invoice", "Add member". The button says what will happen when pressed.
- **Use the user's nouns**, the same ones everywhere (glossary in `information-architecture.md`).
- **Sentence case** for everything: titles, buttons, labels, menu items. It reads faster, avoids debates about which words to capitalize, and translates cleanly. Capitalize only the first word and proper nouns.
- **Present tense, active voice, second person.** "You can export up to 1,000 rows", not "Up to 1,000 rows may be exported".
- **Cut filler**: "please", "successfully", "simply", "just", "in order to", "Are you sure you want to". "Please" stays only when asking for something inconvenient.
- **No periods on labels, buttons, headings or single-phrase hints.** Full sentences in body text and messages get periods.
- **Be specific with numbers and objects**: "3 files uploaded", "Delete 12 contacts".
- **One idea per string.** If a tooltip needs three sentences, the design needs fixing.
- **Write the words before the layout.** Text that is added last gets squeezed into whatever space remains.

Length guides (rules of thumb): button one to three words; field label one to three words; toast under about ten words; dialog title one line; helper text one sentence; error message one or two sentences.

By stage: at Prototype, write real words in the first wireframe and keep the glossary. At Launch, review every string on the signup, payment, error and deletion paths against this file and write the one-page voice guide. A translation process waits until a second language is scheduled; the rules for translatable copy below apply from the start because they cost nothing.

## Labels, buttons and confirmations

| Element | Rule | Weak | Better |
|---|---|---|---|
| Button | Verb plus object; matches the title of what it opens | "Submit", "OK", "Continue" | "Create account", "Send invoice" |
| Paired buttons | The second is the plain opposite | "Yes" / "No" | "Delete project" / "Cancel" |
| Field label | Noun, visible above the field, never only a placeholder | Placeholder "Enter your email" | Label "Work email" |
| Placeholder | An example of the format, or nothing | "Enter amount" | "e.g. 1,200.00" |
| Helper text | Why it is asked or the constraint, before the user errs | "Invalid password" after typing | "At least 12 characters" shown from the start |
| Checkbox, switch | Positive statement that is true when on | "Disable notifications" | "Email me when an invoice is paid" |
| Link | Describes the destination out of context | "Click here", "Learn more" | "Read about invoice reminders" |
| Menu item | Verb for actions, noun for destinations; an ellipsis when more input follows | "Export" (opens a dialog) | "Export..." |
| Toast or confirmation | Object plus past participle; add the undo or the next step | "Success!" | "Invoice sent to Acme" with "View" |
| Loading | Say what is happening when it lasts more than a few seconds | "Loading..." | "Importing 240 contacts..." |
| Timestamps | Relative when recent, absolute when exact time matters; full date on hover | "2026-11-22T10:04:00Z" | "5 minutes ago" |

Placeholders disappear when typing starts, usually have low contrast and are skipped by some assistive technology, so a placeholder can never replace a label. Negative switch labels ("Do not...") produce double negatives when turned off.

Confirm what happened, not that something happened. After a save in a form that stays open, an inline "Saved" near the control is enough; after an action whose result is elsewhere, name the object and link to it.

Words next to money, consent and security are commitments, not decoration. State the price, the billing interval, when a trial converts and how to cancel beside the button that commits, and make the label match what the system does: "Start free trial" must not charge today. Word decline and cancel options as plainly, and show them as clearly, as accept. Guilt-laden declines ("No thanks, I prefer paying more"), pre-ticked consent boxes and buried opt-outs are treated as deceptive design by regulators in many jurisdictions, with rules that differ by country (`0x:privacy-compliance`). Claims such as "secure", "encrypted", "compliant" or "we never share your data" go in the interface only when they are true of the system as built.

## Error messages

Every error message answers three questions, in this order: **what happened, why (if known and useful), and what to do next.**

| Situation | Weak | Better |
|---|---|---|
| Validation | "Invalid input" | "Enter a date in the future" |
| Format | "Error: phone format" | "Enter a phone number with country code, such as +1 555 010 0199" |
| Uniqueness | "Name taken" | "A project named 'Q3 launch' already exists. Choose another name." |
| Permission | "403 Forbidden" | "Only workspace admins can change billing. Ask an admin for access." |
| Not found | "404" | "This project does not exist or was deleted. Go to all projects." |
| Network | "Network error" | "Could not reach the server. Check your connection and try again." (input preserved, Retry button) |
| Server fault | "Something went wrong" | "We could not save your changes. Try again; if it keeps happening, contact support with code R7K2." |
| Limit | "Quota exceeded" | "You have reached 3 projects on the Free plan. Archive one or upgrade." |
| Payment declined | "Payment failed" | "Your bank declined the card. Try another card or contact your bank." |

Rules:

- **Blame the system or state the fact; never blame the user.** "Enter a valid email" beats "You entered an invalid email". No "illegal", "invalid" as the whole message, "fatal", "abort" or "oops".
- **Be specific about the fix.** If the rule is known (length, format, range), state the rule. Better: accept more formats so the error cannot occur (strip spaces from card numbers, trim input, accept several date formats).
- **Place the message at the problem**: next to the field for field errors; at the top of the form with links to the fields when several fail; inline in the affected region for load failures. Toasts are for transient confirmations, not for errors the user must act on, because they disappear.
- **Never lose the user's input.** The message is worthless if the form was cleared.
- **Timing**: validate on leaving the field or on submit, not on the first keystroke; clear the error as soon as the input becomes valid.
- **Technical detail**: plain sentence first; a reference code or expandable detail second, for support. Never show stack traces, SQL or raw exception text; besides being useless to the user, they leak internals.
- **Security exceptions**: sign-in and password-reset messages stay deliberately vague about whether an account exists ("If that email has an account, we sent a link"), and a signup form that answers "this email is already registered" tells an attacker who the customers are; whether signup may reveal it is a decision owned by `0x:auth-identity`. Card declines stay generic as well: do not echo the processor's raw reason, which can expose fraud signals (`0x:payments-billing`). In these places the security rule beats the specificity rule.
- **Do not apologize by reflex.** "Sorry" belongs in messages about the product's own failure, once, without drama.
- **Humor fails in errors.** The user is blocked; a joke the first time is an irritation the fifth.
- Give every error a stable code in logs so support can find it; message catalogs make this easy. Announcing errors to assistive technology belongs to `0x:accessibility`.

## Dialog actions

- **Title is the question or the action, with the object named**: "Delete project 'Website redesign'?" not "Are you sure?" or "Confirm".
- **Body states the consequence** in one or two sentences, including what is not recoverable and what is unaffected: "This removes 14 tasks and 3 files for everyone. This cannot be undone."
- **Buttons repeat the verb from the title**: "Delete project" and "Cancel". A user who reads only the buttons must still know what each does. "Yes", "No" and "OK" force rereading the question, and they become wrong when the question is rephrased.
- **The dismissive action is always "Cancel"** (or "Keep editing", "Not now" where that is clearer), never a second ambiguous verb. Beware the cancel-a-cancellation trap: for "Cancel subscription?" the buttons are "Cancel subscription" and "Keep subscription".
- **Destructive confirm buttons use the danger style**, and are not the default focus; pressing Enter by reflex must not destroy data.
- **Button order**: follow the platform or kit convention consistently across the product; consistency matters more than which side the primary sits on.
- **Unsaved changes**: "Discard changes?" with "Discard" and "Keep editing"; offer "Save" as a third action only when saving is possible from the dialog.
- If the dialog only informs, it probably should not be a dialog; use an inline message or a toast.

Which actions deserve a dialog at all is decided in `ux-flows.md`.

## Empty states and hints

An empty state has three parts: what this place is for, why it is empty, and the one action that changes that.

| Type | Example |
|---|---|
| First use | "No invoices yet" / "Create an invoice to bill a customer and track when it is paid." / [New invoice] |
| No results | "No invoices match 'acme' with status Overdue" / [Clear filters] |
| Done | "All caught up. New requests appear here." |
| No permission | "You do not have access to billing. Ask a workspace admin." |
| Error | "Could not load invoices." / [Try again] |

- The headline states the fact; the body gives the benefit or the cause in one sentence; the button is the same verb and object used elsewhere for that action.
- First-use empty states teach by offering the action, a template or sample data, not by describing features.
- **Hints and tooltips**: a tooltip names an icon-only control or adds a short clarification; it never holds information required to complete the task, because touch and keyboard users may not see it. Text needed to fill a field goes in visible helper text.
- **Teaching hints** appear at the moment of relevance, once, dismissible, and never block the task.
- **Onboarding text** names outcomes ("Send your first invoice"), not features ("Explore the invoice module").

## Voice and tone guide

Voice is constant; tone shifts with the user's situation. A one-page guide is enough and is what keeps copy consistent when an agent or a second person writes strings.

1. **Three or four voice traits, each with a boundary**: "Clear, not clinical. Friendly, not chatty. Confident, not arrogant. Brief, not curt."
2. **Tone by situation**:

| Situation | User's state | Tone |
|---|---|---|
| Routine task | Focused | Neutral, minimal |
| Success, milestone | Pleased | Warm, short; celebrate rarely |
| Error, blocked | Frustrated | Calm, direct, practical; no humor |
| Destructive or money-related | Cautious | Precise, serious, explicit about consequences |
| Onboarding | Curious, uncertain | Encouraging, concrete |

3. **Word list**: the glossary terms; preferred and banned pairs (sign in, not log in or login as a verb; workspace, not team or org; delete versus remove with their meanings); spelling and formatting decisions (email, not e-mail; number, date and currency formats; whether contractions are used; how the product refers to itself: by name, as "we", or not at all).
4. **Mechanics**: sentence case; no exclamation marks except rare celebrations; numerals for all numbers in UI; serial comma or not; ellipsis usage.
5. **Before-and-after examples**, ten or so, taken from the real product. Examples carry the voice better than any description.

Keep the guide in the repository beside the tokens. Marketing voice may be livelier than product voice, but the vocabulary must match; conversion copy belongs to `0x:growth-marketing`.

## Naming features and plans

- **Descriptive beats clever.** A feature name should tell a new user what it does: "Reminders", "Recurring invoices", "Activity log". An invented name ("Pulse", "Beacon") must be taught and supported with a descriptor every time it appears; reserve brand names for at most one or two flagship capabilities, at Scale.
- **Test**: show the name alone to someone unfamiliar and ask what it does. If they cannot guess, add words or rename.
- **Check collisions**: with existing objects in the product, with terms that mean something else in the user's industry, and with competitors' well-known names when the meaning differs.
- **Name the thing, not the technology.** "Smart suggestions" or the outcome, not the model or algorithm behind it.
- **Renaming is expensive**: URLs, documentation, support macros, users' habits. Choose plain names early so renaming is not needed.
- **Plans**: names must rank themselves without a table. Conventional ladders (Free, Starter, Pro, Business, Enterprise) or audience names (Solo, Team, Company) work; abstract themed names (metals, planets, animals) force users to learn the order.
  Three or four plans at most are comprehensible. Each plan gets a one-line "for whom" description. Keep the names identical on the pricing page, in checkout, on invoices and in settings. Which plans exist and what they contain belongs to `0x:pricing-monetization`.
- **Labels for states and statuses** are names too: keep the set small, mutually exclusive and in plain adjectives (Draft, Sent, Paid, Overdue).

## Copy that translates and reads aloud

Even for an English-only product, these rules cost nothing now and avoid a rewrite later.

- **Never build sentences by concatenating fragments.** Word order, gender and case differ between languages. Use one complete message with named placeholders.
- **Plurals go through the message format's plural rules**, not through `count === 1`. Some languages have several plural forms and some have none.

```text
{count, plural, =0 {No invoices} one {# invoice} other {# invoices}}
```

- **Leave room.** As a rule of thumb, translated text runs 30 to 40% longer than English, and short strings can double. Do not fix widths to the English label; let buttons and columns grow or wrap.
- **No text inside images.** Format dates, numbers and currencies with the locale's formatter, never by hand.
- **Avoid idioms, puns, cultural references and humor** in strings that will be translated. Avoid ambiguous words that are both noun and verb without context ("Record", "Archive", "Display"); give translators a description for each key.
- **Keep one string per meaning**, not per English wording: "Open" (verb, a button) and "Open" (status, an adjective) are two keys.
- **Reads aloud**: screen readers and voice interfaces speak the text out of visual context. Links and buttons must make sense alone; no "click", "see below", "the green button" or direction-only references.
  Avoid symbols as words ("&", "/", "→", "w/"); write abbreviations out the first time. Do not use emoji or decorative characters in labels; they are read aloud by name. Put the status word in text, not only in color or an icon.
- **Check by reading every string aloud** once, and by tabbing through the screen listening only to control names.

Implementation of message catalogs, locale formatting and right-to-left layout belongs to `0x:frontend-foundations`.

## Checks

- Every button reads as verb plus object and no dialog uses "Yes", "No" or a bare "OK".
- Every error states what happened and the next step, sits beside its cause, and preserves input.
- A search of the strings finds no "Are you sure", "successfully", "click here", "Oops" or "Something went wrong" without a next step.
- Each object is called one thing across navigation, titles, buttons, emails and URLs.
- Every list and data view has first-use and no-results text that differ.
- No string is assembled by concatenation; plurals use plural rules.
- Buttons and labels survive a 40% longer string without clipping.
- Each link and button makes sense when read alone, aloud.

## Ask the user

- **How should the product sound: three adjectives, and one product whose writing they like?** Sets the voice traits. Default: clear, friendly, brief; no jokes.
- **What do customers call the core objects?** Vocabulary beats style. Default: the terms from support messages and the leading competitor.
- **Which languages will the product support in the next year?** Decides how strict the translation rules must be now. Default: English only, written to be translatable.
- **Does the product speak as "we", by its name, or impersonally?** Affects every error and email. Default: "we" for the company's actions and failures, "you" for the user.
- **Are there legal or regulated phrases that must appear verbatim (consent, pricing, cancellation terms)?** Those strings are not to be shortened or restyled. Default: none; confirm for billing, consent and deletion screens.
