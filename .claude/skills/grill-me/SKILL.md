---
name: grill-me
description: Audit a plan or design by interviewing the user relentlessly until shared understanding is reached, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me".
type: workflow
version: 1.0.0
allowed-tools: Read, Grep, Glob
argument-hint: [optional context about the plan or design]
---

Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time.

If a question can be answered by exploring the codebase, explore the codebase instead.

## When to use

- The user has a plan, design, spec, or proposed approach they want pressure-tested
- The user says "grill me", "stress-test this", "drill into this", or "interview me"
- Before committing to a non-trivial architectural decision
- When the user is uncertain whether their plan covers all the branches

## When NOT to use

- Pure factual questions with a single correct answer
- Tasks where the user has already decided and just wants execution
- Quick yes/no clarifications (a single clarification question is enough)

## STEP 1: Map the decision tree

Read whatever context the user shared — a plan file, a message thread, or the question on the table.
List the top-level decision points along with the dependencies between them.
Do not ask anything yet; mapping first prevents premature commitment to a path.

## STEP 2: Pick the first unresolved branch

Choose the branch with the highest leverage — the one whose answer constrains the most downstream decisions.
Prefer load-bearing questions over leaf-level details that can wait.

## STEP 3: Read the codebase before asking

If the question can be answered by reading the code, read the relevant files first.
Only ask the user if real ambiguity remains after the read.
This prevents wasting the user's time on questions you could have answered yourself.

## STEP 4: Ask ONE question with your recommended answer

Frame the question as a single decision with an explicit recommendation.
Example: "Should X be A or B? Recommended: A, because Y."
Do not batch multiple questions into one turn.

## STEP 5: Wait for the response

Block on the user's answer.
Do not move to the next branch until this one is resolved or explicitly deferred.

## STEP 6: Update the tree and repeat

When an answer arrives, update the decision tree.
New branches may appear; mark them.
Loop back to STEP 2 with the updated tree.

## STEP 7: Stop when the tree is resolved

The interview ends when every branch has an explicit decision OR the user signals satisfaction.
Summarize the resolved decisions back to the user as a final checkpoint.

## Stopping conditions

- All design branches have explicit decisions
- The user says "stop", "enough", "I'm convinced", or similar
- A blocker emerges that requires research before the interview can continue
- The plan has changed enough that re-mapping is needed before continuing
