"""
Regex patterns and parsing constants used throughout the address parser.

Includes:
- State code definitions
- ZIP code patterns
- Street and route detection patterns
- Unit and building designators
- Special-case patterns (PO Box, trust/legal keywords, etc.)

This file isolates pattern definitions from parsing logic to improve
readability, maintainability, and ease of updates.
"""

import re

STATE_CODES = (
    "AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|"
    "MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|"
    "WA|WV|WI|WY"
)

ZIP_RE = re.compile(r"\b\d{5}(?:-\d{4})?\b")

STATE_ONLY_RE = re.compile(
    rf"^\s*(?P<state>{STATE_CODES})\s*$"
)

STATE_ZIP_RE = re.compile(
    rf"^\s*(?P<state>{STATE_CODES})\s+(?P<zip>\d{{5}}(?:-\d{{4}})?)\s*$"
)

CITY_STATE_RE = re.compile(
    rf"^\s*(?P<city>[A-Z][A-Z\s.\-']+?)\s+(?P<state>{STATE_CODES})\s*$"
)

CITY_STATE_ZIP_RE = re.compile(
    rf"^\s*(?P<city>[A-Z][A-Z\s.\-']+?)\s+(?P<state>{STATE_CODES})\s+(?P<zip>\d{{5}}(?:-\d{{4}})?)\s*$"
)

PO_BOX_RE = re.compile(
    r"\b(?:P\s*\.?\s*O\s*\.?\s*|POST\s+OFFICE\s+)?BOX\s+[A-Z0-9\-]+\b"
)

DIRECTIONALS = r"(?:N|S|E|W|NE|NW|SE|SW|NORTH|SOUTH|EAST|WEST)"
UNIT_DESIGNATORS = (
    r"APT|APARTMENT|STE|SUITE|UNIT|FL|FLOOR|RM|ROOM|BLDG|BUILDING|"
    r"DEPT|LOT|TRLR|TRAILER|BSMT|BASEMENT|UPPR|UPPER|LOWER|HNGR|HANGAR|"
    r"SPC|SPACE|SLIP"
)
STREET_SUFFIXES = (
    r"ST(?:REET)?|AVE(?:NUE)?|RD|ROAD|DR(?:IVE)?|LN|LANE|BLVD|BOULEVARD|"
    r"CIR(?:CLE)?|CT|COURT|CV|COVE|TRL|TRAIL|WAY|PL|PLACE|TER|TERRACE|"
    r"PKWY|PARKWAY|PIKE|PATH|LOOP|POINTE|HWY|HIGHWAY|FWY|FREEWAY|"
    r"EXPY|EXPRESSWAY|TOLLWAY|RDG"
)

STANDARD_STREET_RE = re.compile(
    rf"""
    \b
    \d+[A-Z\-]*
    \s+
    (?:{DIRECTIONALS}\s+)?
    [A-Z0-9#&/\-'\.\s]+?
    \s+
    (?:{STREET_SUFFIXES})
    (?:\s+(?:{DIRECTIONALS}))?
    (?:\s+(?:{UNIT_DESIGNATORS})\s*[A-Z0-9\-#]+)?
    \b
    """,
    re.VERBOSE,
)

ROUTE_STREET_RE = re.compile(
    rf"""
    \b
    \d+[A-Z\-]*
    \s+
    (?:(?:{DIRECTIONALS})\s+)?
    (?:
        FM|RM|RR|
        INTERSTATE|I|
        US\s+HIGHWAY|U\.?S\.?\s+HIGHWAY|
        STATE\s+HIGHWAY|
        HIGHWAY|HWY|
        COUNTY\s+ROAD|CR
    )
    \s+
    \d+[A-Z\-]*
    (?:\s+(?:{DIRECTIONALS}))?
    (?:\s+(?:{UNIT_DESIGNATORS})\s*[A-Z0-9\-#]+)?
    \b
    """,
    re.VERBOSE,
)