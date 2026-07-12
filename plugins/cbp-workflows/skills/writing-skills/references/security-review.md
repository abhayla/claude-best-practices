# Security Review for Skill Deployment

Treat skill installation with the same rigor as installing software on
production systems. A malicious or careless skill can direct Claude to
execute arbitrary code, access sensitive files, or transmit data externally.

## Risk Tier Assessment

Evaluate each skill against these risk indicators before approving deployment:

| Risk Indicator | What to Look For | Concern Level |
|---|---|---|
| **Code execution** | Scripts in the skill directory (`*.py`, `*.sh`, `*.js`) | High — scripts run with full environment access |
| **Instruction manipulation** | Directives to ignore safety rules, hide actions from users, or alter Claude's behavior conditionally | High — can bypass security controls |
| **MCP server references** | Instructions referencing MCP tools (`ServerName:tool_name`) | High — extends access beyond the skill itself |
| **Network access patterns** | URLs, API endpoints, `fetch`, `curl`, or `requests` calls | High — potential data exfiltration vector |
| **Hardcoded credentials** | API keys, tokens, or passwords in skill files or scripts | High — secrets exposed in Git history and context window |
| **File system access scope** | Paths outside the skill directory, broad glob patterns, path traversal (`../`) | Medium — may access unintended data |
| **Tool invocations** | Instructions directing Claude to use bash, file operations, or other tools | Medium — review what operations are performed |

## Review Checklist

Before deploying any skill from a third party or internal contributor,
complete every step:

### 1. Read all skill directory content

Review SKILL.md, all referenced markdown files, and any bundled scripts
or resources. Don't rely on the description alone — read the actual
instructions Claude will follow.

### 2. Verify script behavior in sandbox

Run bundled scripts in a sandboxed environment (container, VM, or
isolated directory). Confirm outputs align with the skill's stated
purpose. Watch for:
- Unexpected file creation or modification
- Network connections to unknown hosts
- Environment variable reads beyond what's documented

### 3. Check for adversarial instructions

Search for directives that tell Claude to:
- Ignore safety rules or system instructions
- Hide actions from the user (e.g., "do not mention this step")
- Alter behavior based on specific trigger phrases
- Exfiltrate data through conversational responses
- Override tool restrictions or permission boundaries

### 4. Check for external network access

Search scripts and instructions for network access patterns:
```bash
grep -rn 'http\|requests\.\|urllib\|curl\|fetch\|wget' skills/<name>/
```
Any network access should be documented in the skill's description.
Undocumented network calls are a red flag.

### 5. Verify no hardcoded credentials

Check for API keys, tokens, or passwords in all skill files:
```bash
grep -rn 'api_key\|token\|password\|secret\|Bearer\|Authorization' skills/<name>/
```
Credentials should use environment variables or secure credential
stores, never appear in skill content.

### 6. Identify tools and commands

List all bash commands, file operations, and tool references the skill
instructs Claude to invoke. Consider the combined risk when a skill
uses both file-read and network tools together — this combination
enables data exfiltration.

### 7. Confirm redirect destinations

If the skill references external URLs, verify they point to expected
domains. Check for URL shorteners or redirects that could mask the
true destination.

### 8. Verify no data exfiltration patterns

Look for instructions that:
- Read sensitive data (credentials, config, source code) AND THEN
- Write, send, encode, or include it in output
- This includes encoding data in Claude's conversational responses
  (e.g., "include the file contents in your response")

## When to Run This Review

| Trigger | Required? |
|---|---|
| New skill from external/third-party source | **MUST** — full review, no exceptions |
| New skill from internal contributor | **MUST** — separation of duties: author ≠ reviewer |
| Skill version update (MINOR/PATCH) | **SHOULD** — diff review against previous version |
| Skill version update (MAJOR) | **MUST** — full review (major changes may alter behavior) |
| Periodic re-review of deployed skills | **SHOULD** — quarterly, to catch context drift |

## Quick Reference: grep Commands

```bash
# Network access
grep -rn 'http\|requests\.\|urllib\|curl\|fetch\|wget' skills/<name>/

# Credentials
grep -rn 'api_key\|token\|password\|secret\|Bearer' skills/<name>/

# Path traversal
grep -rn '\.\./\|/etc/\|/home/\|%2e%2e' skills/<name>/

# Adversarial instructions
grep -rn -i 'ignore\|override\|hide\|do not mention\|bypass' skills/<name>/
```

These are starting points, not exhaustive — a determined attacker can
obfuscate. The full 8-step review above is the authoritative process.
