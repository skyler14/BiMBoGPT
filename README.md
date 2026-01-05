# BiMBoGPT

**Babble In Means Better Out** — Drop-in OpenAI replacement with babble priming.

## The Insight

Asking LLMs to copy filler text before answering forces them to "show their work" — producing better reasoning chains. More babble = better outputs.

## Installation

```bash
pip install bimbogpt
```

## Usage

`BimboClient` inherits from `OpenAI` — just swap your import:

```python
from bimbogpt import BimboClient

client = BimboClient()  # Inherits from OpenAI, same API
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Answer in 1 word: ..."}]
)
# Babble injected automatically, stripped from response
```

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
