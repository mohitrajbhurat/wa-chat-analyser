import re
import emoji
import numpy as np
import pandas as pd
from collections import Counter, defaultdict

# ── Stop words to exclude from word frequency ──────────────────────────────
_STOP_WORDS = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "is", "it", "this", "that", "was", "are", "be", "been",
    "have", "has", "had", "do", "did", "will", "would", "could", "should",
    "i", "you", "he", "she", "we", "they", "my", "your", "his", "her",
    "our", "their", "me", "him", "us", "them", "so", "if", "as", "up",
    "out", "no", "not", "what", "all", "just", "by", "from", "about",
    "can", "when", "there", "which", "also", "into", "its", "than", "then",
    "like", "ok", "okay", "yeah", "yes", "lol", "omitted", "media",
    "deleted", "message", "null", "yea", "haha", "hahaha", "na", "nah",
}

_URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
_WORD_PATTERN = re.compile(r"\b[a-zA-Z]{2,}\b")

_FAREWELL_WORDS = {
    "bye", "goodbye", "good bye", "goodnight", "good night",
    "good morning", "gm", "gn", "ttyl", "see you", "see ya",
    "cya", "later", "take care", "night", "nite", "morning",
    "brb", "gtg", "got to go", "gotta go", "sleep", "sleeping",
    "tc", "ok bye", "okay bye", "alright bye", "talk later",
    "talk soon", "chat later", "speak later", "going to sleep",
    "going to bed", "heading to bed", "going offline",
}


def _is_farewell(message: str) -> bool:
    msg = message.lower().strip()
    return any(word in msg for word in _FAREWELL_WORDS)


# ── Basic counts ────────────────────────────────────────────────────────────

def message_counts(df: pd.DataFrame) -> pd.Series:
    return df["author"].value_counts()


def word_counts(df: pd.DataFrame) -> pd.Series:
    df = df.copy()
    df["word_count"] = df["message"].apply(lambda x: len(_WORD_PATTERN.findall(x)))
    return df.groupby("author")["word_count"].sum().sort_values(ascending=False)


def avg_message_length(df: pd.DataFrame) -> pd.Series:
    df = df.copy()
    df["word_count"] = df["message"].apply(lambda x: len(_WORD_PATTERN.findall(x)))
    return df.groupby("author")["word_count"].mean().round(1).sort_values(ascending=False)


def active_days_per_month(df: pd.DataFrame) -> pd.DataFrame:
    result = df.groupby("year_month")["day"].nunique().reset_index()
    result.columns = ["year_month", "active_days"]
    result["year"] = result["year_month"].str[:4]
    return result


