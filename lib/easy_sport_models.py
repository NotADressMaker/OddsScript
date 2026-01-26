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
