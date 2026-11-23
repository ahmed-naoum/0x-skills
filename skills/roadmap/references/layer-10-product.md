# Layer 10: Product

Read this when: the user asks what there is to know about product, wants a study list or a gap check for this layer, or you need to see which skill and file owns a topic here.

What should I build next, and is it working for users?

Competencies: 86 (36 ● / 41 ◐ / 9 ○). ● core: every shipped product needs it   ◐ pro: needed once real users and money arrive   ○ expert: needed at scale or in special cases

Each heading is a skill (`0x:<name>`); each bold line is one of its reference files.

## product-discovery

Decide what to build and why: customer interviews, problem validation, jobs-to-be-done, MVP scoping, specs, prioritization and roadmaps, and the feedback loops that tell you whether it worked.

**Customer interviews and research** (`references/customer-interviews.md`)

- ● Recruit target-customer interviews through cold outreach and communities
- ● Run a non-leading interview about past behavior, not hypothetical futures
- ● Extract jobs-to-be-done, triggers and current spend from interview notes
- ● Synthesize interviews into ranked problems with evidence counts
- ◐ Pick the research method that fits the decision and deadline
- ◐ Write a survey without leading questions and interpret results cautiously
- ◐ Keep a weekly habit of customer conversations after launch
- ○ Maintain a research repository that links every insight to evidence

**Problem and demand validation** (`references/problem-validation.md`)

- ● Write a one-sentence problem statement naming who suffers and how often
- ● Define an ideal customer profile narrow enough to list 100 named prospects
- ● Map existing alternatives, including spreadsheets and doing nothing
- ● Score ideas on pain, payer clarity, reachability and founder advantage
- ● Test demand with a landing page, fake door or concierge test
- ● Set a falsifiable validation threshold and decide pivot, persevere or kill
- ◐ Collect pre-orders or letters of intent to prove willingness to pay
- ◐ Sign design partners who commit time and feedback before launch
- ◐ Estimate bottom-up market size from countable customers and realistic price
- ◐ Tear down a competitor's onboarding, pricing and reviews to find gaps

**MVP scoping** (`references/mvp-scoping.md`)

- ● Cut the MVP to one user, one job and one happy path
- ● Scope around the riskiest assumption and cut everything else
- ● Decide what to fake, do manually or buy instead of build
- ● Ship a narrow MVP in weeks and iterate on real usage
- ● Define what is good enough to charge for
- ◐ Set the quality bar per area: polish the core, stub the rest

**Specs and requirements** (`references/specs.md`)

- ● Write a one-page spec with problem, non-goals and a success metric
- ● Write user stories with acceptance criteria someone else can test
- ● Specify edge cases, states and error behavior before building
- ◐ Define in the spec how success will be measured and instrumented
- ◐ Review a spec with customers or teammates before committing
- ◐ Write a press release and FAQ first for a larger bet

**Prioritization and roadmaps** (`references/prioritization-roadmaps.md`)

- ● Prioritize the backlog by impact, confidence and effort
- ● Decide which feature requests to refuse and say no gracefully
- ◐ Balance customer requests, strategic bets and maintenance
- ◐ Run a quarterly roadmap process tied to metrics, not opinions
- ◐ Publish a now, next, later roadmap without committing to dates
- ◐ Decide to kill, pivot or double down on a feature from usage data
- ◐ Deprecate a feature using usage data and a migration notice
- ○ Delegate a product area with outcome targets instead of feature lists
- ○ Hire a first product manager once founder attention is the bottleneck

**Feedback loops and product-market fit** (`references/feedback-loops.md`)

- ● Onboard the first fifty users by hand and record every stumble
- ● Collect in-app feedback at the moment of use
- ◐ Turn support tickets and calls into tagged, counted product feedback
- ◐ Run churn-reason surveys and exit interviews
- ◐ Run win/loss interviews and fix the top objection
- ◐ Run a beta or early-access program for new features
- ◐ Tell users when the thing they asked for ships
- ◐ Judge product-market fit from retention, the 40% survey and organic pull

## product-analytics

Instrument the product and decide what to measure: event taxonomy and tracking, funnels and activation, cohorts and retention, north-star metrics and metric trees, A/B test design and its traps, and attribution.

**Event taxonomy and tracking** (`references/event-tracking.md`)

- ● Define an event tracking plan with consistent names and properties
- ● Choose an analytics tool: product suite, warehouse-first or both
- ● Track revenue and activation events server-side, where they are facts
- ● Instrument analytics that respect consent and minimize personal data
- ● Identify users and accounts across devices and anonymous sessions
- ◐ Validate events in tests so tracking does not silently break
- ○ Version and govern the tracking plan as the product changes

**Funnels and activation** (`references/funnels-activation.md`)

- ● Define the activation event that predicts retention and measure it
- ● Find the biggest drop-off in the signup-to-paid funnel
- ◐ Build conversion funnels segmented by source, device and plan
- ◐ Measure time to first value and what delays it
- ◐ Analyze feature adoption and what retained users do differently
- ◐ Separate correlation from causation in funnel findings

**Cohorts and retention** (`references/retention-cohorts.md`)

- ● Define active use in a way that reflects real value
- ● Build cohort retention curves and find where they flatten
- ◐ Track logo churn and net revenue retention by cohort
- ◐ Segment retention by acquisition channel, plan and persona
- ◐ Measure engagement depth: frequency, breadth and stickiness
- ○ Break growth into new, retained, resurrected and churned users

**North-star metric and metric trees** (`references/north-star-metrics.md`)

- ● Choose a north-star metric and the input metrics that move it
- ● Specify one weekly scorecard: the few numbers, their owners and targets
- ◐ Build a metric tree linking product inputs to revenue
- ◐ Write metric definitions once so everyone reports the same numbers
- ◐ Set guardrail and counter-metrics so one number is not gamed
- ◐ Run a weekly metrics review that ends in decisions

**A/B tests and their statistical traps** (`references/experiments.md`)

- ● Decide when traffic is too low to A/B test and what to do instead
- ◐ Design an A/B test with sample size, guardrails and a stopping rule
- ◐ Avoid peeking, multiple-comparison and novelty-effect traps
- ◐ Assign variants consistently and check for sample-ratio mismatch
- ◐ Write an experiment brief and record the decision and learning
- ○ Choose the randomization unit: user, account or session
- ○ Run holdouts to measure long-term retention effects

**Attribution** (`references/attribution.md`)

- ● Capture first-touch attribution with consistent UTM conventions
- ● Ask new users how they heard about you and reconcile with tracked data
- ◐ Connect acquisition source to revenue and retention, not only signups
- ◐ Choose an attribution model and know what it cannot tell you
- ◐ Track paid conversions server-side within consent limits
- ○ Attribute signups despite cookie loss and AI-referral traffic
- ○ Measure channel incrementality with holdouts or geo tests
