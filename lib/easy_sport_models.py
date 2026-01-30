#!/usr/bin/env python3
"""
Easy Sport Models - Simplified interface for sport-specific ML models

Makes it easier to use sport models by:
- Automatic feature preparation
- Data validation
- Quick prediction functions
- End-to-end workflows
"""

from typing import List, Dict, Optional, Tuple, Union
from lib.model_builder import Model, split_data
from lib.sport_models import get_sport_model
from lib.sport_features import get_sport_features


class EasySportModel:
    """Simplified interface for sport-specific ML models"""

    def __init__(self, sport: str, model_type: str):
        """
        Create an easy-to-use sport model

        Args:
            sport: Sport name ('nba', 'nfl', 'nhl', etc.)
            model_type: Model type ('game_winner', 'spread', 'total_points', etc.)

        Example:
            >>> model = EasySportModel('nba', 'game_winner')
            >>> model.fit(games_data)
            >>> prediction = model.predict(new_game)
        """
        self.sport = sport.lower()
        self.model_type = model_type
        self.model = get_sport_model(sport, model_type)
        self.feature_class = get_sport_features(sport)
        self._is_trained = False

    def fit(self, data: List[Dict], labels: List = None):
        """
        Train model from dictionary data

        Args:
            data: List of game dictionaries with feature names as keys
            labels: Optional labels (if not included in data['result'])

        Example:
            >>> games = [
            ...     {'team_off_rtg': 112, 'team_def_rtg': 108, ...,'result': 1},
            ...     {'team_off_rtg': 110, 'team_def_rtg': 109, ...,'result': 0}
            ... ]
            >>> model.fit(games)
        """
        # Extract features in correct order
        X = []
        y = labels if labels is not None else []

        feature_names = self.model.feature_names
        if not feature_names:
            raise ValueError(f"Model {self.model_type} doesn't have feature names defined")

        for i, game in enumerate(data):
            features = []
            for feature_name in feature_names:
                if feature_name not in game:
                    raise ValueError(f"Missing feature: {feature_name} in game {i}")
                features.append(game[feature_name])
            X.append(features)

            # Get label if not provided separately
            if labels is None:
                if 'result' not in game:
                    raise ValueError(f"Missing 'result' in game {i} and no labels provided")
                y.append(game['result'])

        # Split and train
        X_train, X_test, y_train, y_test = split_data(X, y, test_size=0.2)
        self.model.train(X_train, y_train)
        self._is_trained = True

        # Store test set for later
        self._X_test = X_test
        self._y_test = y_test

        return self

    def predict(self, game: Dict) -> Union[int, float]:
        """
        Predict outcome for a single game

        Args:
            game: Game dictionary with required features

        Returns:
            Prediction (1/0 for classification, numeric for regression)

        Example:
            >>> prediction = model.predict({
            ...     'team_off_rtg': 112,
            ...     'team_def_rtg': 108,
            ...     ...
            ... })
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained. Call fit() first.")

        # Extract features in correct order
        features = []
        for feature_name in self.model.feature_names:
            if feature_name not in game:
                raise ValueError(f"Missing feature: {feature_name}")
            features.append(game[feature_name])

        prediction = self.model.predict([features])
        return prediction[0]

    def predict_proba(self, game: Dict) -> float:
        """
        Predict probability for classification models

        Args:
            game: Game dictionary with required features

        Returns:
            Probability of positive class

        Example:
            >>> prob = model.predict_proba({'team_off_rtg': 112, ...})
            >>> print(f"Win probability: {prob:.1%}")
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained. Call fit() first.")

        if self.model.task != 'classification':
            raise ValueError("predict_proba only available for classification models")

        features = []
        for feature_name in self.model.feature_names:
            if feature_name not in game:
                raise ValueError(f"Missing feature: {feature_name}")
            features.append(game[feature_name])

        proba = self.model.predict_proba([features])
        return proba[0]

    def evaluate(self) -> Dict:
        """
        Evaluate model on test set

        Returns:
            Dictionary of metrics

        Example:
            >>> metrics = model.evaluate()
            >>> print(f"Accuracy: {metrics['accuracy']:.3f}")
        """
        if not self._is_trained:
            raise RuntimeError("Model not trained. Call fit() first.")

        return self.model.evaluate(self._X_test, self._y_test)

    def summary(self):
        """Print model performance summary"""
        if not self._is_trained:
            raise RuntimeError("Model not trained. Call fit() first.")

        self.model.print_performance(self._X_test, self._y_test)

    def required_features(self) -> List[str]:
        """Get list of required features"""
        return self.model.feature_names

    def __repr__(self):
        trained = "trained" if self._is_trained else "not trained"
        return f"EasySportModel(sport='{self.sport}', model='{self.model_type}', {trained})"


