import csv
import os
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable, Optional

from .rating import fuzzy_rating
from .sources import TrendsSource, TwitterSource


def csv_path(data_dir: str, name: str) -> Path:
    return Path(data_dir) / f"{name}.csv"


def read_rows(path: Path) -> Optional[list[list[str]]]:
    try:
        with path.open(newline="", encoding="utf-8") as fh:
            return [row for row in csv.reader(fh) if row]
    except FileNotFoundError:
        return None


def write_rows_atomic(path: Path, rows: Iterable[list]) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.stem}-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def drug_key(name: str) -> str:
    parts = name.split()
    return parts[0].lower() if parts else ""


@dataclass
class Ranker:
    twitter: TwitterSource
    trends: TrendsSource
    google_source: str = "twitter"

    def _google_input(self, term: str, today: date) -> Optional[float]:
        if self.google_source == "trends":
            return self.trends.interest(term, today)
        return self.twitter.count(term, today - timedelta(days=1))

    def rank(self, drugs: list[tuple[str, str]], today: date) -> list[list]:
        seen: set[str] = set()
        scored = []
        for name, price in drugs:
            key = drug_key(name)
            if not key or key in seen:
                continue
            term = name.split()[0]
            tw = self.twitter.count(term, today - timedelta(days=3))
            if tw is not None and tw <= 0:
                continue
            seen.add(key)
            tw2 = self.twitter.count(term, today - timedelta(days=2))
            google = self._google_input(term, today)
            rating = fuzzy_rating(google or 0, tw or 0, tw2 or 0)
            scored.append((name, price, rating))
        scored.sort(key=lambda row: row[2], reverse=True)
        return [[i, name, price, rating] for i, (name, price, rating) in enumerate(scored)]
