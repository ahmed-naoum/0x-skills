# Customer interviews and research

Read this when: planning who to talk to and how to reach them, writing an interview guide,
running interviews or surveys, turning notes into ranked problems, or setting up a research
habit and repository after launch.

## Pick the method from the decision, not from habit

Write down the decision the research must inform and the date it must be made. The method
follows from that; most wasted research answers a question nobody was going to act on.

| Decision to make | Method | Typical time | Sample |
|---|---|---|---|
| Is there a problem worth solving, and for whom? | Problem interviews about past behavior | 1–3 weeks | 8–15 per segment |
| Why did people buy or switch to what they use now? | Switch (jobs-to-be-done) interviews with recent buyers | 1–2 weeks | 6–10 recent switchers |
| What do users of existing tools hate? | Review and forum mining | 1–2 days | 50–200 reviews |
| How common is a problem already understood? | Survey with closed questions | 1–2 weeks | 100+ responses from the segment |
| Will they pay? | Pre-sale or letter of intent, not interviews (`problem-validation.md`) | 1–4 weeks | Real commitments |
| Can people use this design? | Usability test → `0x:ui-ux-design` | Days | About 5 per round |
| How many do X in the product, where do they drop? | Product analytics → `0x:product-analytics` | Hours | All users |
| Why are customers leaving or not buying? | Exit and win/loss interviews (`feedback-loops.md`) | Ongoing | 8–10 per outcome |

- Interviews find out what and why; surveys and analytics measure how many. Run them in that
  order. A survey written before interviews only offers the options the founder imagined.
- When the deadline is days, mine what already exists before recruiting anyone: support tickets,
  sales notes, competitor reviews, community threads, the words people search with.
- Observed behavior (spend, workarounds, tickets, usage) outranks anything said about the future.
  When the decision involves money, choose a method that captures behavior.

## Recruit the right people

Screen on behavior, not identity or interest. "Ran payroll for a team of 5–50 in the last month"
finds people with the problem; "small-business owner interested in HR software" finds people who
like answering questions.

Sources, in the order they usually pay off for a solo founder:

1. **Second-degree introductions.** Ask everyone already known for two people who do the job,
   and end every interview with the same ask. Warm introductions convert far better than cold
   messages; watch that the sample does not become one friend group.
2. **Cold outreach to a named list.** Build the list from the ICP (`problem-validation.md`): job
   titles on professional networks, business directories, conference speaker lists, people who
   posted publicly about the problem. Personalize the first line to something real.
3. **Communities.** Forums, subreddits, Slack and Discord groups where the ICP talks shop. Read the
   rules, ask the moderator before posting, contribute answers first. Ask for conversations about
   the problem; never post a product pitch.
4. **Existing signups and waitlists.** Already biased toward the idea: useful for depth on the
   solution, weak for proving the problem exists.

```text
Subject: Question about how you handle <job>

Hi <name>, I saw <specific real thing>. I'm researching how <role>s deal with <job> and would
value 20 minutes on how you do it today. I'm not selling anything, and I'm happy to share what
I learn across these conversations. Would <two specific times> work?
```

- Do not describe the idea in the outreach. It filters toward fans and turns the call into a
  pitch the person politely agrees with.
- "Not selling anything" must stay true. Pitching on a call booked under that promise burns the
  contact and the channel.
- Send in batches of 20–30, measure the reply rate, and fix the targeting or the first line before
  sending more. Most cold messages go unanswered; that is a reason to send more, not to widen
  the target.
- Incentives: professionals often accept the findings summary or a small donation; consumers
  usually need a gift card. Keep it modest; a large incentive attracts people who fake the
  screener.
- Five to eight interviews per segment usually show repeating patterns (rule of thumb). If ten
  still show no pattern, the segment is too broad: split it rather than adding interviews.

## Run the interview: past behavior, not hypotheticals

People predict their own behavior badly and are kind about other people's ideas. Ask about the
last specific time something happened, and stay inside that story.

