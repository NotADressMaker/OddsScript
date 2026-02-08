"""Parsing and extraction utilities."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup


@dataclass
class ParsedDocument:
    url: str
    title: str
    text: str
    author: Optional[str]
    published_date: Optional[str]
    tables: List[List[List[str]]] = field(default_factory=list)
    json_ld: List[Dict[str, Any]] = field(default_factory=list)


def parse_html(content: bytes, url: str) -> ParsedDocument:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    for tag in soup.find_all(attrs={"class": re.compile(r"(cookie|consent)", re.I)}):
        tag.decompose()
    for tag in soup.find_all(attrs={"id": re.compile(r"(cookie|consent)", re.I)}):
        tag.decompose()

    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    text = " ".join(soup.stripped_strings)
    author = _extract_meta(soup, ["author", "article:author"])
    published_date = _extract_meta(soup, ["article:published_time", "date", "pubdate"])
    if not published_date:
        time_tag = soup.find("time")
        if time_tag and time_tag.get("datetime"):
            published_date = time_tag["datetime"]

    tables = _extract_tables(soup)
    json_ld = _extract_json_ld(soup)

    return ParsedDocument(
        url=url,
        title=title,
        text=text,
        author=author,
        published_date=published_date,
        tables=tables,
        json_ld=json_ld,
    )


def _extract_meta(soup: BeautifulSoup, names: List[str]) -> Optional[str]:
    for name in names:
        meta = soup.find("meta", attrs={"name": name}) or soup.find(
            "meta", attrs={"property": name}
        )
        if meta and meta.get("content"):
            return meta["content"].strip()
    return None


def _extract_tables(soup: BeautifulSoup) -> List[List[List[str]]]:
    tables: List[List[List[str]]] = []
    for table in soup.find_all("table"):
        rows: List[List[str]] = []
        for row in table.find_all("tr"):
            cells = [cell.get_text(strip=True) for cell in row.find_all(["td", "th"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def _extract_json_ld(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            data.append(payload)
        elif isinstance(payload, list):
            data.extend(item for item in payload if isinstance(item, dict))
    return data


def extract_dates(text: str) -> List[str]:
    pattern = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
    return pattern.findall(text)


def is_soft_404(document: ParsedDocument) -> bool:
    title = document.title.lower()
    text = document.text.lower()
    if "404" in title or "page not found" in title or "not found" in title:
        return True
    if "not found" in text and len(document.text.split()) < 60:
        return True
    return False
