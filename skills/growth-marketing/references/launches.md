# Launches

Read this when: planning a product launch or a major feature release, building a waitlist,
writing posts for Product Hunt, Hacker News, Reddit or other communities, pitching press,
newsletters or creators, or turning a launch spike into retained users.

## A launch is a sequence, not a day

Launch day concentrates attention for a few days. What the product keeps from it depends on the
weeks before (who is waiting) and the weeks after (who stays). A "big bang" on every channel on
one day wastes attention: nobody can answer everyone, a bug hits everyone at once, and there is
no second shot.

| When | Stage | Goal | Done when |
|---|---|---|---|
| From the first week of building | Audience | Collect people who have the problem | A waitlist and a personal contact list grow every week |
| Launch minus 6 to 4 weeks | Private beta | Make the first session work | A hand-picked cohort activates without the founder's help |
| Launch minus 4 to 1 weeks | Waitlist drip | Fix onboarding at rising volume | Activation holds across successive invite batches |
| Launch week | Public, own channels first | Convert the warm audience | List, social followers and personal network have been told |
| Launch week and after | Public, borrowed channels | Reach new people | Each community gets its own day and its own post |
| Launch plus 1 to 4 weeks | Follow-up | Turn signups into retained users | Launch-cohort retention measured, lessons applied |

The offsets are rules of thumb: compress them for a small feature, stretch them for a product
that needs data or integrations before it is useful.

## Audience before launch day

- **Start the list in the first week of building.** One page with the specific promise, an
  email field and one qualifying question (role, use case or current tool). The answer lets
  invites go to the best-fit people first.
- **A personal launch list.** A spreadsheet of everyone the founder can message personally:
  former colleagues, people interviewed during discovery, community acquaintances, other
  founders. One-to-one messages on launch day convert far better than broadcasts; a hundred
  names on this list are worth more than a large follower count.
- **Show the work.** Regular posts about the problem and the progress (building in public,
  `content-marketing.md`) turn followers into waitlist signups.
- **Earn standing in the launch communities months ahead** (`community-partnerships.md`). An
  account whose only post is its own launch is ignored or removed.
- **"Move up the line by inviting friends" waitlists** create buzz for consumer products with
  real scarcity; for B2B tools they mostly add throwaway signups. Skip them otherwise.

Keep the waitlist warm with a short update every two to four weeks: what was built, a
screenshot, one question. A list left silent for months has forgotten why it signed up.

## Staged rollout

1. **Private beta**: a handful to a few dozen hand-picked users who match the target customer.
   High touch: watch them use it, fix what blocks the first session, collect the first
   testimonials. Free or discounted in exchange for feedback calls.
2. **Waitlist drip**: invite in batches ordered by fit, sized so support stays manageable.
   Measure activation per batch and fix the top blocker between batches. If activation stalls
   across batches, onboarding is the constraint, not traffic: do not go public yet.
3. **Public, own channels**: email the list, post from the founder's accounts, message the
   personal list. These people are warm; give a reason to act now (a launch offer, early
   pricing, a founder call).
4. **Public, borrowed channels**: Product Hunt, Hacker News, relevant subreddits and other
   communities, newsletters. Spread them over different days so each gets full attention and
   the lessons from one improve the next.

Gates before going public:

- Onboarding activates drip cohorts without manual help.
- Signup and the first session survive a spike: marketing pages static and cached, rate limits
  in place, error tracking and alerts on (launch readiness: `0x:site-reliability`).
- Billing is live and tested, and the payment provider has been told about the expected volume
  spike (`0x:payments-billing`).
- Analytics records the source (UTM parameters and a "how did you hear about us" field) and
  activation.
- Someone answers the support inbox within hours during launch week.

## Writing for each community

Each community rewards different things and punishes different mistakes. One post pasted
everywhere reads as spam and is treated as spam.

| Channel | What works | What gets the post removed or ignored |
|---|---|---|
| Product Hunt | A clear tagline, a gallery showing the product working, a first comment from the maker on why it exists, replies to every comment all day | Asking for upvotes, vote rings, fake accounts; launching with no audience lined up |
| Hacker News (Show HN) | Something people can try immediately, technical substance, a plain title, the founder answering in the thread for hours | Marketing language, signup walls, nothing to try, asking anyone to upvote |
| Reddit | A post useful to that subreddit (a lesson, a story, a free tool), with the maker relationship disclosed | Ignoring the subreddit's self-promotion rules; new or promotion-only accounts |
| Niche Slack and Discord groups | The group's designated promotion channel; answering questions | Posting in general channels; unsolicited direct messages to members |
| LinkedIn | A founder's personal post with a story and a visual | A company-page announcement on its own |
| X, Bluesky, Threads | A short demo clip; a thread on why it was built | A bare link with no context |
| Own email list | A personal note, the launch offer, one link | A designed corporate announcement |

Durable rules for the big ones:

