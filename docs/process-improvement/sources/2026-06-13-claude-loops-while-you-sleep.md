Source: https://x.com/i/status/2065807526268920103
Article: https://x.com/i/article/2065759873225072640 (via https://t.co/IXGLJU9dce)
Author: Hanako (@hanakoxbt) · Telegram: https://t.me/+75nMf005jRpjMDU1
Posted: 2026-06-13
Captured: 2026-06-29 (image-based gist) · UPDATED 2026-06-30 (full article body added)
Capture method: ADHX API (twitter-x skill Option A) returned the complete `article.content` (6,472 chars) — verified-complete, not reconstructed
Media: 4 images saved under ./img/claude-loops-sleep-*.jpg

# How to Set Up Claude Loops That Keep Working While You Sleep (Step by Step)

The tweet itself is just a link; the substance is in the linked X-native article.
**Capture history:** the first pass (2026-06-29) reconstructed the gist from the 4 carousel
images + an API summary and was only PARTIAL — it missed several prose-only sections. On
2026-06-30 the full article body was fetched via the ADHX API and is included verbatim below
under "Full article text", so this note is now self-contained and complete even if the post
is deleted. The image-derived summary is kept as the quick-read; the full text is authoritative.

## Thesis
Stop typing one prompt at a time. A single prompt **runs once and dies**; a **loop** is
Claude scheduled on cron that **shows up on its own schedule** and keeps working unattended.
Stack several narrow loops and one person gets the output of a team that never logs off.

Progression: **one prompt at a time → set once, runs forever → works while you sleep.**

## The three levels (cover image — `img/claude-loops-sleep-cover.jpg`)
1. **A loop** — Claude scheduled on cron; runs itself, no prompt needed. `$ claude loop --cron 5m` → `active`. (repeats · no human)
2. **Many loops** — each owns one job, all running side by side at once (e.g. babysit PRs / fix CI, cluster feedback). (parallel)
3. **Routines** — the same loops on a server; keep running with the laptop closed. `trigger: webhook` → running overnight. (on server · 24/7)

## Step 1 · The Loop (`img/claude-loops-sleep-step1.jpg`)
"A single prompt runs once. A loop runs on its own, forever." No framework — just Claude scheduled on cron.

```
$ claude "watch CI, fix breaks"
schedule: cron every 5m
✓ loop active
runs again in 5:00...
```
- **Pick the interval** — tight for fast things, nightly for slow ones.
- **It repeats itself** — no human kicks it off, ever again.
- **You walk away** — the job shows up on its own schedule.

What changes: *type a prompt → runs once, dies* **vs** *set a loop → shows up on its own.*

## Step 2 · Run Them in Parallel (`img/claude-loops-sleep-step2.jpg`)
"One loop is useful. A stack of them is a team that never logs off." Each loop owns one job; they run side by side, without you. Example fleet:

| Loop | Job | Cadence |
|---|---|---|
| **PR babysitter** | Watches open PRs, auto-rebases, fixes failing CI before you see it | every 5 min |
| **CI medic** | Keeps the test suite green, patches flaky tests on its own | every 10 min |
| **Feedback cluster** | Pulls feedback from a feed, groups it into clean themes | every 30 min |
| **Nightly report** | Summarizes the day's work so it's waiting for you in the morning | once, overnight |

Rule of thumb: **anything you do more than twice is a loop waiting to exist.** → one person, the output of a team.

## Step 3 · A good loop has a narrow job (`img/claude-loops-sleep-step3.jpg`)
"A good loop has a narrow job. A bad loop is just a wish." The tighter the task, the more you can trust it running without you.

| Property | A real loop | A wish |
|---|---|---|
| schedule | Runs on cron, every 5m or nightly | No schedule — when does it run? |
| scope | One job it cannot misread | Fuzzy — interprets it ten ways |
| output | Verify it in seconds | Can't tell if it worked |

- Real loop looks like: **"find functions over 50 lines, open an issue for each"**
- A wish looks like: ~~"improve the codebase"~~

Keep humans in charge of risky decisions; transition from a chat interface to an automated agent system.

---
## Full article text (verified-complete via ADHX API, fetched 2026-06-30)
> Verbatim body of the linked X article — the authoritative source. Image references point to the saved local copies under `./img/`.

Most people use Claude one prompt at a time. You type, it answers, you read it, you type again. The moment you close the laptop, everything stops.

The person who built Claude Code stopped working that way a while ago. He hasn't written a line of code this year, runs most of it from his phone, and has a few thousand agents working overnight while he sleeps. The thing making that possible isn't a secret model. It's loops.