| Instead of | Ask | Why |
|---|---|---|
| "Would you use a tool that …?" | "Tell me about the last time you had to <job>." | Hypotheticals produce polite yeses |
| "How much would you pay?" | "What do you spend on this today, in money and hours?" | Stated prices are fiction; current spend is fact |
| "Is <problem> a pain for you?" | "What's the hardest part of <job>?" | The leading version names the answer |
| "Do you usually …?" | "When did that last happen? Walk me through it." | "Usually" invites the idealized version |
| "Would this feature help?" | "What have you tried to fix that? What happened?" | No attempted fix means low pain |

Structure for a 20–30 minute call:

1. Context (2 min): their role, team, what a normal week involves.
2. Last instance (15 min): "Tell me about the last time…". Follow the timeline: what triggered it,
   each step, who else was involved, which tools, where it went wrong, how long it took, what it
   cost.
3. Attempts (5 min): what they have tried, bought, built or abandoned, and why.
4. Wrap (3 min): "What should I have asked?", then an ask that costs them something: a follow-up
   call, an introduction to a colleague or the budget owner, or a pilot.

During the call:

- Talk less than a fifth of the time. Silence after an answer draws out the useful second answer.
- Dig on emotion and workarounds: "Why was that frustrating?", "How did you get around that?"
- Deflect compliments and generalities back to facts. "Sounds great!" carries no information;
  "We pay an assistant eight hours a week to do this" does.
- Do not demo or describe the idea until the problem part is finished, and preferably not at all
  in a first interview.
- Record only with consent asked at the start; otherwise note key phrases verbatim. Write up the
  same day, while memory still fills the gaps.
- The founder runs these. Delegated interviews lose the follow-up question that matters.

Switch interviews, with people who recently bought or changed tools, reconstruct the purchase as
a timeline: the first thought that something had to change, passive looking, the event that
started active looking, what was compared, what nearly stopped them, the moment of deciding. Map
four forces: the push of the current situation, the pull of the new solution, anxiety about the
new one, habit of the old. A new product wins only when push plus pull exceed anxiety plus habit;
the interview shows which side needs work (often reducing anxiety, through migration help or a
trial, beats adding pull).

Signs an interview was wasted: mostly opinions and futures, a pitch happened, no numbers were
heard, the next step was "keep me posted".

## Extract the job, trigger and spend from each interview

Turn each interview into one card the same day. Empty fields become the next interview's
questions.

| Field | What to write |
|---|---|
| Who | Role, company type and size, segment tag ("solo marketer at a 20-person B2B SaaS", not "marketer") |
| Job | When <situation>, I want to <motivation>, so I can <outcome>. A feature is not a job |
| Trigger | The event that made the job urgent this time ("board report due Friday") |
| Current solution | The actual tools, people, files or vendors, or "nothing" |
| Spend | Money, hours per week or month, people involved, each with unit and period |
| Frequency | Daily, weekly, monthly, quarterly, once |
| Pain rung | Highest rung reached on the ladder below |
| Buyer | Who approves money for this, and whether that person feels the pain |
| Quotes | Two or three verbatim lines with timestamps |

Pain ladder, weakest to strongest: mentions it when asked → raises it unprompted → has looked
for a solution → has built a workaround → pays for a workaround (a tool, a contractor, staff time
assigned to it) → has budget allocated and is actively replacing the current solution. Rank
interviews by the highest rung reached, not by how loudly the pain was described.

## Synthesize into ranked problems with evidence counts

After each batch of about five interviews:

1. Split the cards into atomic observations: one fact or quote each, tagged with interview ID.
2. Cluster by underlying problem, not requested feature. "Slack integration" and "email alerts"
   may both be the problem "I miss changes to X".
3. Count per problem and per segment: raised unprompted, has a workaround, pays today.
4. Rank by those counts, with pain rung and frequency as tie-breakers.

```text
| Problem                           | Segment         | Unprompted | Workaround | Pays today | Freq    | Evidence         |
|-----------------------------------|-----------------|------------|------------|------------|---------|------------------|
| Reconciling X by hand at month end| Agencies 10-50  | 7/9        | 6/9        | 3/9        | Monthly | I-03, I-07, I-11 |
| Clients miss approval requests    | Agencies 10-50  | 4/9        | 2/9        | 0/9        | Weekly  | I-02, I-05       |
```

- Report "7 of 9", never percentages, at interview scale.
- Keep prompted mentions in a separate column or drop them; a problem raised only when asked is
  rarely the one people pay to fix.
