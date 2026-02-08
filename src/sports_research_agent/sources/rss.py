from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from bs4 import BeautifulSoup

from ..fetch.http_client import HttpClient


@dataclass(frozen=True)
class FeedEntry:
    title: str
    url: str
    published_at: datetime | None


def _parse_pub_date(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def parse_feed(xml_text: str) -> list[FeedEntry]:
    soup = BeautifulSoup(xml_text, "xml")
    entries: list[FeedEntry] = []
    for item in soup.find_all(["item", "entry"]):
        title_tag = item.find("title")
        link_tag = item.find("link")
        link = link_tag.get("href") if link_tag else None
        if not link and link_tag:
            link = link_tag.text
        pub_tag = item.find(["pubDate", "published", "updated"])
        if title_tag and link:
            entries.append(
                FeedEntry(
                    title=title_tag.text.strip(),
                    url=link.strip(),
                    published_at=_parse_pub_date(pub_tag.text if pub_tag else None),
                )
            )
    return entries


def fetch_feeds(client: HttpClient, feed_urls: Iterable[str]) -> list[FeedEntry]:
    entries: list[FeedEntry] = []
    for feed_url in feed_urls:
        response = client.get(feed_url)
        if not response:
            continue
        entries.extend(parse_feed(response.text))
    return entries
