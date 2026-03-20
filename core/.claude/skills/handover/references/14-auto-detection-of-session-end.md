# 1.4 Auto-Detection of Session End

### 1.4 Auto-Detection of Session End

Watch for signals that the user is wrapping up:

| Signal | Example Phrases |
|--------|----------------|
| **Explicit stop** | "let's stop", "that's enough", "let's wrap up", "I'm done for today" |
| **Time reference** | "continue tomorrow", "pick this up later", "next session" |
| **Parking** | "let's park this", "save progress", "bookmark where we are" |
| **Handover request** | "handover", "session summary", "what should I tell the next session" |

When any of these signals are detected, suggest:

> "Would you like me to generate a handover document before we stop? This will help the next session pick up exactly where we left off."

Do NOT generate automatically — always ask first. The user may want to do more work before stopping.

---