**A loop is just Claude on a schedule.** A single prompt runs once and dies. A loop runs on its own, again and again, without you starting it each time. The mechanism is boring on purpose: have Claude use cron to schedule a job and tell it how often to repeat — every minute, every 30 minutes, every night. No framework, no orchestration layer. The simplest thing that works, which is exactly why it works. Once a job repeats on its own, Claude stops being a chat window and starts being a worker that shows up on its own schedule. *(image: claude-loops-sleep-step1.jpg)* The trick is matching the interval to the task: fast-changing things get tight loops; slow things get a nightly pass (CI watcher every few minutes; day's-work summary once at night so the report waits for you in the morning).

**The real power is running many loops at once.** One loop is useful; a stack of them in parallel is a different thing entirely. The setup that turns heads is a handful of loops, each owning one job — one babysits open PRs and fixes failing CI; one keeps the test suite healthy and patches flaky tests; one clusters feedback from a feed every 30 minutes. None need you; they run side by side on their own intervals. This is how one person does the volume of a team — not by typing faster, but by having dozens of loops typing for them around the clock. *(image: claude-loops-sleep-step2.jpg)* The mental shift is the hard part: stop thinking "what do I prompt next" and start thinking "what job should run on its own from now on." Anything you do more than twice, keep checking manually, or that breaks at 3am is a loop waiting to exist.

**Close the laptop and the work keeps going.** Running loops locally stops when you shut the laptop. The fix is routines — the same idea moved to the server: configure the job once and it runs on a schedule, webhook, or API call whether your machine is on or not. The work that used to need a human to kick it off just happens.

**The bottleneck was never the model.** Put it together and the chat window disappears. You stop running Claude by hand and start running a system that runs itself: loops own the recurring work, routines keep them alive when you're gone, you just decide what should exist. The skill that matters now isn't writing one perfect prompt — it's spotting which parts of your work should never need you again. "You're paying for a fleet of agents and using one chat window."

**Start with one loop, not ten.** The mistake everyone makes is building the whole system on day one (ten loops, a dashboard) — it collapses by the weekend because you can't tell which loop did what. Start with one: pick the most annoying recurring task, turn that single job into a loop, let it run a few days, watch where it overreaches or misses. Once you trust one, the second takes ten minutes; by the fifth you think in jobs, not mechanics. A good first loop has three properties — a clear schedule, a narrow job it can't misread, and output you can glance at in seconds (CI watcher, PR rebaser, daily digest: boring, bounded, easy to verify). *(image: claude-loops-sleep-step3.jpg)* The loops that fail are the vague ones: "improve the codebase" is a wish; "find functions over 50 lines and open an issue for each" is a loop. The tighter the job, the more you can trust it running without you.

**Keep a human in the loop, just not in every loop.** The people running agents overnight don't hand the agent a blank check — each loop has a lane, and risky steps still wait for a yes. A PR babysitter can rebase and fix CI on its own, but merging to main still pings you. A migration loop can open a hundred PRs, but a human approves the first before the rest go out. The agent does the volume, you keep the judgment. The goal isn't zero humans — it's zero humans on the boring 95% and your full attention on the 5% that carries risk. Set the boundaries once in the loop's instructions and they hold every run after: "you're not babysitting the work, you're babysitting the rules, and the rules are written down."

**What changes after a week.** Day one feels like overhead (writing schedules, watching loops misfire). By week's end the math flips: the PR babysitter saved forty context switches, the nightly report waits every morning with no prompt, the feedback cluster turned an ignored feed into clean themes. You stop opening Claude to ask it things and start opening it to check on things it already did — the chat window becomes a status board, not a workspace. "That's the real shift Boris was pointing at: not that the model got smarter, but that the work moved off your hands and onto a schedule."

(Author CTA in original: follow @hanakoxbt + Telegram https://t.me/+75nMf005jRpjMDU1)

---
## Relevance to THIS hub (why it was captured)
Directly maps to existing hub machinery — useful when we do the process-improvement pass:
- `/loop` skill + `/schedule` (cloud routines) = the "loop" and "routine" levels above.
- `loop-engineering` workflow + G5 "autonomous self-improving machine" goal = the parallel-fleet idea.
- The hub already runs analogues: auto-pr / auto-pr-reconcile (PR babysitter), the test-pipeline fix-loop (CI medic), `aggregate_telemetry` (feedback cluster), `/end-session` digests (nightly report).
- The "narrow job vs a wish" + "verify in seconds" framing reinforces the hub's trust-score / hard-gate doctrine and the `rule-curation` reactive-not-speculative principle.
