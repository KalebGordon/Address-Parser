"""
Configuration module for the address parsing pipeline.

Contains all user-editable settings, including:
- Input/output file paths
- Column mappings (parse columns, passthrough columns)
- Optional fallback column definitions
- Feature flags or runtime options (if added later)
"""

# Full file path of the file you want to parse
file_path = r'data\TESTS\TEST_1.csv'

# The columns you want to parse (case sensitive).
parse_columns = [
    "ADDRESS_LINE_1",
    "ADDRESS_LINE_2",
    "ADDRESS_LINE_3",
    "ADDRESS_LINE_4",
    "ADDRESS_LINE_5",
]

# The parsed column names and their associated fallback columns. 
# (if you want to have the parser fallback to a different column when a value is not parsed, otherwise leave blank)
parsed_columns = {
    'PARSED_STREET': '',
    'PARSED_CITY': '',
    'PARSED_STATE': '',
    'PARSED_ZIP': '',
    'PARSED_COUNTRY': ''
}

# The columns you want to remain in the output dataset that are present in the input dataset
passthrough_columns = []

