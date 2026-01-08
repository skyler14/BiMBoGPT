# BiMBoGPT

**Babble In Means Better Out** — Just change your import.

> "My thoughts will NOT put me in shackles any longer 💖"  
> — 2022 Tiktok Bimbo Manifesto 

## Install

```bash
pip install git+https://github.com/skyler14/BiMBoGPT.git
```

## Quick Start

```python
# Before
from openai import OpenAI

# After
from bimbogpt import OpenAI

# Everything else stays exactly the same
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Answer in 1 word: What is the capital of France?"}]
)
print(response.choices[0].message.content)  # "Paris"
```

Babble injection happens automatically when triggers are detected, then stripped from the response.

## Triggers

Auto-detected phrases that activate babble priming:

| Trigger | Mode | Example |
|---------|------|---------|
| `in X word(s)` | word | "answer in 1 word" |
| `in X sentence(s)` | sentence | "explain in 2 sentences" |
| `X word answer` | word | "one word answer" |
| `tldr` / `tl;dr` | word | "give me the tldr" |
| `concisely` | sentence | "explain concisely" |
| `short answer` | sentence | "short answer please" |
| `/bimbo`, `/babble` | word | slash commands |
| `[babble]`, `--babble` | word | explicit flags |

## Force Custom Babble

Override auto-detection with custom babble:

```python
# String: auto-repeated (100x default)
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    force_babble="meow"
)

# List: used as-is (no repetition)
response = client.chat.completions.create(
    model="gpt-4", 
    messages=[{"role": "user", "content": "What is 2+2?"}],
    force_babble=["blah"] * 100
)

# Custom priming instruction
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What is 2+2?"}],
    force_babble=["Count to 100 first"]
)
```

## Multi-Model Support

Query different LLM providers (Groq, Anthropic, Ollama) via `models.jsonl`:

### Setup

Create `models.jsonl` in your project root or `~/.bimbogpt/`:

```jsonl
{"name": "groq-llama3", "provider": "groq", "model": "llama-3.3-70b-versatile", "api_key": "gsk_...", "base_url": "https://api.groq.com/openai/v1"}
{"name": "local-ollama", "provider": "ollama", "model": "llama3", "base_url": "http://localhost:11434/v1"}
{"name": "openai-gpt4", "provider": "openai", "model": "gpt-4", "api_key": "sk-..."}
```

> ⚠️ **Security:** Add `models.jsonl` to `.gitignore` - it contains API keys!

### CLI Usage

```bash
# Query a configured model
bimbogpt query groq-llama3 "In 1 word: What is 2+2?"

# With verbose error output
bimbogpt query groq-llama3 "test" --verbose
```

### Python Usage

```python
from bimbogpt.models import query_model, list_models

# List available models
print(list_models())  # ['groq-llama3', 'local-ollama', 'openai-gpt4']

# Query with automatic retry on rate limits
response = query_model("groq-llama3", [
    {"role": "user", "content": "In 1 word: What is the capital of France?"}
])
print(response)  # "Paris"
```

## CLI Commands

```bash
# Initialize config file
bimbogpt init

# Strip babble from piped input
echo "blah blah blah Paris" | bimbogpt strip
# Output: Paris

# Query configured model
bimbogpt query <model-name> "<prompt>"

# Register for agent integration
bimbogpt --register agent  # Creates .agent/workflows/bimbo.md
bimbogpt --register code   # Creates CLAUDE.md
```

## Configuration

### Config File

```bash
bimbogpt init  # Creates ~/.bimbogpt/config.toml
```

```toml
[babble]
word = "blah"
repetitions = 100
auto_scale = true

[stripping]
threshold = 0.6
typo_tolerance = 2

[agent]
default_model = "gpt-4"
```

### Environment Variables

```bash
export BIMBOGPT_WORD="meow"
export BIMBOGPT_REPETITIONS=50
```

### Constructor Args

```python
from bimbogpt import OpenAI

client = OpenAI(
    babble_word="blah",
    repetitions=100,
    verbose=True  # Enable debug logging
)
```

## Logging

BiMBoGPT uses Python's standard logging (like OpenAI SDK):

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now you'll see:
# DEBUG:bimbogpt.client:Trigger: 'in 1 word'
# DEBUG:bimbogpt.client:Forced babble: 100 words
```

## How It Works

1. **Detect** trigger phrases ("in 1 word", "tldr", etc.)
2. **Inject** babble: `First, copy this text exactly: "blah blah blah..." Then answer:`
3. **Send** to LLM - the copying primes better reasoning
4. **Strip** babble from response, return clean answer

The key insight: making models "show their work" by copying filler text forces longer reasoning chains before answering, producing better results for concise outputs.

## License

MIT
