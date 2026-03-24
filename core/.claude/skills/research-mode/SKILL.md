---
name: research-mode
description: >
  Analyze questions or documents with citation-backed rigor and zero tolerance
  for fabricated claims. Use when accuracy matters more than speed — factual
  decisions, document analysis, technical research. Applies three anti-hallucination
  constraints: admit knowledge gaps, verify with citations, and extract direct
  quotes before analyzing.
triggers:
  - research
  - fact-check
  - verify claims
  - citation
  - deep research
  - analyze document
allowed-tools: "Read Grep Glob Agent WebSearch WebFetch"
argument-hint: "<question or file-path> [--deep]"
version: "1.0.0"
type: workflow
---

# Research Mode — Citation-Backed Analysis

Rigorous research with anti-hallucination constraints. Every claim must have
a source. Unsupported claims are retracted, not softened.

**Anti-hallucination constraints active:**
1. Admit knowledge gaps — say "I don't know" instead of guessing
2. Verify with citations — every claim needs a source or gets retracted
3. Direct quotes first — extract exact text before analyzing

**Input:** $ARGUMENTS

---

## STEP 1: Classify Input & Scope

Determine the research type from the input:

| Input Pattern | Research Type | Primary Sources |
|--------------|---------------|-----------------|
| A question or topic | **Knowledge research** | Web search, codebase, documentation |
| A file path | **Document analysis** | The file itself, cross-references |
| `--deep` flag present | **Deep research** | All sources, multiple subagents |

### Scope the Research

1. Restate the research question in one sentence
2. Define what counts as a satisfactory answer (what evidence would resolve this?)
3. Identify 2-3 source categories to search (e.g., official docs, codebase, academic)
4. Set a boundary: what is OUT of scope for this research pass

---

## STEP 2: Gather Sources

### For Knowledge Research

1. **Codebase search** — Use `Grep` and `Glob` to find relevant code, configs, and docs in the project
2. **Web search** — Use `WebSearch` for external documentation, specifications, and authoritative sources
3. **Fetch primary sources** — Use `WebFetch` to read the actual content of authoritative pages (official docs, RFCs, specs)

### For Document Analysis

1. **Read the document** — Use `Read` to load the full document
2. **Extract direct quotes** — Pull word-for-word passages that are relevant to the research question BEFORE any interpretation
3. **Cross-reference** — Search the codebase for related files that provide context

### For Deep Research (--deep flag)

Dispatch parallel subagents for breadth:

```
Agent(subagent_type="Explore", prompt="Find all references to {topic} in the codebase")
Agent(subagent_type="web-research-specialist-agent", prompt="Research {topic}: find authoritative sources, official documentation, and expert analysis")
```

Collect results from all subagents before proceeding.

**CRITICAL:** At the end of this step, you MUST have at least one primary source.
If you found zero sources, state this explicitly and do NOT proceed to fabricate
claims. Instead, report: "Insufficient sources found. Here is what I searched
and why it came up empty."

---

## STEP 3: Extract Direct Quotes

Before ANY analysis or interpretation, extract word-for-word quotes from every
source. This prevents paraphrase drift where meaning subtly changes during
summarization.

For each source, record:

```
> "{exact text copied word-for-word}"
> — Source: {file path, URL, or document name}, {line number or section}
```

### Rules for Quote Extraction

- Copy text EXACTLY — do not fix grammar, update terminology, or modernize phrasing
- Include enough surrounding context that the quote is not misleading
- If the source is code, quote the relevant code block with its file path and line numbers
- If the source is a web page, include the URL and the specific section heading
- Minimum 3 quotes for knowledge research, minimum 5 for deep research
- If you cannot extract enough quotes, this is a signal that sources are insufficient

---

## STEP 4: Build Claims with Citations

Now — and ONLY now — analyze the quotes and build claims. Each claim MUST
link to a specific quote from Step 3.

### Claim Construction Rules

1. **Every factual claim must cite a quote** — If you cannot point to a specific
   quote that supports the claim, the claim is unsupported
