# How to Run a One Person Company with Claude

- **Source:** [@mikenevermiss X article](https://x.com/mikenevermiss/status/2069657093200609686) (shared as `x.com/i/status/2069657093200609686`)
- **Author:** MIKE (@mikenevermiss, ~18.6k followers, "partner @ourbit")
- **Published:** 2026-06-24
- **Captured:** 2026-08-06 (via ADHX API, full article JSON)
- **Engagement at capture:** ~715k views, 549 likes, 2,192 bookmarks, 76 RTs

## Relevance to this hub

**LOW-MODERATE — consumer claude.ai Projects piece; no net-new mechanism.** A 5-project setup
(Company OS context project + 4 specialist "agents": Researcher / Writer / Closer / Operator)
run as plain Claude Projects, with work manually shuttled between them by the human.

- Near-duplicate of two prior captures: cyril's "Claude Projects full course"
  (2026-07-08, precision-context doctrine) and Khairallah's "First Team of AI Agents"
  (4-agent Cowork team with file handoffs). This one is shallower: no automation, no
  scheduling, no file handoffs — the human IS the message bus between the four Projects.
- **This appears to be the ORIGINAL of an already-captured derivative:** the DivyanshT
  piece ("One Person. Four AI Agents. An Entire Company.", published 2026-07-09, ~3.6k
  views) uses the identical Company-OS + 4-agent structure. This article is 2 weeks
  earlier with ~200x the views — treat this note as the canonical capture of that idea.
- Core thesis corroborates existing hub doctrine, doesn't extend it: **context pre-loaded
  in the Project beats re-prompting per session** ("the company runs on the setup, not on
  you showing up"), **voice is calibrated from pasted examples, not descriptions** (already
  captured in the cyril note), and **instruction misses feed back into the Project
  instructions** (a weak, manual form of the hub's lessons/self-improvement loop).
- One clean reusable artifact: the five instruction-prompt templates themselves (Company
  OS / Researcher / Writer / Closer / Operator) are tight and copy-pastable — usable as
  seed material if PIFS/5Wealths ever wants a claude.ai-Projects-level business setup.
- ⚠️ **Unverified marketing framing — do not propagate:** "$300–500/mo stack replaces
  $80,000–120,000/mo in salaries". No sourcing in the article.

## Full article text (verbatim)

learn how to set up Claude as the operating system of your business. configure four specialist agents, build a Company OS project, and run research, writing, sales, and operations from a single Claude setup that works while you sleep.

a one person company in 2026 is not a freelancer with ambition. it is one person running strategy while a configured set of agents handles execution underneath. the typical solo founder stack costs $300 to $500 a month. the team it replaces costs $80,000 to $120,000 a month in salaries. the gap is real and it is available right now.

Claude is the center of this stack. not because it is the only tool, but because it is the most capable single interface for thinking, writing, researching, and decision-making. the rest of your tools connect to it. it does not connect to them.

Build Your Company OS First

-----------------------------

before you create a single agent, build the Company OS. this is one Claude Project that holds every piece of context your business needs to function. everything lives here: your positioning, your offer, your voice, your processes, your ICP.

go to Claude.ai, create a new Project, and name it "Company OS." in the Project instructions field, paste this prompt and fill in your own details:

---

you are the operating intelligence of [your company name]. here is everything you need to know to do high-quality work for this business.

COMPANY: [what you do and who you do it for in two sentences]

OFFER: [your core product or service, the price, and what the client gets]

ICP: [describe your ideal client, their role, their problem, what they have tried before]

VOICE: [how your content sounds, pick three adjectives and give one example sentence]

NON-NEGOTIABLES: [things you never do, positions you never take, tone you never use]

PROCESS: [how a new client goes from first contact to onboarded in numbered steps]

---

every agent you build from here inherits context from this OS. you write it once. you never re-explain your business again.

Create the Researcher Agent

------------------------------

the Researcher handles market intelligence, competitor tracking, lead research, and content sourcing. it saves you the two to three hours per day most founders spend hunting for information.

create a new Project called "Researcher." in the Project instructions, paste this:

---

you are a specialist research agent for [company name]. your job is to find, verify, and organize information so the operator can make decisions and create content without doing the digging themselves.

when given a research task:

1. identify exactly what decision or output this research will feed

2. search for primary sources first, not summaries

3. return findings in this format: KEY FINDING → SUPPORTING EVIDENCE → SOURCE → WHY IT MATTERS

4. flag anything you cannot verify as unconfirmed

5. never pad the output. if you found three useful things, return three useful things.

you have access to web search. use it on every task unless the operator specifies otherwise.

---

test it immediately. give it a task like "research the top three pain points freelance designers report when dealing with clients in 2026." if the output is specific, sourced, and structured, the agent is working.

Create the Writer Agent

--------------------------

the Writer handles all external content: newsletters, LinkedIn posts, proposals, cold outreach, landing page copy, and case studies. it needs to write in your voice, not Claude's default voice.

create a Project called "Writer." paste this into the instructions:

---

you are the staff writer for [company name]. you write in [owner's name]'s voice exclusively. you do not write in a generic AI voice. you do not use filler phrases like "in today's fast-paced world" or "it's no secret that."

VOICE RULES:

- sentences are short. never more than 20 words unless rhythm demands it.

- no fluff openings. the first sentence is always the point.

- write like a smart person talking to another smart person. no hand-holding.

- always end with something that makes the reader want to act or think differently.

when given a writing task:

1. ask what the goal of this piece is if it is not clear

2. draft without showing your reasoning

3. never add a summary conclusion that repeats what was already said

VOICE SAMPLE: [paste two to three paragraphs of your own writing here]

---

the voice sample is the most important part. paste real writing you have done, not an idealized version. the agent calibrates from examples, not descriptions.

Create the Closer Agent

--------------------------

the Closer handles sales-adjacent work: writing proposals, responding to inbound inquiries, handling objections in writing, and drafting follow-up sequences. it does not replace a sales call. it handles everything around it.

create a Project called "Closer." paste this:

---

you are the sales operator for [company name]. your job is to help convert interested prospects into paying clients through written communication. you understand that selling is not persuading, it is helping the right person make the right decision.

when writing a proposal:

1. open with the client's problem in their own words, not yours

2. describe the outcome they will get, not the process you will follow

3. include scope, timeline, and investment on one page maximum

4. close with a specific next step, not "let me know if you have questions"

when handling an objection:

1. acknowledge what is true in it before responding

2. never argue. redirect to the outcome.

3. offer one option, not three. multiple options create hesitation.

when writing follow-up:

- day 1: confirm receipt and next step

- day 3: add one piece of value relevant to their situation

- day 7: ask a direct yes or no question

---

feed it real context when you use it. paste the sales call notes, the prospect's LinkedIn, or the initial inquiry email. the output quality scales directly with the input quality.

Create the Operator Agent

---------------------------

the Operator handles internal work: project tracking, SOPs, scheduling logic, decision frameworks, and anything that keeps the business running but does not face clients. this agent keeps you from carrying the operating logic of your business in your head.

create a Project called "Operator." paste this:

---

you are the operations manager for [company name]. your job is to help the founder keep the business organized, documented, and running without relying on memory.

when asked to create an SOP:

1. write it in numbered steps that a new person could follow

2. include what to do if something goes wrong at each step

3. keep it short enough to actually be read

when asked to track a project:

1. list the current status, the next action, and who owns it

2. flag anything that is blocked or overdue

3. update the record every time new information is provided

when asked for a decision framework:

1. identify what is actually being decided

2. list the two to three factors that matter most

3. give a recommendation with the reasoning, not just the options

you do not manage tools. you manage information. every output should make the next action obvious.

---

use the Operator agent for your weekly review. every Monday, open it and paste in what happened last week, what is in progress, and what is coming. it will return a structured operating picture in under two minutes.

Run the Four Agents as One System

------------------------------------

the four agents do not replace each other. each one stays in its lane and the work flows between them. the sequence looks like this in practice: Researcher finds the intelligence, Writer turns it into content or copy, Closer converts the interested, Operator keeps the whole thing organized.

a real workflow example: you want to land a new client in the brand consulting space. send the Researcher their company, ask for a brief on their positioning gaps and recent moves. take those findings to the Closer, paste them in, and ask for a first outreach email. if they respond, take the conversation to the Closer again for the follow-up. once they sign, hand the project details to the Operator to set up the SOP.

you are not doing the work. you are directing four agents that each know their job and have the context to do it well. your job shifts from execution to review and decision.

What to Build Into the System Over Time

-----------------------------------------

in the first two weeks, focus on getting the four agents running and using them daily. do not optimize yet. use them on real tasks and notice where the output misses. those misses are your signal to update the Project instructions.

by week four, you will have a clear pattern of which tasks you are still doing manually that an agent could handle. add those tasks to the relevant agent's instructions as explicit procedures. every procedure you add is a task you never have to explain again.

the Company OS Project should grow every week. every time you make a significant business decision, document it there. every time you refine your positioning or change your pricing, update the OS. the agents draw from it, so keeping it current is the same as training your team.

The One Thing That Makes This Work

-------------------------------------

most people set up agents and then keep prompting them like they are chatbots. they re-explain context on every session, they write long prompts for simple tasks, and they wonder why the output is inconsistent.

the system above works because the context is already loaded before you type a single word. every session with the Writer already knows your voice. every session with the Closer already knows your offer. every session with the Researcher already knows what decision the research will feed.

your job is not to prompt better. it is to build better Projects, keep the instructions current, and let each agent do the work it is configured to do. the company runs on the setup, not on you showing up to manage it every time.
