from sportsbetlang.ingestion.normalizers.markets import normalize_market


def test_normalize_market_spread():
    item = {
        "event_id": "game-1",
        "book": "book-a",
        "market": "spread",
        "selection": "Team A",
        "line": "-3.5",
        "price": -110,
    }
    normalized = normalize_market(item)
    assert normalized["market"] == "spread"
    assert normalized["line"] == -3.5
    assert normalized["price"] == -110.0


def test_normalize_market_missing_price_defaults():
    item = {
        "event_id": "game-1",
        "book": "book-a",
        "market": "total",
        "selection": "over",
    }
    normalized = normalize_market(item)
    assert normalized["price"] == 0.0
