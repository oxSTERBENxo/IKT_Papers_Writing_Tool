# Model training-data dates (checked 2026-10-20 on the official model cards)

| Model (Ollama tag) | What the official card says | Source |
|---|---|---|
| Llama-2-7B-chat (`llama2:7b-chat`) | "The pretraining data has a cutoff of September 2022, but some tuning data is more recent, up to July 2023." "Llama 2 was trained between January 2023 and July 2023." | https://huggingface.co/meta-llama/Llama-2-7b-chat-hf |
| Llama-3.2-3B-Instruct (`llama3.2:latest`) | "The pretraining data has a cutoff of December 2023." Release date: Sept 25, 2024. | https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct |
| Gemma-3-4B-it (`gemma3:4b`) | "The knowledge cutoff date for the training data was August 2024." | https://ai.google.dev/gemma/docs/core/model_card_3 |
| Qwen2.5-7B-Instruct (`qwen2.5:7b`) | No cutoff stated. The model card's citation gives September 2024. | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct |

Implication for the design:
- **S2023** (submitted Jan–Aug 2023) falls before the cut-off for Llama-3.2, Gemma-3 and (by release date) Qwen2.5, and after Llama-2's pretraining cut-off.
- **S2026** (Jan–Aug 2026) falls after every model's cut-off.
- **Caveat:** Llama-2's tuning data reaches July 2023.
