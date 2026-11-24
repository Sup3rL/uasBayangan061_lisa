# models/

This folder is bind-mounted into the Oracle container at `/opt/oracle/models`
(directory object `MODEL_DIR`). Put the ONNX embedding model here:

    models/all_MiniLM_L12_v2.onnx

It is Oracle's pre-built, "augmented" ONNX version of the sentence-transformers
model all-MiniLM-L12-v2 (384 dimensions, tokenizer included), so the database
can create embeddings itself with `VECTOR_EMBEDDING()`.
The `.onnx` file (~130 MB) is ignored by git; see README.md for the download step.