- **Product Hunt**: a launch runs for one day on US Pacific time; schedule for the start of that
  day and be available for all of it. Featuring is decided by Product Hunt's curation, not by
  votes alone. Its rules forbid asking for upvotes: ask supporters to "check it out and share
  feedback". Read the current launch guidelines, including those on relaunching, before
  scheduling.
- **Show HN**: only for something readers can use or try now, not for sign-up pages,
  fundraisers or blog posts. Title format `Show HN: Name – what it does`, factual, no
  superlatives. The text says who built it, what it does, why, how it works, and what feedback
  is wanted. HN detects voting rings and penalizes posts pushed through links asking for votes.
  A post that drew little attention may be reposted after a while; read the current FAQ.
- **Reddit**: read each subreddit's rules and recent top posts first; many allow promotion only
  in a designated thread.

A launch post, adapted per channel:

1. The problem, in the words that community uses.
2. What it is, in one line.
3. How it differs from the alternative this community already knows.
4. A demo: screenshot, short clip, or a link that works without signup where possible.
5. One ask: feedback on a specific question, a free trial, or an offer for that community.

## Launch-day run sheet

Write it the week before, with times in the founder's time zone:

- Posts drafted per channel, links tagged with UTM parameters, images and clips ready.
- Order and timing: one major borrowed channel per day.
- Personal messages to the launch list, written individually, sent in the first hours.
- Monitoring open: signups, errors, payment failures, support inbox, the threads themselves.
- The rule for the day: every comment and email answered, criticism thanked and acted on, no
  arguing.

Set targets before launching and read them at 24 hours, 7 days and 30 days: signups by source,
activation rate of the launch cohort, paid conversions, list growth. Votes and rank are vanity
numbers: record them, do not optimize for them.

## Pitching journalists, newsletters and creators

A product launch is not news. A story is: a surprising number from the product's data, a trend
the product reveals, a founder with an unusual path, a strong position in a debate the writer
covers.

- **Target a person, not a publication**: a writer who recently covered an adjacent story.
  Reference that piece in one line.
- **The email**: the subject line is the story; three to five sentences; why it matters to their
  readers now; what is available (data, interview, early access, screenshots).
- **Exclusive or embargo**: one outlet gets it first, or several get it under an embargo until a
  stated date and time. Either gives a reason to cover it on schedule. Never break an agreed
  embargo.
- **Press kit page**: logo files, screenshots, founder photo and short bio, a one-paragraph
  description, a contact.
- **Niche newsletters and curators** often accept tips or submissions; one read by the exact
  buyer beats a general tech outlet.
- **Creators**: offer free access with no control over their opinion. When anything of value is
  exchanged, they must disclose it, and the agreement should say so. Paid placements are
  sponsorships (`paid-acquisition.md`).
- Follow up once after a few days, then stop. Paid press-release wire distribution rarely
  produces coverage for a startup.

## After the launch

Attention decays within days. The launch's real result is the retained users it leaves behind.

1. **Greet early signups personally**: a plain email from the founder or a reply to each
   comment, asking what brought them.
2. **Activation follow-up** for launch signups who did not reach first value
   (`email-lifecycle.md`).
3. **Fix the top three blockers** seen in launch-week recordings and support, within the week.
4. **Collect testimonials** from launch users who activated.
5. **Publish a results or lessons post** a week or two later: numbers, surprises, what changed.
   It is a second launch moment for the build-in-public audience.
6. **Measure launch-cohort retention** against other sources. Launch traffic is often curious
   rather than in need and retains worse; judge the launch by retained and paying users.
7. **Thank supporters** individually and tell the list what comes next.

## Every major feature is a launch moment

A product that announces something every month looks alive and gives every channel a reason to
mention it again. Tier releases so effort matches impact:

| Tier | Qualifies | Channels |
|---|---|---|
| 1 | New product, major capability, new audience or market | The full sequence: list, blog post, communities, press, a Product Hunt relaunch if permitted, in-app |
| 2 | A meaningful feature for a segment, a notable integration | Changelog, email to the affected segment, in-app announcement, social posts, docs, the partner's channels |
| 3 | Improvements and fixes | Changelog, a monthly "what's new" roundup |

- Announce the outcome, not the feature: "Invoices now reconcile themselves" beats "Bank sync v2".
- Every tier 1 and tier 2 release ships with docs, a screenshot or clip, and a one-click way for
  existing users to try it.
- A public changelog is proof of momentum and raw material for the newsletter (release-notes
  practice: `0x:git-collaboration`).

## Ask the user

- **Is there a hard launch date, and what drives it?** Default: no fixed date; go public when
  drip cohorts activate reliably.
- **Is a launch offer acceptable, and which one?** Default: a time-limited discount for the first
  cohort, within the pricing rules (`0x:pricing-monetization`).
- **Which communities does the founder already belong to?** Default: launch only where the
  founder has a history; build standing elsewhere for the next launch.
- **What may be said publicly: numbers, customer names, the founder's story?** Default: no
  revenue figures or customer names without explicit consent.
- **Who answers comments and support on launch day?** Default: the founder, all day, with
  nothing else planned.
