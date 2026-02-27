import pandera as pa
from pandera import Check, Column, DataFrameSchema

eia_schema = DataFrameSchema(
    {
        "week": Column(pa.DateTime),
        "value": Column(
            pa.Float,
            coerce=True,
            checks=Check.ge(0),
            nullable=False,
        ),
    }
)
