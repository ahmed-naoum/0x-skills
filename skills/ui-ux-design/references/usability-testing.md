# Usability testing and design review

Read this when: checking whether people can actually use a design or prototype; planning or running test sessions; writing test tasks; recruiting participants; reading session replays; reviewing a screen against usability heuristics; running a design critique.

## Pick the method by the question

| Question | Method | Cost |
|---|---|---|
| Are there obvious usability defects? No users available yet | Heuristic review | 1 to 2 hours |
| Can people complete this flow, and where do they stumble and why? | Moderated think-aloud test, five participants | 1 to 2 days |
| Where do real users struggle in the live product? | Session replays plus funnel data | Hours; needs traffic |
| Do people click the right place first on this layout? | First-click test, unmoderated | Hours; needs a tool and a panel |
| Does a fix measurably work at larger sample sizes? | Unmoderated task test | 1 to 2 days |
| Can people find things in this structure? | Tree test (see `information-architecture.md`) | 1 to 2 days |
| Which of two designs performs better on a metric? | A/B test; see `0x:product-analytics` | Weeks; needs volume |
| Is this the right problem or feature? | Not usability testing; see `0x:product-discovery` | |

Usability testing tells whether people *can* use something, not whether they *want* it. Participants being polite about a prototype is not demand.

Stage guidance: at Prototype, a heuristic review and three to five hallway sessions on the core flow. At Launch, five-user tests on signup, onboarding and the core task, plus weekly replay review. At Scale, a regular cadence and unmoderated tests for quantitative checks.

## The five-user test

Five participants from one user group, each attempting the same tasks while thinking aloud, expose most of the serious problems in the tested flow.
The figure comes from a model in which each participant reveals roughly a third of the problems; it is a rule of thumb, and it holds only per distinct user group and per flow. It finds problems; it does not measure rates. Never report "60% of users failed" from five sessions.

The better plan is several small rounds: test five, fix, test five more on the revised design. Three rounds of five beat one round of fifteen.

### Sequence

1. **Decide the questions** (three at most): "Can a new user create and send an invoice without help?"
2. **Write three to five tasks** as scenarios (next section) with a success definition for each.
3. **Prepare the prototype or build** with realistic but invented data and a test account that can be reset between sessions. Never a real customer's records: the session is recorded and the participant is a stranger.
4. **Pilot once** with anyone available. The pilot always finds a broken link, an ambiguous task or a missing state; fix those before real participants.
5. **Recruit five**, plus one spare for no-shows.
6. **Run sessions** of 30 to 45 minutes, recorded with consent (screen, voice, and face if agreed).
7. **Debrief within the hour** and log observations while memory is fresh.
8. **Rank the issues** and decide fixes the same week.

### Running a session

| Phase | Minutes | Content |
|---|---|---|
| Opening | 3 | "The design is being tested, not you. Nothing you do is wrong. Please say what you are thinking as you go. I did not design this, so you cannot hurt my feelings." Ask permission to record |
| Warm-up | 3 to 5 | Their role and how they handle this job today; confirms they match the profile |
| Tasks | 20 to 30 | One at a time, read aloud and shown in writing; observe |
| Wrap-up | 5 | "What was hardest? What did you expect that was missing? Anything else?" |

Moderator rules, in order of how often they are broken:

- **Do not help.** When the participant is stuck, wait. Count to ten silently. The struggle is the data. Help only when they give up, and record the task as failed.
- **Answer questions with questions**: "What would you expect it to do?" "What are you looking for?"
- **Do not explain or defend the design**, during or after.
- **Prompt thinking aloud neutrally**: "What are you thinking?" Never "Did you see the button at the top?"
- **Watch behavior over opinion.** What people do outranks what they say they would do; "I liked it" from someone who failed the task is a failure.
- **Do not ask participants to design.** A feature request is a signal of a problem; ask what they were trying to accomplish.
- Founders moderating their own product must be strictest about these rules; the urge to explain is strongest for the person who built it. A second person taking notes helps.

### Ranking the issues

Log each observation as: task, what happened, quote or timestamp, participant. Merge duplicates, then score.

| Severity | Definition | Action |
|---|---|---|
| 4 Blocker | Prevents completing the task | Fix before release |
| 3 Major | Completed only with significant delay, errors or workarounds | Fix before release or next iteration |
| 2 Minor | Hesitation or annoyance; task completed | Schedule |
| 1 Cosmetic | Noticed, no effect on the task | Batch with other work |

Rank by severity, then by frequency (how many of the five), then by how central the task is. A blocker seen once on the core flow outranks a minor issue seen five times.
Record whether each issue is in the flow, the layout, the wording or the concept, because the fix differs. The output is a list of at most ten issues with a proposed fix and an owner, not a report. Also note what worked, so it is not redesigned away.

## Task scenarios that do not lead

A task gives a goal and a context, never the route.

| Leading | Neutral |
|---|---|
| "Click New Invoice and add a line item." | "You finished a website job for Acme for 1,200 dollars. Bill them." |
| "Use the filter to find overdue invoices." | "Find out which customers are late paying you." |
| "Go to Settings and invite a teammate." | "Your colleague Sam needs to be able to send invoices too. Make that possible." |
| "Do you find the dashboard useful?" | "You just logged in on Monday morning. What would you do first?" |

