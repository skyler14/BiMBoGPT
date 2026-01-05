"""
Registration system for integrating BiMBoGPT with AI platforms.

Generates configuration files for:
- stdout (none): Print usage instructions
- Claude Code (code): Create CLAUDE.md
- Antigravity (agent): Create workflow file
- MCP (mcp): Start JSON-RPC server
"""

import os
import sys
import json
from pathlib import Path

PLATFORMS = ["none", "code", "agent", "mcp"]

# Templates
USAGE_TEMPLATE = """\
# BiMBoGPT

Babble In Means Better Out - drop-in OpenAI wrapper with babble priming.

## Installation

```bash
pip install bimbogpt
```

## Usage

```python
from bimbogpt import BimboClient

client = BimboClient()  # Uses OPENAI_API_KEY
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Explain this in 1 word: ..."}]
)
```

## CLI

```bash
bimbogpt process "summarize in 1 word: <content>"
echo "long text" | bimbogpt process --mode sentence
```
"""

CLAUDE_MD_TEMPLATE = """\
# Tool: BiMBoGPT

Summarize content concisely. Use when user asks for tldr, summary, 
or requests output "in 1 word" / "in one sentence".

## Command

```bash
bimbogpt process "<content>" --mode word|sentence|paragraph
```

## Triggers

- "in 1 word", "in one word"
- "in 2 sentences", "in two sentences"
- "tldr", "gimme the gist"
- "summarize", "briefly"
"""

WORKFLOW_TEMPLATE = """\
---
description: Inject babble priming for better LLM reasoning. Use /bimbo to enhance concise answers.
---
# BiMBoGPT

When user requests concise output (one word, tldr, summarize), inject babble priming.

## FIFO Delegation

```bash
bimbogpt process "<content>" -f
```
"""


def register_none(verbose: bool = False) -> None:
    """Print usage instructions to stdout."""
    print(USAGE_TEMPLATE)


def register_code(verbose: bool = False) -> None:
    """Create CLAUDE.md in current directory."""
    path = Path.cwd() / "CLAUDE.md"
    
    # Append if exists, create if not
    mode = "a" if path.exists() else "w"
    
    with open(path, mode) as f:
        if mode == "a":
            f.write("\n\n")
        f.write(CLAUDE_MD_TEMPLATE)
    
    if verbose:
        print(f"{'Appended to' if mode == 'a' else 'Created'}: {path}", file=sys.stderr)


def register_agent(verbose: bool = False) -> None:
    """Create workflow files for Antigravity agent discovery."""
    workflow_dir = Path.cwd() / ".antigravity" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    # Create main workflow file
    main_file = workflow_dir / "bimbo.md"
    main_file.write_text(WORKFLOW_TEMPLATE)
    if verbose:
        print(f"Created: {main_file}", file=sys.stderr)
    
    # Create symlink alias
    alias_file = workflow_dir / "babble.md"
    if alias_file.exists() or alias_file.is_symlink():
        alias_file.unlink()
    alias_file.symlink_to("bimbo.md")
    if verbose:
        print(f"Symlinked: {alias_file} -> bimbo.md", file=sys.stderr)


def register_mcp(verbose: bool = False) -> None:
    """Start MCP JSON-RPC server on stdio."""
    manifest = {
        "name": "bimbogpt",
        "version": "0.1.0",
        "tools": [
            {
                "name": "summarize",
                "description": "Summarize content with babble priming",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Content to summarize"},
                        "mode": {"type": "string", "enum": ["word", "sentence", "paragraph"]},
                    },
                    "required": ["content"],
                },
            }
        ],
    }
    
    # Print manifest and enter server loop
    print(json.dumps(manifest))
    sys.stdout.flush()
    
    # Simple JSON-RPC loop
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            req_id = request.get("id")
            
            if method == "summarize":
                # Would process here - for now just echo
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"status": "processed", "input": params},
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"},
                }
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            pass


def register_help() -> None:
    """Print registration help."""
    help_text = """\
BiMBoGPT Registration
=====================

Register BiMBoGPT with AI platforms:

  --register none     Print instructions to stdout (default)
  --register code     Register with Claude Code (CLAUDE.md)
  --register agent    Register with Antigravity (.antigravity/workflows/)
  --register mcp      Start MCP server mode
"""
    print(help_text)


def register(platform: str, verbose: bool = False) -> None:
    """Register with the specified platform."""
    handlers = {
        "none": register_none,
        "code": register_code,
        "agent": register_agent,
        "mcp": register_mcp,
        "help": register_help,
    }
    
    handler = handlers.get(platform)
    if handler:
        if platform == "help":
            handler()
        else:
            handler(verbose=verbose)
    else:
        print(f"Unknown platform: {platform}", file=sys.stderr)
        sys.exit(1)