# Convenience functions for quick predictions

def quick_nba_prediction(team_off_rtg: float, team_def_rtg: float,
                        opp_off_rtg: float, opp_def_rtg: float,
                        home: bool = True, rest_team: int = 2, rest_opp: int = 2,
                        pace: float = 100.0, historical_games: List[Dict] = None) -> float:
    """
    Quick NBA game winner prediction

    Args:
        team_off_rtg: Team offensive rating
        team_def_rtg: Team defensive rating
        opp_off_rtg: Opponent offensive rating
        opp_def_rtg: Opponent defensive rating
        home: True if team is home
        rest_team: Days rest for team
        rest_opp: Days rest for opponent
        pace: Expected pace
        historical_games: Historical games for training (required first time)

    Returns:
        Win probability

    Example:
        >>> prob = quick_nba_prediction(112, 108, 110, 109, home=True)
        >>> print(f"Win probability: {prob:.1%}")
    """
    if historical_games is None:
        # Use simple calculation without ML
        team_net = team_off_rtg - team_def_rtg
        opp_net = opp_off_rtg - opp_def_rtg
        diff = team_net - opp_net + (3 if home else 0)
        # Logistic function
        return 1 / (1 + 10 ** (-diff / 15))
    else:
        # Train model on historical data
        model = EasySportModel('nba', 'game_winner')
        model.fit(historical_games)

        # Predict
        game = {
            'team_offensive_rating': team_off_rtg,
            'team_defensive_rating': team_def_rtg,
            'opponent_offensive_rating': opp_off_rtg,
            'opponent_defensive_rating': opp_def_rtg,
            'home_court': 1 if home else 0,
            'rest_days_team': rest_team,
            'rest_days_opponent': rest_opp,
            'pace': pace
        }
        return model.predict_proba(game)


def quick_nfl_prediction(team_dvoa: float, opp_dvoa: float,
                        home: bool = True, temperature: float = 70,
                        wind_speed: float = 5, historical_games: List[Dict] = None) -> float:
    """
    Quick NFL game winner prediction

    Args:
        team_dvoa: Team total DVOA
        opp_dvoa: Opponent total DVOA
        home: True if team is home
        temperature: Temperature in Fahrenheit
        wind_speed: Wind speed in mph
        historical_games: Historical games for training

    Returns:
        Win probability
    """
    from lib.sport_features import NFLFeatures

    # Calculate weather factor
    weather = NFLFeatures.create_weather_factor(temperature, wind_speed, 0)

    if historical_games is None:
        # Simple calculation
        diff = team_dvoa - opp_dvoa + (2 if home else 0) - (weather * 3)
        return 1 / (1 + 10 ** (-diff / 10))
    else:
        model = EasySportModel('nfl', 'game_winner')
        model.fit(historical_games)

        game = {
            'team_offensive_dvoa': team_dvoa * 0.5,
            'team_defensive_dvoa': team_dvoa * 0.5,
            'opponent_offensive_dvoa': opp_dvoa * 0.5,
            'opponent_defensive_dvoa': opp_dvoa * 0.5,
            'home_field': 1 if home else 0,
            'weather_factor': weather,
            'rest_days_team': 7,
            'rest_days_opponent': 7
        }
        return model.predict_proba(game)