Rules:

- **Do not use the words on the screen.** If the button says "Invoice", the task says "bill". Otherwise the test measures word matching.
- **Give the data needed** (names, amounts) so the participant does not have to invent it, and so sessions are comparable.
- **One goal per task**, with an observable end state defined in advance: what counts as success, as success with difficulty, and as failure.
- **Order tasks as a real session would go**, first use first. Put the most important task early, in case time runs out.
- **Avoid hypotheticals and opinion questions** during tasks ("Would you use this?"). Save impressions for the wrap-up and weigh them lightly.
- **Include one task that should hit an edge**: an empty state, an error, an undo.
- Where a rating helps comparison across rounds, ask one question after each task: "Overall, how easy or difficult was that?" on a seven-point scale. Treat it as a direction, not a statistic, at this sample size.

## Recruiting quickly and cheaply

Match behavior, not demographics: people who do the job the product serves, at the experience level of the target user.

| Source | Good for | Watch for |
|---|---|---|
| Existing users (in-app prompt, email to recent signups) | Tests of new features and of advanced flows | Too expert for first-run tests; they already know the product |
| Waitlist and recently churned signups | First-run and onboarding tests | Small pool |
| Personal network once removed (friends of friends in the target role) | Prototype stage | Politeness; never close friends or family |
| Communities where the audience gathers | Niche professional audiences | Follow the community's rules on solicitation |
| Recruiting panels and testing platforms | Speed, consumer audiences, unmoderated tests | Professional testers who rush; screen carefully |
| Anyone nearby (hallway test) | Catching gross problems in labels and layout | Not valid for domain-specific tasks |

- **Screener**: three to five questions that identify behavior without revealing the wanted answer. Ask "Which of these did you do in the past month?" with distractors, not "Do you send invoices?". Include one open question; a thoughtful answer predicts a useful participant.
- **Incentive**: pay for people's time at a rate appropriate to their profession; gift cards or account credit are common. Busy professionals need more; existing customers often accept credit or early access. Two traps: employees of public bodies and of some regulated companies may not accept gifts at all, so ask before sending one; and payments to individuals can carry tax-reporting duties above thresholds that differ by country, which matters once incentives are large or repeated.
- **Logistics**: schedule with a booking link, send a reminder the day before, over-recruit by one, keep sessions remote by default (video call with screen share) and test their ability to share a screen in the first minute.
- **Do not reuse the same participants for first-run tests**; they are no longer new.
- **Consent and data**: get explicit agreement before recording starts, in writing or spoken on the recording; say how the recording is used, who sees it and for how long it is kept, and store it with access limits. Do not publish clips or named quotes without separate permission. Recruit adults only unless minors are the audience, which needs a guardian's consent and legal advice. Recordings are personal data; requirements belong to `0x:privacy-compliance`.

## Session replays

Replays show where; they rarely show why. Use them to locate problems and to choose what to test with people.

Start from a signal, not from random sessions:

1. Open the funnel for the flow and find the step with the largest drop (funnels belong to `0x:product-analytics`).
2. Filter replays to sessions that reached that step and did not complete it; watch 10 to 20, at increased speed, slowing down at the trouble spot.
3. Add filters for frustration signals where the tool offers them: rage clicks (repeated fast clicks on one spot), dead clicks (clicks on something that does nothing), error events, rapid back-and-forth navigation, long idle time on a form field, form abandonment.
4. Segment before concluding: new or returning, device class, browser, plan. A problem present only on small phones is a layout bug, not a concept problem.
5. Tag each observation with the same severity scale as test findings, and count sessions affected.
6. For any pattern that is not self-explanatory, run a five-user test or ask affected users directly.

What replays reveal well: elements that look clickable and are not, controls that are missed, fields that cause repeated correction, loops between two pages, layout breakage at real viewport sizes, confusing error states. What they do not reveal: intent, expectations, and anything about people who never arrived.

Traps: watching without a question (hours gone, nothing decided); generalizing from the few most dramatic sessions; ignoring that replays record only consenting, non-blocked users. Mask all input fields and sensitive on-screen text by default, and exclude payment and authentication pages; replay tools capture personal data and need the same care as any other processor.

Replay is also the analytics feature most likely to create legal exposure. In the EU and UK it generally needs the visitor's consent before recording starts. In the United States it has drawn many lawsuits under wiretapping and interception laws, with courts disagreeing on the outcome; the recurring allegation is recording that began before any consent was given. Design for the mechanism: the recorder loads only after whatever consent the visitor's jurisdiction requires, the privacy notice names the tool, and masking is on by default. Which rule applies to this product's visitors is a question for `0x:privacy-compliance`, and for a lawyer where the product handles health, financial or children's data.

## Heuristic review

Walk the two or three core tasks as a new user, twice (once to get the flow, once to inspect), and check each screen against the ten usability heuristics (Nielsen). Record each violation with the screen, the heuristic, a severity from the scale above and a proposed fix.

