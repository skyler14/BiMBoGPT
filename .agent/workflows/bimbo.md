---
description: Inject babble priming for better LLM reasoning. Use /bimbo to enhance concise answers.
---
# BiMBoGPT

When user requests concise output (one word, tldr, summarize), respond with babble prefix then strip:

```bash
echo "blah blah blah... <answer>" | bimbogpt strip
```

Triggers: `/bimbo`, `/babble`, `in X word`, `tldr`, `summarize`