def messages_by_hour(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["hour"].value_counts().sort_index().reset_index()
    counts.columns = ["hour", "message_count"]
    # Fill missing hours with 0
    all_hours = pd.DataFrame({"hour": range(24)})
    counts = all_hours.merge(counts, on="hour", how="left").fillna(0)
    counts["message_count"] = counts["message_count"].astype(int)
    return counts


def monthly_volume(df: pd.DataFrame) -> pd.DataFrame:
    counts = df.groupby(["year", "month"]).size().reset_index(name="message_count")
    return counts.sort_values(["year", "month"])


def monthly_by_author(df: pd.DataFrame) -> pd.DataFrame:
    counts = df.groupby(["author", "year_month"]).size().reset_index(name="message_count")
    counts["year_month"] = pd.to_datetime(counts["year_month"])
    return counts.sort_values("year_month")


# ── Response analysis ───────────────────────────────────────────────────────

def _turns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse consecutive messages from the same author into one 'turn'.
    Returns a DataFrame with one row per turn: author, first_time, last_time.
    """
    df = df.sort_values("datetime").reset_index(drop=True)
    df["turn"] = (df["author"] != df["author"].shift()).cumsum()
    turns = df.groupby("turn", sort=False).agg(
        author=("author", "first"),
        first_time=("datetime", "min"),
        last_time=("datetime", "max"),
    ).reset_index(drop=True)
    return turns


def reply_matrix(df: pd.DataFrame, window_hours: int = 2) -> pd.DataFrame:
    """Counts who replies to whom within `window_hours`."""
    turns = _turns(df)
    turns["next_author"] = turns["author"].shift(-1)
    turns["next_time"] = turns["first_time"].shift(-1)
    turns["gap"] = turns["next_time"] - turns["last_time"]

    valid = turns[
        turns["gap"].notna() &
        (turns["gap"] <= pd.Timedelta(hours=window_hours))
    ]

    counts = valid.groupby(["author", "next_author"]).size()
    authors = sorted(df["author"].unique())
    result = pd.DataFrame(0, index=authors, columns=authors, dtype=float)
    for (sender, responder), n in counts.items():
        if sender in result.index and responder in result.columns:
            result.loc[sender, responder] = n

    normalized = result.div(result.sum(axis=1), axis=0).fillna(0)
    return normalized


def avg_response_time(df: pd.DataFrame, window_hours: int = 12) -> pd.DataFrame:
    """Average first-reply time in minutes between each pair."""
    turns = _turns(df)
    turns["next_author"] = turns["author"].shift(-1)
    turns["next_time"] = turns["first_time"].shift(-1)
    turns["gap"] = turns["next_time"] - turns["last_time"]

    valid = turns[
        turns["gap"].notna() &
        (turns["gap"] <= pd.Timedelta(hours=window_hours))
    ].copy()
    valid["gap_min"] = valid["gap"].dt.total_seconds() / 60

    authors = sorted(df["author"].unique())
    result = pd.DataFrame(index=authors, columns=authors, dtype=float)
    for (sender, responder), group in valid.groupby(["author", "next_author"]):
        if sender in result.index and responder in result.columns:
            result.loc[sender, responder] = round(group["gap_min"].mean(), 1)
    return result


# ── Word & emoji analysis ───────────────────────────────────────────────────

def top_words(df: pd.DataFrame, n: int = 15) -> dict[str, pd.DataFrame]:
    """Returns {author: DataFrame(word, count)} for each author."""
    result = {}
    for author, group in df.groupby("author"):
        all_words = []
        for msg in group["message"]:
            words = _WORD_PATTERN.findall(msg.lower())
            all_words.extend(w for w in words if w not in _STOP_WORDS)
        counts = Counter(all_words).most_common(n)
        result[author] = pd.DataFrame(counts, columns=["word", "count"])
    return result


def emoji_analysis(df: pd.DataFrame, n: int = 10) -> dict[str, pd.DataFrame]:
    """Returns {author: DataFrame(emoji, count)} for each author."""
    result = {}
    for author, group in df.groupby("author"):
        all_emojis = []
        for msg in group["message"]:
            all_emojis.extend(c for c in msg if c in emoji.EMOJI_DATA)
        counts = Counter(all_emojis).most_common(n)
        result[author] = pd.DataFrame(counts, columns=["emoji", "count"])
    return result


# ── Conversation behaviour ──────────────────────────────────────────────────

def conversation_starters(df: pd.DataFrame, gap_hours: int = 4) -> pd.Series:
    """Who sends the first message after a gap of `gap_hours` hours."""
    df = df.sort_values("datetime").reset_index(drop=True)
    starters = []
    starters.append(df.loc[0, "author"])  # First message ever counts
    for i in range(1, len(df)):
        gap = df.loc[i, "datetime"] - df.loc[i - 1, "datetime"]
        if gap > pd.Timedelta(hours=gap_hours):
            starters.append(df.loc[i, "author"])
    return pd.Series(starters).value_counts()


def ghosting_index(df: pd.DataFrame, ghost_hours: int = 24) -> pd.Series:
    """
    Turns with no reply within `ghost_hours` hours, excluding farewell turns.
    A turn = a consecutive run of messages from the same person.
    """
    df = df.sort_values("datetime").reset_index(drop=True).copy()
    df["turn"] = (df["author"] != df["author"].shift()).cumsum()

    last_msg = df.groupby("turn")["message"].last()
    turns = df.groupby("turn", sort=False).agg(
        author=("author", "first"),
        last_time=("datetime", "max"),
    ).reset_index(drop=True)
    turns["last_message"] = last_msg.values
    turns["next_time"] = turns["last_time"].shift(-1)
    turns["gap"] = turns["next_time"] - turns["last_time"]

    unanswered = turns[
        (turns["gap"].isna() | (turns["gap"] > pd.Timedelta(hours=ghost_hours))) &
        (~turns["last_message"].apply(_is_farewell))
    ]
    return unanswered.groupby("author").size().sort_values(ascending=False)


def longest_streak(df: pd.DataFrame) -> dict:
    """Returns the longest consecutive-day streak and who was active."""
    dates = pd.to_datetime(df["datetime"].dt.date.unique())
    dates = sorted(dates)
    max_streak = 1
    current_streak = 1
    max_end = dates[0]

    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            current_streak += 1
            if current_streak > max_streak:
                max_streak = current_streak
                max_end = dates[i]
        else:
            current_streak = 1

    max_start = max_end - pd.Timedelta(days=max_streak - 1)
    return {"streak_days": max_streak, "start": str(max_start.date()), "end": str(max_end.date())}


def weekend_vs_weekday(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["is_weekend"] = df["weekday"].isin(["Saturday", "Sunday"])
    result = df.groupby(["author", "is_weekend"]).size().reset_index(name="count")
    result["day_type"] = result["is_weekend"].map({True: "Weekend", False: "Weekday"})
    return result[["author", "day_type", "count"]]


def night_owl_score(df: pd.DataFrame) -> pd.DataFrame:
    """% of messages sent between 10pm–5am (night) vs 6am–10am (morning)."""
    rows = []
    for author, group in df.groupby("author"):
        total = len(group)
        night = ((group["hour"] >= 22) | (group["hour"] < 5)).sum()
        morning = ((group["hour"] >= 6) & (group["hour"] < 10)).sum()
        rows.append({
            "author": author,
            "night_pct": round(night / total * 100, 1),
            "morning_pct": round(morning / total * 100, 1),
        })
    return pd.DataFrame(rows)


def link_sharing(df: pd.DataFrame) -> pd.Series:
    """Count of URLs shared per author."""
    df = df.copy()
    df["has_link"] = df["message"].str.contains(_URL_PATTERN, regex=True)
    return df[df["has_link"]].groupby("author").size().sort_values(ascending=False)


def most_active_day(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date_only"] = df["datetime"].dt.date
    daily = df.groupby("date_only").size().reset_index(name="count")
    return daily.sort_values("count", ascending=False).head(10).reset_index(drop=True)


def summary_stats(df: pd.DataFrame) -> dict:
    """Top-level numbers shown on the dashboard header."""
    first = df["datetime"].min()
    last = df["datetime"].max()
    total_days = (last - first).days + 1
    active_days = df["datetime"].dt.date.nunique()

    return {
        "total_messages": len(df),
        "total_authors": df["author"].nunique(),
        "date_from": first.strftime("%d %b %Y"),
        "date_to": last.strftime("%d %b %Y"),
        "total_days": total_days,
        "active_days": active_days,
        "activity_rate": f"{round(active_days / total_days * 100, 1)}%",
    }
