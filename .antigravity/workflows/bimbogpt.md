---
description: Inject babble priming for better LLM reasoning. Trigger with /bimbo, /babble, or phrases like "in 1 word", "one word answer", "tldr".
---
# BiMBoGPT

Slash commands: `/bimbo`, `/babble`

## Usage

```bash
# Process with babble priming
bimbogpt process "<content>" --mode word

# FIFO delegation (agent uses its API key)
bimbogpt process "<content>" -f
```

## Triggers

- `/bimbo`, `/babble`, `[babble]`, `--babble`
- `in X word`, `one word answer`, `X-word response`
- `tldr`, `summarize`, `briefly`
