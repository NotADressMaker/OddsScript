from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from bs4 import BeautifulSoup

from ..fetch.http_client import HttpClient


@dataclass(frozen=True)
class SitemapEntry:
    url: str
    last_modified: datetime | None


def _parse_lastmod(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def parse_sitemap(xml_text: str) -> list[SitemapEntry]:
    soup = BeautifulSoup(xml_text, "xml")
    entries: list[SitemapEntry] = []
    for url_tag in soup.find_all("url"):
        loc = url_tag.find("loc")
        lastmod = url_tag.find("lastmod")
        if loc and loc.text:
            entries.append(
                SitemapEntry(url=loc.text.strip(), last_modified=_parse_lastmod(lastmod.text))
            )
    return entries


def fetch_sitemaps(client: HttpClient, sitemap_urls: Iterable[str]) -> list[SitemapEntry]:
    entries: list[SitemapEntry] = []
    for sitemap_url in sitemap_urls:
        response = client.get(sitemap_url)
        if not response:
            continue
        entries.extend(parse_sitemap(response.text))
    return entries