def quick_soccer_btts(team_goals_avg: float, opp_goals_avg: float,
                     team_clean_sheets: float = 0.35,
                     opp_clean_sheets: float = 0.35,
                     league_btts_rate: float = 0.50) -> float:
    """
    Quick Soccer Both Teams To Score prediction

    Args:
        team_goals_avg: Team goals per game
        opp_goals_avg: Opponent goals per game
        team_clean_sheets: Team clean sheet rate
        opp_clean_sheets: Opponent clean sheet rate
        league_btts_rate: League BTTS rate

    Returns:
        BTTS probability

    Example:
        >>> prob = quick_soccer_btts(1.8, 1.5)
        >>> print(f"BTTS probability: {prob:.1%}")
    """
    from lib.sport_features import SoccerFeatures

    return SoccerFeatures.create_btts_probability(
        team_goals_avg, 0, opp_goals_avg, 0,
        team_clean_sheets, opp_clean_sheets
    )


def quick_cbb_prediction(team_kenpom: float, opp_kenpom: float,
                        team_adj_em: float, opp_adj_em: float,
                        home: bool = True, conference: bool = False,
                        tournament: bool = False) -> float:
    """
    Quick College Basketball prediction using KenPom ratings

    Args:
        team_kenpom: Team KenPom rating
        opp_kenpom: Opponent KenPom rating
        team_adj_em: Team adjusted efficiency margin
        opp_adj_em: Opponent adjusted efficiency margin
        home: Home court advantage
        conference: Conference game
        tournament: Tournament game (March Madness)

    Returns:
        Win probability

    Example:
        >>> prob = quick_cbb_prediction(25.5, 18.2, 20.5, 15.2, home=True, tournament=True)
        >>> print(f"Win probability: {prob:.1%}")
    """
    # Calculate efficiency margin difference
    em_diff = team_adj_em - opp_adj_em

    # Home court advantage (stronger in college)
    if home:
        em_diff += 3.25  # 6.5% advantage = 3.25 point spread

    # Conference game adjustment
    if conference and abs(em_diff) > 10:
        em_diff *= 0.95  # Reduce favorite's edge

    # Tournament adjustment (upsets more common)
    if tournament and em_diff > 15:
        em_diff *= 0.90  # Big favorites perform worse

    # Convert to probability using logistic function
    import math
    prob = 1 / (1 + math.exp(-em_diff / 11))

    return max(0.05, min(0.95, prob))


def quick_cfb_prediction(team_sp: float, opp_sp: float,
                        home: bool = True, rivalry: bool = False,
                        conference: bool = False,
                        team_recruiting_rank: float = 50,
                        opp_recruiting_rank: float = 50) -> float:
    """
    Quick College Football prediction using SP+ ratings

    Args:
        team_sp: Team SP+ rating
        opp_sp: Opponent SP+ rating
        home: Home field advantage
        rivalry: Rivalry game
        conference: Conference game
        team_recruiting_rank: Team recruiting rank (1-130)
        opp_recruiting_rank: Opponent recruiting rank (1-130)

    Returns:
        Win probability

    Example:
        >>> prob = quick_cfb_prediction(18.5, 12.3, home=True, rivalry=True)
        >>> print(f"Win probability: {prob:.1%}")
    """
    # Calculate SP+ difference
    sp_diff = team_sp - opp_sp

    # Home field advantage (stronger in college)
    if home:
        sp_diff += 4.0  # 8% advantage = 4 point spread

    # Rivalry game adjustment
    if rivalry and sp_diff > 15:
        sp_diff *= 0.85  # Favorites perform worse

    # Conference game adjustment
    if conference and abs(sp_diff) > 20:
        sp_diff *= 0.93

    # Talent/recruiting adjustment
    recruiting_diff = opp_recruiting_rank - team_recruiting_rank
    sp_diff += recruiting_diff / 50  # Subtle effect

    # Convert to probability
    import math
    prob = 1 / (1 + math.exp(-sp_diff / 13))

    return max(0.05, min(0.95, prob))


