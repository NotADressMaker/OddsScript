from __future__ import annotations

from bs4 import BeautifulSoup


def extract_tables(html: str) -> list[list[list[str]]]:
    soup = BeautifulSoup(html, "html.parser")
    tables: list[list[list[str]]] = []
    for table in soup.find_all("table"):
        rows: list[list[str]] = []
        for row in table.find_all("tr"):
            cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
            if cells:
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables
