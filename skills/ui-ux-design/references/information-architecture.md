# Information architecture and navigation

Read this when: organizing a product's sections; naming objects and features; choosing between sidebar, tabs, breadcrumbs and a command palette; the navigation is getting messy; designing search, filters and sorting; shaping URLs; deciding what the home screen shows; checking a structure with card sorting or tree testing.

## Start from the object model

Navigation problems are usually naming and modeling problems. Before touching the menu, write the object model on one page:

| Column | Content |
|---|---|
| Object | The nouns users think in: Project, Invoice, Customer, Member |
| Definition | One sentence a user would agree with |
| Relationships | Contains, belongs to, references (a Project has many Tasks; a Task belongs to one Project) |
| Actions | The verbs available: create, send, archive, duplicate |
| Key attributes | What identifies it in a list: name, status, owner, date |
| Synonyms banned | The other words that must not be used for it |

Rules:

- **Use the user's word, not the database's.** If customers say "client", the interface says "client" even when the table is `accounts`. Collect words from support messages, sales calls and competitor products users already know; discovery interviews belong to `0x:product-discovery`.
- **One name per object, everywhere**: navigation, page titles, buttons, emails, URLs, API and documentation. "Workspace", "team", "organization" and "account" used for the same thing is the most common cause of user confusion in B2B products.
- **One object per name.** If "report" means both a saved query and an exported PDF, split the terms.
- **Same verb for the same action.** Choose between delete and remove, archive and hide, edit and update, and record the difference where both exist (remove takes it out of this list; delete destroys it).
- **Navigation lists objects; buttons hold actions.** "Invoices" is a destination, "New invoice" is a button on it. A sidebar of verbs ("Create", "Manage", "Analyze") hides where things live.
- **Avoid internal and clever names** for destinations. A branded feature name needs a descriptive companion until users have learned it (see `microcopy.md`).
- Keep the glossary in the repository. It is the reference for copy, for code naming and for anyone writing with an agent.

## Choosing navigation patterns

| Pattern | Use for | Limits and rules |
|---|---|---|
| Sidebar (left, vertical) | Products with five or more top-level destinations, or where the list will grow; the default for B2B tools | Scales to about 7 to 10 visible items plus grouped sections; collapsible to an icon rail; labels always available |
| Top bar (horizontal) | Three to six destinations that will not grow; content-wide products | Runs out of room quickly; overflow menus ("More") hide things |
| Tabs | Sibling views of the same object or the same list (Overview, Activity, Settings of a project) | Two to seven; never nested tabs inside tabs; a tab changes the view, not the object; each tab has a URL |
| Breadcrumbs | Hierarchies three or more levels deep, or when users arrive by deep link | Show the location in the hierarchy, not the click history; the last crumb is the current page and is not a link |
| Bottom tab bar (phone) | Three to five primary destinations in a mobile layout | Icon plus label; no scrolling tab bar |
| Menu drawer (hamburger) | Secondary destinations on phones | Hidden navigation is used less; never the only route to a primary destination on desktop |
| Command palette | Power users, many objects, keyboard-heavy tools | A supplement: everything in it must also be reachable by visible navigation; add at Launch or later |
| Segmented control or switcher | Changing a mode or a scope within a page (list or board; this week or this month) | Two to four options; not for navigation between pages |
| Workspace or project switcher | Multi-tenant or multi-project scope | One consistent place, top of the sidebar; current scope always visible |

Decisions that follow from the pattern:

- **Global, local, contextual.** Global navigation is the same on every screen. Local navigation (tabs, a secondary sidebar) belongs to the current section or object. Contextual links sit in the content. Do not let a local item jump to global scope without the user noticing.
- **Always show where the user is**: highlighted item in the navigation, page title matching the navigation label exactly, breadcrumbs when deep.
- **Depth**: two levels of navigation cover most products (section, then page or tab). A third level is a signal to restructure, or to treat the object as its own space with its own local navigation.
- **Icons in navigation need labels.** An icon-only rail is acceptable only as a collapsed state the user chose.
- **Utilities are not destinations.** Search, notifications, help and the account menu live in fixed corners, not in the main list.
- **Settings and billing** sit behind the account or workspace menu, not in the primary list, unless administration is the product.

## Navigation that survives ten times more features

The menu that works with five items breaks at fifteen unless growth has a planned shape.

- **Organize by object and user goal, never by team, release date or technology.** "Integrations" is a place; "New features" and "Advanced" are junk drawers that grow forever.
- **Hub and detail.** Top-level items are collections (Projects, Customers, Reports). Features attach to an object as tabs or sections inside it rather than as new top-level items. Most new features belong inside an existing object; ask "which object is this about?" before adding a menu entry.
- **Group with headings at about eight items**: three to five groups with plain labels (Workspace, Sales, Reports). Groups add structure without adding depth.
- **Frequency decides visibility.** Daily destinations stay visible; monthly ones move under a group, into settings, or into the command palette. Use product analytics on navigation clicks, not opinion, to rank; see `0x:product-analytics`.
- **Let users shape their own shortcuts** (pinned or favorite items, recents) before adding levels. Recents solve a large share of "I cannot find it" complaints.
- **Budget rule**: adding a top-level item requires demoting or merging another once the list passes the visible limit.
- **Role-aware navigation**: hide sections a role can never use; do not show disabled items with no explanation. Show an upgrade-gated item only if it is a deliberate sales surface, and mark it clearly.
- **Search and the command palette are the release valve** for long-tail destinations, which keeps the visible navigation short.
- **Renaming and moving cost trust.** Change navigation rarely and in one step, redirect old URLs, and announce the move where the item used to be.
- **Signs of trouble**: a "More" or "Other" item; the same page reachable under two different names; users relying on browser history or bookmarks; support answering "where is X" weekly.

## Search, filtering and sorting

Pick the mechanism by collection size and how users recall items.

| Collection | Provide |
|---|---|
| Under about 20 items | A sensible default sort; nothing else |
| 20 to a few hundred | Sort, a quick text filter on the name, one or two key filters (status, owner) |
| Thousands or more | Server-side search, faceted filters, saved views, pagination or virtualized scrolling |
| Many object types across the product | Global search grouped by type, plus recents |

**Search**

- Search what users type: names, identifiers, emails, and the text they remember. Tolerate case, accents, leading and trailing spaces, partial words and minor typos.
- Show results as the user types for small sets; for server search debounce the request, keep the previous results visible while loading, and discard out-of-order responses.
- Show the matched field and highlight the match, so the user can see why a result appeared.
- On opening, show recent items and recent searches before any typing.
- The zero-result state states the query, suggests a fix (check spelling, clear filters, search everywhere) and offers creation when that makes sense ("Create customer 'Acme'").
- Scope must be visible: searching within this project or across everything.
- Search technology belongs to the data and backend skills; choose the design first.

**Filters**

- Offer filters for attributes users actually discriminate on; three well-chosen filters beat fifteen.
- Within one filter, multiple values combine with OR; across filters, with AND. This matches expectation; do not expose boolean builders until users ask for them (Scale).
- Show applied filters as removable chips, a result count, and "Clear all". Apply instantly on desktop; on phones collect choices in a sheet with an Apply button showing the count.
- Show counts per option when cheap. Do not offer options that lead to zero results without marking them.
- **Saved views** (a named combination of filters, sort and columns) are the scaling step once users repeat the same filtering; shared views come after personal ones.
- Filter and sort state lives in the URL, so views can be bookmarked, shared and survive refresh and back.

**Sorting**

- The default sort answers "what do I need now": most recently updated for work items, most urgent for queues, alphabetical only for reference lists users scan by name.
- Sortable column headers show the current direction. The sort must be stable (add a unique tiebreaker such as the ID), or rows jump between pages.
- "Relevance" is a valid sort only for search results.

**Pagination**: numbered pages when users need position and totals (records, admin); "Load more" or infinite scroll for feeds and browsing. Infinite scroll must preserve scroll position on back navigation and must not hide a footer the user needs.

## URLs mirror the structure

A URL is part of the interface: users read, share, bookmark and edit it.

```text
/projects                       collection
/projects/new                   creation
/projects/{id}                  object (default tab)
/projects/{id}/settings         tab or section of the object
/projects/{id}/tasks/{taskId}   child object
/projects?status=active&sort=-updated   view state in the query string
/settings/billing               stable address for support links
```

