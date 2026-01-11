from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def coerce_float_list_column(df: pd.DataFrame, *, column: str) -> pd.DataFrame:
    if column not in df.columns:
        return df
    df[column] = df[column].apply(lambda v: None if v is None else [float(x) for x in v])
    return df


def expand_embedding_column(df: pd.DataFrame, *, column: str, dim: int, prefix: str = "emb_") -> pd.DataFrame:
    if column not in df.columns:
        return df

    values = df[column].tolist()
    if not values:
        return df.drop(columns=[column])

    if any(v is None for v in values):
        raise ValueError(f"Embedding column '{column}' contains nulls; cannot expand reliably")

    emb = np.vstack(values)
    if emb.ndim != 2 or emb.shape[1] != dim:
        raise ValueError(f"Expected embedding dim={dim} for '{column}', got shape={emb.shape}")

    emb_df = pd.DataFrame(emb, columns=[f"{prefix}{i}" for i in range(dim)], index=df.index)
    return pd.concat([df.drop(columns=[column]), emb_df], axis=1)


def slice_vector_column(
    df: pd.DataFrame,
    *,
    column: str,
    indices: list[int],
    out_column: str,
    expected_dim: int | None = None,
) -> pd.DataFrame:
    if column not in df.columns:
        return df

    values = df[column].tolist()
    if not values:
        df[out_column] = []
        return df

    if any(v is None for v in values):
        raise ValueError(f"Vector column '{column}' contains nulls; cannot slice reliably")

    mat = np.vstack(values)
    if mat.ndim != 2:
        raise ValueError(f"Expected '{column}' to be 2D after stacking, got shape={mat.shape}")
    if expected_dim is not None and mat.shape[1] != expected_dim:
        raise ValueError(f"Expected dim={expected_dim} for '{column}', got shape={mat.shape}")

    sliced = mat[:, indices]
    df[out_column] = [list(map(float, row)) for row in sliced]
    return df


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
