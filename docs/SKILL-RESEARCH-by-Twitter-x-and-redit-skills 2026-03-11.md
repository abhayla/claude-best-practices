# Claude Code Skills Research — Twitter/X + Reddit Combined Results

**Date:** 2026-03-11
**Sources:** Twitter/X (27 results) + Reddit (20 results) = 39 unique skills after dedup
**Window:** Dec 2025 – March 2026 (3 months)
**12 skills found on both platforms (2x validated)**

---

## TIER 1 — HIGH PRIORITY: Fills Priority Stack Gaps

### 1. Redis Agent Skill [2x validated]
- **Source:** [redis/agent-skills](https://github.com/redis/agent-skills) | [Redis blog](https://redis.io/blog/we-built-an-agent-skill-so-ai-writes-redis-code/) | [Redis X](https://x.com/Redisinc/status/2019859245890695218) | r/ClaudeAI
- **Category:** Stack-specific (Redis)
- **What it does:** Official Redis team skill for Redis 7+ patterns: cache-aside, write-through, rate limiting with sorted sets, session management, vector search, semantic caching, pub/sub, streams. Anti-pattern guardrails (no KEYS * in production, connection pooling, pipelining).
- **Overlap:** 0% — No existing Redis skill.
- **Proposed command:** `/redis-patterns`
- **Validation:** Official Redis Inc. release (Feb 2026). Both platforms. awesome-claude-skills (8.6k stars).

### 2. Firebase Agent Skills Suite [2x validated]
- **Source:** [Firebase blog](https://firebase.blog/posts/2026/02/ai-agent-skills-for-firebase/) | [Firebase docs](https://firebase.google.com/docs/ai-assistance/agent-skills) | r/ClaudeAI
- **Category:** Stack-specific (Firebase)
- **What it does:** 5 official Firebase skills: firebase-auth-basics, firebase-firestore-basics, firebase-data-connect-basics (PostgreSQL + GraphQL), firebase-app-hosting-basics (Next.js/Angular deploy), firebase-ai-logic-basics (Gemini API). Install via npx skills add firebase/agent-skills.
- **Overlap:** ~10% with firebase-auth.md (empty placeholder).
- **Proposed command:** `/firebase-setup`, `/firebase-auth`, `/firebase-firestore`
- **Validation:** Official Google/Firebase release (Feb 2026). Both platforms.

### 3. Flutter Expert Skill [2x validated]
- **Source:** [jeffallan/claude-skills](https://github.com/jeffallan/claude-skills) | [VoltAgent](https://github.com/VoltAgent/awesome-claude-code-subagents) | [fastmcp.me](https://fastmcp.me/skills/details/242/flutter-development) | [Async Redux](https://asyncredux.com/flutter/claude-code-skills/)
- **Category:** Stack-specific (Flutter/Dart)
- **What it does:** Flutter 3+ development: widget architecture, state management (Riverpod/BLoC), GoRouter navigation, platform-specific code, performance optimization, Material Design 3, cross-platform builds. 5-phase workflow.
- **Overlap:** 0% — No Flutter skill exists.
- **Proposed command:** `/flutter-dev`
- **Validation:** 4 independent implementations. Both platforms.

### 4. Flutter E2E Testing Skill
- **Source:** [ai-dashboad/flutter-skill](https://github.com/ai-dashboad/flutter-skill) (64 stars)
- **Category:** Stack-specific (Flutter + 9 other platforms)
- **What it does:** E2E testing across 10 platforms (Flutter, React Native, iOS, Android, Web, Electron, Tauri, KMP, .NET MAUI) with 253 MCP tools, semantic element recognition, 98.8% test success rate, 95% fewer tokens than screenshot-based tools.
- **Overlap:** ~25% with android-run-e2e (cross-platform vs Android-only, MCP protocol, semantic trees).
- **Proposed command:** `/flutter-e2e-test`
- **Validation:** 64 stars. Supports Claude, Cursor, Windsurf, Copilot.

### 5. Android Architecture & Compose Suite (15 skills) [2x validated]
- **Source:** [awesome-android-agent-skills](https://github.com/new-silvermoon/awesome-android-agent-skills) | [dpconde/claude-android-skill](https://github.com/dpconde/claude-android-skill) | [ProAndroidDev](https://proandroiddev.com/building-a-claude-skill-xml-to-jetpack-compose-converter-bc4b68268499) | [Adit Lal on X](https://x.com/aditlal/status/2027628991428067543)
- **Category:** Stack-specific (Android/Kotlin/Jetpack Compose)
- **What it does:** 15 skills: Clean Architecture, Compose UI, ViewModel & StateFlow, offline-first (Room + Retrofit), accessibility, Gradle plugins, Roborazzi screenshots, Kotlin coroutines, Compose perf auditing, XML-to-Compose migration, Compose Navigation, Retrofit, Gradle perf, Coil, emulator automation.
- **Overlap:** ~15% with android-adb-test, android-run-tests, android-run-e2e (testing only). Expands to full lifecycle.
- **Proposed command:** `/android-arch`, `/compose-ui`, `/xml-to-compose`, `/compose-perf-audit`, `/kotlin-concurrency`
- **Validation:** ProAndroidDev article. Adit Lal. Chris Krueger. Both platforms. 100+ stars.

### 6. Kotlin Multiplatform Subagents
- **Source:** [Chris Krueger on X](https://x.com/ChrisKruegerDev/status/1977399075734520267)
- **Category:** Stack-specific (Kotlin/KMP)
- **What it does:** KMP subagents: localize apps, guide Compose UI with MVVM, build data layer with Android-standard patterns.
- **Overlap:** ~30% with android-compose.md rule. Adds KMP, i18n, data layer.
- **Proposed command:** `/kmp-develop`
- **Validation:** Chris Krueger (known Android developer).

### 7. Vue/Nuxt Skills Suite (8 skills)
- **Source:** [onmax/nuxt-skills](https://github.com/onmax/nuxt-skills) | [Nuxt PR #33498](https://github.com/nuxt/nuxt/pull/33498) | [alexop.dev](https://alexop.dev/posts/why-you-dont-need-nuxt-mcp-claude-code/)
- **Category:** Stack-specific (Vue/Nuxt)
- **What it does:** 8 skills: vue, nuxt, nuxt-modules, nuxthub, nuxt-content, nuxt-ui, nuxt-better-auth, reka-ui. Covers Composition API, SSR, server routes, middleware, multi-cloud, theming.
- **Overlap:** 0% — No Vue/Nuxt skills.
- **Proposed command:** `/vue-dev`, `/nuxt-dev`
- **Validation:** PR to nuxt/nuxt repo. Multiple blog posts.

### 8. PostgreSQL Read-Only Query Skill
- **Source:** [jawwadfirdousi/agent-skills](https://github.com/jawwadfirdousi/agent-skills) | awesome-claude-code
- **Category:** Stack-specific (PostgreSQL)
- **What it does:** SELECT, SHOW, EXPLAIN queries with validation and timeouts. Prevents destructive operations. Schema exploration and query optimization.
- **Overlap:** 0% — No PostgreSQL skill.
- **Proposed command:** `/pg-query`
- **Validation:** awesome-claude-code. PostgreSQL = #1 database for Claude Code projects.

### 9. iOS Simulator Skill
- **Source:** [Jack Culpan on X](https://x.com/JackCulpan/status/2010109413663879553) | [conorluddy/ios-simulator-skill](https://github.com/conorluddy/ios-simulator-skill) (593 stars)
- **Category:** Stack-specific (iOS/Swift)
- **What it does:** 21 scripts for iOS simulator testing. Semantic navigation, 96% token reduction, accessibility audits, visual diffing, CI/CD integration.
- **Overlap:** ~25% concept with android-adb-test (device testing). iOS vs Android.
- **Proposed command:** `/ios-simulator-test`
- **Validation:** 593 stars.

### 10. React Native Agent Skills (Callstack)
- **Source:** [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills) (998 stars) | [Daniel Williams on X](https://x.com/Danny_H_W/status/2011833470956212489)
- **Category:** Stack-specific (React Native)
- **What it does:** 5 skills: RN best practices (profiling, FPS, re-renders), GitHub workflows, CI/CD for simulator/emulator, upgrading RN, brownfield migration.
- **Overlap:** ~15% with android-run-tests. Cross-platform mobile.
- **Proposed command:** `/rn-best-practices`, `/rn-upgrade`, `/rn-brownfield-migrate`
- **Validation:** 998 stars, 57 forks, 15 contributors. Callstack = major RN consultancy.

### 11. Expo Skills (React Native/Mobile)
- **Source:** [expo/skills](https://github.com/expo/skills)
- **Category:** Stack-specific (React Native/Expo)
- **What it does:** Official Expo: expo-app-design (Router UI), upgrading-expo (framework updates), expo-deployment (app store publishing).
- **Overlap:** 0% — No Expo skill.
- **Proposed command:** `/expo-dev`, `/expo-deploy`
- **Validation:** Official Expo team release.

### 12. Elasticsearch Skill
- **Source:** [Leonie on X](https://x.com/helloiamleonie/status/2018637826850467848) | David Hope (Elastic employee)
- **Category:** Stack-specific (Elasticsearch)
- **What it does:** Elasticsearch REST API: index management, search query construction, cluster health.
- **Overlap:** 0% — Not covered.
- **Proposed command:** `/elasticsearch`
- **Validation:** Created by Elastic employee.

---

## TIER 2 — MEDIUM PRIORITY: Universal Workflows

### 13. Trail of Bits Security Skills (19-20 skills) [2x validated]
- **Source:** [trailofbits/skills](https://github.com/trailofbits/skills) (3.5k stars) | [AISecHub on X](https://x.com/AISecHub/status/2011560139749527811) | r/ClaudeAI
- **Category:** Universal (Security)
- **What it does:** 19+ security skills: static analysis (CodeQL + Semgrep + SARIF), variant analysis, supply-chain auditing, insecure defaults, differential review, false-positive checking, Semgrep rules, smart contract security (6 blockchains), YARA, constant-time crypto, property-based testing, GitHub Actions security.
- **Overlap:** ~10% with claude-guardian (general safety vs professional-grade tooling).
- **Proposed command:** `/security-audit`, `/supply-chain-audit`, `/semgrep-rules`
- **Validation:** 3.5k stars, 274 forks. Trail of Bits = top security firm. Both platforms.

### 14. Superpowers [2x validated]
- **Source:** [obra/superpowers](https://github.com/obra/superpowers) (77.5k stars, 6k forks) | Composio | r/ClaudeAI | [omarsar on X](https://x.com/omarsar0/status/1979242073372164306)
- **Category:** Universal
- **What it does:** Agentic workflow: brainstorm -> spec -> plan -> subagent execution -> review -> merge. 15+ skills. TDD, context management, sub-agents, git worktrees.
- **Overlap:** ~40% with implement + plan-to-issues + strategic-architect. Adds brainstorm, parallel dispatch, worktrees.
- **Proposed command:** `/superpowers` (upgrade placeholder)
- **Validation:** 77.5k stars. Most starred Claude Code repo. Both platforms.

### 15. GSD (Get Shit Done)
- **Source:** [gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done) | [Nnenna on X](https://x.com/nnennahacks/status/2015467678022979773) | [The New Stack](https://thenewstack.io/beating-the-rot-and-getting-stuff-done/)
- **Category:** Universal
- **What it does:** Context rot prevention: externalizes state, atomic 2-3 task plans, fresh context per plan, auto git commits. Requirement tiers (Must/Nice/Out of Scope).
- **Overlap:** ~35% with implement + plan-to-issues. Core innovation = context rot prevention.
- **Proposed command:** `/gsd`
- **Validation:** The New Stack article. Ported to OpenCode/Gemini CLI.

### 16. /batch (Parallel Codebase-Wide Changes)
- **Source:** [Boris Cherny on X](https://x.com/bcherny/status/2027534984534544489) (Claude Code creator)
- **Category:** Universal (official)
- **What it does:** Orchestrates parallel code changes (renames, API migrations). Research, decompose, execute in parallel, auto /simplify, create PRs.
- **Overlap:** 0% — No batch/parallel change skill.
- **Proposed command:** `/batch`
- **Validation:** Claude Code creator. Very high X engagement.

### 17. /handover (Session Continuity)
- **Source:** [Zara Zhang on X](https://x.com/zarazhangrui/status/2020992712825241801)
- **Category:** Universal
- **What it does:** Generates handover document: decisions, pitfalls, lessons, current state, next steps. Next session loads for continuity.
- **Overlap:** ~40% with continue. Adds structured decision/pitfall capture.
- **Proposed command:** `/handover`
- **Validation:** Shared on X with significant engagement.

### 18. TDD Cycle Workflow [2x validated]
- **Source:** [wshobson/commands](https://github.com/wshobson/commands) | r/ClaudeAI | multiple articles
- **Category:** Universal (Testing)
- **What it does:** Red-Green-Refactor TDD: tdd-red (failing tests), tdd-green (minimal impl), tdd-refactor (improve while green).
- **Overlap:** ~25% with auto-verify + test-knowledge. Drives from tests first vs verify after.
- **Proposed command:** `/tdd-red`, `/tdd-green`, `/tdd-refactor`
- **Validation:** Both platforms. Multiple sources.

### 19. DevOps Skills Collection [2x validated]
- **Source:** [akin-ozer/cc-devops-skills](https://github.com/akin-ozer/cc-devops-skills) | [Pulumi blog](https://www.pulumi.com/blog/top-8-claude-skills-devops-2026/)
- **Category:** Universal (DevOps)
- **What it does:** Docker optimization, Kubernetes manifests, CI/CD automation, monitoring (Prometheus/Grafana), SLO/SLI, incident response, Terraform, Pulumi IaC.
- **Overlap:** ~10% with fastapi-deploy (stack-specific vs universal).
- **Proposed command:** `/docker-optimize`, `/k8s-deploy`, `/ci-cd-setup`, `/incident-response`
- **Validation:** Pulumi official blog. Both platforms.

### 20. Playwright E2E Testing
- **Source:** [lackeyjb/playwright-skill](https://github.com/lackeyjb/playwright-skill) | Jenny Ouyang "37 Skills"
- **Category:** Universal (Testing)
- **What it does:** Browser automation: navigate, click, fill forms, extract JS-rendered content, screenshots, E2E tests. MCP Execution Debugger companion.
- **Overlap:** ~20% with verify-screenshots (full E2E vs screenshot-only).
- **Proposed command:** `/playwright-test`
- **Validation:** 85% flaky test reduction. 700+ test case study.

### 21. Production Workflows (shinpr)
- **Source:** [shinpr/claude-code-workflows](https://github.com/shinpr/claude-code-workflows)
- **Category:** Universal
- **What it does:** 16 recipe-based workflows. 15+ agents. Complexity-based routing (simple=skip docs, complex=full PRs). Cross-layer verification.
- **Overlap:** ~35% with implement + fix-issue. Adds complexity routing + fullstack verification.
- **Proposed command:** `/recipe-implement`, `/recipe-fullstack`
- **Validation:** Production-tested.

### 22. /apex (Feature-to-PR)
- **Source:** [Melvyn on X](https://x.com/melvynxdev/status/2011242872297886149)
- **Category:** Universal
- **What it does:** 10 autonomous steps: init branch -> analyze -> plan -> execute -> validate -> review -> fix -> test -> verify -> create PR.
- **Overlap:** ~50% with implement + auto-verify. Fully autonomous end-to-end.
- **Proposed command:** `/apex`
- **Validation:** Shared on X.

### 23. Qodo PR Skills
- **Source:** [Qodo on X](https://x.com/QodoAI/status/2024859095321194575) | [Nnenna on X](https://x.com/nnennahacks/status/2024131324122911142)
- **Category:** Universal (Code Review)
- **What it does:** Team standards enforcement + PR auto-fix by severity + inline comment replies.
- **Overlap:** ~25% with auto-verify + post-fix-pipeline. External review integration.
- **Proposed command:** `/qodo-rules`, `/qodo-pr-resolver`
- **Validation:** Official Claude plugin. Multiple X endorsements.

### 24. Adversarial Review (Claude + Codex)
- **Source:** [Aseem Shrey on X](https://x.com/AseemShrey/status/2024753461259047000)
- **Category:** Universal (Code Review)
- **What it does:** Codex reviews Claude's plans. Back-and-forth until approved. 3 rounds, 14 issues caught, zero manual review.
- **Overlap:** ~25% with claude-guardian + auto-verify. Cross-model adversarial.
- **Proposed command:** `/adversarial-review`
- **Validation:** Blog post with metrics.

---

## TIER 3 — WORTH ADDING: Unique Capabilities

### 25. Context Engineering Kit
- **Source:** [NeoLabHQ/context-engineering-kit](https://github.com/NeoLabHQ/context-engineering-kit)
- **Category:** Universal
- **What it does:** Context saving/restoring, architecture decision capture, token budget management.
- **Overlap:** ~20% with continue + status. Token conservation focus.
- **Proposed command:** `/context-save`, `/context-restore`
- **Validation:** Top Reddit discussion topic.

### 26. RIPER Workflow
- **Source:** [tony/claude-code-riper-5](https://github.com/tony/claude-code-riper-5)
- **Category:** Universal
- **What it does:** Research -> Innovate -> Plan -> Execute -> Review. Memory persistence. Entry/exit criteria.
- **Overlap:** ~30% with strategic-architect + implement. Adds Research + Innovate phases.
- **Proposed command:** `/riper`
- **Validation:** awesome-claude-code.

### 27. Compound Engineering Plugin
- **Source:** [EveryInc/compound-engineering-plugin](https://github.com/EveryInc/compound-engineering-plugin)
- **Category:** Universal
- **What it does:** Persistent error-to-learning cycles across sessions.
- **Overlap:** ~40% with learn-n-improve. Cross-session persistence.
- **Proposed command:** `/compound-learn`
- **Validation:** r/devops traction.

### 28. Agent Sandbox (E2B)
- **Source:** [disler/agent-sandbox-skill](https://github.com/disler/agent-sandbox-skill)
- **Category:** Universal
- **What it does:** Isolated cloud sandboxes for full-stack builds. Vue + FastAPI + SQLite.
- **Overlap:** 0%
- **Proposed command:** `/sandbox-build`
- **Validation:** Composio top-10.

### 29. /last30days (Web Research)
- **Source:** [Matt Van Horn on X](https://x.com/mvanhorn/status/2015551849710190697) | [@slashlast30days](https://x.com/slashlast30days)
- **Category:** Universal
- **What it does:** Scans last 30 days on Reddit, X, web for any topic. Returns patterns and workflows.
- **Overlap:** ~20% with twitter-x + reddit. Research-oriented vs posting.
- **Proposed command:** `/last30days`
- **Validation:** Own X account. Multiple endorsements.

### 30. Skill Learner / Meta-Skill
- **Source:** [Siqi Chen on X](https://x.com/blader/status/2012667150440476851) (CEO of Runway)
- **Category:** Universal (Meta)
- **What it does:** Auto-learns skills by observing work patterns.
- **Overlap:** ~50% with skill-factory + learn-n-improve. Fully automatic.
- **Proposed command:** `/skill-learner`
- **Validation:** Siqi Chen (CEO of Runway).

### 31. CCPM (Claude Code Project Management)
- **Source:** [Ran Aroussi on X](https://x.com/aroussi/status/1958181744601166059)
- **Category:** Universal (PM)
- **What it does:** Brainstorm -> PRD -> Epic -> Tasks -> parallel execution via worktrees. GitHub Issues.
- **Overlap:** ~45% with plan-to-issues. Full PM lifecycle + parallel execution.
- **Proposed command:** `/ccpm`
- **Validation:** Used internally months before open-sourcing.

### 32. Web Quality Skills (Addy Osmani)
- **Source:** [AaddyOsmani/web-quality-skills](https://github.com/AaddyOsmani/web-quality-skills) (496 stars)
- **Category:** Universal (Web Performance)
- **What it does:** Core Web Vitals, accessibility, performance, responsive design, SEO, progressive enhancement.
- **Overlap:** ~20% with ui-ux-pro-max. Quantitative metrics vs design aesthetics.
- **Proposed command:** `/web-quality`
- **Validation:** 496 stars. Addy Osmani (Google Chrome team).

### 33. Obsidian Knowledge Management
- **Source:** [kepano on X](https://x.com/kepano/status/2008578873903206895) (CEO of Obsidian)
- **Category:** Universal
- **What it does:** Edit .md/.base/.canvas in Obsidian vaults. Log decisions, bug fixes, snippets.
- **Overlap:** ~15% with learn-n-improve. Structured vault management.
- **Proposed command:** `/obsidian`
- **Validation:** kepano (CEO of Obsidian). Greg Isenberg.

### 34. Frontend Slides Skill
- **Source:** [Zara Zhang on X](https://x.com/zarazhangrui/status/2016337615843434646)
- **Category:** Universal (Content Creation)
- **What it does:** Web-based slides: design directions, transitions, animations, auto-fitting, PPTX-to-web.
- **Overlap:** 0%
- **Proposed command:** `/slides`
- **Validation:** Zara Zhang on X.

### 35. Remotion Video Generation
- **Source:** [remotion-dev/skills](https://github.com/remotion-dev/skills)
- **Category:** Stack-specific (Video/React)
- **What it does:** Programmatic video with React/Remotion: animations, timing, audio, captions, 3D.
- **Overlap:** 0%
- **Proposed command:** `/remotion-video`
- **Validation:** 117k+ weekly installs. Top 5 globally.

### 36. D3.js Data Visualization
- **Source:** [chrisvoncsefalvay/claude-d3js-skill](https://github.com/chrisvoncsefalvay/claude-d3js-skill)
- **Category:** Stack-specific (D3.js)
- **What it does:** D3.js patterns: selections, joins, transitions, scales, axes, interactive charts.
- **Overlap:** 0%
- **Proposed command:** `/d3-viz`
- **Validation:** awesome-claude-skills.

### 37. WooYun Security Knowledge Base
- **Source:** [blackorbird on X](https://x.com/blackorbird/status/2015459116224008532)
- **Category:** Universal (Security)
- **What it does:** 88,636 real vulnerability cases (2010-2016). Historical pattern recognition.
- **Overlap:** ~10% with claude-guardian. Knowledge-based vs process-based.
- **Proposed command:** `/security-kb`
- **Validation:** Security community on X.

### 38. Solidity Security Skill
- **Source:** [Patrick Collins on X](https://x.com/PatrickAlphaC/status/2024225364550275194) (Cyfrin founder)
- **Category:** Stack-specific (Solidity/Web3)
- **What it does:** Production Solidity: private key safety, testing, security. Multiple audit variants.
- **Overlap:** 0%
- **Proposed command:** `/solidity-audit`
- **Validation:** Patrick Collins (Cyfrin founder, major Solidity educator).

### 39. Railway Deployment
- **Source:** [Matt Shumer on X](https://x.com/mattshumer_/status/2014444641630785910)
- **Category:** Stack-specific (DevOps)
- **What it does:** Deploy/manage Railway projects autonomously.
- **Overlap:** ~30% with fastapi-deploy. Platform-specific.
- **Proposed command:** `/railway-deploy`
- **Validation:** Matt Shumer (well-known AI dev).

---

## Review Status Tracker

| # | Skill | Decision | Notes |
|---|-------|----------|-------|
| 1 | Redis Agent Skill | APPROVED | Priority stack, 0% overlap, official vendor |
| 2 | Firebase Agent Skills Suite | APPROVED | Consolidate to 2-3 skills, replaces empty placeholder |
| 3 | Flutter Expert Skill | APPROVED | New stack, 0% overlap, 4 independent implementations |
| 4 | Flutter E2E Testing | APPROVED | Scoped to Flutter/Android/Web, complements flutter-dev |
| 5 | Android Architecture & Compose Suite | APPROVED | 4 new skills, merge android-adb-test into android-arch |
| 6 | Kotlin Multiplatform Subagents | DEFERRED | Single-source, niche. Add KMP section to android-arch instead |
| 7 | Vue/Nuxt Skills Suite | APPROVED | Consolidate 8 → 2: /vue-dev + /nuxt-dev |
| 8 | PostgreSQL Read-Only Query | APPROVED | Priority stack, 0% overlap, safe by design |
| 9 | iOS Simulator Skill | DEFERRED | iOS not on priority list, macOS only |
| 10 | React Native (Callstack) | APPROVED | 998 stars, cross-platform mobile, Callstack backing |
| 11 | Expo Skills | APPROVED | Consolidated to 1 skill, pairs with react-native-dev |
| 12 | Elasticsearch Skill | REJECTED | Not priority, single source, Redis covers search |
| 13 | Trail of Bits Security | APPROVED | Consolidate 19 → 3: security-audit, supply-chain-audit, semgrep-rules |
| 14 | Superpowers (umbrella) | IN REVIEW | Reviewing 14 sub-skills individually below |
| 14a | Superpowers: brainstorming | APPROVED | On-demand /brainstorm, Socratic questioning |
| 14b | Superpowers: writing-plans | APPROVED | Fills gap between brainstorm and plan-to-issues |
| 14c | Superpowers: executing-plans | APPROVED | Created `core/.claude/skills/executing-plans/` — bridges /writing-plans → /plan-to-issues pipeline gap |
| 14d | Superpowers: subagent-driven-development | APPROVED | Created `core/.claude/skills/subagent-driven-dev/` — orchestration patterns for delegating to subagents |
| 14e | Superpowers: dispatching-parallel-agents | SKIPPED | Redundant with 14d subagent-driven-dev |
| 14f | Superpowers: test-driven-development | SKIPPED | Already covered by /implement step 2 + workflow.md rule |
| 14g | Superpowers: systematic-debugging | APPROVED | Created `core/.claude/skills/systematic-debugging/` — structured root cause analysis |
| 14h | Superpowers: verification-before-completion | MERGED | Enhanced `/implement` Step 6 with mandatory gate, multi-layer checklist, partial failure protocol |
| 14i | Superpowers: using-git-worktrees | APPROVED | Created `core/.claude/skills/git-worktrees/` — isolation patterns for parallel development |
| 14j | Superpowers: requesting-code-review | APPROVED | Created `core/.claude/skills/request-code-review/` — risk-aware PR creation with intelligent review questions |
| 14k | Superpowers: receiving-code-review | APPROVED | Created `core/.claude/skills/receive-code-review/` — feedback triage, disagreement protocol, learning extraction |
| 14l | Superpowers: finishing-a-development-branch | APPROVED | Created `core/.claude/skills/branching/` (renamed from finish-branch) — full branch lifecycle: create + finish |
| 14m | Superpowers: writing-skills | APPROVED | Created `core/.claude/skills/writing-skills/` — skill authoring guide, templates, quality checklist |
| 14n | Superpowers: using-superpowers | APPROVED | Created `core/.claude/skills/skill-master/` — universal dynamic skill router, discovers all skills at runtime |
| 15 | GSD | MERGED | Context rot prevention → `context-management.md` rule #7; Requirement tiers → `/brainstorm` Step 5; Atomic plans → `/writing-plans` Step 2 |
| 16 | /batch | APPROVED | Created `core/.claude/skills/batch/` — parallel codebase-wide changes, renames, API migrations |
| 17 | /handover | APPROVED | Created `core/.claude/skills/handover/` + cross-refs in context-management rules #3, #6 |
| 18 | TDD Cycle | APPROVED | Created `core/.claude/skills/tdd/` — self-contained red-green-refactor with phase gates |
| 19a | DevOps: docker-optimize | APPROVED | Created `core/.claude/skills/docker-optimize/` — multi-stage builds, caching, security |
| 19b | DevOps: k8s-deploy | APPROVED | Created `core/.claude/skills/k8s-deploy/` — manifests, probes, HPA, RBAC, Helm |
| 19c | DevOps: ci-cd-setup | APPROVED | Created `core/.claude/skills/ci-cd-setup/` — GitHub Actions, GitLab CI, pipeline stages |
| 19d | DevOps: monitoring-setup | APPROVED | Created `core/.claude/skills/monitoring-setup/` — Prometheus, Grafana, SLO/SLI |
| 19e | DevOps: incident-response | APPROVED | Created `core/.claude/skills/incident-response/` — triage, mitigation, post-mortem |
| 19f | DevOps: iac-deploy | APPROVED | Created `core/.claude/skills/iac-deploy/` — Terraform, Pulumi, state management |
| 20 | Playwright E2E | APPROVED | Created `core/.claude/skills/playwright/` + enhanced `verify-screenshots` (baselines, CI, thresholds) + enhanced `testing.md` (flaky prevention) |
| 21 | Production Workflows (shinpr) | MERGED | Complexity routing → `/skill-master` step 2.2; Cross-layer analysis → `/implement` step 1.5 |
| 22 | /apex | MERGED | Branch init → `/branching` step 0; Complexity routing → `/skill-master` step 2.2 (from #21) |
| 23 | Qodo PR Skills | APPROVED | Created `core/.claude/skills/pr-standards/` — team standards enforcement against PR diffs |
| 24 | Adversarial Review | APPROVED | Created `core/.claude/skills/adversarial-review/` — cross-model multi-round debate for plans and code |
| 25 | Context Engineering Kit | MERGED | ADR format → `/handover` step 3.3; token budget/compression/snapshots → SKIP (already covered) |
| 26 | RIPER Workflow | MERGED | Deep research → `/brainstorm` step 2 (expanded to 2.1-2.3); Entry/exit criteria → `/skill-master` step 5.3 |
| 27 | Compound Engineering | MERGED | Error→fix→lesson DB + pattern detection → `/learn-n-improve` steps 3,5; Past learning search → `/systematic-debugging` step 0 |
| 28 | Agent Sandbox (E2B) | SKIPPED | Too platform-specific (E2B only), requires external account, worktree isolation covers most use cases |
| 29 | /last30days | SKIPPED | Covered by /reddit + /twitter-x + /github + WebSearch; cross-platform aggregation better as /skill-master workflow chain |
| 30 | Skill Learner | MERGED | Workflow pattern detection + frequency-based promotion → `/learn-n-improve` step 5.5 |
| 31 | CCPM | MERGED | PRD output format → `/brainstorm` step 5 alt; Epic/milestone hierarchy → `/plan-to-issues` step 3 |
| 32 | Web Quality (Osmani) | APPROVED | Created `core/.claude/skills/web-quality/` — Core Web Vitals, a11y, SEO, performance, responsive design |
| 33 | Obsidian Knowledge Mgmt | APPROVED | Created `core/.claude/skills/obsidian/` — vault management, .md/.base/.canvas files, CLI integration, dev brain logging, wikilinks, callouts |
| 34 | Frontend Slides | SKIPPED | Single source, niche use case, no established framework patterns |
| 35 | Remotion Video | APPROVED | Created `core/.claude/skills/remotion-video/` — compositions, animations, audio, captions, 3D, batch rendering, Zod schemas |
| 36 | D3.js Visualization | APPROVED | Created `core/.claude/skills/d3-viz/` — selections, scales, axes, transitions, 9 chart types, interactions, responsive SVG |
| 37 | WooYun Security KB | SKIPPED | Outdated (2010-2016), shut-down platform, no skill implementation, /security-audit covers modern patterns |
| 38 | Solidity Security | APPROVED | Created `core/.claude/skills/solidity-audit/` — CEI pattern, Foundry/Hardhat testing, UUPS upgrades, gas optimization, Cyfrin audit methodology, ERC standards |
| 39 | Railway Deployment | SKIPPED | Single source, platform-specific, small market share, /ci-cd-setup + /iac-deploy cover generic deployment |
