# UX flows and screen states

Read this when: a feature's screens are about to be built; designing first run, settings, team or permission flows; a flow has too many steps; deciding phone, tablet and desktop behavior; deciding how a destructive action is confirmed or undone.

## Order of work

Design the flow before any screen, and the screen's states before its styling. The sequence that avoids rework:

1. **Write the job in one sentence**: who, in what situation, wants what outcome. If it cannot be written, the feature is not ready for design; that question belongs to `0x:product-discovery`.
2. **Map the journey** as a list of steps with entry points and exits.
3. **List the objects and their names** (see `information-architecture.md`).
4. **Wireframe every screen in gray boxes**, including each state.
5. **Walk the flow with real content and the unhappy paths.**
6. **Prototype only what is uncertain**, test it (see `usability-testing.md`), then build.

Steps 1 to 5 take an hour or two for a typical feature and can be done as text and ASCII or as a plain unstyled route. Skipping them moves the same decisions into code review, where they cost ten times more.

## Journey: first visit to repeated value

Map five moments and write, for each, what the user knows, what they want, what the product shows, and the single action that moves them on.

| Moment | The design question | Typical failure |
|---|---|---|
| Arrival (landing, invite link, shared item, search result) | Does the first screen match the promise that brought them? | Deep link dumps an invited user on a generic signup with no context |
| Signup and setup | What is the least needed before value? | Asking for profile, team and billing before showing anything |
| First value (the "aha") | What is the first outcome the user would describe to someone else, and how many steps away is it? | First session ends on an empty dashboard |
| Return | Why come back, and what do they see when they do? | Home screen identical on day 1 and day 30 |
| Habit and expansion | What makes the second, tenth, hundredth use faster? Who else gets invited? | Power features hidden, or shown before the basics work |

Mark every entry point, not only the front door: email links, notifications, invitations, a shared URL opened while signed out, the back button, a second device. Each needs to land somewhere sensible, including the return trip to the original destination after sign-in.

Define first value as a concrete, observable event (created a first invoice, saw the first report with their own data) so that the flow can be measured; instrumentation belongs to `0x:product-analytics`.

## Wireframes first

- **Fidelity**: boxes, real labels, real content, no color, no font choices. Real words matter more than layout at this stage; a wireframe with "Lorem ipsum" and "Button" hides exactly the problems wireframes exist to find.
- **Cover every screen and every state** in the flow, including the ones nobody wants to draw: the error after submit, the empty list, the permission-denied view, the expired link.
- **One screen, one purpose.** Write the purpose and the primary action above each wireframe. A screen with two primary actions is two screens or one decision not yet made.
- **Use realistic extremes**: the longest name, 0 items, 1 item, 10,000 items, a slow connection, a user without permission.
- Text-first works well with a coding agent: an outline of regions, their content and their actions per screen is a sufficient wireframe for most product UI.

```text
Screen: Invoices (list)            Purpose: find or create an invoice
Primary action: New invoice
Header:  title | search | [New invoice]
Filters: Status (All/Draft/Sent/Paid/Overdue) | Date range | Customer
Table:   Number | Customer | Amount (right) | Status | Due | row menu
States:  empty (no invoices yet) | no results | loading | error | partial (stale data)
```

## The states of every screen

Every screen that shows data has at least these states. Design them in the wireframe; they are most of what users experience during the first week.

| State | What it must do | Details |
|---|---|---|
| Empty, first use | Explain what will appear here and offer the one action that fills it | Headline, one line, one button. Sample data or a template beats an illustration |
| Empty, no results | Say that the filter or search matched nothing; offer to clear or broaden | Never reuse the first-use empty state here; it implies the data is gone |
| Empty, cleared | Confirm the user is done (inbox zero) | A quiet positive message; no call to action required |
| Loading | Show the page structure at once; fill in as data arrives | Skeleton for layout that is known; rules in `motion-design.md` |
| Partial | Show what loaded; mark the part that failed with its own retry | One failing widget must not blank the page |
| Error | Say what happened, keep the user's input, offer retry or a way out | Wording in `microcopy.md`; never a dead end, never a raw code alone |
| Success | Confirm the result where the user is looking, and show the next step | Inline change or toast for small actions; a result screen only for major milestones |
| Offline or stale | Show last known data with its age; queue or block writes explicitly | Matters for mobile and long-lived tabs |
| No permission | Say what is restricted and who can grant access | Prefer hiding navigation the user can never use, but explain on direct URL access |
| Too much | Pagination or virtualized list, search and filters | Decide the threshold before launch, not after the first large customer |

The first-use empty state is the most valuable screen in a new product: every user sees it, and it is the natural place for onboarding. Treat it as a designed screen, not a fallback.

## Cutting steps, decisions and fields

For each step, decision and field ask, in order: can it be removed, inferred, defaulted, or deferred until after first value?

