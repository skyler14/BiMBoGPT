# BiMBoGPT

**Babble In Means Better Out** — Drop-in OpenAI wrapper that injects babble priming for better LLM reasoning.

## The Insight

When you ask an LLM to copy filler text before answering, it's forced to "show its work" — producing longer reasoning chains that lead to better answers. More babble = more verbose reasoning = better outputs.

## Installation

```bash
pip install bimbogpt
```

## Usage

Just swap your OpenAI import:

```python
# Before
from openai import OpenAI
client = OpenAI()

# After  
from bimbogpt import BimboClient
client = BimboClient()
```

That's it. When your prompts contain triggers like "in 1 word" or "summarize", babble is automatically injected.

```python
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{
        "role": "user", 
        "content": "What's the capital of the country bordering both Spain and Germany? Answer in 1 word."
    }]
)
# Babble priming is injected → model reasons more → better answer
```

## Triggers

- `in 1 word`, `in one word`, `in 2 sentences`, etc.
- `tldr`, `tl;dr`
- `summarize`, `briefly`
- `gimme the gist`

## Configuration

```python
client = BimboClient(
    babble_word="blah",      # Word to repeat (default: "blah")
    repetitions=100,         # Fixed count (default: auto-scales)
    auto_scale=True,         # More babble for terser outputs
    verbose=True,            # Log when triggers detected
)
```

## CLI

```bash
bimbogpt --help
bimbogpt --register code    # Create CLAUDE.md
bimbogpt --register agent   # Create Antigravity workflow
```

## License

MIT
