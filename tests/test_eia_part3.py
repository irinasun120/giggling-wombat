import pandas as pd
import pytest

from tests.eia_part3 import (
    build_df_from_eia_data,
    filter_since,
    latest_value,
    sum_by_week,
)


def test_build_df_from_eia_data_parses_and_drops_bad_rows():
    # includes: valid row, invalid date, invalid value
    data = [
        {"period": "2012-01-06", "value": "100"},
        {"period": "not-a-date", "value": "200"},
        {"period": "2012-01-13", "value": "not-a-number"},
    ]
    df = build_df_from_eia_data(data)

    # only the first row should survive
    assert len(df) == 1
    assert pd.api.types.is_datetime64_any_dtype(df["week"])
    assert pd.api.types.is_numeric_dtype(df["value"])
    assert df["week"].iloc[0] == pd.to_datetime("2012-01-06")
    assert df["value"].iloc[0] == 100


def test_filter_since_keeps_2012_and_after():
    data = [
        {"period": "2011-12-30", "value": "1"},
        {"period": "2012-01-06", "value": "2"},
    ]
    df = build_df_from_eia_data(data)
    df2 = filter_since(df, date_col="week", start_date="2012-01-01")

    assert len(df2) == 1
    assert df2["week"].iloc[0] == pd.to_datetime("2012-01-06")
    assert df2["value"].iloc[0] == 2


def test_latest_value_returns_value_of_most_recent_date_even_if_unsorted():
    # intentionally unsorted
    data = [
        {"period": "2012-01-13", "value": "300"},
        {"period": "2012-01-06", "value": "100"},
        {"period": "2012-01-20", "value": "500"},
    ]
    df = build_df_from_eia_data(data)
    v = latest_value(df, date_col="week", value_col="value")

    assert v == 500.0


def test_latest_value_raises_on_empty_df():
    with pytest.raises(ValueError):
        latest_value(pd.DataFrame(), date_col="week", value_col="value")


def test_sum_by_week_sums_duplicates():
    data = [
        {"period": "2012-01-06", "value": "10"},
        {"period": "2012-01-06", "value": "7"},
        {"period": "2012-01-13", "value": "3"},
    ]
    df = build_df_from_eia_data(data)
    out = sum_by_week(df, date_col="week", value_col="value")

    assert list(out.columns) == ["week", "value"]
    assert len(out) == 2
    assert out.loc[out["week"] == pd.to_datetime("2012-01-06"), "value"].iloc[0] == 17
    assert out.loc[out["week"] == pd.to_datetime("2012-01-13"), "value"].iloc[0] == 3