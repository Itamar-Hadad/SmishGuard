# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Final Degree Project: SMS smishing (SMS phishing) detection using NLP/ML. The pipeline extracts Sentence-BERT semantic embeddings and combines them with binary pattern-detection flags (URL, email, phone) to produce feature vectors for a classifier.

## Running the Code

```bash
# Install dependencies (first time)
pip install sentence-transformers scikit-learn pandas numpy

# Run the preprocessing pipeline
python MLsmish.py
```

The script must be run from the directory containing `SMSSmishCollection_with_flags.csv`.  
On first run, the Sentence-BERT model (`all-MiniLM-L6-v2`) is downloaded and cached automatically.

## Dataset

Expected file: `SMSSmishCollection_with_flags.csv` (place in working directory or `dataset/`)

Required columns:
- `message` — raw SMS text
- `label` — `ham` or `smish`
- `url`, `email`, `phone` — `yes`/`no` flags (case-insensitive; also auto-detected from text)

## Architecture

`MLsmish.py` is a single-file pipeline executed top-to-bottom:

1. **Pattern detection** (`detect_url`, `detect_phone`, `detect_email`) — regex-based binary flags extracted from raw text
2. **Text preprocessing** (`preprocess_text`) — lowercase + whitespace normalization
3. **Embedding generation** — `SentenceTransformer('all-MiniLM-L6-v2')` produces 384-dim vectors per message (batch size 32)
4. **Feature fusion** — `np.hstack([sbert_embedding, flags])` → 387-dim feature vector (384 + 3)
5. **Train/test split** — 80/20, stratified by label, `random_state=42`

After the pipeline runs, `X_train_combined`, `X_test_combined`, `y_train`, `y_test` are ready for a classifier (not yet included in the script).

### Key configuration constants (top of file)

| Constant | Default | Purpose |
|---|---|---|
| `SBERT_MODEL_NAME` | `all-MiniLM-L6-v2` | Swap to `all-mpnet-base-v2` for 768-dim higher-quality embeddings |
| `TEST_SIZE` | `0.2` | Fraction of data held out for testing |
| `BATCH_SIZE` | `32` | Embedding batch size |
| `RANDOM_STATE` | `42` | Reproducibility seed |

### Inference on new messages

```python
features = process_new_message("Your parcel is ready. Click http://...", sbert_model=sbert_model)
# auto_detect=True (default) runs regex detectors on the message text
# Returns numpy array of shape (1, 387) ready for classifier.predict()
```

Use `print_feature_summary(features, message_text)` to inspect the vector without printing all 387 values.

## Other Files

- `ML Model Examples/` — standalone Jupyter notebooks (Titanic, HousePricing) used for learning; unrelated to the main smishing model
- `Articles/` — reference research papers on smishing detection
- `dataset/` — intended location for the CSV dataset
