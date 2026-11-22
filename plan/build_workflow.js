// Workflow script for Claude Code's Workflow tool: writes and reviews the skills in plan/skills/*.json.
// args: { plan, build, date, lanes: [[{ name, stage?, writeEffort?, reviewEffort? }]], writeEffort?, reviewEffort? }
// Each lane runs its skills one after another (write, then review); lanes run in parallel.
// stage: "review" skips the writer for a skill whose draft is already published.
export const meta = {
  name: 'build-0x-skills-lean',
  description: 'Write each 0x skill from the plan in few steps, then adversarially review and fix it, publishing to GitHub after each stage',
  phases: [
    { title: 'Write', detail: 'one writer per skill: reference files, then SKILL.md, from knowledge' },
    { title: 'Review', detail: 'adversarial accuracy and coverage review with web search, fixes in place' },
  ],
}
const PLAN = args.plan
const BUILD = args.build
const DATE = args.date
const WRITTEN = {
  type: 'object',
  properties: {
    lines: { type: 'integer', description: 'total lines across all files of the skill' },
    uncovered: { type: 'array', items: { type: 'string' }, description: 'leaves you could not cover, with the reason; empty if all are covered' },
    doubts: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, claim: { type: 'string' } }, required: ['file', 'claim'] }, description: 'every claim you are not sure of, for the reviewer' },
    checker: { type: 'string', description: 'the last line check_skill.py printed' },
    published: { type: 'boolean', description: 'true if commit_skill.sh printed "committed"' },
  },
  required: ['lines', 'uncovered', 'doubts', 'checker', 'published'],
}
const REVIEW = {
  type: 'object',
  properties: {
    score: { type: 'integer', description: '1 to 5, the state of the skill after your fixes' },
    summary: { type: 'string', description: 'three or four sentences: what was wrong, what you changed, what remains' },
    fixes: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, was: { type: 'string' }, now: { type: 'string' } }, required: ['file', 'was', 'now'] }, description: 'the errors you corrected, most serious first, at most 12, each side in one short sentence' },
    unverified: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, claim: { type: 'string' } }, required: ['file', 'claim'] }, description: 'claims you could neither confirm nor rewrite durably' },
    weakest: { type: 'string', description: 'the weakest file or section that remains, and why' },
    checker: { type: 'string', description: 'the last line check_skill.py printed' },
    published: { type: 'boolean', description: 'true if commit_skill.sh printed "committed"' },
  },
  required: ['score', 'summary', 'fixes', 'unverified', 'weakest', 'checker', 'published'],
}
const LIMIT = `This build runs under a hard usage limit, and every step you take re-reads your whole context, so the number of steps is what costs. Put several tool calls in one step wherever they do not depend on each other.`

const writePrompt = name => `You are writing one skill of the 0x set: \`${name}\`. The set covers web development from the machine to the customer. Claude Code loads a skill when the task of a solo developer-founder falls in its area, and then follows it.

${LIMIT} Aim for about ten steps in all:

Step 1. In one step: read ${PLAN}/WRITING.md (the standard every skill follows: it decides what belongs in the files and how they are shaped), read ${PLAN}/skills/${name}.json (the plan entry: summary, useWhen, notFor, and the reference files with the competencies, called leaves, each must cover), read ${PLAN}/index.md (every sibling skill and its files), and list ${BUILD}/skills/${name}/ with its references folder. If files are already there, an earlier writer was cut off: read them in the next step, keep each one unless it misses the standard, and write only what is missing.

Next steps. Write the reference files into ${BUILD}/skills/${name}/references/ , two files per step (two Write calls in the same step), with the file names the plan gives. Write SKILL.md last, so its stance, route table and defaults reflect what the references really say.

Last step. Run this as one command:
python3 ${PLAN}/check_skill.py ${name} ${BUILD} && bash ${PLAN}/commit_skill.sh ${name} draft
If the checker prints anything, fix all of it with several Edit calls in one step and run the command again, until it prints "committed".

What makes a file good: before writing it, decide what a person with twenty years in exactly that territory does differently from a competent generalist: the handful of decisions, numbers, sequences and traps that matter. Build the file around those, and make sure every leaf the plan lists for the file is covered. A file that reads like documentation or a tutorial has failed, however correct it is. Aim for 150 to 220 lines per reference file, all of it signal.

Do not use web search, do not install or run anything to test, and do not explore the machine: a reviewer with web search checks every claim after you. Write from what you know. Today is ${DATE}. Where a fact changes over time (versions, limits, prices, vendor features, browser support, legal thresholds and dates) and you are not certain of it, state the point durably without the number. Commands, configuration and code must be right: keep snippets short and write only what you are sure of. List every claim you are unsure of under doubts, so the reviewer checks those first.

The files are reference documents for a model, not chat replies: no first person, no conversational framing, no confidence tags, no emojis.

Then return the report.`

