"""
Entry point for the address parsing pipeline.

This script orchestrates the full workflow:
1. Loads configuration settings (file paths, columns, etc.)
2. Ingests input data (CSV or Excel)
3. Applies address parsing logic across the dataset
4. Writes the parsed output to disk
"""

import pandas as pd
from tqdm import tqdm
import config
from pathlib import Path

def load_data(file_path: Path) -> pd.DataFrame:
    if file_path.suffix == ".csv":
        return pd.read_csv(
            file_path,
            dtype=str,
            low_memory=False,
            keep_default_na=False
        )
    elif file_path.suffix == ".xlsx":
        return pd.read_excel(
            file_path,
            dtype=str,
            keep_default_na=False
        )
    else:
        raise ValueError("File must be .csv or .xlsx")
    
def parse_data(df: pd.DataFrame) -> pd.DataFrame:
    from parser import parse_row

    parsed_rows = df.progress_apply(parse_row, axis=1)
    parsed_df = pd.DataFrame(parsed_rows.tolist())

    return parsed_df


def main():
    file_path = Path(config.file_path)
    tqdm.pandas()

    df = load_data(file_path)

    parsed_df = parse_data(df)

    parsed_df.to_csv('test.csv', index=False)


if __name__ == "__main__":
    main()