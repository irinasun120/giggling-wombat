import pandas as pd
import pandera as pa
import pytest

from validation import eia_schema


def test_schema_rejects_negative_values():
    df = pd.DataFrame(
        {
            "week": pd.to_datetime(["2012-01-06"]),
            "value": [-5],
        }
    )

    with pytest.raises(pa.errors.SchemaError):
        eia_schema.validate(df)
