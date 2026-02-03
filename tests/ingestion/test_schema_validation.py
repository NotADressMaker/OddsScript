from sportsbetlang.ingestion.schemas import registry


def test_schema_validation_basic_required():
    schema = registry.load_schema("odds_snapshot.json")
    payload = {
        "event_id": "game-1",
        "book": "book-a",
        "market": "spread",
        "selection": "Team A",
        "price": -110,
        "observed_at": "2025-10-01T00:00:00Z",
        "source": "unit-test",
    }
    ok, errors = registry.validate_basic(schema, payload)
    assert ok
    assert errors == []


def test_schema_validation_missing_required():
    schema = registry.load_schema("odds_snapshot.json")
    payload = {
        "event_id": "game-1",
        "book": "book-a",
    }
    ok, errors = registry.validate_basic(schema, payload)
    assert not ok
    assert any("Missing required field" in err for err in errors)
