import re
import pandas as pd

# Matches lines like: 12/06/23, 9:45 am - Author: message
_PATTERN = re.compile(
    r"^(\d{1,2}/\d{1,2}/\d{2,4}),\s*(\d{1,2}:\d{2}(?:\s?[aApP][mM])?)\s*-\s*([^:]+):\s*(.*)$"
)

_SYSTEM_SUBSTRINGS = [
    "messages and calls are end-to-end encrypted",
    "changed the subject",
    "added",
    "removed",
    "left",
    "created group",
    "changed this group",
    "changed the group",
    "security code changed",
    "you're now an admin",
]


def _is_system_message(author: str, message: str) -> bool:
    combined = (author + " " + message).lower()
    return any(s in combined for s in _SYSTEM_SUBSTRINGS)


def parse_chat(file_bytes: bytes) -> pd.DataFrame:
    """
    Parse raw WhatsApp export bytes into a DataFrame.

    Returns columns: date, time, author, message, datetime,
                     year, month, day, hour, weekday, year_month
    """
    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")

    lines = text.splitlines()
    rows = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = _PATTERN.match(line)
        if match:
            date, time_str, author, message = match.groups()
            author = author.strip()
            # WhatsApp sometimes labels the exporter's messages as "~" alone
            if author == "~" or author == "":
                author = "You"
            elif author.startswith("~ "):
                # Group chat format: "~ Contact Name"
                author = author[2:].strip()
            message = message.strip()

            if not author:
                continue
            if message.lower() == "<media omitted>":
                continue
            if _is_system_message(author, message):
                continue

            rows.append([date, time_str, author, message])
        else:
            # Continuation line — append to previous message
            if rows:
                rows[-1][3] += "\n" + line

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["date", "time", "author", "message"])

    # Parse datetime — try 12h then 24h format
    df["datetime"] = _parse_datetime(df["date"] + " " + df["time"])

    df = df.dropna(subset=["datetime"]).copy()
    df = df.sort_values("datetime").reset_index(drop=True)

    df["year"] = df["datetime"].dt.year
    df["month"] = df["datetime"].dt.month
    df["day"] = df["datetime"].dt.day
    df["hour"] = df["datetime"].dt.hour
    df["weekday"] = df["datetime"].dt.day_name()
    df["year_month"] = df["datetime"].dt.to_period("M").astype(str)

    return df


def _parse_datetime(series: pd.Series) -> pd.Series:
    formats = [
        "%d/%m/%y %I:%M %p",
        "%d/%m/%y %I:%M%p",
        "%d/%m/%Y %I:%M %p",
        "%d/%m/%Y %I:%M%p",
        "%m/%d/%y %I:%M %p",
        "%m/%d/%y %I:%M%p",
        "%d/%m/%y %H:%M",
        "%d/%m/%Y %H:%M",
        "%m/%d/%y %H:%M",
    ]
    for fmt in formats:
        try:
            parsed = pd.to_datetime(series, format=fmt)
            if parsed.notna().sum() > len(series) * 0.8:
                return parsed
        except Exception:
            continue
    # Last resort: let pandas infer
    return pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
