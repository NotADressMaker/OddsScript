from __future__ import annotations

from bs4 import BeautifulSoup


def extract_main_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.find("article")
    if main:
        return " ".join(main.get_text(separator=" ", strip=True).split())
    body = soup.find("body")
    if body:
        return " ".join(body.get_text(separator=" ", strip=True).split())
    return " ".join(soup.get_text(separator=" ", strip=True).split())
