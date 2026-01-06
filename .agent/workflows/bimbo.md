---
description: Inject babble priming for better LLM reasoning. Use /bimbo to enhance concise answers.
---
# BiMBoGPT

## Model Routing

If message contains `@<model-name>`, route to that model:
```bash
bimbogpt query groq-llama3 "In 1 word: <question>"
```

Available models: check `models.jsonl`

## Default (no model specified)

Respond with babble prefix, then strip:
```bash
echo "blah blah blah... <answer>" | bimbogpt strip
```

Triggers: `/bimbo`, `/babble`, `in X word`, `tldr`, `summarize`
