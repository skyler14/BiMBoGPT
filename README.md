# BiMBoGPT

**Babble In Means Better Out** — Just change your import.

> "My thoughts will NOT put me in shackles any longer 💖"  
> — 2022 Tiktok Bimbo Manifesto 

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

### Force Custom Babble

You can override auto-detection and force custom babble:

```python
# String: auto-repeated (100x default)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    force_babble="meow"  # Repeats "meow" 100 times
)

# List: used as-is (no repetition)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    force_babble=["blah"] * 100  # Exactly 100 blahs
)

# Custom instruction
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    force_babble=["Count to 100"]  # Single instruction
)
```

## Install

```bash
pip install git+https://github.com/skyler14/BiMBoGPT.git
```

## Configuration

```bash
bimbogpt init  # Creates ~/.bimbogpt/config.toml
```

## Triggers

`in 1 word`, `in 2 sentences`, `tldr`, `concisely`, `short answer`
