from sportsbetlang.ingestion.normalizers.entities import resolve_player_id, resolve_team_id


def test_team_id_stable():
    first = resolve_team_id("Lakers", "nba")
    second = resolve_team_id("Lakers", "nba")
    assert first == second


def test_player_id_changes_with_team():
    first = resolve_player_id("Player One", "team-a")
    second = resolve_player_id("Player One", "team-b")
    assert first != second
