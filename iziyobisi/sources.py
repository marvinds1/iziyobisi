import logging
import threading
import time
from datetime import date, timedelta
from typing import Callable, Optional

log = logging.getLogger(__name__)

_MISS = object()


class TTLCache:
    def __init__(self, clock: Callable[[], float] = time.monotonic):
        self._data: dict = {}
        self._lock = threading.Lock()
        self._clock = clock

    def get(self, key):
        with self._lock:
            entry = self._data.get(key)
            if entry is None:
                return _MISS
            value, expires = entry
            if expires <= self._clock():
                del self._data[key]
                return _MISS
            return value

    def set(self, key, value, ttl: float) -> None:
        with self._lock:
            self._data[key] = (value, self._clock() + ttl)


class _CachedSource:
    name = "source"

    def __init__(self, timeout: float, ttl: float, failure_ttl: float, cache: Optional[TTLCache] = None):
        self.timeout = timeout
        self.ttl = ttl
        self.failure_ttl = failure_ttl
        self.cache = cache or TTLCache()

    def _cached(self, key, fetch):
        hit = self.cache.get(key)
        if hit is not _MISS:
            return hit
        try:
            value = fetch()
        except Exception as exc:
            log.warning("%s unavailable for %r: %s", self.name, key, type(exc).__name__)
            self.cache.set(key, None, self.failure_ttl)
            return None
        self.cache.set(key, value, self.ttl)
        return value


class TwitterSource(_CachedSource):
    """Tweet counts via the v1.1 standard search API (tweepy.API.search_tweets)."""

    name = "twitter"

    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret, **kwargs):
        super().__init__(**kwargs)
        self._creds = (consumer_key, consumer_secret, access_token, access_token_secret)
        self._api = None
        self._api_lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return all(self._creds)

    def _client(self):
        with self._api_lock:
            if self._api is None:
                import tweepy

                auth = tweepy.OAuth1UserHandler(*self._creds)
                self._api = tweepy.API(
                    auth, wait_on_rate_limit=False, retry_count=0, timeout=self.timeout
                )
            return self._api

    def count(self, term: str, day: date) -> Optional[int]:
        if not self.enabled:
            return None

        def fetch():
            query = f"{term} -filter:retweets since:{day.isoformat()}"
            posts = self._client().search_tweets(
                q=query, lang="id", count=100, until=(day + timedelta(days=1)).isoformat()
            )
            return len(posts)

        return self._cached(("tweets", term.lower(), day.isoformat()), fetch)


class TrendsSource(_CachedSource):
    """Average Google Trends interest (0-100) for a keyword in Indonesia over the last 7 days."""

    name = "google-trends"

    def interest(self, term: str, today: date) -> Optional[float]:
        def fetch():
            from pytrends.request import TrendReq

            start = today - timedelta(days=7)
            client = TrendReq(hl="en-ID", tz=420, timeout=(self.timeout, self.timeout), retries=0)
            client.build_payload(kw_list=[term], timeframe=f"{start} {today}", geo="ID")
            frame = client.interest_over_time()
            if frame.empty or term not in frame:
                return 0.0
            return float(frame[term].mean())

        return self._cached(("trends", term.lower(), today.isoformat()), fetch)
