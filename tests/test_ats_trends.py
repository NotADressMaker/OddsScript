from sportsbetlang.analytics import (
    ATSGameResult,
    calculate_ats_record,
    current_ats_streak,
    find_relevant_ats_trends,
)


def _game(
    spread: float,
    team_score: int,
    opponent_score: int,
    *,
    is_home: bool,
    was_favorite: bool,
) -> ATSGameResult:
    return ATSGameResult(
        team="BOS",
        opponent="NYK",
        sport="nba",
        is_home=is_home,
        was_favorite=was_favorite,
        spread=spread,
        team_score=team_score,
        opponent_score=opponent_score,
    )


def test_calculate_ats_record_counts_wins_losses_and_pushes() -> None:
    games = [
        _game(-4.5, 110, 100, is_home=True, was_favorite=True),   # cover
        _game(-3.0, 102, 99, is_home=False, was_favorite=True),  # push
        _game(+3.5, 97, 102, is_home=False, was_favorite=False),  # loss
    ]

    record = calculate_ats_record(games)

    assert record.wins == 1
    assert record.losses == 1
    assert record.pushes == 1
    assert record.games == 3
    assert record.cover_rate == 0.5


def test_current_ats_streak_skips_pushes() -> None:
    games = [
        _game(-2.5, 98, 100, is_home=False, was_favorite=True),   # loss
        _game(-3.0, 101, 101, is_home=True, was_favorite=True),   # push
        _game(+4.0, 106, 101, is_home=False, was_favorite=False), # win
        _game(+2.5, 107, 102, is_home=True, was_favorite=False),  # win
    ]

    streak_type, streak_length = current_ats_streak(games)

    assert streak_type == "covers"
    assert streak_length == 2


def test_find_relevant_ats_trends_identifies_home_and_favorite_edges() -> None:
    # 8 games: team covers 6/8 overall and 5/6 at home.
    games = [
        _game(-3.5, 108, 100, is_home=True, was_favorite=True),
        _game(-4.5, 112, 101, is_home=True, was_favorite=True),
        _game(+2.5, 104, 99, is_home=True, was_favorite=False),
        _game(-2.5, 105, 100, is_home=True, was_favorite=True),
        _game(+1.5, 98, 102, is_home=True, was_favorite=False),
        _game(-5.5, 115, 108, is_home=True, was_favorite=True),
        _game(-1.5, 99, 102, is_home=False, was_favorite=True),
        _game(+3.5, 101, 99, is_home=False, was_favorite=False),
    ]

    insights = find_relevant_ats_trends(games, min_games=5)
    by_title = {insight.title: insight for insight in insights}

    assert "Overall ATS" in by_title
    assert by_title["Overall ATS"].record.wins == 6
    assert by_title["Overall ATS"].strength == "strong"

    assert "Home ATS" in by_title
    assert by_title["Home ATS"].record.wins == 5


def test_find_relevant_ats_trends_validates_thresholds() -> None:
    try:
        find_relevant_ats_trends([], min_games=0)
    except ValueError as exc:
        assert "min_games" in str(exc)
    else:
        raise AssertionError("Expected ValueError for min_games=0")

    try:
        find_relevant_ats_trends([], moderate_cover_rate=0.7, strong_cover_rate=0.6)
    except ValueError as exc:
        assert "thresholds" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid thresholds")
