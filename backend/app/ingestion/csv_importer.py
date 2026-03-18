import re
import pandas as pd
from pathlib import Path
from app.core.logger import logger

PG_TYPE_MAP = {
    "int64": "INTEGER",
    "float64": "DOUBLE PRECISION",
    "bool": "BOOLEAN",
    "datetime64[ns]": "TIMESTAMP",
    "object": "TEXT",
}


def infer_schema_from_csv(file_path: str | Path) -> dict:
    """Read CSV and infer PostgreSQL column types."""
    df = pd.read_csv(str(file_path), nrows=1000)
    columns = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        pg_type = PG_TYPE_MAP.get(dtype, "TEXT")
        safe_name = re.sub(r"[^a-z0-9_]", "_", col.lower().strip())
        columns.append({
            "name": safe_name,
            "original_name": col,
            "type": pg_type,
            "nullable": bool(df[col].isna().any()),
            "sample_values": [str(v) for v in df[col].dropna().head(3).tolist()],
        })
    return {
        "columns": columns,
        "row_count": len(pd.read_csv(str(file_path))),
        "preview": df.head(10).fillna("").to_dict(orient="records"),
    }
