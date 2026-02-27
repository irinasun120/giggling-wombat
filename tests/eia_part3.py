from __future__ import annotations

import pandas as pd


def build_df_from_eia_data(
    data: list[dict],
    period_col: str = "period",
    value_col: str = "value",
    new_date_col: str = "week",
) -> pd.DataFrame:
    """
    Turn EIA 'response.data' (list of dicts) into a clean DataFrame:
    - parse period -> datetime
    - parse value -> numeric
    - drop rows with NaT/NaN
    """
    df = pd.DataFrame(data)
    if df.empty:
        return df

    df[new_date_col] = pd.to_datetime(df[period_col], errors="coerce")
    df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
    df = df.dropna(subset=[new_date_col, value_col]).copy()
    return df


def filter_since(df: pd.DataFrame, date_col: str, start_date: str) -> pd.DataFrame:
    """Filter rows where date_col >= start_date (YYYY-MM-DD)."""
    if df.empty:
        return df
    start = pd.to_datetime(start_date)
    return df[df[date_col] >= start].copy()


def latest_value(df: pd.DataFrame, date_col: str, value_col: str) -> float:
    """
    Return the value corresponding to the most recent date.
    Works regardless of whether df is sorted asc/desc.
    """
    if df.empty:
        raise ValueError("Empty DataFrame")
    idx = df[date_col].idxmax()
    return float(df.loc[idx, value_col])


def sum_by_week(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """
    Group by date_col and sum value_col.
    Returns DataFrame with columns: [date_col, value_col] sorted by date.
    """
    if df.empty:
        return df

    out = (
        df.groupby(date_col, as_index=False)[value_col]
        .sum()
        .sort_values(date_col)
        .reset_index(drop=True)
    )
    return out

def validate_required_columns(df: pd.DataFrame, required_cols: list[str]) -> None:
    """Raise ValueError if any required column is missing."""
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def add_week_ending_friday_column(
    df: pd.DataFrame,
    date_col: str = "week",
    new_col: str = "week_ending",
) -> pd.DataFrame:
    """
    Create a stable weekly key: week ending Friday (normalized midnight),
    based on an existing datetime column (date_col).
    """
    if df.empty:
        return df
    out = df.copy()
    out[new_col] = out[date_col].dt.to_period("W-FRI").dt.end_time.dt.normalize()
    return out


def coerce_numeric_and_dropna(
    df: pd.DataFrame,
    value_col: str = "value",
) -> pd.DataFrame:
    """Coerce value_col to numeric and drop rows where it becomes NaN."""
    if df.empty:
        return df
    out = df.copy()
    out[value_col] = pd.to_numeric(out[value_col], errors="coerce")
    out = out.dropna(subset=[value_col]).copy()
    return out