- **Remove**: fields nobody reads downstream. Check where each field is used; unused fields are common.
- **Infer**: country and currency from locale, time zone from the browser, company from the email domain, name from the sign-in provider, card type from the number.
- **Default**: pre-select the choice most users make and let them change it. A good default turns a decision into a confirmation.
- **Defer**: ask at the moment the answer is needed (billing details at upgrade, notification permission at the first event worth a notification, team invites after the first success).
- **Split or merge**: one long form is fine when fields are few and related; split into steps when there are more than about seven fields, when later questions depend on earlier answers, or when early steps give value by themselves. Show progress and allow going back without losing data.
- **Optional fields**: delete them or collapse them behind "Add details". Mark the few optional fields rather than putting an asterisk on every required one.
- **Count decisions, not clicks.** Three obvious clicks beat one screen with a hard choice. The "three-click rule" has no evidence behind it; uncertainty at each click is what loses people.
- **Do not make users choose a plan, a template and a workspace name before they have seen the product**, unless the answer changes what they see first.

Signup and payment forms have their own owners: authentication flows in `0x:auth-identity`, checkout in `0x:payments-billing`, form mechanics in `0x:frontend-foundations`.

## First-run onboarding

The goal is first value in the first session, not a tour of features.

| Pattern | Use when | Avoid when |
|---|---|---|
| Straight into the product with a strong empty state | The core action is obvious and quick | Setup is needed before anything works |
| Setup wizard, three to five steps | Value requires configuration (connect an account, import data) | Steps only collect profile data |
| Sample data or a template, pre-loaded | Value depends on having content; the product looks dead when empty | Sample data could be confused with real data (finance, production systems) |
| Checklist of three to five tasks, persistent and dismissible | Several actions are needed to be set up, across sessions | It lists features rather than outcomes |
| Contextual hints at the moment of use | A feature is non-obvious and met later | The hint blocks the task |
| Product tour with sequential tooltips | Almost never | Always, as the main onboarding; users dismiss it and remember nothing |

Rules:

- Ask at most one or two personalization questions, and only if the answers visibly change the first screen.
- Let users skip any step that is not technically required, and make the skipped step easy to find later.
- The slowest step (import, integration, verification) must not block exploration: start it, show progress, let the user continue.
- Count the checklist's first item as already done (account created); visible progress encourages completion.
- An invited user's first run differs from the creator's: skip workspace setup, land on the thing they were invited to.
- Design the second session too: returning before setup is finished must resume, not restart.

## Phone, tablet and desktop

Start from the content priorities, not from breakpoints. For each screen, rank the regions; the phone layout shows them in rank order in a single column, and wider layouts place lower ranks beside higher ones.

| Aspect | Phone (under about 640px) | Tablet (about 640 to 1024px) | Desktop (1024px and up) |
|---|---|---|---|
| Navigation | Bottom tab bar for three to five destinations, or a menu drawer | Collapsed icon rail or drawer | Persistent sidebar or top bar |
| Layout | One column | One or two columns; list and detail side by side in landscape | Multi-column; list plus detail; side panels |
| Tables | Stacked cards or key columns only | Fewer columns, horizontal scroll with frozen first column | Full table |
| Dialogs | Full-screen sheet or bottom sheet | Centered dialog or sheet | Centered dialog, popovers, side panel |
| Primary action | Within thumb reach: bottom bar or sticky footer | Header or footer | Header, near the content it affects |
| Hover content | Not available; must be visible or tap-revealed | Often not available | Available as an enhancement |
| Input | Touch targets 44px or more, correct mobile keyboards, 16px input text | Both touch and pointer | Pointer and keyboard; shortcuts |
| Density | Comfortable | Comfortable | Compact acceptable |

Decisions to make explicitly:

- **Which tasks are realistic on a phone.** For many B2B tools the phone job is check, approve and reply, not configure. Design those well and keep the rest merely usable rather than hiding it; removing features on small screens strands users who have only a phone.
- **Tablets are not big phones.** A phone layout stretched to 1024px wastes the screen; test the layout at an in-between width.
- **Use the same content and order across sizes**; change arrangement, not information.
- **Design at 360px wide and at 1440px wide**, then check the widths in between by dragging the window. Problems live between breakpoints.

CSS techniques belong to `0x:frontend-foundations`.

## Undo, confirmation and forgiveness

Choose by reversibility and blast radius, not by how nervous the action feels.

