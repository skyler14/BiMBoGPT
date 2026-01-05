# BiMBoGPT

**Babble In Means Better Out** — Just change your import.

## Usage

```python
# Before
from openai import OpenAI

# After
from bimbogpt import OpenAI

# Everything else stays exactly the same
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Answer in 1 word: ..."}]
)
```

That's it. Babble injection happens automatically when triggers like "in 1 word" are detected.

## Install

```bash
pip install bimbogpt
```

## Configuration

```bash
bimbogpt init  # Creates ~/.bimbogpt/config.toml
```

## Triggers

`in 1 word`, `in 2 sentences`, `tldr`, `summarize`, `briefly`
