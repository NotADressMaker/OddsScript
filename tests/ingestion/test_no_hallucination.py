from sportsbetlang.ingestion.extractors.injury_extractor import extract_injuries


def test_no_hallucination_for_unknown_text():
    raw = "Team update: roster changes announced tomorrow."
    result = extract_injuries(raw, observed_at="2025-10-01T00:00:00Z", source="unit-test")
    assert result.records == []
    assert result.data_gaps