2. **Distinguish fact from inference** — Facts have direct quote support;
   inferences are logical conclusions drawn from facts. Label each clearly
3. **Flag contradictions** — If two sources contradict each other, present both
   quotes and state the contradiction explicitly. Do NOT silently pick one
4. **Retract unsupported claims** — If during analysis you write something that
   has no backing quote, cross it out immediately: ~~claim~~ — Insufficient evidence

### Confidence Classification

For each claim, assign a confidence level:

| Level | Criteria | Marker |
|-------|----------|--------|
| **Verified** | Direct quote from authoritative source | `[Verified: source]` |
| **Supported** | Multiple quotes that collectively support the claim | `[Supported: sources]` |
| **Inferred** | Logical conclusion from verified facts, but no direct statement | `[Inferred: reasoning]` |
| **Unverified** | Plausible but no source found — flag, do NOT present as fact | `[Unverified]` |
| **Unknown** | Insufficient information to make any claim | `[Unknown]` |

Claims marked `[Unverified]` or `[Unknown]` MUST be in the Knowledge Gaps
section, NOT in the Verified Claims section.

---

## STEP 5: Produce Research Brief

Present findings in this exact structure:

```markdown
## Research Brief: {topic}

### Research Question
{One-sentence restatement of what was investigated}

### Sources Consulted
- {source 1: type, location, relevance}
- {source 2: type, location, relevance}
- {source N}

### Direct Quotes
> "{exact text}" — Source: {location}
> "{exact text}" — Source: {location}
(All quotes from Step 3)

### Verified Claims
- {claim} [Verified: {quote reference}]
- {claim} [Supported: {quote references}]
- {claim} [Inferred: {reasoning from verified facts}]

### Retracted Claims
- ~~{claim that had no source}~~ — Insufficient evidence
- ~~{claim where sources contradicted}~~ — Contradictory sources: {details}
(If none, state: "No claims were retracted.")

### Knowledge Gaps
- {what we don't know and where to look for it}
- {questions that remain unanswered with suggested next steps}
(If none, state: "No significant knowledge gaps identified.")

### Confidence Assessment: {High | Medium | Low}
{1-2 sentence justification based on source quality and coverage}
```

### Confidence Thresholds

| Rating | Criteria |
|--------|----------|
| **High** | 3+ verified claims from authoritative sources, zero retracted claims, no contradictions |
| **Medium** | Mix of verified and inferred claims, minor gaps, sources are credible but not primary |
| **Low** | Mostly inferred claims, significant gaps, sources are secondary or sparse |

---

## STEP 6: Suggest Next Steps

Based on the research brief, recommend one actionable next step:

- If confidence is **High** and the research answers the question → Summarize the answer and suggest proceeding
- If confidence is **Medium** with identified gaps → Suggest specific follow-up searches or documents to read
- If confidence is **Low** → Recommend what additional sources would raise confidence, or suggest the user consult a domain expert
- If research was for a **decision** → Present the evidence-based recommendation with the strongest supporting quote

---

## CRITICAL RULES

- NEVER present a claim without a citation — every factual statement must trace back to a specific quote or source
- NEVER paraphrase a source and present the paraphrase as a direct quote — quotes must be word-for-word
- NEVER skip the quote extraction step (Step 3) — extracting quotes before analysis is the core anti-hallucination mechanism
- NEVER silently drop a claim that lacks evidence — explicitly retract it in the Retracted Claims section with the reason
- NEVER present [Unverified] or [Unknown] claims in the Verified Claims section — they belong in Knowledge Gaps
- NEVER fabricate sources, URLs, page numbers, or quote text — if a source doesn't exist, say so
- ALWAYS say "I don't have enough information" when sources are insufficient — never fill gaps with plausible fiction
- ALWAYS show contradictions between sources rather than silently resolving them
- ALWAYS produce the full Research Brief structure even for simple questions — the structure IS the anti-hallucination mechanism
