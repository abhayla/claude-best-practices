# 10.3 Resumption Protocol

### 10.3 Resumption Protocol

If a handover exists:

1. **Read the handover document**
2. **Read the Handoff Mail section first** — it contains the outgoing session's most important unstructured context
3. **Present a brief summary to the user:**

   > Resuming from handover dated {date}.
   >
   > **Last session:** {summary in 1-2 sentences}
   >
   > **Next steps queued:**
   > 1. [P1] {first item} [complexity]
   > 2. [P1] {second item} [complexity]
   > 3. [P2] {third item} [complexity]
   >
   > **Active pitfalls:** {count} — will avoid these.
   > **Active workarounds:** {count} — aware of these.
   >
   > Continue from next steps, or would you like to start fresh?

3. **Wait for user direction** — do NOT auto-start work. The user may:
   - Continue from the queued next steps
   - Reprioritize the next steps
   - Start something entirely different
   - Ask for details on a specific section

