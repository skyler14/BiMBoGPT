"""
FIFO-based agent communication for delegating LLM calls.

When running as a subprocess of an AI agent, BiMBoGPT can delegate
LLM queries back to the calling agent via named pipes.

Protocol:
1. Tool prints a query to stderr with special markers
2. Tool writes JSON query to query_pipe (blocks until agent reads)
3. Agent reads query, makes LLM call, writes response to response_pipe
4. Tool reads response and continues
"""

import os
import sys
import json
import tempfile
from typing import Optional


QUERY_START_MARKER = "<<<BIMBOGPT_LLM_QUERY>>>"
QUERY_END_MARKER = "<<<END_QUERY>>>"


def get_pipe_paths() -> tuple[str, str]:
    """Get paths for query and response pipes based on current PID."""
    pipe_dir = os.path.join(tempfile.gettempdir(), "bimbogpt_pipes")
    os.makedirs(pipe_dir, exist_ok=True)
    
    pid = os.getpid()
    query_pipe = os.path.join(pipe_dir, f"query_{pid}")
    response_pipe = os.path.join(pipe_dir, f"response_{pid}")
    
    return query_pipe, response_pipe


def create_pipes(query_pipe: str, response_pipe: str) -> None:
    """Create the named pipes (FIFOs)."""
    for pipe in [query_pipe, response_pipe]:
        if os.path.exists(pipe):
            os.unlink(pipe)
        os.mkfifo(pipe)


def cleanup_pipes(query_pipe: str, response_pipe: str) -> None:
    """Remove the named pipes."""
    for pipe in [query_pipe, response_pipe]:
        try:
            if os.path.exists(pipe):
                os.unlink(pipe)
        except OSError:
            pass


def signal_agent(query_pipe: str, response_pipe: str, query: dict) -> None:
    """Print the query protocol to stderr for the agent to read."""
    print(QUERY_START_MARKER, file=sys.stderr)
    print(f"QUERY_PIPE: {query_pipe}", file=sys.stderr)
    print(f"RESPONSE_PIPE: {response_pipe}", file=sys.stderr)
    print(json.dumps(query), file=sys.stderr)
    print(QUERY_END_MARKER, file=sys.stderr)
    sys.stderr.flush()


def delegate_to_agent(
    messages: list[dict],
    model: str = "gpt-4",
    timeout: Optional[float] = None,
) -> str:
    """
    Delegate an LLM query to the calling agent via FIFO.
    
    This allows BiMBoGPT to request LLM calls from an AI agent that
    invoked it as a subprocess, enabling the agent to use its own
    API keys and rate limits.
    
    Args:
        messages: OpenAI-style messages list
        model: Model to request (hint to agent)
        timeout: Optional timeout in seconds (not enforced by FIFO)
        
    Returns:
        The agent's response string
        
    Raises:
        BrokenPipeError: If agent doesn't respond
        TimeoutError: If timeout specified and exceeded
    """
    query_pipe, response_pipe = get_pipe_paths()
    
    try:
        # Create pipes
        create_pipes(query_pipe, response_pipe)
        
        # Build query
        query = {
            "messages": messages,
            "model": model,
        }
        if timeout:
            query["timeout"] = timeout
        
        # Signal the agent (stderr)
        signal_agent(query_pipe, response_pipe, query)
        
        # Write query to pipe (blocks until agent reads)
        with open(query_pipe, 'w') as f:
            json.dump(query, f)
        
        # Read response (blocks until agent writes)
        with open(response_pipe, 'r') as f:
            response = f.read()
        
        return response
        
    finally:
        cleanup_pipes(query_pipe, response_pipe)


def parse_agent_query(stderr_output: str) -> Optional[dict]:
    """
    Parse an agent query from stderr output.
    
    Utility function for agents to extract the query protocol.
    
    Returns dict with keys: query_pipe, response_pipe, query
    """
    if QUERY_START_MARKER not in stderr_output:
        return None
    
    try:
        start = stderr_output.index(QUERY_START_MARKER) + len(QUERY_START_MARKER)
        end = stderr_output.index(QUERY_END_MARKER)
        content = stderr_output[start:end].strip()
        
        lines = content.split('\n')
        result = {}
        
        for line in lines:
            if line.startswith("QUERY_PIPE:"):
                result["query_pipe"] = line.split(":", 1)[1].strip()
            elif line.startswith("RESPONSE_PIPE:"):
                result["response_pipe"] = line.split(":", 1)[1].strip()
            else:
                # Try to parse as JSON
                try:
                    result["query"] = json.loads(line)
                except json.JSONDecodeError:
                    pass
        
        return result if "query_pipe" in result else None
        
    except (ValueError, KeyError):
        return None