const reviewPrompt = (name, w) => `You are the adversarial reviewer of one skill of the 0x set: \`${name}\`. Claude Code will follow this skill while building and running a real product for a solo developer-founder. A wrong instruction here costs that person money, data, a security hole or a legal problem, and they will not know enough to catch it. The writer worked from memory, without web search and without running anything. Assume the draft contains errors. Your job is to find them and fix them in the files.

${LIMIT} Aim for about twelve steps in all:

Step 1. In one step, read ${PLAN}/WRITING.md (the standard the skill must meet), ${PLAN}/skills/${name}.json (the plan entry: the reference files and the competencies, called leaves, each must cover), ${BUILD}/skills/${name}/SKILL.md and every file in ${BUILD}/skills/${name}/references/ . ${PLAN}/index.md lists the sibling skills, if you need to see who owns a neighboring topic.

Then accuracy, which matters most. From your reading, collect the claims that could be wrong: commands and flags, code, configuration syntax, SQL, HTTP headers and status codes, defaults, limits, thresholds and other numbers, formulas, and statements about what a tool, protocol, browser, vendor or law does. Most of them you can judge from what you know. For those that change over time, or that you are not sure of, use WebSearch (load it with ToolSearch, query "select:WebSearch"): several searches in one step, about fifteen in all, spent on the claims that carry the most weight. Today is ${DATE}. If commands or code need a syntax check, put them in one script and run it once; bash, Python 3 and Node.js are here, and nothing should be installed.
Look hardest at advice that is dangerous when wrong: anything touching authentication, secrets, permissions, deleting or migrating data, backups, money and billing, cryptography, legal or tax statements, and anything stated with "always" or "never".
The writer flagged these doubts; settle every one: ${w && w.doubts && w.doubts.length ? JSON.stringify(w.doubts) : '(none reported; find your own)'}
Where a number or vendor fact cannot be confirmed, replace it with durable wording that tells the reader to check the current value. Delete invented statistics, benchmarks and case studies. Legal, tax and accounting statements must describe the mechanism and common practice, say where jurisdictions differ, and never present one country's rule as universal.

Then coverage and usefulness:
- Every leaf in the plan entry must be covered in its file well enough that the reader could do that thing: at least the decision rule and the main trap. Add what is missing.${w && w.uncovered && w.uncovered.length ? ' The writer reported these as not covered: ' + JSON.stringify(w.uncovered) : ''}
- Cut or replace text that could sit unchanged in a beginner tutorial. Do not pad: a shorter file that is all signal beats a longer one.
- Advice must say which stage it applies to (Prototype, Launch, Scale) wherever that changes the answer, and named defaults must agree with the house defaults in the standard.
- SKILL.md: the description must win this skill's requests and not a sibling's; the route table must send each kind of task to the right file; "Before you call it done" must be checks someone can actually perform.
- Each reference file ends with "Ask the user" entries that are real business, money, risk or legal choices, each with the default to assume.

Apply all fixes in place with precise Edit calls, many in one step. Do not rewrite a whole file unless it is beyond repair.

Last step. Run this as one command:
python3 ${PLAN}/check_skill.py ${name} ${BUILD} && bash ${PLAN}/commit_skill.sh ${name} review
If the checker prints anything, fix it and run the command again, until it prints "committed".

Report honestly. Under unverified, list the claims you could neither confirm nor rewrite durably. Score the final state from 1 to 5: 5 means you would stake your reputation on Claude following it exactly as written; 3 means useful but with weak files; 1 means it should be rewritten.`

// Reasoning effort per stage: set writeEffort / reviewEffort on a lane item or in args; unset inherits the session's.
const effortOf = e => (e ? { effort: e } : {})

const results = await parallel(args.lanes.map(lane => async () => {
  const out = []
  for (const item of lane) {
    const name = item.name
    let w = null
    if (item.stage !== 'review') {
      w = await agent(writePrompt(name), { label: `write:${name}`, phase: 'Write', schema: WRITTEN, ...effortOf(item.writeEffort || args.writeEffort) })
      if (!w) {
        log(`${name}: the writer did not finish; skipping its review`)
        out.push({ name, written: false, reviewed: false })
        continue
      }
      log(`${name}: draft written, ${w.lines} lines, ${w.doubts.length} doubts, checker "${w.checker}"`)
    }
    const r = await agent(reviewPrompt(name, w), { label: `review:${name}`, phase: 'Review', schema: REVIEW, ...effortOf(item.reviewEffort || args.reviewEffort) })
    if (r) log(`${name}: reviewed, score ${r.score}/5, ${r.fixes.length} fixes, ${r.unverified.length} unverified`)
    else log(`${name}: the reviewer did not finish`)
    out.push({
      name, written: true, reviewed: !!r,
      lines: w ? w.lines : null, uncovered: w ? w.uncovered : null,
      score: r ? r.score : null, summary: r ? r.summary : null, weakest: r ? r.weakest : null,
      fixes: r ? r.fixes.length : null, topFixes: r ? r.fixes.slice(0, 5) : null, unverified: r ? r.unverified : null,
      checker: r ? r.checker : (w ? w.checker : null), published: r ? r.published : (w ? w.published : false),
    })
  }
  return out
}))
return results.filter(Boolean).flat()
