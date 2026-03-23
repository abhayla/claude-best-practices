---
name: mcp-server-builder
description: >
  Build MCP (Model Context Protocol) servers that extend Claude Code's capabilities.
  Covers agent-centric design, Python FastMCP and Node/TypeScript SDK, registration,
  resource management, error handling, and evaluation-driven development.
  Use when creating or extending an MCP server for Claude Code integration.
triggers:
  - build mcp server
  - create mcp
  - mcp tool
  - model context protocol
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<what the MCP server should do, e.g., 'connect to Jira API' or 'manage Docker containers'>"
version: "1.0.0"
type: workflow
---

# MCP Server Builder

Build an MCP server that extends Claude Code with new tools, resources, or prompts.

**Server Purpose:** $ARGUMENTS

---

## STEP 1: Define the Server Scope

Before writing code, define what the MCP server will expose:

### 1.1 Identify Capabilities

| MCP Primitive | Use When | Examples |
|---------------|----------|---------|
| **Tools** | Claude needs to perform actions or retrieve computed data | Query a database, create a ticket, run a deployment |
| **Resources** | Claude needs to read structured data | Config files, API schemas, documentation |
| **Prompts** | Claude needs reusable prompt templates | Code review checklist, incident response template |

### 1.2 Agent-Centric Design Principles

MCP servers are consumed by AI agents, not humans. Design accordingly:

1. **Build for workflows, not endpoints** — Group related operations into tools that match how an agent thinks about a task. One tool that "creates a PR with tests" beats three tools for "create branch", "commit files", "open PR".

2. **Optimize for limited context** — Return only what the agent needs. A tool that returns a 10,000-line log is worse than one that returns the 20 relevant lines with context.

3. **Make errors actionable** — Instead of `"Error: 403"`, return `"Permission denied: the API token lacks 'write:issues' scope. Add this scope at https://..."`. The agent should be able to fix the problem from the error message alone.

4. **Provide discovery** — Include a tool that lists available resources or explains what the server can do. Agents need to understand capabilities at runtime.

5. **Idempotent where possible** — Agents may retry tools. Design create/update operations to be safe to call multiple times with the same input.

### 1.3 Define Tool Signatures

For each tool, define:

```
Tool: <name>
  Description: <what it does — this is what Claude reads to decide whether to use it>
  Input: <parameters with types and descriptions>
  Output: <what it returns>
  Side effects: <what it changes in the external system>
  Error cases: <what can go wrong and what the error message should say>
```

**Description quality matters.** Claude selects tools based on their descriptions. A vague description like "manage issues" produces poor tool selection. Be specific: "Create a new GitHub issue with title, body, labels, and assignee. Returns the issue URL and number."

---

## STEP 2: Choose SDK and Scaffold

### Option A: Python with FastMCP

FastMCP is the recommended Python SDK — minimal boilerplate, decorator-based.

```bash
# Initialize project
mkdir mcp-server-<name> && cd mcp-server-<name>
python -m venv .venv && source .venv/bin/activate  # or .venv/Scripts/activate on Windows
pip install fastmcp
```

Scaffold:

```python
# server.py
from fastmcp import FastMCP

mcp = FastMCP(
    name="<server-name>",
    description="<what this server does>",
)

@mcp.tool()
def example_tool(param: str) -> str:
    """Description that Claude reads to decide when to use this tool.

    Args:
        param: What this parameter controls
    """
    # Implementation here
    return "result"

@mcp.resource("resource://{name}")
def example_resource(name: str) -> str:
    """Provides access to <what>."""
    return "resource content"

if __name__ == "__main__":
    mcp.run()
```

### Option B: Node.js / TypeScript SDK

```bash
mkdir mcp-server-<name> && cd mcp-server-<name>
npm init -y
npm install @modelcontextprotocol/sdk
npm install -D typescript @types/node
npx tsc --init
```

Scaffold:

```typescript
// src/index.ts
import { McpServer, ResourceTemplate } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new McpServer({
  name: "<server-name>",
  version: "1.0.0",
});

server.tool(
  "example-tool",
  "Description that Claude reads to decide when to use this tool",
  { param: { type: "string", description: "What this parameter controls" } },
  async ({ param }) => {
    // Implementation here
    return { content: [{ type: "text", text: "result" }] };
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
```

---

## STEP 3: Implement Tools

### 3.1 Tool Implementation Checklist

For each tool:

- [ ] Description is specific and tells Claude WHEN to use it (not just what it does)
- [ ] All parameters have types, descriptions, and sensible defaults where applicable
- [ ] Return values are concise — only what the agent needs for next steps
- [ ] Errors include actionable remediation instructions
- [ ] Side effects are documented in the description
- [ ] Tool is idempotent or clearly marked as non-idempotent

### 3.2 Input Validation

Validate inputs and return helpful messages:

```python
@mcp.tool()
def create_issue(title: str, body: str, labels: list[str] | None = None) -> str:
    """Create a GitHub issue in the current repository.

    Args:
        title: Issue title (required, max 256 chars)
        body: Issue body in markdown
        labels: Optional list of label names (must already exist in repo)
    """
    if not title.strip():
        return "Error: title is required and cannot be empty."
    if len(title) > 256:
        return f"Error: title is {len(title)} chars, max is 256. Shorten the title."
    # ... implementation
```

