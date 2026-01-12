# MLflow Link Prediction Plan (Intra-Window Strategy)

## Goal

Predict missing `FAMILY` links **on-the-fly** within each rolling window. This ensures that predictions rely on the specific network structure (embeddings) of that time period and avoids the complexity of aligning embeddings across time.

## Rationale (Why Intra-Window?)

- **Embedding Alignment**: We use FastRP embeddings which are stochastic and rotation-variant. Embeddings from Window A cannot be used with a model trained on Window B.
- **Temporal Drift**: The definition of a "likely link" may change over time. Training a lightweight model per window captures local temporal dynamics.
- **Efficiency**: Avoids a massive "global" training step; distributes training cost across the window pipeline.

## Methodology

### 1. Integration into `rolling_windows/pipeline.py`

The `run_windows` loop will be augmented with a **Link Prediction Step** after projection and before export.

#### Step A: Data Preparation (Inside Loop)

1.  **Project Window Graph**: Filtered for `tStart`/`tEnd`.
2.  **Identify Trusted Edges**: `r:FAMILY` where `source != 'imputed'`.
3.  **Generate Negative Samples**: Randomly sample non-edges between Person nodes.
4.  **Feature Extraction**:
    - **Graph Features**:
      - Retrieve `FastRP` embeddings (already computed for the window).
      - Compute link features (Hadamard, Cosine, L2) for both positive and negative pairs.
    - **String Features (Levenshtein)**:
      - For each pair `(u, v)`, compute in Python using `python-Levenshtein` or `rapidfuzz`:
        - `patronymic_similarity`: Levenshtein ratio between `u.FirstName` and `v.MiddleName` (and vice-versa).
        - `surname_similarity`: Levenshtein ratio between `u.LastName` and `v.LastName`.
      - **Note**: This replicates the legacy APOC logic efficiently in Python.

#### Step B: Model Training (Inside Loop)

1.  **Model**: `LogisticRegression` (scikit-learn).
2.  **MLflow Tracking**:
    - **Standard**: Use `mlflow_utils.tracking` utilities.
    - **Nested Run**: Start a nested run `mlflow.start_run(run_name=f"window_{window_name}", nested=True)` under the main `exp_014_link_prediction` experiment.
    - **Metrics**: Use `mlflow_utils.tracking.log_metrics_classification` to log AUC, Recall, etc.
    - **Params**: Log model hyperparameters (e.g., C, penalty) and feature list.

#### Step C: Prediction & Export

1.  **Candidate Generation**:
    - **Blocking Strategy**:
      - Filter 1: `surname_similarity > 0.8` (matches legacy).
      - Filter 2: `patronymic_similarity > 0.55` (matches legacy).
    - **Implementation**: Use blocking on First Letter of LastName to reduce comparisons, then compute Levenshtein.
2.  **Scoring**: Apply the trained `LR` model to candidates.
3.  **Thresholding**: Filter for `prob > 0.7` (configurable).
4.  **Export**:
    - Create a `predicted_edges_df` DataFrame: `[source_id, target_id, prob, window_start]`.
    - Save to `rolling_windows/output/predicted_edges/`.

## Updated Pipeline Logic (`rolling_windows/pipeline.py`)

```python
from mlflow_utils.tracking import setup_experiment, log_metrics_classification

# ... at start of pipeline ...
setup_experiment("exp_014_link_prediction")

# ... inside run_windows loop ...

# 1. Standard Algorithms (PageRank, Degree, FastRP)
run_window_algorithms(gds, G, cfg)

# 2. Link Prediction (New)
if cfg.run_link_prediction:
    with mlflow.start_run(run_name=f"window_{window_name}", nested=True):
        # A. Train
        train_df = get_training_data_with_names(gds, window_name)

        # Compute features
        train_df['patronymic_sim'] = compute_levenshtein(train_df)
        train_df['surname_sim'] = compute_levenshtein(train_df)

        # Train
        model = LogisticRegression(penalty='l2')
        model.fit(X_train, y_train)

        # Log Metrics (Standard)
        log_metrics_classification(y_test, model.predict(X_test), model.predict_proba(X_test)[:,1])

        # B. Predict
        candidates_df = get_candidates_by_name_blocking(nodes_df)
        # ... compute features ...
        probs = model.predict_proba(candidates_df[features])[:, 1]

        # C. Filter & Save
        predicted_edges = candidates_df[probs > cfg.lp_threshold]
        write_parquet(predicted_edges, ...)
```

## Downstream Integration

- **Temporal FCR**: The `fcr_temporal` calculation (separate plan) will ingest these `predicted_edges`.
- **Survival Analysis**: `exp_007` regressions will use `QuarterlyWindowDataLoader` to load the new `fcr_temporal` feature, ensuring consistency with existing valid-interval logic.

## Artifacts

1.  `rolling_windows/output/predicted_edges/`: Parquet files.
2.  `mlflow`: Tracks per-window model performance using standard metrics.