| Heuristic | What to look for in practice |
|---|---|
| Visibility of system status | Feedback within 100ms of every action; progress for waits; saved or unsaved state; where the user is |
| Match with the real world | The user's words, not internal terms; natural order; dates, numbers and currency in the user's format |
| User control and freedom | Undo, cancel, back that works, a way out of every dialog and flow |
| Consistency and standards | Same word and same control for the same thing; platform conventions (links look like links, primary action placement) |
| Error prevention | Constraints, sensible defaults, confirmation only for the irreversible, inline validation at the right time |
| Recognition rather than recall | Options visible; recent items; no need to remember values from an earlier screen |
| Flexibility and efficiency | Shortcuts, bulk actions, defaults that remember; nothing that slows a novice |
| Aesthetic and minimalist design | Each element competes with every other; remove what does not serve the task |
| Help users recover from errors | Plain message, cause, next step, input preserved (see `microcopy.md`) |
| Help and documentation | Help at the point of need; searchable; task-oriented |

- One reviewer finds a minority of the issues; two or three independent reviewers who then merge lists find far more. For a solo founder: do one pass, then have an agent or a colleague do an independent pass before comparing.
- Review the unhappy paths: wrong input, empty account, slow network, permission denied, small screen.
- A heuristic review predicts problems; it over-reports minor issues and misses domain-specific ones. It is a filter before user testing, not a replacement.
- Add a quick accessibility pass at the same time (keyboard only, 200% zoom, contrast); the full method belongs to `0x:accessibility`.

## Design critique that ends in decisions

A critique evaluates a design against its goals. Without stated goals it becomes a taste contest.

1. **Presenter frames** (2 minutes): the user, the job, the constraints, the stage of the work, and the specific question ("Is the primary action clear?" not "Thoughts?").
2. **Silent review** (3 to 5 minutes): everyone looks and writes notes separately. This prevents the first speaker from anchoring the room.
3. **Clarifying questions only.**
4. **Feedback, tied to goals**: "Because the goal is X, this element does Y, which helps or hurts." Describe the problem; leave the solution to the designer unless asked.
5. **Decide and record**: each point becomes one of *change* (with owner), *test with users* (when it is a prediction about behavior), or *no change* (with the reason). One named person makes the call when views differ.

Ground rules: critique the work at the fidelity it is in (no color comments on wireframes); "I like" and "I do not like" are replaced by an effect on the user; disagreements about what users will do are settled by a test, not by seniority; keep it to 30 minutes.
A solo founder can run the same structure with an agent or an advisor: state goals and the question, ask for problems ranked by severity against those goals, then decide in writing.

## Unmoderated and first-click tests

Use unmoderated tests when the question is narrow and numbers matter, or when schedules make moderated sessions impractical. They trade depth for scale: nobody can ask "why", and nobody can rescue a participant from a broken prototype.

- **Unmoderated task test**: participants follow written tasks on a prototype or live site, recorded. Write tasks even more carefully than for moderated tests, one at a time, with an unambiguous end condition. Limit to three to five tasks and about 15 minutes.
  Pilot with two people first; an unclear task wastes the whole batch. For rough completion rates use 20 or more participants per variant, as a rule of thumb; five to eight suffice when only watching recordings for problems.
- **First-click test**: show a screenshot or mockup, give a task, record where the participant clicks first and how long it takes. A correct first click strongly predicts eventual task success, so this is a cheap check of layout and labels before anything is built.
  Reading results: clustered clicks on the right target is the goal; scattered clicks mean no clear affordance; a cluster on a wrong element means that element promises the wrong thing. Use roughly 30 or more participants per design to compare two layouts, as a rule of thumb; at that size only a large difference is real, so treat a close result as a tie.
- **Five-second test**: show a screen for five seconds and ask what it was about and what could be done there. Checks first impression and hierarchy; unsuitable for evaluating flows.
- **Quality control**: add an attention-check question, discard sessions completed implausibly fast, and screen as for moderated tests.
- Testing platforms and their panels change often; compare current options and prices when needed rather than assuming one.

## Checks

- Each test round had written questions, tasks with success criteria and a pilot.
- No task wording contained a label from the screen.
- Findings are logged with severity, frequency and evidence, capped at about ten, each with a decision.
- No percentage is reported from fewer than about 20 participants.
- Blockers and majors from the previous round were retested after the fix.
- Recordings and replays have consent, masking and a retention period.
- A critique ended with a written list of change, test or no change.

## Ask the user

- **Who exactly is the target user, by role and behavior?** Testing with the wrong people gives confident wrong answers. Default: people who performed the core job in the past month.
- **Are there existing users or a waitlist that can be contacted?** Decides the recruiting route. Default: recent signups first, then the extended network.
- **What can be spent on incentives and tools?** Sets moderated versus panel-based methods. Default: five moderated remote sessions with a modest incentive, no paid platform.
- **Which flow matters most to the business right now?** Tests cover few tasks. Default: signup through first value.
- **Is session replay already enabled, and is it covered by the privacy policy and consent setup?** Must be settled before relying on it. Default: not enabled; enable with input masking after confirming consent requirements.
