"""
Core address parsing logic.

This module converts each row into an ordered list of parse fields and applies
structured parsing passes to extract address components.

Current version:
- builds ordered field objects from configured parse columns
- detects trailing geographic clusters across 1 to 3 adjacent fields
- detects a street candidate anchored to the left of the geo cluster
- returns parsed output using the configured parsed column names

Future versions can add:
- unit parsing
- fallback value support
- confidence scoring
- warnings / parse type metadata
"""

import re
import config
from patterns import (
    ZIP_RE,
    STATE_ONLY_RE,
    STATE_ZIP_RE,
    CITY_STATE_RE,
    CITY_STATE_ZIP_RE,
    PO_BOX_RE,
    STANDARD_STREET_RE,
    ROUTE_STREET_RE,
)


def normalize_text(value: str) -> str:
    """Normalize a field value for parsing while preserving useful structure."""
    if value is None:
        return ""

    text = str(value).strip().upper()
    text = re.sub(r"\s+", " ", text)
    return text


def empty_parsed_result() -> dict:
    """Return an empty parsed result using the configured output column names."""
    return {key: "" for key in config.parsed_columns.keys()}


def build_parse_fields(row, parse_columns: list[str]) -> list[dict]:
    """
    Build an ordered list of non-empty parse fields from a row.

    Each field object preserves:
    - original index in parse_columns
    - source column name
    - normalized text
    """
    fields = []

    for idx, col in enumerate(parse_columns):
        raw_value = row.get(col, "")
        text = normalize_text(raw_value)

        if text:
            fields.append(
                {
                    "idx": idx,
                    "column": col,
                    "text": text,
                }
            )

    return fields


def parse_geo_cluster(fields: list[dict]) -> dict:
    """
    Detect the strongest trailing geographic cluster from right to left.

    Supported shapes:
    - city | state | zip
    - city | state+zip
    - city+state | zip
    - city+state+zip
    - city | state
    - city+state

    Returns a dictionary containing parsed values and metadata.
    """
    if not fields:
        return {
            "PARSED_CITY": "",
            "PARSED_STATE": "",
            "PARSED_ZIP": "",
            "PARSED_COUNTRY": "",
            "field_indices": [],
            "parse_type": "",
            "confidence": 0.0,
        }

    n = len(fields)
    last = fields[-1]["text"]

    # --- 1 field: CITY STATE ZIP
    m = CITY_STATE_ZIP_RE.match(last)
    if m:
        return {
            "PARSED_CITY": m.group("city").strip(),
            "PARSED_STATE": m.group("state").strip(),
            "PARSED_ZIP": m.group("zip").strip(),
            "PARSED_COUNTRY": "",
            "field_indices": [fields[-1]["idx"]],
            "parse_type": "CITY_STATE_ZIP",
            "confidence": 0.98,
        }

    # --- 2 fields: CITY | STATE ZIP
    if n >= 2:
        second_last = fields[-2]["text"]
        m_right = STATE_ZIP_RE.match(last)

        if m_right and second_last:
            return {
                "PARSED_CITY": second_last.strip(),
                "PARSED_STATE": m_right.group("state").strip(),
                "PARSED_ZIP": m_right.group("zip").strip(),
                "PARSED_COUNTRY": "",
                "field_indices": [fields[-2]["idx"], fields[-1]["idx"]],
                "parse_type": "CITY__STATE_ZIP",
                "confidence": 0.97,
            }

    # --- 2 fields: CITY STATE | ZIP
    if n >= 2:
        second_last = fields[-2]["text"]
        m_left = CITY_STATE_RE.match(second_last)
        m_zip = ZIP_RE.fullmatch(last)

        if m_left and m_zip:
            return {
                "PARSED_CITY": m_left.group("city").strip(),
                "PARSED_STATE": m_left.group("state").strip(),
                "PARSED_ZIP": m_zip.group(0).strip(),
                "PARSED_COUNTRY": "",
                "field_indices": [fields[-2]["idx"], fields[-1]["idx"]],
                "parse_type": "CITY_STATE__ZIP",
                "confidence": 0.97,
            }

    # --- 3 fields: CITY | STATE | ZIP
    if n >= 3:
        city_text = fields[-3]["text"]
        state_text = fields[-2]["text"]
        zip_text = fields[-1]["text"]

        m_state = STATE_ONLY_RE.match(state_text)
        m_zip = ZIP_RE.fullmatch(zip_text)

        if city_text and m_state and m_zip:
            return {
                "PARSED_CITY": city_text.strip(),
                "PARSED_STATE": m_state.group("state").strip(),
                "PARSED_ZIP": m_zip.group(0).strip(),
                "PARSED_COUNTRY": "",
                "field_indices": [fields[-3]["idx"], fields[-2]["idx"], fields[-1]["idx"]],
                "parse_type": "CITY__STATE__ZIP",
                "confidence": 0.99,
            }

    # --- 1 field: CITY STATE
    m = CITY_STATE_RE.match(last)
    if m:
        return {
            "PARSED_CITY": m.group("city").strip(),
            "PARSED_STATE": m.group("state").strip(),
            "PARSED_ZIP": "",
            "PARSED_COUNTRY": "",
            "field_indices": [fields[-1]["idx"]],
            "parse_type": "CITY_STATE",
            "confidence": 0.90,
        }

    # --- 2 fields: CITY | STATE
    if n >= 2:
        second_last = fields[-2]["text"]
        m_state = STATE_ONLY_RE.match(last)

        if second_last and m_state:
            return {
                "PARSED_CITY": second_last.strip(),
                "PARSED_STATE": m_state.group("state").strip(),
                "PARSED_ZIP": "",
                "PARSED_COUNTRY": "",
                "field_indices": [fields[-2]["idx"], fields[-1]["idx"]],
                "parse_type": "CITY__STATE",
                "confidence": 0.88,
            }

    return {
        "PARSED_CITY": "",
        "PARSED_STATE": "",
        "PARSED_ZIP": "",
        "PARSED_COUNTRY": "",
        "field_indices": [],
        "parse_type": "",
        "confidence": 0.0,
    }