def quick_wnba_prediction(team_off_rtg: float, team_def_rtg: float,
                         opp_off_rtg: float, opp_def_rtg: float,
                         home: bool = True,
                         rest_days_team: int = 2,
                         rest_days_opp: int = 2) -> float:
    """
    Quick WNBA prediction

    Args:
        team_off_rtg: Team offensive rating
        team_def_rtg: Team defensive rating
        opp_off_rtg: Opponent offensive rating
        opp_def_rtg: Opponent defensive rating
        home: Home court advantage
        rest_days_team: Team rest days
        rest_days_opp: Opponent rest days

    Returns:
        Win probability

    Example:
        >>> prob = quick_wnba_prediction(105, 100, 102, 101, home=True, rest_days_team=3, rest_days_opp=1)
        >>> print(f"Win probability: {prob:.1%}")
    """
    from lib.wnba_analytics import WNBAAnalytics

    return WNBAAnalytics.calculate_moneyline_probability(
        team_off_rtg,
        team_def_rtg,
        opp_off_rtg,
        opp_def_rtg,
        home,
        rest_days_team,
        rest_days_opp
    )


def quick_nhl_prediction(team_xg_for: float, team_xg_against: float,
                        opp_xg_for: float, opp_xg_against: float,
                        home: bool = True,
                        home_advantage: float = 0.25,
                        team_goalie_gsax: float = 0.0,
                        opp_goalie_gsax: float = 0.0,
                        include_overtime: bool = True) -> float:
    """
    Quick NHL prediction using Expected Goals (xG)

    Args:
        team_xg_for: Team expected goals for per game
        team_xg_against: Team expected goals against per game
        opp_xg_for: Opponent expected goals for per game
        opp_xg_against: Opponent expected goals against per game
        home: Home ice advantage
        home_advantage: Goals to add for home ice (default 0.25)
        team_goalie_gsax: Team goalie goals saved above expected
        opp_goalie_gsax: Opponent goalie goals saved above expected
        include_overtime: Whether to split regulation draws into OT

    Returns:
        Win probability

    Example:
        >>> prob = quick_nhl_prediction(3.2, 2.8, 2.9, 3.0, home=True)
        >>> print(f"Win probability: {prob:.1%}")
    """
    from lib.nhl_analytics import NHLAdvancedAnalytics

    # Blend team offense with opponent defense for expected scoring
    expected_team_xg = (team_xg_for + opp_xg_against) / 2.0
    expected_opp_xg = (opp_xg_for + team_xg_against) / 2.0

    # Apply home ice advantage to the home team expected goals
    if home:
        expected_team_xg += home_advantage
    else:
        expected_opp_xg += home_advantage

    # Clamp to avoid extreme values on small samples
    expected_team_xg = max(0.25, min(expected_team_xg, 5.5))
    expected_opp_xg = max(0.25, min(expected_opp_xg, 5.5))

    home_xg = expected_team_xg if home else expected_opp_xg
    away_xg = expected_opp_xg if home else expected_team_xg
    home_gsax = team_goalie_gsax if home else opp_goalie_gsax
    away_gsax = opp_goalie_gsax if home else team_goalie_gsax

    home_xg, away_xg = NHLAdvancedAnalytics.adjust_for_goalies(
        home_xg=home_xg,
        away_xg=away_xg,
        home_gsax=home_gsax,
        away_gsax=away_gsax,
    )

    result = NHLAdvancedAnalytics.predict_game_from_xg(
        home_xg=home_xg,
        away_xg=away_xg,
        include_overtime=include_overtime,
    )

    return float(result["home_win_probability"] if home else result["away_win_probability"])


