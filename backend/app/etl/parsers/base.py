from abc import ABC, abstractmethod
from typing import Any
import pandas as pd
from pathlib import Path


class BaseParser(ABC):
    """
    Base class for all source-specific Excel/CSV parsers.
    Subclasses implement column_map and transform_row().
    """

    source_type: str = "other"

    # Override in subclass: maps canonical field → list of possible source column names
    column_map: dict[str, list[str]] = {}

    def get_sheet_preview(self, file_path: str | Path) -> dict:
        """Return sheet names and sample columns without full parse."""
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, nrows=5)
            return {
                "sheets": ["Sheet1"],
                "default_sheet": "Sheet1",
                "columns": list(df.columns),
                "sample_rows": df.head(3).fillna("").to_dict(orient="records"),
            }
        xl = pd.ExcelFile(path)
        sheet = xl.sheet_names[0]
        df = xl.parse(sheet, nrows=5)
        return {
            "sheets": xl.sheet_names,
            "default_sheet": sheet,
            "columns": list(df.columns),
            "sample_rows": df.head(3).fillna("").to_dict(orient="records"),
        }

    def load_dataframe(self, file_path: str | Path, sheet_name: str | None = None, mapping_config: dict | None = None) -> pd.DataFrame:
        path = Path(file_path)
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path, dtype=str)
        else:
            df = pd.read_excel(path, sheet_name=sheet_name or 0, dtype=str)
        df = df.where(pd.notna(df), None)
        return df

    def resolve_column(self, df: pd.DataFrame, canonical_field: str, mapping_config: dict | None) -> str | None:
        """Find the actual DataFrame column for a canonical field."""
        # User-supplied mapping takes priority
        if mapping_config and canonical_field in mapping_config:
            col = mapping_config[canonical_field]
            if col in df.columns:
                return col
        # Fall back to class-level auto-detect
        candidates = self.column_map.get(canonical_field, [])
        for c in candidates:
            for col in df.columns:
                if col.strip().lower() == c.lower():
                    return col
        return None

    def extract_field(self, row: pd.Series, canonical_field: str, df: pd.DataFrame, mapping_config: dict | None) -> Any:
        col = self.resolve_column(df, canonical_field, mapping_config)
        if col and col in row.index:
            val = row[col]
            return None if pd.isna(val) or val == "" else val
        return None

    def parse(self, file_path: str | Path, sheet_name: str | None = None, mapping_config: dict | None = None) -> list[dict]:
        """
        Parse file and return list of normalized row dicts.
        Each dict has raw_data (original row) and extracted canonical fields.
        """
        df = self.load_dataframe(file_path, sheet_name, mapping_config)
        results = []
        for idx, row in df.iterrows():
            try:
                record = self.transform_row(row, df, mapping_config, int(idx))
                if record:
                    results.append(record)
            except Exception as e:
                results.append({
                    "row_index": int(idx),
                    "error": str(e),
                    "raw_data": row.to_dict(),
                })
        return results

    @abstractmethod
    def transform_row(self, row: pd.Series, df: pd.DataFrame, mapping_config: dict | None, row_index: int) -> dict | None:
        """Transform a single row into a normalized record dict."""
        ...