### 3.3 Error Handling Pattern

```python
try:
    result = external_api.call(params)
    return format_result(result)
except AuthenticationError:
    return (
        "Error: Authentication failed. Check that your API token is set in the "
        "environment variable EXAMPLE_API_TOKEN and has the required scopes: "
        "read:data, write:data. Generate a token at https://example.com/settings/tokens"
    )
except RateLimitError as e:
    return f"Error: Rate limited. Retry after {e.retry_after} seconds."
except Exception as e:
    return f"Error: Unexpected failure — {type(e).__name__}: {e}"
```

### 3.4 Output Formatting

Return structured, scannable output:

```python
# BAD: Wall of text
return json.dumps(full_api_response)

# GOOD: Curated summary
return f"""Issue created successfully.
- URL: {issue.html_url}
- Number: #{issue.number}
- Labels: {', '.join(issue.labels)}

Next: assign the issue with the assign-issue tool, or link it to a PR."""
```

---

## STEP 4: Implement Resources (if needed)

Resources provide read-only data that Claude can reference:

```python
@mcp.resource("config://settings")
def get_settings() -> str:
    """Current project settings including API endpoints and feature flags."""
    settings = load_settings()
    # Return only what's relevant, not the entire config
    return yaml.dump({
        "api_base": settings["api_base"],
        "features": settings["features"],
        "environment": settings["environment"],
    })
```

### Resource Design Rules

1. **URI scheme matters** — Use descriptive schemes: `docs://`, `config://`, `schema://`
2. **Keep payloads small** — Resources are loaded into context. A 50KB resource wastes tokens.
3. **Provide templates for parameterized access** — `docs://{topic}` is better than dumping all docs at once

---

## STEP 5: Configure for Claude Code

### 5.1 Register in .mcp.json

Add the server to the project's `.mcp.json`:

```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "python",
      "args": ["path/to/server.py"],
      "env": {
        "EXAMPLE_API_TOKEN": "${EXAMPLE_API_TOKEN}"
      }
    }
  }
}
```

For Node.js:
```json
{
  "mcpServers": {
    "<server-name>": {
      "command": "node",
      "args": ["path/to/dist/index.js"]
    }
  }
}
```

### 5.2 Environment Variables

NEVER hardcode credentials in the server. Use environment variables:

```python
import os

API_TOKEN = os.environ.get("EXAMPLE_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError(
        "EXAMPLE_API_TOKEN environment variable is required. "
        "Set it in .mcp.json env block or your shell profile."
    )
```

---

## STEP 6: Test the Server

### 6.1 Manual Testing

```bash
# Test with MCP Inspector (if available)
npx @modelcontextprotocol/inspector python server.py

# Or test directly by running the server and sending JSON-RPC
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | python server.py
```

### 6.2 Automated Tests

Write tests for each tool:

```python
# test_server.py
import pytest
from server import mcp

@pytest.fixture
def client():
    """Create a test client for the MCP server."""
    return mcp.test_client()

def test_example_tool_happy_path(client):
    result = client.call_tool("example-tool", {"param": "test"})
    assert "expected output" in result

def test_example_tool_missing_param(client):
    result = client.call_tool("example-tool", {})
    assert "Error:" in result

def test_example_tool_error_is_actionable(client):
    result = client.call_tool("example-tool", {"param": "invalid"})
    # Error messages MUST tell the agent how to fix the problem
    assert any(word in result.lower() for word in ["try", "check", "use", "set"])
```

### 6.3 Evaluation-Driven Development

Beyond unit tests, evaluate how well Claude uses your tools:

1. **Discovery test** — Ask Claude "what tools do you have for X?" Does it find your tool?
2. **Selection test** — Give Claude a task that should use your tool. Does it pick the right one?
3. **Error recovery test** — Trigger an error. Can Claude fix the problem from the error message?
4. **Workflow test** — Give Claude a multi-step task. Does it chain your tools correctly?

If Claude struggles with any of these, improve the tool descriptions and error messages — don't blame the model.

---

## STEP 7: Document and Ship

### 7.1 README

Create a README with:
- What the server does (one paragraph)
- Prerequisites (API keys, services, permissions)
- Installation and configuration steps
- List of tools with descriptions
- Example usage scenarios

### 7.2 Version and Maintain

- Pin dependency versions in `requirements.txt` or `package.json`
- Follow semantic versioning — breaking tool signature changes = major version bump
- Test after Claude Code updates — MCP protocol may evolve

---

## MUST DO

- Always validate all tool inputs and return actionable error messages
- Always keep tool descriptions specific enough for Claude to select correctly
- Always use environment variables for credentials — never hardcode
- Always test each tool with both happy path and error cases
- Always keep resource payloads small — curate, don't dump
- Always make tools idempotent where the external system allows it

## MUST NOT DO

- MUST NOT return raw API responses — curate the output for agent consumption
- MUST NOT use vague tool descriptions — "manages data" tells Claude nothing
- MUST NOT expose credentials in error messages or logs
- MUST NOT create tools with overlapping purposes — Claude will pick randomly between them
- MUST NOT return more than ~2KB per tool call unless the agent specifically needs bulk data
- MUST NOT skip error handling — an unhandled exception crashes the MCP server