def quick_mlb_prediction(team_rating: float, opp_rating: float,
                        home: bool = True,
                        park_factor: float = 1.0) -> float:
    """
    Quick MLB prediction with park factors

    Args:
        team_rating: Team rating (Elo, power rating, etc.)
        opp_rating: Opponent rating
        home: Home field advantage
        park_factor: Park factor (1.0 = neutral, >1.0 = hitter-friendly)

    Returns:
        Win probability

    Example:
        >>> prob = quick_mlb_prediction(1550, 1500, home=True, park_factor=1.05)
        >>> print(f"Win probability: {prob:.1%}")
    """
    rating_diff = team_rating - opp_rating

    # Home advantage
    if home:
        rating_diff += 25  # 5% advantage

    # Park effect (subtle)
    park_effect = (park_factor - 1.0) * 15
    rating_diff += park_effect

    # Convert to probability
    import math
    prob = 1 / (1 + 10 ** (-rating_diff / 400))  # Elo-style

    return max(0.1, min(0.9, prob))


# Data validation helpers

def validate_nba_data(games: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate NBA game data

    Args:
        games: List of game dictionaries

    Returns:
        (is_valid, list_of_errors)

    Example:
        >>> valid, errors = validate_nba_data(games)
        >>> if not valid:
        ...     print("Errors:", errors)
    """
    required_features = [
        'team_offensive_rating', 'team_defensive_rating',
        'opponent_offensive_rating', 'opponent_defensive_rating',
        'home_court', 'rest_days_team', 'rest_days_opponent', 'pace'
    ]

    errors = []

    for i, game in enumerate(games):
        for feature in required_features:
            if feature not in game:
                errors.append(f"Game {i}: Missing '{feature}'")

        # Validate ranges
        if 'home_court' in game and game['home_court'] not in [0, 1]:
            errors.append(f"Game {i}: 'home_court' must be 0 or 1")

        if 'pace' in game and not (80 <= game['pace'] <= 110):
            errors.append(f"Game {i}: 'pace' {game['pace']} seems unusual (expected 80-110)")

    return len(errors) == 0, errors


def validate_sport_data(sport: str, model_type: str, games: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate data for any sport model

    Args:
        sport: Sport name
        model_type: Model type
        games: List of game dictionaries

    Returns:
        (is_valid, list_of_errors)
    """
    model = get_sport_model(sport, model_type)
    required_features = model.feature_names

    if not required_features:
        return True, []

    errors = []

    for i, game in enumerate(games):
        for feature in required_features:
            if feature not in game:
                errors.append(f"Game {i}: Missing '{feature}'")

    return len(errors) == 0, errors


# End-to-end workflow helper

def train_and_predict(sport: str, model_type: str,
                     historical_games: List[Dict],
                     new_games: List[Dict],
                     show_performance: bool = True) -> List[Union[int, float]]:
    """
    Complete workflow: train model and make predictions

    Args:
        sport: Sport name
        model_type: Model type
        historical_games: Historical games for training
        new_games: New games to predict
        show_performance: Whether to print performance metrics

    Returns:
        List of predictions

    Example:
        >>> predictions = train_and_predict(
        ...     'nba', 'game_winner',
        ...     historical_games=past_games,
        ...     new_games=upcoming_games
        ... )
    """
    # Validate data
    valid, errors = validate_sport_data(sport, model_type, historical_games)
    if not valid:
        raise ValueError(f"Data validation failed:\n" + "\n".join(errors[:5]))

    # Train model
    model = EasySportModel(sport, model_type)
    model.fit(historical_games)

    # Show performance
    if show_performance:
        print(f"\n{sport.upper()} {model_type} Model Performance:")
        print("=" * 60)
        metrics = model.evaluate()

        if 'accuracy' in metrics:
            print(f"Accuracy:  {metrics['accuracy']:.3f}")
            print(f"Precision: {metrics['precision']:.3f}")
            print(f"Recall:    {metrics['recall']:.3f}")
        else:
            print(f"R²:   {metrics['r_squared']:.3f}")
            print(f"RMSE: {metrics['rmse']:.3f}")
        print("=" * 60)
        print()

    # Make predictions
    predictions = []
    for game in new_games:
        pred = model.predict(game)
        predictions.append(pred)

    return predictions


# Auto-feature creation helper

class AutoFeatures:
    """Automatically create sport-specific features from basic data"""

    @staticmethod
    def nba_game_features(team_stats: Dict, opp_stats: Dict,
                         game_info: Dict) -> Dict:
        """
        Create NBA game features from team stats

        Args:
            team_stats: {'off_rtg': 112, 'def_rtg': 108, 'pace': 100, 'rest_days': 2}
            opp_stats: {'off_rtg': 110, 'def_rtg': 109, 'pace': 98, 'rest_days': 1}
            game_info: {'home': True}

        Returns:
            Dictionary of features ready for model
        """
        return {
            'team_offensive_rating': team_stats['off_rtg'],
            'team_defensive_rating': team_stats['def_rtg'],
            'opponent_offensive_rating': opp_stats['off_rtg'],
            'opponent_defensive_rating': opp_stats['def_rtg'],
            'home_court': 1 if game_info.get('home', False) else 0,
            'rest_days_team': team_stats.get('rest_days', 2),
            'rest_days_opponent': opp_stats.get('rest_days', 2),
            'pace': (team_stats['pace'] + opp_stats['pace']) / 2
        }

    @staticmethod
    def nfl_game_features(team_stats: Dict, opp_stats: Dict,
                         game_info: Dict) -> Dict:
        """
        Create NFL game features from team stats

        Args:
            team_stats: {'off_dvoa': 12, 'def_dvoa': -8}
            opp_stats: {'off_dvoa': 5, 'def_dvoa': -3}
            game_info: {'home': True, 'temp': 45, 'wind': 15}

        Returns:
            Dictionary of features ready for model
        """
        from lib.sport_features import NFLFeatures

        weather = NFLFeatures.create_weather_factor(
            game_info.get('temp', 70),
            game_info.get('wind', 5),
            game_info.get('precipitation', 0)
        )

        return {
            'team_offensive_dvoa': team_stats['off_dvoa'],
            'team_defensive_dvoa': team_stats['def_dvoa'],
            'opponent_offensive_dvoa': opp_stats['off_dvoa'],
            'opponent_defensive_dvoa': opp_stats['def_dvoa'],
            'home_field': 1 if game_info.get('home', False) else 0,
            'weather_factor': weather,
            'rest_days_team': game_info.get('rest_team', 7),
            'rest_days_opponent': game_info.get('rest_opp', 7)
        }

    @staticmethod
    def soccer_game_features(team_stats: Dict, opp_stats: Dict,
                            game_info: Dict, model_type: str = 'btts') -> Dict:
        """
        Create Soccer game features from team stats

        Args:
            team_stats: {'gf_avg': 1.8, 'ga_avg': 1.2, 'clean_sheet_pct': 0.35}
            opp_stats: {'gf_avg': 1.5, 'ga_avg': 1.3, 'clean_sheet_pct': 0.40}
            game_info: {'home': True, 'league': 'epl'}
            model_type: 'btts', 'total_goals', or 'three_way_result'

        Returns:
            Dictionary of features ready for model
        """
        if model_type == 'btts':
            return {
                'team_goals_for_avg': team_stats['gf_avg'],
                'opponent_goals_for_avg': opp_stats['gf_avg'],
                'team_clean_sheet_pct': team_stats['clean_sheet_pct'],
                'opponent_clean_sheet_pct': opp_stats['clean_sheet_pct'],
                'league_btts_frequency': 0.50  # Default
            }
        elif model_type == 'total_goals':
            return {
                'team_goals_for_avg': team_stats['gf_avg'],
                'opponent_goals_for_avg': opp_stats['gf_avg'],
                'team_expected_goals_avg': team_stats.get('xg_avg', team_stats['gf_avg']),
                'opponent_expected_goals_avg': opp_stats.get('xg_avg', opp_stats['gf_avg']),
                'league_avg_goals': 2.7  # Default
            }

        return {}
