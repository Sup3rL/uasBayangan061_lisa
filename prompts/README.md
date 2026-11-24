# prompts/

Every LLM prompt used in the experiment is stored here as a plain-text file,
exactly as sent to the model (placeholders written as `{like_this}`).

| File | Phase | Used for |
|---|---|---|
| *(added in Phase 6)* `06_zero_shot_task.txt` | 6 | zero-shot task classification |
| *(added in Phase 6)* `06_rag_task.txt` | 6 | RAG task classification with retrieved examples |

Raw model answers are saved in `results/06_llm_raw_outputs.jsonl`.
