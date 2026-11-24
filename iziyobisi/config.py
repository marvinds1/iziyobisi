import os
import secrets
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

DISEASES = ("asma", "batuk", "flu", "demam", "diabetes", "hipertensi", "kulit")


def _int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value else default


def load_config() -> dict:
    return {
        "SECRET_KEY": os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        "MYSQL_HOST": os.environ.get("MYSQL_HOST", "127.0.0.1"),
        "MYSQL_PORT": _int("MYSQL_PORT", 3306),
        "MYSQL_USER": os.environ.get("MYSQL_USER", "iziyobisi"),
        "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
        "MYSQL_DB": os.environ.get("MYSQL_DB", "iziyobisi"),
        "DATA_DIR": os.environ.get("DATA_DIR", str(ROOT_DIR)),
        "ADMIN_TOKEN": os.environ.get("ADMIN_TOKEN", ""),
        "TWITTER_CONSUMER_KEY": os.environ.get("TWITTER_CONSUMER_KEY", ""),
        "TWITTER_CONSUMER_SECRET": os.environ.get("TWITTER_CONSUMER_SECRET", ""),
        "TWITTER_ACCESS_TOKEN": os.environ.get("TWITTER_ACCESS_TOKEN", ""),
        "TWITTER_ACCESS_TOKEN_SECRET": os.environ.get("TWITTER_ACCESS_TOKEN_SECRET", ""),
        "RATING_GOOGLE_SOURCE": os.environ.get("RATING_GOOGLE_SOURCE", "twitter"),
        "EXTERNAL_TIMEOUT": _int("EXTERNAL_TIMEOUT", 10),
        "SOURCE_CACHE_TTL": _int("SOURCE_CACHE_TTL", 6 * 3600),
        "SOURCE_FAILURE_TTL": _int("SOURCE_FAILURE_TTL", 300),
        "MAX_CONTENT_LENGTH": 16 * 1024,
    }
