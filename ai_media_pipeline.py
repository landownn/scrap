"""Pipeline utilities for analyzing AI coverage in The Guardian."""

from __future__ import annotations

import argparse
import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Optional

import requests

GUARDIAN_API_URL = "https://content.guardianapis.com/search"
DEFAULT_QUERY = (
    '"artificial intelligence" OR AI OR "machine learning" OR ChatGPT '
    'OR OpenAI OR "large language model" OR LLM'
)


@dataclass
class Article:
    """Represents a Guardian article with relevant metadata."""

    article_id: str
    url: str
    date: str
    section: str
    content_type: str
    title: str
    trail_text: str
    body_text: str
    tags: List[str]

    @property
    def combined_text(self) -> str:
        return " ".join(part for part in [self.title, self.trail_text, self.body_text] if part)


class GuardianAPIError(RuntimeError):
    """Raised when Guardian API requests fail."""


def fetch_guardian_articles(
    api_key: str,
    query: str = DEFAULT_QUERY,
    page_size: int = 50,
    max_pages: int = 5,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    sleep_seconds: float = 0.2,
) -> List[Article]:
    """Fetch articles from The Guardian API matching a query.

    Args:
        api_key: Guardian API key.
        query: Search query for AI topics.
        page_size: Results per page (max 200).
        max_pages: Max number of pages to fetch.
        from_date: Optional start date YYYY-MM-DD.
        to_date: Optional end date YYYY-MM-DD.
        sleep_seconds: Delay between requests to avoid rate limits.
    """

    articles: List[Article] = []
    for page in range(1, max_pages + 1):
        params = {
            "api-key": api_key,
            "q": query,
            "page-size": page_size,
            "page": page,
            "show-fields": "trailText,bodyText",
            "show-tags": "all",
        }
        if from_date:
            params["from-date"] = from_date
        if to_date:
            params["to-date"] = to_date

        response = requests.get(GUARDIAN_API_URL, params=params, timeout=30)
        if response.status_code != 200:
            raise GuardianAPIError(
                f"Guardian API error {response.status_code}: {response.text[:200]}"
            )

        payload = response.json().get("response", {})
        results = payload.get("results", [])
        if not results:
            break

        for item in results:
            fields = item.get("fields", {})
            articles.append(
                Article(
                    article_id=item.get("id", ""),
                    url=item.get("webUrl", ""),
                    date=item.get("webPublicationDate", ""),
                    section=item.get("sectionName", ""),
                    content_type=item.get("type", ""),
                    title=item.get("webTitle", ""),
                    trail_text=fields.get("trailText", ""),
                    body_text=fields.get("bodyText", ""),
                    tags=[tag.get("webTitle", "") for tag in item.get("tags", [])],
                )
            )

        time.sleep(sleep_seconds)

    return articles


def clean_text(text: str) -> str:
    """Lowercase and strip HTML, URLs, and extra whitespace."""

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.lower().strip()


def tokenize(text: str, min_len: int = 3) -> List[str]:
    """Tokenize cleaned text with a minimum token length."""

    tokens = [token for token in text.split() if len(token) >= min_len]
    return tokens


def lemmatize_tokens(tokens: Iterable[str]) -> List[str]:
    """Lemmatize tokens using spaCy if available; otherwise return original tokens."""

    try:
        import spacy  # type: ignore

        nlp = spacy.load("en_core_web_sm", disable=["ner", "parser"])
        doc = nlp(" ".join(tokens))
        return [token.lemma_.lower() for token in doc]
    except (ImportError, OSError):
        return list(tokens)


def build_ngrams(tokens: Iterable[str], n: int = 2) -> Counter:
    """Build n-gram counts from tokens."""

    token_list = list(tokens)
    ngrams = [" ".join(token_list[i : i + n]) for i in range(len(token_list) - n + 1)]
    return Counter(ngrams)


def frame_score(tokens: Iterable[str], frame_words: Iterable[str]) -> float:
    """Compute the share of frame words in the token list."""

    token_list = list(tokens)
    if not token_list:
        return 0.0
    frame_set = {word.lower() for word in frame_words}
    hits = sum(1 for token in token_list if token in frame_set)
    return hits / len(token_list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch and analyze Guardian AI articles.")
    parser.add_argument("--api-key", default=os.getenv("GUARDIAN_API_KEY"))
    parser.add_argument("--query", default=DEFAULT_QUERY)
    parser.add_argument("--page-size", type=int, default=50)
    parser.add_argument("--max-pages", type=int, default=3)
    parser.add_argument("--from-date")
    parser.add_argument("--to-date")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.api_key:
        raise SystemExit("Missing API key. Set GUARDIAN_API_KEY or --api-key.")

    articles = fetch_guardian_articles(
        api_key=args.api_key,
        query=args.query,
        page_size=args.page_size,
        max_pages=args.max_pages,
        from_date=args.from_date,
        to_date=args.to_date,
    )

    cleaned = [clean_text(article.combined_text) for article in articles]
    tokenized = [tokenize(text) for text in cleaned]
    lemmatized = [lemmatize_tokens(tokens) for tokens in tokenized]

    all_tokens = [token for doc in lemmatized for token in doc]
    top_unigrams = Counter(all_tokens).most_common(10)
    top_bigrams = build_ngrams(all_tokens, n=2).most_common(10)

    print("Top unigrams:")
    for term, count in top_unigrams:
        print(f"{term}: {count}")

    print("\nTop bigrams:")
    for term, count in top_bigrams:
        print(f"{term}: {count}")


if __name__ == "__main__":
    main()