- **Path for identity and hierarchy; query string for view state** (filters, sort, page, selected tab if it is only a view toggle, search query).
- **Every meaningful state has a URL**: tabs, an open detail panel, a modal that represents an object (opening an item in a dialog over the list). Test: copy the URL into a new tab; the same thing must appear. Transient states (an open menu, a confirmation dialog) do not get one.
- **Use the glossary's nouns**, plural for collections, lowercase with hyphens. The URL word and the navigation label should match.
- **IDs**: an opaque stable ID in the path survives renames; add a readable slug only for content that is shared publicly, and redirect when the slug changes. Do not put personal data such as email addresses in paths; URLs end up in logs, analytics and referrers.
- **Multi-tenant scope** is explicit in the URL (`/acme/projects/...` or a subdomain) when users belong to several workspaces; otherwise a shared link opens in the wrong workspace or fails mysteriously. Tenancy design belongs to `0x:backend-architecture`.
- **Back button**: navigating to a page pushes history; changing a filter usually replaces the entry, so Back leaves the list instead of unwinding ten filter changes.
- **URLs are promises.** When structure changes, redirect old paths permanently. Signed-out visits return to the requested URL after sign-in.
- Routing implementation belongs to `0x:react-nextjs`.

## The home screen

The home screen answers "what needs my attention, and where was I?" It is not a place to display everything the product has.

| Product type | Home should lead with |
|---|---|
| Work or task tool | Items assigned to the user or awaiting them; recents; quick create |
| Monitoring or analytics | Three to five key numbers with comparison and anything abnormal; link to detail |
| Content or document tool | Recent documents, continue where left off, templates |
| Marketplace or transactional | Status of open orders or requests; the primary next action |
| Administration | Things that need a decision: pending invites, failed payments, expiring keys |

- **Three states to design**: brand new (onboarding and the first action), active (attention and resume), dormant return (what changed while away).
- If no meaningful summary exists yet, do not build a dashboard: land the user on the main collection or the last place they worked. An invented dashboard of vanity tiles is worse than a useful list.
- Every item on home is a link to act on it. Numbers without a destination are decoration.
- Announcements and promotions take one dismissible slot at most.
- Role matters: an admin and a member need different homes once the product has both.

## Validating structure: card sorting and tree testing

Worth doing when the product has roughly 30 or more destinations or content items, before a navigation redesign, or when "cannot find X" dominates support. Below that, a tree test is still cheap; card sorting is usually unnecessary.

| Method | Question it answers | How |
|---|---|---|
| Open card sort | How do users group these things, and what do they call the groups? | 30 to 60 cards, each one item in plain words; participants group and name the groups. Generates candidate structures |
| Closed card sort | Do the proposed categories make sense? | Same cards, fixed category names; look for cards placed inconsistently |
| Tree test | Can users find things in this hierarchy, with no visual design to help? | Text-only tree; 8 to 10 tasks ("Where would you change who receives invoices?"); measure success, directness and first choice |

- **Sequence**: open sort to generate, draft the tree, tree test to verify, revise, retest the failing tasks.
- **Sample sizes (rules of thumb)**: about 15 to 20 participants for a card sort to see stable groupings; about 30 to 50 for a tree test to trust the percentages. Five moderated participants thinking aloud still expose the worst labels.
- **Task wording must not contain the label being tested**; describe the goal in other words, as in `usability-testing.md`.
- **Reading results**: the first click predicts the outcome; a task where people start in the wrong branch points at a top-level label problem. Items that are split between two groups either need a clearer name or legitimately belong in both (cross-link them).
- **Trap**: card sorts show how people group, not how they search for something during a task. Never ship a structure from a card sort without a tree test.
- Dedicated tools exist for both methods; a spreadsheet and a video call also work for a handful of sessions.

## Checks

- The glossary exists; a search of interface strings finds no banned synonym.
- Each navigation label equals the title of the page it opens.
- Every tab, filter combination and detail view can be reached by pasting its URL into a new tab, signed in and after sign-in.
- The current location is visibly marked in the navigation on every screen.
- A new feature's placement was decided by "which object is this about", and the top-level count did not grow without a demotion.
- Search handles a typo, a partial word and an identifier, and its zero-result state offers a next step.
- Back from a detail page returns to the list with the same filters and scroll position.
- The home screen was designed for a new, an active and a returning user.

## Ask the user

- **What do customers call the main things in the product?** Their words become the labels. Default: the terms used in support messages and by the best-known competitor.
- **Which three destinations do users visit most, and which are monthly?** Drives what is visible. Default: rank by analytics; if none, core objects first and settings last.
- **Can a user belong to more than one workspace or organization?** Changes URLs, the switcher and every shared link. Default: yes for B2B; keep scope explicit in the URL.
- **Which features are planned for the next year?** The structure has to have a place for them. Default: assume each core object gains two or three sub-features and one new object appears.
- **Is there budget and access to users for a tree test?** Decides between testing and reasoning from heuristics. Default: five-person moderated walkthrough of the tree.