| Action | Pattern |
|---|---|
| Reversible, small scope (archive, delete one item, remove a tag, move) | Do it immediately; show a toast with **Undo** for about 5 to 10 seconds; keep the item in trash or soft-deleted |
| Reversible but disruptive (bulk changes, sending to many, changing a role) | Confirmation that states the scope in numbers ("Archive 42 projects?"); undo afterward if possible |
| Irreversible, contained (permanently delete one record, revoke an API key) | Confirmation dialog naming the object and the consequence; button labeled with the verb; default focus on Cancel |
| Irreversible, large blast radius (delete workspace, delete account, drop production data) | Type the object's name to confirm; state what is lost and what is kept; consider a grace period during which it can be restored |
| External and irreversible (send email, charge a card, publish) | Review step showing exactly what will happen; a short delayed-send window with cancel where feasible |

- **Confirmation dialogs wear out.** A dialog on every delete trains users to press Enter. Reserve dialogs for the rows above that need them; use undo for the rest.
- **Undo requires backend support**: soft delete or delayed execution. Decide during design, because it changes the data model; see `0x:backend-architecture` and the data skills for the implementation.
- **Protect work in progress**: autosave drafts; warn before leaving a form with unsaved changes; never clear a form on a failed submit; restore state after a session expiry and re-login.
- **Separate destructive controls physically** from frequent ones; a Delete next to Save is an accident waiting.
- **Make state visible so mistakes are noticed**: show what was changed, by whom and when, for anything shared.

## Settings, permissions and team flows

- **Settings are for preferences, not for missing design decisions.** Each setting is a permanent cost in testing and support. Before adding one, try a better default.
- **Structure by scope**: personal (profile, notifications, appearance, security), workspace (general, members, roles, billing, integrations, API keys, danger zone). Keep the two visibly separate; users confuse "my setting" with "everyone's setting".
- **Save model**: toggles and selects apply immediately with visible confirmation; text fields and anything risky save with an explicit button per section. Do not mix both models in one section.
- **Scale path**: a single page until about 15 settings; then sections with a side navigation; add settings search past roughly 50. Every settings page has a stable URL so support can link to it.
- **Roles**: start with two or three fixed roles (owner, admin, member; add viewer or billing when asked). Custom roles and per-resource permissions are Scale features driven by enterprise deals. Show what each role can do in a plain table at the point of choosing. The authorization model belongs to `0x:auth-identity`.
- **Invitations**: accept several emails at once, set the role in the invite, show pending invites with resend and revoke, handle the invitee who already has an account and the one who signs up with a different email, and land the invitee in the workspace, not in a new empty one.
- **Guard the last owner**: the last owner cannot leave or demote themselves; ownership transfer is an explicit flow.
- **Permission-denied is a designed state**: say what is needed and who to ask; offer "request access" when that is cheap to build.
- **Danger zone** at the bottom of workspace settings, each action with the confirmation level from the table above.

## Prototyping

Prototype to answer a question; pick the cheapest medium that can answer it.

| Question | Medium |
|---|---|
| Do people understand the structure and the labels? | Clickable wireframes or a text outline walked through aloud |
| Can people complete the flow? | Coded prototype in the real stack with hard-coded data, behind a flag or on a throwaway branch |
| Does the interaction feel right (drag, transitions, typing speed)? | Code only; static tools cannot answer this |
| Does the visual direction fit the brand? | Two or three styled key screens, in a design tool or in code |

With a coding agent and a component kit, a coded prototype is usually as fast as a design-tool one, tests real behavior and uses real components. Default to code for flows; use a design tool when comparing visual directions side by side or when a designer is involved.
Keep prototype code out of production unless it is rewritten deliberately: fake the data, skip error handling, and say so in the branch name. Stop prototyping as soon as the question is answered.

## Checks

- The job, the primary action and the entry points are written for each screen.
- Every data screen has designed empty (first use and no results), loading, error and success states.
- The flow was walked with a brand-new account, an invited user, a user without permission and an expired or signed-out link.
- Every field in every form has a named downstream use; optional fields are removed or collapsed.
- A new user can reach first value in the first session without leaving the product; the steps are counted and written down.
- Each destructive action is classified by the table above and has the matching pattern.
- The flow works at 360px wide with touch only, and at an in-between width.
- Refresh, back button and session expiry in the middle of the flow do not lose the user's work.

## Ask the user

- **What is the one outcome that makes a new user say the product works?** Onboarding is built toward it. Default: the first completed core object with the user's own data.
- **What must be collected at signup for legal, billing or technical reasons?** Everything else is deferred. Default: email and authentication only.
- **How much real work happens on phones?** Decides whether mobile gets full design effort or a usable fallback. Default: desktop-first B2B, with check, approve and reply flows designed for phones.
- **Which deletions must be recoverable, and for how long?** A product and sometimes a legal choice that shapes the data model. Default: soft delete with a 30-day restore for user content; confirm retention duties with `0x:privacy-compliance`.
- **Who administers a customer account, and which roles exist in their organization?** Drives the roles and team flows. Default: owner, admin and member.
- **Is sample data acceptable in a new account?** Some domains must never show fake records. Default: yes, clearly labeled and removable in one action.
