# Address Parser

A Python-based address parsing pipeline designed to extract structured address components from messy, unordered, multi-column address data.

This project was built to handle real-world address datasets where address components may appear across several fields, in inconsistent order, with incomplete or partially merged values. The parser converts unstructured address columns into standardized output fields such as street, city, state, ZIP, and country.

## Overview

Many enterprise datasets store address information across multiple free-text fields rather than in clean, standardized columns. In practice, the street address, city, state, ZIP code, unit number, PO Box, or route information may appear in different columns depending on the source system, vendor, customer record, or historical data process.

This parser addresses that problem by scanning a configurable set of address fields, identifying likely geographic and street components, ranking candidate matches, and returning structured parsed output.

## Key Features

* Parses any number of configured address columns
* Supports CSV and Excel input files
* Extracts structured street, city, state, ZIP, and country fields
* Handles unordered and inconsistently populated address fields
* Detects trailing geographic clusters such as:

  * `CITY | STATE | ZIP`
  * `CITY | STATE ZIP`
  * `CITY STATE | ZIP`
  * `CITY STATE ZIP`
  * `CITY | STATE`
* Detects street candidates using regex-based pattern matching
* Supports standard street addresses, PO Boxes, highways, county roads, routes, and unit designators
* Appends standalone unit fields when they are positioned next to a street candidate
* Uses parsing metadata internally, including parse type and confidence values
* Designed for dataframe-scale processing using pandas

## Technical Stack

* Python
* pandas
* regular expressions
* tqdm
* openpyxl

## Parsing Approach

The parser uses a multi-pass strategy instead of assuming addresses are already clean or consistently ordered.

### 1. Field Normalization

Each configured input column is normalized by trimming whitespace, uppercasing text, and standardizing spacing. Empty values are ignored so the parser can focus only on meaningful address fragments.

### 2. Ordered Field Objects

Each non-empty field is converted into an ordered field object containing:

* Original column index
* Source column name
* Normalized text value

This allows the parser to reason about both the content of each field and its position relative to other fields.

### 3. Geographic Cluster Detection

The parser first looks for strong city/state/ZIP patterns, especially near the right side of the address fields where geographic components commonly appear.

Supported geographic patterns include:

* Single-field: `CITY STATE ZIP`
* Two-field: `CITY | STATE ZIP`
* Two-field: `CITY STATE | ZIP`
* Three-field: `CITY | STATE | ZIP`
* Single-field: `CITY STATE`
* Two-field: `CITY | STATE`

Each detected pattern is assigned metadata such as parse type, source field indices, and confidence.

### 4. Street Candidate Ranking

After identifying a geographic cluster, the parser searches for the strongest street candidate.

The preferred candidate is the field immediately to the left of the geographic cluster. This reflects a common address layout:

`STREET | CITY | STATE | ZIP`

If no street is found there, the parser scans remaining non-geographic fields from right to left and selects the strongest street-like value.

This helps support records where non-address fields, names, business names, or secondary values appear before the actual street address.

### 5. Street Pattern Matching

Street extraction supports multiple address types, including:

* Standard numbered street addresses
* PO Boxes
* Highway and route-based addresses
* County roads
* Farm roads
* Unit, suite, apartment, building, room, floor, and trailer designators

Pattern definitions are separated from parsing logic to keep the system easier to maintain and extend.

### 6. Geo Left-of-Street Recovery

If a trailing geographic cluster is not found, the parser attempts to identify geographic fields immediately to the left of the selected street field.

This supports records where the source data is ordered differently, such as:

`CITY STATE ZIP | STREET`

or:

`CITY | STATE | ZIP | STREET`

### 7. Unit Handling

If a standalone unit field appears immediately next to the selected street field, the parser appends it to the parsed street address.

Example:

`APT 12 | 123 MAIN ST`

becomes:

`123 MAIN ST APT 12`

## Example Output

Input columns:

| ADDRESS_LINE_1 | ADDRESS_LINE_2 | ADDRESS_LINE_3 | ADDRESS_LINE_4 |
| -------------- | -------------- | -------------- | -------------- |
| JOHN SMITH     | 123 MAIN ST    | COLUMBUS       | OH 43215       |

Parsed output:

| PARSED_STREET | PARSED_CITY | PARSED_STATE | PARSED_ZIP | PARSED_COUNTRY |
| ------------- | ----------- | ------------ | ---------- | -------------- |
| 123 MAIN ST   | COLUMBUS    | OH           | 43215      |                |

## Why This Project Matters

This project demonstrates how messy operational data can be transformed into structured, usable information through deterministic parsing, pattern recognition, field ranking, and scalable dataframe processing.

The parser is especially useful in environments where address quality affects downstream workflows such as customer communication, mailing accuracy, deduplication, record matching, regulatory reporting, or data integration.

## Repository Structure

```text
Address-Parser/
├── main.py          # Pipeline entry point
├── parser.py        # Core parsing logic
├── patterns.py      # Regex patterns and parsing constants
├── config.py        # User-editable configuration
├── requirements.txt # Python dependencies
└── data/            # Sample input/output data
```

## How to Use

1. Clone the repository.

```bash
git clone https://github.com/KalebGordon/Address-Parser.git
cd Address-Parser
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Update the configuration file.

Set the input file path and address columns in `config.py`.

```python
file_path = r"data/TESTS/TEST_1.csv"

parse_columns = [
    "ADDRESS_LINE_1",
    "ADDRESS_LINE_2",
    "ADDRESS_LINE_3",
    "ADDRESS_LINE_4",
    "ADDRESS_LINE_5",
]
```

4. Run the parser.

```bash
python main.py
```

The output file will be written to the same directory as the input file with the prefix `PARSED_`.

## Current Limitations

* Primarily designed for U.S. address formats
* Uses deterministic regex and positional logic rather than a probabilistic parsing model
* Country parsing is not yet fully implemented
* Confidence scores are currently used internally and are not included in the default output
* Future versions could add candidate scoring, warnings, fallback columns, and parse explainability metadata

## Future Enhancements

* Add candidate bucketing and ranking output
* Add parse confidence columns to final output
* Add warning flags for ambiguous records
* Add support for fallback columns
* Add batch validation reports
* Add unit tests for common address layouts
* Add optional integration with address standardization APIs
* Add CASS/NCOA-ready preprocessing support

## What This Project Demonstrates

* Analytics engineering
* Data cleaning and standardization
* Python pipeline development
* Regex-based parsing
* Dataframe-scale processing
* Address quality workflows
* Data validation and transformation
* Real-world messy data handling