def extract_street_candidate(text: str) -> str:
    """
    Extract a strong street candidate from a field.

    Current version only supports strong patterns:
    - PO BOX
    - standard numbered streets with suffixes
    - route/highway/FM/CR style streets

    This intentionally avoids weaker fallback patterns for now.
    """
    if not text:
        return ""

    m = PO_BOX_RE.search(text)
    if m:
        return m.group(0).strip()

    m = ROUTE_STREET_RE.search(text)
    if m:
        return m.group(0).strip()

    m = STANDARD_STREET_RE.search(text)
    if m:
        return m.group(0).strip()

    return ""


def parse_street(fields: list[dict], geo: dict) -> dict:
    """
    Parse a street candidate anchored to the geographic cluster.

    Strategy:
    - if geo fields were found, look immediately left of the leftmost geo field
    - only accept strong street patterns for now

    Returns a dictionary with street value and metadata.
    """
    if not fields:
        return {
            "PARSED_STREET": "",
            "field_indices": [],
            "parse_type": "",
            "confidence": 0.0,
        }

    geo_field_indices = geo.get("field_indices", [])
    if not geo_field_indices:
        return {
            "PARSED_STREET": "",
            "field_indices": [],
            "parse_type": "",
            "confidence": 0.0,
        }

    leftmost_geo_idx = min(geo_field_indices)

    # Find the field object whose parse-column idx is immediately left of the geo cluster
    left_candidate = None
    for field in fields:
        if field["idx"] == leftmost_geo_idx - 1:
            left_candidate = field
            break

    if left_candidate is None:
        return {
            "PARSED_STREET": "",
            "field_indices": [],
            "parse_type": "",
            "confidence": 0.0,
        }

    street = extract_street_candidate(left_candidate["text"])
    if street:
        return {
            "PARSED_STREET": street,
            "field_indices": [left_candidate["idx"]],
            "parse_type": "LEFT_OF_GEO",
            "confidence": 0.95,
        }

    return {
        "PARSED_STREET": "",
        "field_indices": [],
        "parse_type": "",
        "confidence": 0.0,
    }


def parse_row(row) -> dict:
    """
    Parse a single row into structured address output.

    Current version:
    - parses the geographic cluster
    - parses a street candidate immediately left of that geo cluster
    """
    result = empty_parsed_result()
    fields = build_parse_fields(row, config.parse_columns)

    geo = parse_geo_cluster(fields)
    street = parse_street(fields, geo)

    result["PARSED_STREET"] = street["PARSED_STREET"]
    result["PARSED_CITY"] = geo["PARSED_CITY"]
    result["PARSED_STATE"] = geo["PARSED_STATE"]
    result["PARSED_ZIP"] = geo["PARSED_ZIP"]
    result["PARSED_COUNTRY"] = geo["PARSED_COUNTRY"]

    return result