- Do not merge segments. A problem 7 of 9 agencies have and 0 of 6 freelancers have is a
  segmentation finding, not a 7-of-15 problem.
- For the top problem, write what evidence would disprove it and look for it in the next batch.
  Synthesis by the person who wants the idea to work drifts toward confirmation.
- Stop interviewing on a question when two consecutive batches add no new problem cluster; move
  on to quantifying or testing.

## Surveys: write them neutrally, read them skeptically

Use a survey when the answer options are known from interviews and the question is how common
they are. Never use one to discover the problem.

Writing:

- Ask about behavior in a bounded recent period ("In the last 30 days, how many times did you…"),
  not attitudes or intentions.
- One concept per question; "How fast and reliable is…" is two questions.
- Neutral wording and balanced scales, with as many negative as positive options.
- Include "None", "Other (specify)" and "Not applicable"; forcing a choice manufactures data.
- Randomize the order of unordered options; position biases picks.
- Screening and behavior questions first, demographics last, under five minutes in total.
  Respondents drop out with each extra minute, and not at random.
- Pilot with three people from the segment, watching them answer, before sending.

Reading:

- Respondents chose to answer and are more engaged than the population; say so in every summary.
- Stated intent ("would buy", "very likely") overstates behavior by a wide margin. Use it to rank
  options against each other, never as a forecast.
- Sampling error for a proportion at 95% confidence is at most about ±1/√n: roughly ±10 points at
  100 responses, ±5 at 400. It covers random noise only, not who chose to respond.
- Under about 30 responses in a segment, report raw counts, not percentages.
- Code open-text answers into categories and count them; quotes explain, counts decide.

## Keep talking to customers every week after launch

Discovery that stops at launch goes stale within months. The habit: at least one customer
conversation every week, booked automatically so it survives busy weeks.

- Automate recruiting: a line in the onboarding email and an occasional in-app prompt offering a
  20-minute call, with a booking link to a standing weekly slot.
- Rotate who is talked to: new signups (first-run friction), power users (what to deepen), trials
  that did not convert, churned accounts (`feedback-loops.md`).
- Bring the question behind the decision currently in flight, and still start with the last real
  instance of the job.
- Fill the same card, add the observations to the repository, and review the ranked problem table
  at the weekly planning session.
- Count conversations per week. Two weeks at zero means the habit has broken.

By stage: at Prototype, interviewing is most of the work. At Launch, the weekly habit is
mandatory. At Scale, everyone making product decisions keeps it, not only the founder.

## A research repository that links insights to evidence

Skip a dedicated tool until about twenty interviews or a second person doing research; before
that, one folder of cards and the ranked problem table are enough. Then use four linked layers:

| Layer | Content | Rule |
|---|---|---|
| Sources | Recordings, transcripts, notes, ticket exports | Date, participant ID, segment, consent status |
| Observations | One fact or quote each | Links to exactly one source |
| Insights | A claim about customers | Links to at least three observations from more than one source |
| Decisions | What was built, cut or changed | Links to the insights that justified it |

- An insight without linked observations is an opinion; label it a hypothesis.
- Date every insight and re-check those older than about a year; markets and tools move.
- Tag observations with the same problem and segment vocabulary as support tickets, so interview
  and ticket evidence count together.
- Store participants under IDs with contact details in one place, and set a retention period for
  recordings. Recordings are personal data; consent and deletion rules apply
  (`0x:privacy-compliance`).
- Any tool works (a docs database, a spreadsheet, a research tool) as long as tag search and the
  links survive.

## Ask the user

- **What decision does this research inform, and by when?** It sets the method and the sample.
  Default: decide within three weeks whether to build for the top problem.
- **Which segment first?** Mixing segments in one round produces averaged mush. Default: the
  segment the founder can reach fastest and knows best.
- **Can the founder run the calls personally?** Delegating loses the follow-up questions.
  Default: yes, about five per week during discovery.
- **Is there a budget for incentives?** Default: none for professionals beyond a findings
  summary; a small gift card for consumers.
- **May calls be recorded, and how long may recordings be kept?** Default: record with consent
  asked at the start, delete recordings after synthesis, keep pseudonymized notes.
