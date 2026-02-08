from __future__ import annotations

import json

from bs4 import BeautifulSoup


def extract_jsonld(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    data: list[dict] = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            payload = json.loads(script.text)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            data.extend(item for item in payload if isinstance(item, dict))
        elif isinstance(payload, dict):
            data.append(payload)
    return data
